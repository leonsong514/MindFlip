import { HealthPanel } from "@/features/health/HealthPanel";

export function App() {
  return (
    <main className="shell">
      <h1 className="brand">MindFlip</h1>
      <p className="tagline">
        本地优先、模型无关的 AI 决策辅助桌面应用。下方健康面板用于验证 React →
        Tauri → Python 端到端链路。
      </p>
      <HealthPanel />
    </main>
  );
}
