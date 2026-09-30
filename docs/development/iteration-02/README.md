# 迭代 02：Engineering Reliability

## 状态

**17 条 AC 全部通过本地验证（2026-09-30）。** 本轮属于 P0 Engineering Foundation，目标是建立可靠、可验证、可自动化检查的前后端工程基础。范围为 Issues [#5](https://github.com/leonsong514/MindFlip/issues/5)、[#6](https://github.com/leonsong514/MindFlip/issues/6)、[#7](https://github.com/leonsong514/MindFlip/issues/7)、[#8](https://github.com/leonsong514/MindFlip/issues/8)。Issue 页面无法直接读取时，以用户粘贴的完整任务清单为准。

实现要点：

- 共享契约：新增 `apps/backend/app/api/contracts.py` 的 Pydantic 边界模型；`parse_request` 走 Pydantic 校验；新增 `tests/test_contracts.py` 与 `tests/test_ipc.py` 6 个负例；前端 `src/api/types.ts` 维持 `HealthResponse` 判别联合，Vitest 覆盖 typed invoke。
- 质量工具：前端 ESLint 9 + Prettier 3 + Vitest 2；后端 Ruff（lint + format）+ pytest。命令通过 `apps/desktop/package.json` scripts 与 `apps/backend/pyproject.toml` 入口；临时违规样例验证 lint/typecheck/format 真的会失败。
- 本地配置与凭证：新增 `apps/backend/app/config.py`、`tests/test_config.py`、`.env.example` 与 `docs/architecture/adr/0002-config-and-credentials.md`；`tests/test_credentials.py` 覆盖 `git check-ignore` 与明文 Key 扫描。
- CI：`.github/workflows/ci.yml` 在 `ubuntu-latest` 上分 `backend` 与 `frontend` 两个 job；`tests/ci/test_workflow.py` 校验 YAML 结构与无硬编码密钥。

按 [开发计划](01-development-plan.md) 实施，[测试方案](02-test-plan.md) 与实际命令、退出码、证据记录在 [验证结果](03-verification.md)。真实 GitHub PR 触发与失败传播需在 GitHub 上完成；本环境无 Actions 访问权限，仅静态校验 YAML。

**不在本轮：** Decision Core、Agent Loop、模型接入、业务页面和 Windows 最终发行打包。架构路线图中的 Phase 1 Decision Core 不应被误当作本轮范围。

## 已有基础

- 桌面工程：`apps/desktop`，React/Vite/Tauri 2，健康面板通过 `src/api/health.ts` 调用 Rust command。
- 后端工程：`apps/backend`，独立健康 CLI、单请求 stdio IPC、SQLAlchemy 2 与 Alembic 初始迁移。技术验证表 `storage_probe` 不是 Decision 领域模型。
- 跨进程契约：`packages/contracts` 的 JSON Schema、示例与 [IPC 协议 v1](../../../packages/contracts/protocol.md)；传输选型见 [ADR-IPC-001](../../architecture/adr/0001-ipc-transport.md)。
- 运行环境：Windows + MSVC；桌面安装包带后端源码但不带 Python 解释器。现有 Conda `mindflip` 环境可用，设置 `MINDFLIP_PYTHON` 为该环境的 `python.exe`。
- SQLite 通过 `python -m app --init-db` 显式迁移；`--health` 不依赖数据库。

## 开始前的工作

1. 阅读 [迭代 01 复核记录](../iteration-01/04-verification.md)、[测试手册](../iteration-01/03-test-and-acceptance.md)和当前 IPC 协议，先复跑基础检查。
2. 按 #5 契约、#6 质量工具、#8 本地配置、#7 CI 的依赖顺序实施；#6 与 #8 可交错，CI 在本地命令稳定后收尾。
3. 补记迭代 01 尚无逐项人工结果的 UI 健康成功、后端不可用、超时与重试；本轮契约变更必须保留原有 Health Check 能力。
4. 不创建 Decision 业务实体、业务迁移、CRUD 或业务页面。

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
