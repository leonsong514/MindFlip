// Shared IPC contract types. These mirror the JSON Schemas in
// packages/contracts and the request/response shapes implemented by
// apps/desktop/src-tauri/src/health.rs and apps/backend/app/api/ipc.py.
// Do not add ad-hoc fields here.

export const PROTOCOL_VERSION = 1 as const;

export type ErrorCode =
  "backend_unavailable" | "timeout" | "invalid_protocol" | "unknown_method";

export interface HealthResult {
  status: "ok";
  version: string;
  timestamp: string;
}

export type HealthResponse =
  | { kind: "ok"; result: HealthResult }
  | { kind: "err"; code: ErrorCode; message: string };
