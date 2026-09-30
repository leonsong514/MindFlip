# MindFlip Desktop

迭代 01 任务 1 与任务 3 的交付：Tauri 2 + React + TypeScript + Vite 桌面壳，集成健康 IPC 面板。单根视图渲染 MindFlip 占位内容与健康检查入口；业务决策功能不在本迭代范围。

## 前置条件

- Node.js v24.x（已验证 v24.18.0）
- npm v11.x（已验证 v11.16.0）
- Rust stable-x86_64-pc-windows-msvc（已验证 1.98.1）
- Microsoft Edge WebView2 Runtime
- MSVC x64 工具链（cargo 自动通过 vswhere 发现，本机已验证可链接）

安装依赖：

```powershell
cd apps\desktop
npm install
```

## 开发启动

```powershell
cd apps\desktop
npm run tauri -- dev
```

首次启动会自动执行 `npm run dev` 启动 Vite，并由 Tauri 打开 WebView2 窗口。

## 类型检查与生产构建

前端类型检查：

```powershell
cd apps\desktop
npm run typecheck
```

前端生产构建（Vite 输出到 `dist/`）：

```powershell
cd apps\desktop
npm run build
```

Tauri 桌面生产构建（Rust release + 安装包/可执行产物）：

```powershell
cd apps\desktop
npm run tauri -- build
```

产物位于 `src-tauri\target\release\mindflip-desktop.exe` 与 `src-tauri\target\release\bundle\`。
Tauri 资源配置会把后端 `app/`、`migrations/` 和 `alembic.ini` 放入安装包的 `backend/` 资源目录。当前版本不内嵌 Python 解释器；在运行产物前设置 `MINDFLIP_PYTHON` 为已安装后端依赖的 `python.exe` 绝对路径。开发模式可使用 PATH 中的 Python，或同样设置该变量。

## Lint / 格式 / 测试

迭代 02 引入 ESLint 9、Prettier 3 和 Vitest 2 作为前端质量工具链；命令在 `package.json` 的 `scripts` 中，与 CI 复用同一调用。

```powershell
cd apps\desktop
npm run lint          # ESLint
npm run typecheck     # tsc --noEmit
npm run format:check  # Prettier（不修改文件）
npm run test          # Vitest
```

或通过仓库根目录脚本一次跑完：

```powershell
.\scripts\lint-frontend.ps1     # ESLint + typecheck
.\scripts\test-frontend.ps1     # format:check + Vitest
```

`tsconfig.json` 的 `paths` 别名 `@/*` 已通过 `vitest.config.ts` 同步提供给测试。

## 项目结构

```text
apps/desktop/
├── src/                       React 入口、视图、样式
│   ├── api/                   typed invoke 封装
│   └── features/health/       健康面板 UI（idle/loading/ok/error）
├── src-tauri/                 Tauri Rust 主机
│   ├── src/
│   │   ├── main.rs            入口
│   │   ├── lib.rs             桌面生命周期、health_check_command
│   │   └── health.rs          stdio 子进程调用 + 超时 + 错误码映射
│   ├── capabilities/          最小 capability（仅 core:default）
│   ├── icons/                 应用图标
│   └── tauri.conf.json        Tauri 配置
├── index.html                 Vite HTML 入口
├── package.json               前端依赖与脚本
├── tsconfig.json              TypeScript 编译选项
├── vite.config.ts             Vite 配置（含 HMR、端口固定 1420）
└── README.md
```

## 验证记录

- `npx tsc --noEmit` 退出码 0
- `npm run lint` 退出码 0（迭代 02 引入 ESLint 9）
- `npm run format:check` 退出码 0（迭代 02 引入 Prettier 3）
- `npm run test` 退出码 0，2 passed（迭代 02 引入 Vitest 2）
- `npm run build` 退出码 0，产出 `dist/index.html` + `dist/assets/*`
- `cargo check --release` 退出码 0
- `npm run tauri -- build` 退出码 0，生成 MSI 与 NSIS 安装包；WiX 清单包含后端源码和迁移文件，无 `__pycache__`
- `cargo test --release --lib health` 退出码 0，4 passed（含 Rust → Python 真实链路）

Tauri 端启动与窗口验证按迭代 01 测试与验收手册 T01/T03 由人工执行（窗口启动需要交互式桌面会话，不在 headless 自动化范围）。

## 后续迭代

- 后续迭代才会引入 Tailwind、shadcn、Agent、模型供应商或决策业务代码
- 已通过 IPC 通道的 health IPC 将在新业务方法中沿用同一信封
