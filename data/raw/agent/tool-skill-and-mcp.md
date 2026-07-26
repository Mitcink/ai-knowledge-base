# Tool、Skill 与 MCP

本文讨论 Agent 的“外部能力层”。如果 Prompt 解决的是理解问题，那么 Tool、Skill 和 MCP 解决的是执行问题。

最后核对日期：2026-07-26

## 1. 定义与边界

- Tool：单一能力接口，例如搜索、查库、发请求、执行代码
- Skill：为某类任务封装的一组固定流程、规则和工具组合
- MCP：让模型以标准协议连接外部工具、资源与提示的一层集成协议

可以把它们理解为三个抽象层级：

`Tool < Skill < MCP 集成面`

其中 MCP 不等于某个具体工具，而是让外部能力可被发现、调用、审计和复用的一套标准接口。

## 2. Tool 设计原则

### 2.1 单一职责优先

一个 Tool 只解决一个动作，效果通常比“万能工具”更稳定。

好工具的特征：

- 名称明确
- 输入参数少且稳定
- 输出结构固定
- 失败模式可感知

### 2.2 输入输出要可验证

OpenAI 当前函数调用文档明确支持更严格的 schema 约束。对需要稳定执行的业务工具，优先使用严格模式与明确 schema。

工程建议：

- 参数使用对象 schema
- `required` 字段显式声明
- `additionalProperties: false`
- 输出也尽量结构化

### 2.3 决策权与执行权分离

模型负责“是否调用”和“用什么参数”，代码负责：

- 参数校验
- 权限校验
- 实际执行
- 错误标准化
- 审计日志

不要让模型直接拼 shell 或 SQL 然后无约束执行。

## 3. Skill 设计原则

Skill 不是“更多工具”，而是“已经验证过的一段高频解决方案”。

适合做成 Skill 的场景：

- 同类任务总是按固定步骤走
- 工具组合稳定
- 有重复出现的约束和最佳实践
- 需要把复杂度从主 Agent 中抽离

典型 Skill 例子：

- PR Review
- 文档润色
- 数据采集与清洗
- 测试失败定位

Skill 的价值在于减少主 Agent 的即时推理负担，让模型少做一次“怎么做”的选择题。

## 4. MCP 的工程意义

MCP 当前官方架构是 Host / Client / Server 模式。Host 是 Agent 应用，Client 负责连接具体 Server，Server 对外暴露工具、资源或提示。

这带来几个实际收益：

- 能力接入标准化
- 工具发现与描述一致化
- 多服务集成成本下降
- 更容易做权限与审批

如果你要接很多第三方系统，MCP 往往比手写一堆 ad-hoc tool wrapper 更适合长期维护。

## 5. 什么时候直接 Tool，什么时候 Skill，什么时候 MCP

### 5.1 直接 Tool

适合：

- 单次查询
- 单次动作
- 参数简单
- 没有额外编排需求

### 5.2 Skill

适合：

- 多步但稳定的流程
- 同类任务重复出现
- 需要沉淀最佳实践

### 5.3 MCP

适合：

- 需要接多种外部系统
- 希望统一能力注册与发现
- 需要远程工具服务
- 需要统一审批与审计入口

## 6. 安全与审批

当前 OpenAI 关于 MCP 和连接器的文档已经明确提醒：远程 MCP 服务本质上是第三方服务，默认需要谨慎审批，尤其是在数据发送和敏感动作上。

落地时建议：

- 默认开启审批
- 只信任官方或自托管服务
- 记录发往第三方 MCP 的数据
- 对 URL、文件、下载结果做额外校验
- 区分“可自动执行工具”和“必须人工确认工具”

## 7. 常见错误与避坑

### 7.1 工具太粗

把“搜索、过滤、排序、下单、发送通知”混进一个工具，模型很难稳定调用。

### 7.2 Skill 只是 Prompt 别名

如果没有固定流程、固定边界和复用价值，它只是另一个 Prompt，不是 Skill。

### 7.3 接了 MCP 就默认可信

MCP 解决的是协议一致性，不自动解决安全问题。第三方 server 仍然可能注入脏数据、恶意提示或越权动作。

## 8. 最小实践建议

1. 先写 3 到 5 个单一职责工具
2. 用真实任务回放找出稳定流程
3. 再把稳定流程升级为 Skill
4. 当外部系统接入增多时，再引入 MCP 作为统一能力面

## 9. 资料来源

- OpenAI Using tools: <https://developers.openai.com/api/docs/guides/tools>
- OpenAI Function calling: <https://developers.openai.com/api/docs/guides/function-calling>
- OpenAI Programmatic Tool Calling: <https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling>
- OpenAI MCP and Connectors: <https://developers.openai.com/api/docs/guides/tools-connectors-mcp>
- OpenAI Secure MCP Tunnel: <https://developers.openai.com/api/docs/guides/secure-mcp-tunnels>
- MCP Architecture: <https://modelcontextprotocol.io/docs/learn/architecture>
- MCP Tools Spec (2025-06-18): <https://modelcontextprotocol.io/specification/2025-06-18/server/tools>
