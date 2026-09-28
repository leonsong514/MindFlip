# IPC 契约

迭代 01 任务 3 在此放置 `health/check` 请求、成功/失败响应的单一契约来源及示例。类型和运行时实现分别位于桌面与后端工程；本目录不包含任何进程实现。

## 文件

- `schemas/health.schema.json` 健康请求/成功响应/失败响应的 JSON Schema
- `examples/health.request.json` 请求样例
- `examples/health.success.json` 成功响应样例
- `examples/health.error.json` 失败响应样例（错误码 `backend_unavailable`）
- `protocol.md` 协议说明（envelope、错误码、版本约定）
