# 迭代 02：Engineering Reliability 开发计划

## 1. 任务来源与完成定义

本计划依据用户提供的《Iteration 2 — Engineering Reliability》任务清单整理。Issue 页面当前无法直接读取，以下 AC 以该清单为准；实施时如 Issue 正文与清单有差异，先更新本文件与测试映射。前置条件为 Issues #1–#4 已完成。开发阶段是 **P0 — Engineering Foundation**，目标是建立可靠、可验证、可自动化检查的前后端工程基础。

| Issue | 工作项 | 交付目标 |
| --- | --- | --- |
| [#5](https://github.com/leonsong514/MindFlip/issues/5) | Shared Contracts and Validation | 稳定的前后端数据契约、输入验证、统一错误结构 |
| [#6](https://github.com/leonsong514/MindFlip/issues/6) | Frontend and Backend Quality Tooling | 可重复执行的格式、静态、类型和测试检查 |
| [#7](https://github.com/leonsong514/MindFlip/issues/7) | GitHub Actions CI Foundation | Pull Request 自动质量验证 |
| [#8](https://github.com/leonsong514/MindFlip/issues/8) | Local Configuration and Credential Boundaries | 安全的本地配置与敏感信息存储边界 |

**完成条件：** 四项 Issue 的全部 **17 条 AC** 都在[测试方案](02-test-plan.md)中有对应验证，并在[验证记录](03-verification.md)中记下实际结果。构建成功本身不等于 AC 全部通过。

**范围外：** Decision Core、Agent Loop、模型接入、业务页面、Windows 最终发行打包。SQLite 基础设施已在迭代 01 建立，本轮不得引入 Decision、Alternative、Criterion 的业务实体、字段、迁移或 CRUD。架构文档 Phase 1 是后续路线图，并非本轮任务来源。

## 2. 已有基线

- React 通过 `apps/desktop/src/api` 调用 Tauri；Rust 管理原生边界与 Python 子进程；Python 端的单请求 stdio JSON Lines IPC 已接通。传输选择见 [ADR-IPC-001](../../architecture/adr/0001-ipc-transport.md)。
- [IPC 协议 v1](../../../packages/contracts/protocol.md)、JSON Schema、TypeScript 类型和 Python 解析代码均已存在。#5 应先核对这些现状，避免另建不兼容的第二套协议。
- Python 健康服务不依赖 SQLite。SQLite 由 SQLAlchemy 2 与 Alembic 管理，`storage_probe` 仅为技术验证表。
- 当前安装包包含 Python 源码而不包含解释器，`MINDFLIP_PYTHON` 指向 Conda 环境；本轮配置任务不得在 SQLite 或日志中存放 API Key。
- 第一迭代自动检查与安装窗口反馈见[复核记录](../iteration-01/04-verification.md)。UI 健康成功、失联与超时尚无逐项人工记录。

## 3. Issue #5：Shared Contracts and Validation

**建议交付位置：** `apps/backend/app/api` 的 Pydantic 边界模型、`apps/desktop/src/api/types.ts` 的对应类型、`packages/contracts` 的规范与样例，以及契约测试。具体文件名可随实现调整，保持单一清晰来源。

| AC | 必须达到的结果 |
| --- | --- |
| AC5.1 | Health contract 同时存在于前端与后端 |
| AC5.2 | 无效 payload 以可预测方式失败 |
| AC5.3 | 错误响应有稳定、类型明确的结构 |
| AC5.4 | 跨边界功能代码不依赖无类型的任意字典或对象 |

**实施 checkpoint：**

1. 盘点现有请求、成功响应、错误响应的真实 wire format，列出与 JSON Schema/TS 类型的差异；保留现有 `health/check` 调用可用。
2. 确定 Health 与 Error 的最小字段、必填/可选规则、错误码及协议版本策略，在契约文档中记录。Issue 未指定精确字段、版本格式或 OpenAPI/JSON Schema 生成工具，开发时再选，不把候选方案写成既定事实。
3. Python 入口用 Pydantic 验证不可信输入；内部使用明确模型或类型，而不是把原始 `dict` 贯穿业务边界。TypeScript 定义匹配的判别联合或等价类型。
4. 增加有效、缺失字段、类型错误、未知方法和错误响应测试；校验前后端示例与实际序列化一致。若更改现有协议语义，说明兼容策略，并审查 ADR 是否需要更新。

**完成定义：** 四条 AC 逐项通过；现有健康 IPC 回归通过；契约字段与版本约定可从文档和测试复现。

## 4. Issue #6：Frontend and Backend Quality Tooling

**建议交付位置：** 前端 lint/format/test 配置、后端 lint/format/pytest 配置、两个工程的命令入口及简明开发说明。ESLint、Prettier、Ruff、pytest 是候选组合，最终以实际配置和锁文件为准；不要添加功能未用到的工具。

| AC | 必须达到的结果 |
| --- | --- |
| AC6.1 | Frontend lint 命令通过 |
| AC6.2 | Frontend type-check 命令通过 |
| AC6.3 | Backend lint 命令通过 |
| AC6.4 | Backend test 命令通过 |
| AC6.5 | 代码格式可自动检查 |

**实施 checkpoint：**

1. 固定前端 lint、typecheck、format-check、test 命令和后端 lint、format-check、pytest 命令，写入各工程 README；格式检查不得默认修改文件。
2. 给前端添加至少一个有意义的自动化测试，验证可观察状态或 API 包装行为；保留现有后端测试。
3. 用临时违规样例验证 lint、类型与格式命令确实会失败；临时文件不得进入提交。
4. 在干净检出上按文档安装依赖并运行命令，记录工具版本、退出码和环境差异。

**完成定义：** 五条 AC 通过；本地命令无隐含全局依赖，CI 能直接复用。

## 5. Issue #8：Local Configuration and Credential Boundaries

**建议交付位置：** `.gitignore`、安全的 `.env.example` 或等价模板、最小配置加载入口、配置/凭证边界文档与测试。本轮不实现完整模型 Key 管理界面。

| AC | 必须达到的结果 |
| --- | --- |
| AC8.1 | 仓库没有提交 API Key 或其他凭证 |
| AC8.2 | `.gitignore` 覆盖本地密钥与敏感配置 |
| AC8.3 | 仓库有安全配置示例 |
| AC8.4 | 架构明确禁止在 SQLite 和日志中明文存储 API Key |

**实施 checkpoint：**

1. 区分普通配置和敏感凭证：普通配置可来自文件/环境变量，敏感凭证未来走 OS 凭据存储边界；明确优先级、默认值与缺失时的错误。
2. 模板只含占位符，不放真实 Key；验证 `.env` 与本地密钥文件被 Git 忽略，且模板本身可提交。
3. 检查已提交内容和当前变更是否含真实凭证；日志与 SQLite 的禁止明文规则写入文档，并覆盖当前可用路径。尚无完整 Key 存取功能时，不伪造端到端测试通过。

**完成定义：** 四条 AC 有可检查证据；开发人员能从模板建立安全的本地配置；不引入明文密钥持久化。

## 6. Issue #7：GitHub Actions CI Foundation

**建议交付位置：** `.github/workflows/ci.yml` 及 CI 命令说明。CI 应在 #5、#6、#8 的本地命令稳定后完成最终验收。

| AC | 必须达到的结果 |
| --- | --- |
| AC7.1 | Pull Request 自动触发 CI |
| AC7.2 | 失败测试导致 CI 失败 |
| AC7.3 | 前后端检查作为独立 Job 或明确区分的步骤显示 |
| AC7.4 | Workflow 无密钥或硬编码凭证 |

**实施 checkpoint：**

1. PR 触发 Checkout → 锁定依赖安装 → 前后端独立可识别检查 → 构建 → 结果；命令复用本地脚本。
2. 检查权限最小化和凭证边界；不把 API Key 写进 workflow。缓存按锁文件键控，可在不影响正确性的前提下加入。
3. 建立测试 PR，确认自动触发；在隔离分支临时引入确定失败的测试，确认相应 Job 与整体工作流失败，然后撤销临时代码，不合并到主分支。

**完成定义：** 四条 AC 在 GitHub Actions 的真实运行中通过；仅查看 YAML 或本地运行不能替代 PR 触发与失败传播验证。

## 7. 顺序与变更控制

顺序：**#5 → #6 → #8 → #7**。#6 与 #8 可交错实施，#7 在本地检查命令固定后收尾。每个 Issue 完成时在验证记录中填 AC、命令、退出码和证据链接；任何测试跳过或未执行都要说明原因。正式工具和契约字段在实现时确定后，回写本计划与测试方案，避免文档停留在候选状态。
