# ADR-CFG-001：本地配置与凭证边界

- 状态：Accepted
- 日期：2026-09-30
- 适用范围：迭代 02 Issue #8（Local Configuration and Credential Boundaries）以及后续所有需要加载运行时配置或访问外部 API 凭据的代码

## 背景

迭代 02 要求建立"普通配置"和"敏感凭证"的边界。架构基线《Architecture Design Document v1.0.md》第 18 节已经规定 API 凭据不得以明文落入 SQLite，但未明确"普通配置"如何加载、"敏感凭证"如何从代码边界隔离。Issue #8 的 4 条 AC 要求：仓库无真实 Key、`.gitignore` 覆盖本地密钥、`.env.example` 模板可用、文档明确禁止明文 Key 落 SQLite 或日志。

## 决定

1. 普通配置（路径、日志级别、功能开关）通过 `apps/backend/app/config.py` 加载；解析顺序固定为 `环境变量 → .env 文件 → 编译期默认值`。
2. 仓库根提供 `.env.example` 作为唯一可提交的模板；真实 `.env`、`.env.*`、`*.local.key`、`*.pem` 等本地密钥文件由根 `.gitignore` 排除。
3. API Key、Access Token 等敏感凭据当前**不**实现完整端到端 Key 管理界面。代码边界禁止将明文 Key 写入 SQLite 表、日志文件或任何会被 `git log` 跟踪的位置。
4. 未来 Key 管理迭代通过 OS 原生凭据存储（Credential Manager / Keychain / Secret Service）提供；本 ADR 不在迭代 02 内提供完整实现。

## 选择理由

- 文档建议"评估逐行 JSON 的 stdio 通道；若使用 loopback HTTP，须记录端口发现、访问控制、超时、退出回收"。本 ADR 把"配置加载优先级 + 凭据边界"作为对应工具类的最小约束，与 IPC ADR 的轻量级精神一致。
- 与架构基线第 18 节 "API credentials must not be stored as plaintext in SQLite" 一致；本 ADR 把"日志明文"也纳入禁止范围，避免仅落库而日志漏出的间接泄漏。
- `.env.example` 模板与 `gitignore` 是低成本、可静态检查、可在 CI 中扫的最小防御；可立即避免常见误提交事故。

## 主要后果

- 任何新引入的运行时配置项优先在 `app/config.py` 增加；Key 类数据禁止走同一通道。
- Python 入口禁止对 SQLite `storage_probe` 或未来业务表执行包含 "api_key"/"token"/"secret" 等字段名的写入。
- 日志库或 print 中禁止记录原始凭据值；记录时只能记录凭据标识符或掩码（如 `sk-***`）。
- CI 必须可静态检查：工作流无硬编码 Key；提交历史可由 secret scanner 校验。
- `.env` 文件不进入版本控制，开发文档告诉用户从 `.env.example` 复制并填写非敏感值。

## 替代方案与未选理由

- **dotenv 库**：本轮只需要 `KEY=VALUE` 的最小语义，使用 pathlib 自带的读取避免引入额外依赖；保留 dotenv 是后续迭代的可选项。
- **完整 OS 凭据存储集成**：依赖 Windows Credential Manager、macOS Keychain、Linux Secret Service 的跨平台抽象。MVP 还没有 Key 接入需求，先禁止明文写入并保留接口位置。
- **加密本地存储**：复杂度超出迭代 02 P0 范围，且未绑定实际 Key 提供方。

## 验收记录

下列检查在仓库根目录通过：

1. `.env` 与代表性本地密钥文件名被 `git check-ignore` 视为忽略。
2. `.env.example` 可被 `git check-ignore -v` 视为跟踪，但不含真实 Key。
3. `apps/backend/tests/test_config.py` 覆盖解析顺序、注释、空白、引号与缺失文件回退。
4. 后端 lint/format/test 全通过且无真实 Key 命中。
5. 架构基线第 18 节规则仍由本 ADR 复述；后续迭代若新增 Key 持久化路径，需另立 ADR。