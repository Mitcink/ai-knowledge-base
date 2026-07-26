# 主流 Agent 框架与平台

本文不做 API 手册搬运，只从“适合解决什么问题”这个角度整理当前主流路线。

最后核对日期：2026-07-26

## 1. OpenAI Agents / Responses

适合：

- 以模型、工具、审批、结果状态为核心的应用
- 需要快速接入 Hosted Tools、MCP、连接器
- 希望减少底层协议样板代码

当前特征：

- Responses API 是核心执行面
- 原生支持工具、函数调用、MCP
- Agents SDK 进一步封装 agent 定义、运行、guardrails、结果状态和评测

更适合“先做成可靠单 Agent 或小规模多 Agent”的路线。

## 2. LangGraph

适合：

- 需要明确状态图和恢复点
- 需要持久化、暂停恢复、人工介入
- 需要把确定性步骤和 agentic 步骤放在同一张图里

LangGraph 更像 orchestration runtime，而不是纯 Prompt 包装层。

如果你关心 durable execution、显式 state、interrupt、subgraph，这条路线很强。

## 3. AutoGen

适合：

- 明确要做多 Agent 协作
- 需要 AgentChat 或 Team 模式
- 想进一步下沉到事件驱动核心

AutoGen 当前分层比较清晰：

- AgentChat：高层多 Agent 开发入口
- Core：更灵活的事件驱动底层
- Extensions：接模型、MCP、代码执行等外部能力

## 4. Dify

适合：

- 希望快速搭可视化 workflow / chatflow
- 需要知识库、模型、工具、插件一体化
- 更重视业务落地速度而非底层控制

从当前官方文档看，Dify 已经把 Tool、Agent Strategy、Datasource、Trigger 等能力做成统一集成面，比较适合业务侧快速编排。

## 5. Coze / Coze Studio

适合：

- 偏可视化、平台化搭建
- 需要 prompt、workflow、plugin、knowledge 一体化资源管理
- 团队希望低代码加快交付

从当前官方快速开始与开源仓库描述看，Coze Studio 走的是“一站式 Agent 开发平台”路线。

## 6. MCP 作为跨框架底座

MCP 不是框架，但它越来越像跨框架能力层。

你可以把它看成：

- 框架无关的工具/资源接入标准
- 多系统能力暴露协议
- Host 与外部能力之间的标准桥

长期看，MCP 很可能成为“工具生态互通层”，而不是某一家框架的专属功能。

## 7. 选型建议

### 7.1 从零开始做可控单 Agent

优先考虑：

- OpenAI Responses / Agents
- LangGraph

### 7.2 明确要做多 Agent 协作

优先考虑：

- AutoGen
- LangGraph + subgraph / handoff 模式
- OpenAI 多 Agent 编排

### 7.3 先要业务落地速度

优先考虑：

- Dify
- Coze / Coze Studio

### 7.4 先要统一工具集成

优先考虑：

- 支持 MCP 的路线

## 8. 常见错误与避坑

### 8.1 先学框架 API，后补概念

这会导致你会“搭框架 demo”，但不会设计可维护的 Agent。

### 8.2 用平台替代工程判断

可视化平台能加速搭建，但不能替你定义边界、评测、安全和恢复策略。

## 9. 资料来源

- OpenAI Learn / Agents SDK 索引: <https://developers.openai.com/learn>
- OpenAI Agent definitions: <https://developers.openai.com/api/docs/guides/agents/define-agents>
- OpenAI Orchestration and handoffs: <https://developers.openai.com/api/docs/guides/agents/orchestration>
- LangGraph Overview: <https://docs.langchain.com/oss/python/langgraph/overview>
- LangGraph Subgraphs: <https://docs.langchain.com/oss/python/langgraph/use-subgraphs>
- AutoGen Home: <https://microsoft.github.io/autogen/stable/>
- AutoGen AgentChat: <https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html>
- AutoGen Workbench and MCP: <https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/workbench.html>
- Dify Quick Start: <https://docs.dify.ai/en/quick-start>
- Dify Plugin: <https://docs.dify.ai/en/develop-plugin/getting-started/getting-started-dify-plugin>
- Dify Integrations: <https://docs.dify.ai/en/self-host/use-dify/workspace/plugins>
- Coze Quickstart: <https://docs.coze.com/guides/quickstart>
- Coze Studio 开源仓库: <https://github.com/coze-dev/coze-studio>
