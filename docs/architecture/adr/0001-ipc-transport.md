# ADR-IPC-001：Python Agent Runtime 与 Tauri Host 之间的 IPC 传输选型

- 状态：Accepted
- 日期：2026-09-29（Proposed 同日转 Accepted）
- 适用范围：迭代 01 任务 3（React → Tauri → Python 健康链路）以及后续迭代中沿用同一通道的 IPC 方法

## 背景

架构基线要求 React 前端只通过 Tauri 调用 Python Agent Runtime，Rust 不承载决策或 Agent 逻辑。在 Windows 桌面上，Tauri 与一个独立 Python 进程之间需要一条稳定、低复杂度、不依赖额外网络配置的本地通信通道。文档建议“评估逐行 JSON 的 stdio 通道；若使用 loopback HTTP，须记录端口发现、访问控制、超时、退出回收”。

## 决定

采用 **逐行 JSON 的 stdio 通道** 作为 Tauri ↔ Python 的 IPC 传输方式。

外层消息采用统一信封：

```json
{"protocol_version":1,"request_id":"r-001","method":"health/check","params":{}}
```

成功响应回传相同 `request_id`：

```json
{"protocol_version":1,"request_id":"r-001","ok":true,"result":{"status":"ok"}}
```

失败响应通过稳定错误码区分 `backend_unavailable`、`timeout`、`invalid_protocol`、`unknown_method`。

完整契约定义见 `packages/contracts/protocol.md` 与 `packages/contracts/schemas/`。

## 选择理由

- 不需要端口分配、ACL、防火墙规则，Windows 上无网络配置开销
- 与 Tauri 2 的子进程模型天然契合，stdout/stdin 句柄可直接读写
- 进程生命周期由 Tauri 接管：崩溃、超时、未响应都可统一映射为错误码，前端不必处理网络异常语义
- 与文档的优选建议一致
- 后续 `decision.*`、`agent.*` 等业务方法可直接复用同一信封，无需引入第二套传输

## 主要后果

- Python 进程的 stdout 必须只输出协议消息；诊断输出统一写到 stderr
- Rust 端封装一条 `health_check_command` Tauri command 负责读一行、解析、超时控制、进程异常映射与回收
- 前端只调用 `apps/desktop/src/api` 中的 typed invoke 包装，不直接接触 IPC 细节
- 协议版本号 `protocol_version` 写入契约，未来不兼容变更必须升版本

## 替代方案与未选理由

- **loopback HTTP**：需要端口发现、ACL、超时与退出回收；本迭代内引入会偏离“最小可验证骨架”目标。若后续业务需要长连接流式输出，再单独评估。
- **命名管道 / Unix domain socket 跨平台抽象**：Windows 上同样可行，但 stdio 已能满足健康链路与未来请求/响应，且实现成本更低。

## 验收记录

下列三条在同一会话中通过：

1. 任务 3 契约集成测试通过：`python -m pytest tests -q` 退出码 0，复核为 23 passed、1 skipped（含 11 个 IPC 测试与 3 个 stdio 子进程往返）
2. Tauri 生产构建成功：`npm run tauri -- build`（`apps/desktop`）退出码 0，生成 MSI 与 NSIS 包；后端源码作为资源进入安装包
3. Windows 桌面上 Python 进程经 stdout 协议往返可复现：`cargo test --release --lib health::tests::health_check_returns_ok` 退出码 0，4 passed（含真实 Rust → Python 子进程往返）

桌面模式下的窗口启动与可视验证由人工按迭代 01 测试与验收手册 T01/T03 执行，不在本 ADR 的自动化验收范围。
