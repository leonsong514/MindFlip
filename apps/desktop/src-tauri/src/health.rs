use std::io::{Read, Write};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};
use thiserror::Error;
use uuid::Uuid;

pub const PROTOCOL_VERSION: u32 = 1;
pub const DEFAULT_TIMEOUT: Duration = Duration::from_secs(3);

#[derive(Debug, Error)]
pub enum HealthError {
    #[error("backend_unavailable: {0}")]
    BackendUnavailable(String),
    #[error("timeout after {0:?}")]
    Timeout(Duration),
    #[error("invalid_protocol: {0}")]
    InvalidProtocol(String),
}

impl HealthError {
    pub fn code(&self) -> &'static str {
        match self {
            HealthError::BackendUnavailable(_) => "backend_unavailable",
            HealthError::Timeout(_) => "timeout",
            HealthError::InvalidProtocol(_) => "invalid_protocol",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResult {
    pub status: String,
    pub version: String,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum HealthResponse {
    Ok(HealthResult),
    Err { code: String, message: String },
}

#[derive(Debug, Serialize)]
struct Request<'a> {
    protocol_version: u32,
    request_id: &'a str,
    method: &'a str,
    params: serde_json::Value,
}

#[derive(Debug, Deserialize)]
struct Response {
    protocol_version: u32,
    #[serde(default)]
    request_id: String,
    #[serde(default)]
    ok: bool,
    #[serde(default)]
    result: Option<HealthResult>,
    #[serde(default)]
    error: Option<ErrorBody>,
}

#[derive(Debug, Deserialize)]
struct ErrorBody {
    code: String,
    message: String,
}

pub fn health_check(python: &str, cwd: &std::path::Path) -> HealthResponse {
    match health_check_inner(python, cwd, DEFAULT_TIMEOUT) {
        Ok(result) => HealthResponse::Ok(result),
        Err(err) => HealthResponse::Err {
            code: err.code().to_string(),
            message: err.to_string(),
        },
    }
}

fn health_check_inner(
    python: &str,
    cwd: &std::path::Path,
    timeout: Duration,
) -> Result<HealthResult, HealthError> {
    let request_id = Uuid::new_v4().to_string();
    let payload = serde_json::to_string(&Request {
        protocol_version: PROTOCOL_VERSION,
        request_id: &request_id,
        method: "health/check",
        params: serde_json::Value::Object(Default::default()),
    })
    .map_err(|e| HealthError::InvalidProtocol(format!("build request: {e}")))?;

    let mut child = Command::new(python)
        .arg("-m")
        .arg("app.ipc_main")
        .current_dir(cwd)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| HealthError::BackendUnavailable(format!("spawn failed: {e}")))?;

    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| HealthError::BackendUnavailable("no stdin".into()))?;
    stdin
        .write_all(payload.as_bytes())
        .map_err(|e| HealthError::BackendUnavailable(format!("write stdin: {e}")))?;
    stdin
        .write_all(b"\n")
        .map_err(|e| HealthError::BackendUnavailable(format!("write newline: {e}")))?;
    drop(stdin);

    let mut stdout = child
        .stdout
        .take()
        .ok_or_else(|| HealthError::BackendUnavailable("no stdout".into()))?;

    let shared: Arc<Mutex<Option<String>>> = Arc::new(Mutex::new(None));
    let shared_for_reader = Arc::clone(&shared);
    let reader = std::thread::spawn(move || {
        let mut buf = String::new();
        let stream = stdout.by_ref();
        let _ = stream.read_to_string(&mut buf);
        if let Ok(mut slot) = shared_for_reader.lock() {
            *slot = Some(buf);
        }
    });

    let deadline = Instant::now() + timeout;
    let timed_out = loop {
        if Instant::now() >= deadline {
            break true;
        }
        if let Ok(slot) = shared.lock() {
            if slot.is_some() {
                break false;
            }
        }
        std::thread::sleep(Duration::from_millis(20));
    };

    if timed_out {
        let _ = child.kill();
        let _ = child.wait();
        return Err(HealthError::Timeout(timeout));
    }

    let _ = child.wait();
    let _ = reader.join();

    let buf = shared
        .lock()
        .ok()
        .and_then(|guard| guard.clone())
        .unwrap_or_default();
    parse_response(&buf, &request_id)
}

fn parse_response(buf: &str, expected_request_id: &str) -> Result<HealthResult, HealthError> {
    let trimmed = buf.trim_end_matches(['\n', '\r']);
    if trimmed.is_empty() {
        return Err(HealthError::BackendUnavailable(
            "python runtime closed stdout without a response".into(),
        ));
    }
    let response: Response = serde_json::from_str(trimmed)
        .map_err(|e| HealthError::InvalidProtocol(format!("parse response: {e}")))?;
    if response.protocol_version != PROTOCOL_VERSION {
        return Err(HealthError::InvalidProtocol(format!(
            "unsupported protocol_version: {}",
            response.protocol_version
        )));
    }
    if response.request_id != expected_request_id {
        return Err(HealthError::InvalidProtocol(format!(
            "request_id mismatch: got {}, expected {}",
            response.request_id, expected_request_id
        )));
    }
    if !response.ok {
        let code = response
            .error
            .as_ref()
            .map(|e| e.code.clone())
            .unwrap_or_else(|| "invalid_protocol".to_string());
        let message = response
            .error
            .as_ref()
            .map(|e| e.message.clone())
            .unwrap_or_else(|| "runtime reported failure".to_string());
        return Err(HealthError::InvalidProtocol(format!("{code}: {message}")));
    }
    response
        .result
        .ok_or_else(|| HealthError::InvalidProtocol("missing result".into()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn repo_root() -> std::path::PathBuf {
        let manifest = std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR");
        std::path::PathBuf::from(manifest)
            .parent()
            .and_then(|p| p.parent())
            .and_then(|p| p.parent())
            .map(|p| p.join("apps").join("backend"))
            .expect("repo layout: <repo>/apps/backend")
    }

    fn python() -> String {
        std::env::var("MINDFLIP_PYTHON").unwrap_or_else(|_| "python".to_string())
    }

    #[test]
    fn health_check_returns_ok() {
        let cwd = repo_root();
        let response = health_check(&python(), &cwd);
        match response {
            HealthResponse::Ok(result) => {
                assert_eq!(result.status, "ok");
                assert!(!result.version.is_empty());
            }
            HealthResponse::Err { code, message } => {
                panic!("expected ok, got {code}: {message}")
            }
        }
    }

    #[test]
    fn parse_response_rejects_mismatched_request_id() {
        let err = parse_response(
            r#"{"protocol_version":1,"request_id":"different","ok":true,"result":{"status":"ok","version":"x","timestamp":"t"}}"#,
            "expected-id",
        )
        .unwrap_err();
        assert!(matches!(err, HealthError::InvalidProtocol(_)));
    }

    #[test]
    fn parse_response_rejects_unsupported_version() {
        let err = parse_response(
            r#"{"protocol_version":2,"request_id":"r","ok":true,"result":{"status":"ok","version":"x","timestamp":"t"}}"#,
            "r",
        )
        .unwrap_err();
        assert!(matches!(err, HealthError::InvalidProtocol(_)));
    }

    #[test]
    fn parse_response_reports_runtime_error() {
        let err = parse_response(
            r#"{"protocol_version":1,"request_id":"r","ok":false,"error":{"code":"unknown_method","message":"x"}}"#,
            "r",
        )
        .unwrap_err();
        assert!(matches!(err, HealthError::InvalidProtocol(_)));
    }
}
