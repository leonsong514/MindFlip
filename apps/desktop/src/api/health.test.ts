import { describe, expect, it, vi } from "vitest";
import type { HealthResponse } from "@/api/types";
import { checkHealth } from "@/api/health";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

import { invoke } from "@tauri-apps/api/core";

const invokeMock = vi.mocked(invoke);

describe("checkHealth", () => {
  it("returns the typed payload from the Tauri command", async () => {
    const payload: HealthResponse = {
      kind: "ok",
      result: {
        status: "ok",
        version: "0.1.0",
        timestamp: "2026-09-30T00:00:00+00:00",
      },
    };
    invokeMock.mockResolvedValueOnce(payload);

    const result = await checkHealth();

    expect(invokeMock).toHaveBeenCalledWith("health_check_command");
    expect(result).toEqual(payload);
  });

  it("propagates typed error responses from the backend", async () => {
    const payload: HealthResponse = {
      kind: "err",
      code: "backend_unavailable",
      message: "python runtime did not respond",
    };
    invokeMock.mockResolvedValueOnce(payload);

    const result = await checkHealth();

    expect(result.kind).toBe("err");
    if (result.kind === "err") {
      expect(result.code).toBe("backend_unavailable");
      expect(result.message).toContain("python");
    }
  });
});
