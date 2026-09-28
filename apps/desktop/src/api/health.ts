// Typed wrapper around the Tauri `health_check` command.
//
// Feature components must import from this module only. They must
// not import from `@tauri-apps/api/core` or know about IPC shapes.

import { invoke } from "@tauri-apps/api/core";
import type { HealthResponse } from "./types";

export async function checkHealth(): Promise<HealthResponse> {
  return invoke<HealthResponse>("health_check_command");
}
