# 迭代 02：开发交接入口

## 状态

**待定范围，尚未开始开发。** 架构基线 Phase 1 提到 Decision Core（Decision、Alternatives、Criteria、Decision history、Dashboard），但下轮的正式任务应以 GitHub Project 中对应条目的正文和验收条件为准。不要仅凭路线图把上述模块全部视为迭代 02 承诺，也不要在确认任务前创建空业务目录或迁移。

确认任务原文后，按顺序填写 [开发计划](01-development-plan.md)、[测试方案](02-test-plan.md)，实施过程中记录 [验证结果](03-verification.md)。

## 已有基础

- 桌面工程：`apps/desktop`，React/Vite/Tauri 2，健康面板通过 `src/api/health.ts` 调用 Rust command。
- 后端工程：`apps/backend`，独立健康 CLI、单请求 stdio IPC、SQLAlchemy 2 与 Alembic 初始迁移。技术验证表 `storage_probe` 不是 Decision 领域模型。
- 跨进程契约：`packages/contracts` 的 JSON Schema、示例与 [IPC 协议 v1](../../../packages/contracts/protocol.md)；传输选型见 [ADR-IPC-001](../../architecture/adr/0001-ipc-transport.md)。
- 运行环境：Windows + MSVC；桌面安装包带后端源码但不带 Python 解释器。现有 Conda `mindflip` 环境可用，设置 `MINDFLIP_PYTHON` 为该环境的 `python.exe`。
- SQLite 通过 `python -m app --init-db` 显式迁移；`--health` 不依赖数据库。

## 开始前的工作

1. 取得下一组 GitHub Project 任务的原文和验收条件，写本目录下的开发计划、测试方案与验证记录；逐条对应任务，不从架构路线图推测交付范围。
2. 阅读 [迭代 01 复核记录](../iteration-01/04-verification.md) 和 [测试手册](../iteration-01/03-test-and-acceptance.md)，先复跑已有自动检查。若下一轮修改 IPC、资源、迁移或环境配置，再针对相应边界做安装后回归。
3. 补记迭代 01 尚无逐项人工结果的 UI 健康成功、后端不可用、超时与重试。当前每次健康请求都会新建 Python 进程；失联测试应在测试会话中覆盖解释器路径，不能靠关闭一个常驻后端进程。
4. 若下一轮要引入 Decision 数据模型，先定义迁移与持久化边界，再让 Application API 暴露领域操作；保持 AI 推荐、用户决定、实际行为和结果为独立概念。

## 最低回归命令

从仓库根目录执行；已有 Conda 环境无需再次安装 Python。

```powershell
Push-Location apps/backend
conda run -n mindflip python -m pytest tests -q
conda run -n mindflip python -m app --health
Pop-Location

Push-Location apps/desktop
npm run typecheck
npm run build
Pop-Location
```

修改 Rust/IPC 时再运行 `cargo test --release --lib health`；修改资源或安装配置时再运行 `npm run tauri -- build` 并安装验证。测试结果、环境版本、未覆盖项应写入本目录的新验证文档，避免沿用迭代 01 的旧通过记录。
