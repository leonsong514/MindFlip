# MindFlip

一个本地优先、模型无关的 AI 决策辅助桌面应用。AI 提供建议，人类做决定，应用忠实记录历史。

## 文档

- [架构基线](./Architecture%20Design%20Document%20v1.0.md)：产品边界、分层、路线图与仓库结构的权威来源
- [文档索引](./docs/README.md)：架构、迭代规划与测试验收入口
- [迭代 01 目录规划](./docs/development/iteration-01/01-repository-layout.md)
- [迭代 01 开发计划](./docs/development/iteration-01/02-development-plan.md)
- [迭代 01 测试与验收](./docs/development/iteration-01/03-test-and-acceptance.md)
- [迭代 01 复核记录](./docs/development/iteration-01/04-verification.md)
- [ADR-IPC-001 IPC 传输选型（Accepted）](./docs/architecture/adr/0001-ipc-transport.md)：Tauri 与 Python 运行时之间的传输选型
- [ADR-CFG-001 本地配置与凭证边界（Accepted）](./docs/architecture/adr/0002-config-and-credentials.md)：普通配置与敏感凭据的隔离规则
- [IPC 协议 v1](./packages/contracts/protocol.md)：envelope、错误码、版本约定

## 当前状态

迭代 01 的四项底座已实现并通过自动化检查；迭代 02 的本地实现已完成，AC7.1/AC7.2 仍待真实 PR 的 GitHub Actions 验证，详见[迭代 02 验证记录](./docs/development/iteration-02/03-verification.md)。CI 在 `.github/workflows/ci.yml` 中以 `ubuntu-latest` 跑前后端独立 job；真实 PR 触发需在 GitHub 上完成。迭代 01 复核记录中关于 UI 健康按钮返回值、失联与超时的人工逐项记录仍待后续迭代补齐。

## 运行与构建

### 前置条件

- Node.js v24.x、npm v11.x
- Rust stable-x86_64-pc-windows-msvc（1.98+）
- Microsoft Edge WebView2 Runtime
- Microsoft Visual Studio（含 MSVC x64 工具链）
- Python 3.12 conda 环境 `mindflip`，按锁文件安装后端依赖

### 后端

`apps/backend/requirements.lock` 固定了本轮的直接及传递依赖版本。新环境只用 conda 安装 Python，其余依赖由 pip 安装；已有的 `mindflip` 环境无需重复安装相同包。

```powershell
conda create -n mindflip python=3.12 pip
conda run -n mindflip python -m pip install -r apps/backend/requirements.lock
```

以下命令从仓库根目录开始：

```powershell
Push-Location apps/backend
# 健康探针（确定性 OK）
conda run -n mindflip python -m app --health
# 初始化/升级本地数据库
conda run -n mindflip python -m app --init-db

# 单元与集成测试
conda run -n mindflip python -m pytest tests -q
Pop-Location
```

### 桌面壳

```powershell
Push-Location apps\desktop
npm install
npm run typecheck           # 前端类型检查
npm run build              # 前端生产构建

# Tauri 桌面开发模式
npm run tauri -- dev

# Tauri 桌面生产构建
npm run tauri -- build
Pop-Location
```

Tauri 端的健康 IPC 由 Rust 集成测试覆盖：

```powershell
$env:MINDFLIP_PYTHON = (conda run -n mindflip python -c "import sys; print(sys.executable)" | Select-Object -Last 1).Trim()
Push-Location apps\desktop\src-tauri
cargo test --release --lib health
Pop-Location
```

生产桌面包包含后端 Python 源码和迁移文件；当前迭代尚未内嵌 Python 解释器。运行桌面产物的机器必须安装兼容的 Python 环境，并通过 `MINDFLIP_PYTHON` 指向该环境的 `python.exe`。这属于当前本地开发交付，不能将其称为无需前置条件的独立安装包。

预期：4 passed（含真实 Rust → Python 子进程往返）。

### 测试与验收

迭代 01 的测试矩阵、命令和验证记录详见各工程 `README.md`：

- [apps/desktop/README.md](./apps/desktop/README.md)
- [apps/backend/README.md](./apps/backend/README.md)

## 仓库结构

```text
MindFlip/
├── apps/
│   ├── desktop/             Tauri 2 + React + TypeScript + Vite 桌面壳
│   └── backend/             独立 Python 包 + SQLite + Alembic
├── packages/
│   └── contracts/           IPC JSON Schema 与示例
├── docs/
│   ├── architecture/adr/    架构决策记录
│   └── development/         迭代规划与验收
└── README.md
```
