# MindFlip Backend Python Runtime

迭代 01 任务 2、3、4 的交付：独立可启动的 Python 包，提供确定性健康服务、stdio IPC 适配以及 SQLite 持久化底座。

## 依赖与运行环境

- Python 3.11+（已验证 3.12.14）
- 运行所需第三方包：SQLAlchemy 2.x、alembic 1.13+
- 开发依赖：pytest

`pyproject.toml` 声明直接依赖与版本范围；`requirements.lock` 固定本轮 Windows/Python 3.12 环境中的直接和传递依赖。新环境由 conda 安装 Python，再由 pip 安装锁文件；不要让 conda 和 pip 分别管理同一个包。

## 独立启动

先从仓库根目录进入 `apps/backend`。健康探针确定性返回 `status: ok`；时间戳会随请求变化：

```powershell
cd apps/backend
conda run -n mindflip python -m app --health
```

初始化或升级应用数据目录中的 SQLite：

```powershell
conda run -n mindflip python -m app --init-db
```

stdio IPC 引擎（读取一行 envelope、写入一行响应后退出）：

```powershell
conda run -n mindflip python -m app.ipc_main
```

查看版本：

```powershell
conda run -n mindflip python -m app --version
```

## 单元与集成测试

```powershell
conda run -n mindflip python -m pytest tests -q
```

预期：**23 passed, 1 skipped**（Windows 上跳过只读目录诊断测试）。

测试覆盖：

- 健康服务（确定性 OK、CLI 子进程单行 JSON 输出、不依赖数据库）
- IPC 引擎（envelope 解析、未知方法、无效协议、子进程往返）
- 持久化（迁移记录、插入/提交/重开数据保留、重复升级不清空、失败事务回滚、健康服务与数据库解耦）

## 数据库与迁移

应用数据目录解析：

- `MINDFLIP_DATA_DIR` 环境变量（测试与覆盖）
- 否则 Windows 使用 `%APPDATA%\MindFlip`，macOS 使用 `~/Library/Application Support/MindFlip`，Linux 使用 `$XDG_DATA_HOME/MindFlip`

数据库位于 `<data_dir>/database/app.db`。显式运行 `--init-db` 时通过 Alembic 创建 `storage_probe` 技术表；健康检查不会初始化数据库。迭代 01 不引入任何业务实体。

## 项目结构

```text
apps/backend/
├── app/
│   ├── __init__.py
│   ├── __main__.py            CLI 入口：--version / --health
│   ├── ipc_main.py            stdio IPC 引擎入口（python -m app.ipc_main）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py          健康服务（stdlib + dataclass，零三方运行时依赖）
│   │   └── ipc.py             IPC envelope 解析、dispatch、错误响应构造
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── paths.py           应用数据目录解析、SQLite URL 构造
│   │   ├── engine.py          SQLAlchemy 2 engine / session 工厂、PRAGMA 事件
│   │   ├── models.py          DeclarativeBase 与 storage_probe 技术表
│   │   └── migrate.py         alembic upgrade / current_revision 封装
│   └── runtime/
│       └── __init__.py
├── migrations/
│   ├── env.py                 alembic env，加载 app.persistence.models
│   └── versions/
│       └── 0001_initial.py    唯一迁移：创建 storage_probe
├── tests/
│   ├── conftest.py            将项目根加入 sys.path
│   ├── test_health.py
│   ├── test_ipc.py
│   └── test_persistence.py
├── alembic.ini                alembic 配置（script_location = migrations）
├── pyproject.toml             PEP 621 项目元数据
├── requirements.lock          Windows/Python 3.12 固定版本依赖列表
└── README.md
```

## 验证记录

- `python -m pytest tests -q -p no:cacheprovider --basetemp <writable-test-dir>` 退出码 0，**23 passed, 1 skipped**（2026-09-29）
- 健康链路端到端验证见 `apps/desktop` 的 `cargo test --release --lib health`（4 passed，含真实 Rust → Python 子进程）

## 后续迭代

- 任务 5+：引入 `app/decisions/`、`app/agent/`、`app/models/`、`app/tools/`、`app/evidence/` 等业务目录
- 业务迁移将替代 `storage_probe` 技术表
- 顶层 IPC 路由器与并发取消将在后续迭代完善
