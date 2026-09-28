mod health;

use std::path::PathBuf;

use tauri::Manager;

use crate::health::{health_check, HealthResponse};

#[tauri::command]
async fn health_check_command(app: tauri::AppHandle) -> HealthResponse {
    let cwd = backend_cwd(&app);
    let python = python_executable();
    tauri::async_runtime::spawn_blocking(move || health_check(&python, &cwd))
        .await
        .unwrap_or_else(|error| HealthResponse::Err {
            code: "backend_unavailable".into(),
            message: format!("health worker failed: {error}"),
        })
}

fn python_executable() -> String {
    std::env::var("MINDFLIP_PYTHON").unwrap_or_else(|_| "python".to_string())
}

fn backend_cwd(app: &tauri::AppHandle) -> PathBuf {
    if let Ok(value) = std::env::var("MINDFLIP_BACKEND_CWD") {
        return PathBuf::from(value);
    }
    if cfg!(debug_assertions) {
        let candidate = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("backend");
        if candidate.join("app").is_dir() {
            return candidate;
        }
    }
    if let Ok(resource) = app.path().resource_dir() {
        let candidate = resource.join("backend");
        if candidate.join("app").is_dir() {
            return candidate;
        }
    }
    PathBuf::from("__mindflip_backend_missing__")
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![health_check_command])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
