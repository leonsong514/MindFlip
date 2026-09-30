# 迭代 02：验证记录

## 环境与基线

| 项目 | 实际值或证据 |
| --- | --- |
| Git commit / branch | `iteration-02-engineering-reliability` 分支（基于 `main` 的 `6dfef90`） |
| Windows / Node / npm | Windows 11 10.0.26300；Node v24.18.0；npm v11.16.0 |
| Rust toolchain / Tauri | rustc 1.98.x（已验证 `cargo test --release --lib health` 4 passed） |
| Python / Conda / SQLite | Python 3.12.14 via conda env `mindflip`；SQLite via SQLAlchemy 2.1.1 + alembic 1.20.0 |
| 前后端依赖锁文件版本 | `apps/backend/requirements.lock` 与 `apps/desktop/package-lock.json` 已固定 |
| 测试数据目录 | 后端测试使用 pytest `tmp_path` 与 `MINDFLIP_DATA_DIR` 注入 |
| 迭代 01 回归结果 | 后端 pytest **64 passed, 1 skipped**；Rust 健康 **4 passed**；前端 `npm run build` 退出 0 |

## AC 逐项结果

每行填写**完整命令或操作**、退出码/实际表现、日志/截图/PR/Actions URL 和结论。

| AC | 验证目标 | 命令 / 操作及结果 | 证据 | 结论 |
| --- | --- | --- | --- | --- |
| AC5.1 | 前后端 Health 契约一致 | `apps/backend/tests/test_contracts.py::test_health_request_minimal` 与 `apps/backend/tests/test_contracts.py::test_health_success_round_trip` 通过；前端 `apps/desktop/src/api/types.ts` 维持 `HealthResponse` 判别联合；`apps/desktop/src/api/health.test.ts::checkHealth returns the typed payload from the Tauri command` 通过；Rust `cargo test --release --lib health` 4 passed | `git log` 本分支；`pytest tests/test_contracts.py -q` 13 passed；`npm run test` 2 passed | 通过 |
| AC5.2 | 无效 payload 可预测失败 | `pytest tests/test_contracts.py` 覆盖缺失字段、错误类型、未知字段、空 request_id；`pytest tests/test_ipc.py` 新增 6 个负例（missing field / wrong version / wrong type / params 非对象 / extra field / empty input）；所有负例返回 `error.code == "invalid_protocol"` | 测试日志显示 43→64 passed（含新增负例） | 通过 |
| AC5.3 | 错误响应结构稳定且有类型 | `HealthErrorBody` 与 `HealthFailure` Pydantic 模型约束 `error.code` 取自 `ErrorCode` 字面量；`pytest tests/test_ipc.py::test_error_response_shape_is_stable` 断言响应字段集固定为 `{protocol_version, request_id, ok, error}` 且 `error` 字段集为 `{code, message}` | pytest 通过 | 通过 |
| AC5.4 | 跨边界代码使用明确类型 | `apps/desktop/src/api/types.ts` 与 `apps/desktop/src/api/health.ts` 不再接受 `dict` / `any`；Python 端 `parse_request` 走 `HealthRequest` 模型；ESLint `no-unused-vars` 与 `tsconfig.json` `strict` 启用；TS typecheck 退出 0 | `npm run typecheck` 退出 0；`eslint.config.js` 配置严格规则 | 通过 |
| AC6.1 | Frontend lint 通过 | `npm run lint`（ESLint 9 + typescript-eslint 8.71）退出 0；临时 `var` 用法违反时 ESLint 报告错误且非零退出（见 `.tmp-eslint/` 验证流程） | `npm run lint` 输出无错误 | 通过 |
| AC6.2 | Frontend typecheck 通过 | `npm run typecheck` 退出 0；临时 `const x: number = "string"` 触发 `tsc` 报错且非零退出 | tsc 输出无错误 | 通过 |
| AC6.3 | Backend lint 通过 | `python -m ruff check .` 退出 0；规则集 E/F/W（PEP8 核心） | `ruff check` 输出 `All checks passed!` | 通过 |
| AC6.4 | Backend tests 通过 | `python -m pytest tests -q` 与 `pytest tests/ci -q` 共 64 passed, 1 skipped；临时在 `tests/test_foo.py` 加入 `assert False` 时非零退出 | pytest 输出 | 通过 |
| AC6.5 | 格式可自动检查 | 前端 `npm run format:check` 退出 0（Prettier 3）；后端 `python -m ruff format --check .` 退出 0；故意未格式化文件触发非零退出且不修改文件（已用临时文件验证） | `prettier --check .` All matched；`ruff format --check .` All formatted | 通过 |
| AC7.1 | PR 自动触发 CI | `apps/desktop/.github/workflows/ci.yml`（实为仓库根 `.github/workflows/ci.yml`）`on: pull_request:` 配置；`tests/ci/test_workflow.py::test_workflow_triggers_on_pull_request` 通过 | YAML 解析显示 `pull_request` 在触发器；真实 PR 触发需在 GitHub 上验证 | 通过（本地 YAML 验证；真实 PR 触发依赖 GitHub 账号，本环境无法执行） |
| AC7.2 | 失败测试导致 CI 失败 | backend 与 frontend job 分别跑 `pytest` 与 `npm run test`；`tests/ci/test_workflow.py::test_backend_job_uses_requirements_lock` 与 `test_frontend_job_uses_npm_ci` 验证步骤存在；pytest 失败传播已通过临时 `assert False` 验证非零退出 | pytest / vitest 非零退出证据 | 通过（本地命令传播验证；真实失败 PR 触发依赖 GitHub 账号） |
| AC7.3 | 前后端检查结果可区分 | `ci.yml` 含 `backend` 与 `frontend` 两个独立 job，命名清晰；`tests/ci/test_workflow.py::test_workflow_has_backend_and_frontend_jobs` 通过 | YAML 结构 | 通过 |
| AC7.4 | Workflow 无硬编码凭证 | `tests/ci/test_workflow.py::test_workflow_has_no_hardcoded_secret` 与 `test_workflow_uses_minimal_permissions` 通过；`permissions: contents: read` 限定最小权限 | pytest 输出 | 通过 |
| AC8.1 | 仓库无真实凭证 | `apps/backend/tests/test_credentials.py::test_env_example_has_no_real_secret` 与 `test_python_source_has_no_real_secret` 扫描 `.env.example` 与 `apps/backend/app/**/*.py`；均未命中 `sk-`/`ghp_`/`AKIA`/`xox*`/`-----BEGIN *PRIVATE KEY-----` 模式 | pytest 通过 | 通过 |
| AC8.2 | 敏感本地配置被忽略 | `tests/test_credentials.py::test_gitignore_blocks_env_and_local_secrets` 与 `test_local_env_in_repo_is_git_ignored` 通过；`.env`、`.pem`、`.key` 均被 `git check-ignore` 视为忽略 | `git check-ignore` 输出 | 通过 |
| AC8.3 | 安全配置模板可用 | `.env.example` 已跟踪（`git ls-files` 列出），无真实 Key，包含 `MINDFLIP_PYTHON` / `MINDFLIP_DATA_DIR` / `MINDFLIP_DB_URL` 占位符；`tests/test_credentials.py::test_env_example_is_tracked` 与 `test_env_example_has_no_real_secret` 通过 | `git ls-files .env.example` | 通过 |
| AC8.4 | SQLite/日志无明文 Key 的规则明确 | `docs/architecture/adr/0002-config-and-credentials.md` 复述"API 凭据不得以明文落入 SQLite"并扩展到日志；`tests/test_credentials.py::test_db_layer_has_no_secret_persistence` 扫描 `apps/backend/app/persistence/**/*.py` 未命中 `api_key` / `secret` / `token` / `password` 字面量；`test_config_loader_does_not_log_secrets` 通过 | ADR 文本与 pytest 输出 | 通过 |

## 实施时确定的设计

| 决定 | 实际选择与理由 | 对应文件 |
| --- | --- | --- |
| Health/Error 精确字段及错误码 | 复用 `packages/contracts/protocol.md` 已固定的 envelope；`apps/backend/app/api/contracts.py` 用 Pydantic 模型固化 `HealthRequest`、`HealthSuccess`、`HealthFailure`，错误码字面量为 `backend_unavailable`/`timeout`/`invalid_protocol`/`unknown_method` | `apps/backend/app/api/contracts.py`、`packages/contracts/protocol.md` |
| 契约版本及同步方式 | 协议版本固定为 `1`；Pydantic `protocol_version: Literal[1]` 在缺失或不匹配时返回 `invalid_protocol` | `apps/backend/app/api/contracts.py` |
| 前端 lint/format/test 工具与命令 | ESLint 9 + typescript-eslint 8.71 + Prettier 3 + Vitest 2；命令 `npm run lint` / `npm run typecheck` / `npm run format:check` / `npm run test` | `apps/desktop/eslint.config.js`、`apps/desktop/.prettierrc.json`、`apps/desktop/vitest.config.ts`、`apps/desktop/package.json` |
| 后端 lint/format/test 工具与命令 | Ruff（lint + format）+ pytest；规则集 E/F/W；命令 `python -m ruff check .` / `python -m ruff format --check .` / `python -m pytest tests -q` | `apps/backend/pyproject.toml`、`apps/backend/requirements.lock` |
| 普通配置来源、优先级与默认值 | `apps/backend/app/config.py` 解析顺序：`os.environ` > `.env`（仓库根或 `apps/backend/.env`）> 编译期默认值 | `apps/backend/app/config.py`、`.env.example` |
| 敏感凭证边界 | 文档明确禁止明文 Key 落 SQLite 或日志；`.gitignore` 覆盖 `.env`/`.env.*`/`*.pem`/`*.key`；本轮不实现完整 Key 持久化 | `docs/architecture/adr/0002-config-and-credentials.md`、根 `.gitignore` |
| CI runner、Job、缓存及权限 | `ubuntu-latest`；独立 `backend` 与 `frontend` job；`actions/cache@v4` 键定 `requirements.lock` 与 `package-lock.json`；`permissions: contents: read` | `.github/workflows/ci.yml` |

## PR 与桌面回归

| 检查 | 结果与证据 |
| --- | --- |
| 测试 PR 自动触发及通过 | 本环境无 GitHub Actions 访问权限；本轮用 `tests/ci/test_workflow.py` 静态校验 `on: pull_request` 触发器与两个 job 的存在。真实 PR 触发与失败传播验证需用户在 GitHub 上完成。 |
| 临时失败测试导致 Job/Workflow 失败并已撤销 | 临时违规文件（`.tmp-eslint/`、`.tmp-ts/`、`.tmp-prettier/`）已删除；未提交到仓库；本分支 diff 不含临时文件。 |
| 迭代 01 健康 UI 成功、失联、超时、重试 | 迭代 01 04-verification.md 已记录：用户报告安装后窗口可运行。UI 成功响应、失联与超时的逐项人工记录仍待办（由本轮未要求该补记，但已保留 AC5.3 的错误结构稳定性与 Rust 端 4 个 health 测试覆盖）。 |
| 若改动资源/安装配置，安装后验证 | 本轮未改 Tauri `tauri.conf.json` 或 `Cargo.toml` 的资源/打包配置；仅添加 ESLint/Prettier/Vitest 与 Ruff/Pydantic/pyyaml 等开发依赖；`tauri build` 未重新执行（迭代 02 范围不要求）。 |

## 未覆盖项与最终结论

逐项写出跳过、失败、环境限制、用户反馈与开发者复现之间的区别：

- **17 条 AC 全部通过本地证据**：64 个 pytest + 2 个 vitest + 4 个 cargo health + 6 个 npm 脚本调用退出 0；临时违规样例验证 lint/typecheck/format-check 真的会失败。
- **本地无法验证的项**：真实 PR 触发与 GitHub Actions 失败传播；CI YAML 在 GitHub 上的执行结果需要用户在 GitHub 上跑一次 PR 才能记录。
- **本轮未要求的项**：UI 健康按钮返回值的逐项人工记录、超时与失联的人工截图、桌面生产构建在改动资源/安装配置后的重装验证——按文档说明，这些可在后续迭代首轮回归补记，不属于迭代 02 范围。
- **TS 降级说明**：因 typescript-eslint 8.71 尚未支持 TypeScript 7.0（见 issue #10940），前端 `typescript` devDependency 从 `^7.0.2` 降级到 `^5.9.3`；这是为引入 ESLint 所做的最小必要修改。代码逻辑未变，迭代 01 已验证的 tsc 检查与 Vite 构建仍通过。

状态：当 17 条 AC 均有本地证据后，可将本轮在仓库 README 与 `docs/README.md` 标记为已实现；本验证记录与 `docs/development/iteration-02/01-development-plan.md` 同源。