# 迭代 01：仓库目录规划

> 本文保留迭代前的目标结构。实际已创建的文件以仓库为准；后续迭代应按已确认任务逐步扩展，不必补齐下文示意树中的所有目录。

## 依据与边界

依据根目录《Architecture Design Document v1.0.md》的第 4、31～34、42～43、50～51 节。本迭代只建设 Windows 桌面基础底座和可验证的模板，不进入决策业务、模型供应商、Agent 工具等后续阶段。职责方向固定为 `React → Tauri IPC → Python Application API → SQLite`；Rust 只负责桌面生命周期、进程与系统边界。前端不得直接访问数据库或 Python 内部模块。

## 建议的目标目录

下面是开发完成后的目标树，并非当前已实现文件。`apps/desktop/src-tauri` 属于 Tauri 工程；`apps/backend` 是独立 Python 包。空目录在 Git 中无意义，实施时随首个真实文件创建。

```text
MindFlip/
├── apps/
│   ├── desktop/
│   │   ├── src/
│   │   │   ├── app/               # Router、QueryClient、应用启动
│   │   │   ├── routes/            # Dashboard、Settings 占位路由
│   │   │   ├── features/          # 后续按 dashboard/decisions/... 扩展
│   │   │   ├── components/        # 跨功能组件
│   │   │   ├── design-system/     # token 与 UI 基础件
│   │   │   ├── api/               # typed invoke 封装，不包含业务实现
│   │   │   ├── stores/            # 仅瞬时 UI 状态
│   │   │   └── types/
│   │   ├── src-tauri/
│   │   │   ├── src/               # command、runtime、window
│   │   │   ├── capabilities/      # 最小权限
│   │   │   └── tauri.conf.json
│   │   └── package.json
│   └── backend/
│       ├── app/
│       │   ├── api/               # IPC 消息路由与校验
│       │   ├── decisions/         # 后续业务域，首轮不建假实现
│       │   ├── persistence/       # DB engine、迁移入口
│       │   └── runtime/           # 启动、健康检查、优雅退出
│       ├── migrations/            # Alembic 版本文件
│       ├── tests/
│       └── pyproject.toml
├── packages/
│   └── contracts/                  # 语言无关 IPC JSON Schema 与示例
├── docs/
│   ├── architecture/adr/          # 决策记录；架构基线暂保留根目录
│   └── development/iteration-01/
├── tests/desktop-e2e/             # Windows 启动与 IPC 烟测
├── scripts/                       # 开发环境、契约同步及构建脚本
├── .github/workflows/             # PR 检查；发布流程以后建立
├── README.md
└── LICENSE.md
```

## 模块规则

| 位置 | 允许依赖 | 禁止依赖 |
| --- | --- | --- |
| `apps/desktop/src` | `packages/contracts` 的生成类型、Tauri command 封装 | Python 包、SQLite 文件路径、供应商 SDK |
| `apps/desktop/src-tauri` | 契约、进程与系统 API | 决策算法、Agent 编排、业务 SQL |
| `apps/backend/app/api` | 服务层、持久化入口、契约校验 | React 组件或 WebView 状态 |
| `apps/backend/app/persistence` | SQLAlchemy、Alembic、数据库模型 | Tauri、UI、模型供应商 |
| `packages/contracts` | JSON Schema、示例载荷与版本说明 | 任一运行时实现 |

依赖锁文件由各自生态维护；根目录只放跨工程命令和文档。用户数据写到应用数据目录，不写到仓库。数据库、日志、临时运行文件及密钥都不得提交。密钥以后通过原生凭据存储提供，不应出现在 SQLite、日志或 IPC 测试示例中。

## 首轮最小实现骨架

第一轮只需要一个桌面壳、一个 `health/check` 请求、一个可独立启动的 Python 运行时、一个 SQLite 初始迁移及对应测试。健康检查是验证跨层链路的技术接口，不是业务接口，也不依赖数据库。建议未来业务方法使用架构文档的 `decision.*`、`agent.*` 等逻辑命名。

## 后续扩展原则

`packages/ui` 与 `packages/plugin-sdk` 可在确有复用需求时添加，不为凑齐架构图创建空包。Agent、model provider、tool registry、evidence 等目录由相应迭代创建。单个功能按 `features/<feature>` 放 UI、hooks、测试；共享模块只有出现真实跨功能复用后才上移。
