# 迭代 01：2026-09-29 复核记录

## 本次修正

- Tauri 安装包显式包含后端 `app/` 源码、Alembic 迁移文件与配置；资源列表逐个指定源文件，避免把本机 `__pycache__` 放入安装包。
- 桌面健康 command 在后台线程执行，避免同步等待 Python 时阻塞 Tauri 命令处理。
- 后端增加 `python -m app --init-db`，显式升级应用数据目录中的 SQLite；`--health` 仍不依赖数据库。
- 根目录和后端 README 修正工作目录、Conda 版本及依赖安装说明；IPC 协议文档与 ADR 状态一致。
- `requirements.lock` 固定本轮 Windows/Python 3.12 的直接与传递依赖版本。

## 已执行验证

| 检查 | 结果 |
| --- | --- |
| `npm run build` | 退出码 0，包含 TypeScript 类型检查与 Vite 构建 |
| `cargo check --release` | 退出码 0 |
| `cargo test --release --lib health` | 退出码 0，4 passed，包含真实 Rust → Python 往返 |
| `python -m pytest tests -q -p no:cacheprovider --basetemp <writable-test-dir>` | 退出码 0，23 passed、1 skipped；跳过项为 Windows 只读目录语义测试 |
| `python -m app --init-db` | 临时数据目录创建数据库并报告 revision `0001_initial`；另有 CLI 集成测试 |
| `npm run tauri -- build` | 退出码 0，生成 MSI 与 NSIS |
| MSI WiX 清单检查 | 包含 `ipc_main.py`、`0001_initial.py`；无 `__pycache__` |
| 仓库根目录 README 的健康命令 | 进入 `apps/backend` 后退出码 0，返回 `status: ok` |

首次 MSI 构建因受限网络无法下载 WiX；允许官方下载后成功。资源列表修改后，在受限运行中 `light.exe` 无法完成；相同构建在允许访问本机打包工具的运行中通过。构建产物属于本机验证结果，不应提交到 Git。

## 用户手动验证反馈

用户于本轮对话中反馈：“安装运行后看起来没问题”。据此记录为**安装后的应用窗口可启动并显示**。未收到健康按钮返回值、截图、安装包类型或错误路径的逐项结果，因此不把 React → Tauri → Python 的安装后成功响应、后端失联或超时标为已人工验证。下轮回归可直接补这三项，不必每次代码修改都重装；仅在资源或安装配置改变时重测安装包。

## 尚需验证与交付限制

- `tauri dev` 窗口启动、安装后健康按钮的返回值，以及失联/超时/重试状态尚无逐项人工记录。自动测试和用户对安装窗口的反馈不替代这些步骤。
- 安装包包含 Python 后端源码，**不包含 Python 解释器及其依赖**。运行机器必须安装兼容环境，并设置 `MINDFLIP_PYTHON`。如未来要求无 Python 前置条件的独立发行版，应另做嵌入式 Python/sidecar 打包任务及安装后的实机验证。
- SQLite 初始化目前通过 `--init-db` 显式执行；健康探针不自动迁移数据库。这保持运行时健康与数据库状态分离。
