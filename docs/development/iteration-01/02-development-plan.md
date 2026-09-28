# 迭代 01：四项任务开发计划

## 来源与边界

按用户提供的 GitHub Project 前四项正文和顺序整理。Project 页面当时在未登录浏览器中返回 404，下面的中文任务名是 Goal 概括，验收内容来自用户提供的原文。架构依据为根目录《Architecture Design Document v1.0.md》第 4、27、29、31～34、42、50～51 节。**本迭代已实现并完成自动化检查；安装后窗口可运行由用户口头确认。** 实际验证和未覆盖项见 [复核记录](04-verification.md)。以下保留开发规格，供下一迭代理解已确立的边界。

| 顺序 | 任务 | 必须完成 |
| --- | --- | --- |
| 1 | Windows 桌面壳 | Tauri 2/React/TypeScript/Vite 开发启动、React 渲染、生产构建并启动 |
| 2 | 独立 Python 运行时 | 独立启动、确定性健康响应、健康单元测试 |
| 3 | React → Tauri → Python 健康链路 | 成功展示、不可用与超时受控、契约集成测试 |
| 4 | SQLite 持久化 | 应用数据目录、迁移、重启保留数据、持久化集成测试 |

本轮没有实现 Agent、模型提供商、工具、决策 CRUD、正式 Dashboard 或 CI 流水线。工程按 [目录规划](01-repository-layout.md) 创建实际需要的文件，没有为未来模块写空实现。为了验证生产构建，已生成本机 MSI 与 NSIS 产物；签名和正式发布不属于本轮。

## 共用约定

- Windows 是本轮验收平台。README 记录实际 Node、Rust、Python 版本、依赖锁文件及完整命令；所有测试无需模型密钥。
- React 只调用 `src/api` 中的 typed Tauri command 包装；Tauri 负责桌面生命周期和进程/IPC；Python API 负责服务和持久化。Rust 不承载决策或 Agent 逻辑。
- Python 可独立启动。桌面模式由 Tauri 管理每次健康请求的 Python 子进程。实际选型为逐行 JSON 的 stdio 通道，见 [ADR-IPC-001](../../architecture/adr/0001-ipc-transport.md)。安装包包含后端源码但未内嵌解释器，运行时通过 `MINDFLIP_PYTHON` 指向现有 Conda Python。
- `health/check` 只证明 Python 运行时可响应，应确定性返回 `ok`，不依赖数据库。数据库就绪可另报状态，不能让运行时健康测试依赖 SQLite。
- 用户 DB 位于系统应用数据目录，测试注入临时路径。密钥不写入数据库、日志或示例。

## 1. Windows 桌面壳

**目标：** 在 `apps/desktop` 初始化 Tauri 2、React、TypeScript、Vite，并提供最小应用壳与开发脚本。

1. 建立工程和 `src-tauri`；提交依赖锁文件、Tauri 配置与最小 capability。
2. 实现单个 React 根视图，显示 MindFlip 标识和清晰的占位内容；无需真实业务页面。
3. README 写明 Windows 前置条件、安装、类型检查、开发启动、生产构建及产物启动命令。
4. 检查 Rust 层只包含原生/桌面集成。

**验收：** Windows 开发模式窗口可启动且 React 渲染；前端类型检查通过；本地生产桌面构建完成并可启动；仓库结构符合架构基线。安装器签名和发布不在本项内。

## 2. 独立 Python 运行时

**目标：** 在 `apps/backend` 建立将来容纳 Agent Core、模型适配、工具和领域服务的独立 Python 包，本轮只写运行入口与健康服务。

1. 建立 `pyproject.toml`、依赖锁定方式、`app/__main__.py` 或等价入口、开发脚本和 `tests/`。
2. 建立 `api`、`runtime` 的真实模块。为 `agent`、`models`、`tools`、`decisions`、`persistence` 保留规划，不创建供应商特定实现。
3. 健康服务稳定返回例如 `{"status":"ok"}`，不依赖网络、模型密钥或数据库。
4. 支持独立启动与清晰退出；若 stdout 用作 IPC，只输出协议消息，诊断写 stderr。

**验收：** 文档命令可从干净环境启动；健康响应确定性为 OK；健康单元测试通过；无模型供应商特定代码。

## 3. 端到端 IPC/API 健康链路

**目标：** 证明 React → Tauri → Python → React，再增加业务功能。

**契约：** 在 `packages/contracts` 固化 `health/check` 请求及成功/失败响应的 JSON Schema 或等价单一来源。推荐外层消息包含 `protocol_version`、`request_id`、`method`、`params`；响应回传相同 ID，以稳定错误码区分后端不可用、超时、无效协议。

```json
{"protocol_version":1,"request_id":"r-001","method":"health/check","params":{}}
```

```json
{"protocol_version":1,"request_id":"r-001","ok":true,"result":{"status":"ok"}}
```

1. 后端实现健康请求适配与解析；未知方法和无效消息返回受控错误。
2. Tauri 暴露单一健康 command，负责转发、超时、进程异常映射与回收。
3. `apps/desktop/src/api` 实现 typed invoke；UI 显示加载、成功、后端不可用、超时和重试。
4. 做请求/响应契约集成测试，手工验证成功和后端失联。

**验收：** UI 可触发并展示真实后端响应；后端失败时有受控错误而不白屏；IPC 细节不进入 feature 组件；集成测试通过。

## 4. 本地 SQLite 持久化

**目标：** 建立 SQLAlchemy 2 + Alembic 底座，不提前设计完整决策模型。

1. 在 `apps/backend/app/persistence` 实现应用数据目录解析、engine/session 工厂和关闭流程；测试可注入临时 DB 路径。
2. 配置 Alembic 并写首个迁移。最小 schema 可为 `storage_probe(id, value)` 等技术验证表，明确非正式业务实体。
3. 通过服务/仓储薄层测试插入、提交、关闭、重开、查询；异常事务回滚。
4. 重复启动不重建已有库或清除数据；启用 SQLite 外键约束和合理 busy timeout；迁移失败须可诊断。

**验收：** DB 位于预期应用数据目录；空库可升级；重开后数据保留；UI/transport 不含 SQL；迁移与持久化集成测试通过。

## 实施顺序与记录

先让 1 和 2 各自独立运行，再做 3；4 可在 2 后独立进行。健康 OK 不等待 SQLite 完成，避免耦合。每项提交应附测试命令、退出码、版本与人工验证结果，依 [测试与验收](03-test-and-acceptance.md) 复核。
