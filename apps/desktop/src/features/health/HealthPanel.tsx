import { useCallback, useState } from "react";
import { checkHealth } from "@/api/health";
import type { HealthResponse } from "@/api/types";
import styles from "./HealthPanel.module.css";

type Status = "idle" | "loading" | "ok" | "error";

interface View {
  status: Status;
  data?: HealthResponse;
  error?: string;
}

const initial: View = { status: "idle" };

export function HealthPanel() {
  const [view, setView] = useState<View>(initial);

  const run = useCallback(async () => {
    setView({ status: "loading" });
    try {
      const response = await checkHealth();
      if (response.kind === "ok") {
        setView({ status: "ok", data: response });
      } else {
        setView({
          status: "error",
          data: response,
          error: `${response.code}: ${response.message}`,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setView({ status: "error", error: message });
    }
  }, []);

  const indicator = view.status;

  return (
    <section className={styles.card} aria-live="polite">
      <div className={styles.row}>
        <span
          className={`${styles.status} ${styles[indicator]}`}
          aria-hidden="true"
        />
        <span className={styles.label}>Python Agent Runtime</span>
      </div>

      {indicator === "idle" && (
        <p className={styles.label}>尚未检查。点击下方按钮触发一次健康探针。</p>
      )}

      {indicator === "loading" && (
        <p className={styles.label}>正在请求健康状态…</p>
      )}

      {indicator === "ok" && view.data?.kind === "ok" && (
        <pre className={styles.payload}>
          {JSON.stringify(view.data.result, null, 2)}
        </pre>
      )}

      {indicator === "error" && (
        <p className={styles.payload} role="alert">
          {view.error}
        </p>
      )}

      <div className={styles.actions}>
        <button type="button" onClick={run} disabled={indicator === "loading"}>
          {indicator === "error" ? "重试" : "检查健康状态"}
        </button>
      </div>
    </section>
  );
}
