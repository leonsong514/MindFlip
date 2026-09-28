# 迭代 02：开发计划（待填写）

## 任务来源

尚未取得迭代 02 的 GitHub Project 条目。此文件是交接模板，不表示已批准或开始任何功能。填表时粘贴任务标题、链接、Goal、Scope、Acceptance Criteria 与 Testing；若 Project 内容不可访问，请让用户提供原文。

| Project 条目 | 目标与范围 | 验收条件 | 本地交付文件 | 状态 |
| --- | --- | --- | --- | --- |
| 待补 | 待补 | 待补 | 待补 | 未开始 |

## 实施前设计检查

1. 对照[架构基线](../../../Architecture%20Design%20Document%20v1.0.md)，确认领域模型、应用 API、Tauri 和 React 的职责边界。
2. 指出涉及现有 `packages/contracts` 协议、SQLite 迁移和数据兼容性的变更；若需要改变已接受的 IPC 决定，先新增或修订 ADR。
3. 只建立当前任务要用的目录、类型和依赖；不为未来 Agent、插件、云同步预留空实现。
4. 写出每项任务的实现顺序、失败/回滚行为及可复现的完成定义，再进入编码。

## 已有技术边界

React feature 调用 `src/api`；Rust 负责桌面/系统边界；Python API 接领域服务；SQLite 由 persistence 层管理。当前 `health/check` 与数据库无关，`storage_probe` 只是技术验证表。详情见[迭代 01 开发规格](../iteration-01/02-development-plan.md)和[交接入口](README.md)。
