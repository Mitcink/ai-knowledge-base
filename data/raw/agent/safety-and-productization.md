# Safety、权限边界与产品化

Agent 真正上线之后，最大的风险通常不是“答得不够聪明”，而是“做了不该做的事，或者坏了以后没人知道为什么坏”。

最后核对日期：2026-07-26

## 1. 定义与边界

- Safety：防止越权、误操作、提示注入、脏数据污染和不受控执行
- Guardrails：对输入、输出、工具调用和流程进行自动约束
- Productization：把 demo 升级为可部署、可监控、可审计、可维护的系统

这三者必须一起设计。只做 Safety 不做运维，会变成“偶尔安全”；只做部署不做权限，会变成“稳定地危险”。

## 2. 安全风险主要来自哪里

### 2.1 工具越权

模型可以决定动作时，风险就从“生成错误文本”升级成“执行错误动作”。

典型风险：

- 发错消息
- 改错数据
- 删除或覆盖文件
- 访问不该访问的第三方系统

### 2.2 提示注入与外部内容污染

只要 Agent 会读网页、文档、邮件、工单、PR 评论，外部内容就可能反过来影响其行为。

### 2.3 远程 MCP 与连接器风险

MCP 让接入更标准，但也意味着更多外部 server、更多数据出口和更多权限边界。

MCP 官方安全文档当前明确强调了授权、来源校验、会话安全和本地服务暴露风险。

## 3. 最低限度的防护层

上线前至少要有这几层：

1. 工具白名单
2. 参数 schema 校验
3. 高风险动作审批
4. 步数与超时上限
5. 运行日志和审计轨迹
6. 故障熔断与人工接管

如果缺任何一层，系统都会在某种情况下出现不可解释的危险行为。

## 4. 审批与人审策略

高风险动作建议一律走审批，例如：

- 发邮件
- 转账
- 改数据库
- 执行命令
- 写生产系统

审批不是 UI 提醒，而是流程状态的一部分。要能做到：

- 暂停
- 展示上下文
- 审批或拒绝
- 从暂停点恢复
- 记录责任链

## 5. MCP 安全落地建议

基于当前 MCP 官方规范与最佳实践，至少要注意：

- HTTP 传输校验 `Origin`
- 本地服务优先绑定 `localhost`
- 对需要用户数据或管理动作的 server 开启授权
- 不把 token 透传给不该持有它的下游
- 对远程 MCP server 保留显式用户同意

如果你的 Agent 会动态接第三方 MCP，默认假设它们不可信更稳妥。

## 6. 从 demo 到产品的关键改造

### 6.1 可恢复执行

真实系统一定会中断。要能恢复：

- 中途暂停
- 工具失败
- 服务重启
- 人工审批后续跑

### 6.2 可观测性

至少要知道：

- 每次请求做了什么
- 哪一步失败
- 失败率是否升高
- 哪类工具最不稳定
- 哪个 Prompt 版本导致退化

### 6.3 成本与时延控制

上线后最常见的问题之一不是正确率，而是：

- 上下文太长
- 工具调用太多
- 步数失控
- 多 Agent 过度编排

因此要持续观察：

- 平均 token
- 平均步数
- 平均工具调用数
- P95 时延

### 6.4 版本与回滚

至少要可追踪这些版本：

- Prompt 版本
- 工具 schema 版本
- workflow 版本
- 模型版本
- eval 基线版本

否则出问题时很难快速定位。

## 7. 常见错误与避坑

### 7.1 以为“只读工具”就安全

读出来的内容本身也可能带注入、误导或脏数据，依然会影响后续动作。

### 7.2 审批只拦最终动作，不拦中间高风险查询

有些风险发生在最终动作之前，例如读取敏感数据、下载危险文件。

### 7.3 只有日志，没有结构化审计

纯文本日志不够。关键动作需要结构化记录，便于过滤、统计和追责。

## 8. 最小实践建议

1. 把工具按风险等级分层
2. 给高风险层统一审批
3. 给所有外部动作记录结构化审计
4. 给每次上线保留可对比的 eval 基线
5. 先做可恢复，再做更复杂的自治

## 9. 资料来源

- OpenAI Guardrails and human review: <https://developers.openai.com/api/docs/guides/agents/guardrails-approvals>
- OpenAI MCP and Connectors: <https://developers.openai.com/api/docs/guides/tools-connectors-mcp>
- MCP Security Best Practices: <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
- MCP Authorization Tutorial: <https://modelcontextprotocol.io/docs/tutorials/security/authorization>
- MCP Authorization Spec (2025-06-18): <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- MCP Transport Security Notes (2025-06-18): <https://modelcontextprotocol.io/specification/2025-06-18/basic/transports>
- LangGraph Overview: <https://docs.langchain.com/oss/python/langgraph/overview>
- LangGraph Persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
