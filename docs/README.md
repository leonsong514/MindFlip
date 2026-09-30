# MindFlip 文档索引

- [架构基线](../Architecture%20Design%20Document%20v1.0.md)：产品边界、分层、路线图与仓库结构的权威来源。
- [仓库目录规划](development/iteration-01/01-repository-layout.md)：首次迭代应创建的目录、边界和依赖方向。
- [迭代 01 开发计划](development/iteration-01/02-development-plan.md)：任务拆分、接口契约、实施顺序及完成定义。
- [迭代 01 测试与验收](development/iteration-01/03-test-and-acceptance.md)：测试矩阵、可复现步骤、交接清单与故障场景。
- [迭代 01 复核记录](development/iteration-01/04-verification.md)：实际检查结果与仍需人工验证的项目。
- [ADR-IPC-001 IPC 传输选型（Accepted）](architecture/adr/0001-ipc-transport.md)：Tauri 与 Python 运行时之间的传输选型。
- [ADR-CFG-001 本地配置与凭证边界（Accepted）](architecture/adr/0002-config-and-credentials.md)：普通配置与敏感凭据的隔离规则。
- [迭代 02 Engineering Reliability](development/iteration-02/README.md)：Issues #5–#8 的范围、开发计划、17 条 AC 测试映射与验证模板。

迭代 01 已实现基础工程，开发规格与实际复核记录分别保留。首次迭代范围依据用户提供的 GitHub Project 前四项正文整理；Project 页面当时无法直接访问。迭代 02 Engineering Reliability 的本地实现已完成，AC7.1/AC7.2 仍需真实 PR 运行证据，详见[验证记录](development/iteration-02/03-verification.md)；真实 PR 触发需在 GitHub 上完成。
