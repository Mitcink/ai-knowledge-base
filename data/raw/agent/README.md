# Agent 知识库总览

这个目录用于系统化沉淀 AI Agent 全链路知识，不只记录概念，也强调工程实现与实践路径。

目标不是收集一堆“看过但用不上”的材料，而是逐步搭建一套你可以真正掌握、实现、维护、演进的 Agent 方法论和工程体系。

## 知识范围

当前计划覆盖这些主题：

- Prompt：提示词设计、上下文组织、约束与输出协议
- Agent：单智能体、多智能体、规划与执行模式
- Skill：可复用能力封装、工具编排、任务模板
- Hook：事件拦截、生命周期扩展、观测点注入
- Harness：用于评测、回放、对比、验收的执行环境与测试基座
- Loop：感知、决策、执行、反思、重试、终止机制
- Memory：短期上下文、长期记忆、知识检索、状态存储
- Tool Use：API、函数调用、浏览器、数据库、代码执行
- Workflow：工作流编排、状态机、图式编排、人工介入
- Eval：自动评测、回归测试、数据集、线上观测
- Safety：权限边界、越权防护、工具沙箱、审计
- Productization：部署、监控、成本、稳定性、权限和协作

## 建议阅读顺序

如果你是从 0 到 1 搭一套 Agent，建议按这个顺序学习：

1. [建设路线图](./roadmap.md)
2. [Agent 快速入门](./agent-basics.md)
3. [核心术语表](./glossary.md)
4. [Prompt 与上下文工程](./prompt-context-engineering.md)
5. [Tool、Skill 与 MCP](./tool-skill-and-mcp.md)
6. [Memory、State 与上下文管理](./memory-state-and-context.md)
7. [Loop、Workflow 与 Human-in-the-Loop](./loop-workflow-and-human-review.md)
8. [Harness、Eval 与观测](./harness-eval-and-observability.md)
9. [Safety、权限边界与产品化](./safety-and-productization.md)
10. [主流 Agent 框架与平台](./frameworks-and-platforms.md)
11. [真实业务里的 Agent 模式](./real-world-agent-patterns.md)

## 知识库写法

这里的每篇文档尽量采用统一结构：

1. 定义与边界
2. 核心原理
3. 常见架构模式
4. 工程实现方式
5. 常见错误与避坑
6. 最小可运行示例或实践建议

## 当前阶段

第一阶段先打基础，不急着追求“大而全”，而是先建立：

- 稳定的信息架构
- 统一术语
- 可持续扩展的文档模板
- 一条可执行的 Agent 学习与搭建路径

## 当前已落库专题

- [Prompt 与上下文工程](./prompt-context-engineering.md)
- [Tool、Skill 与 MCP](./tool-skill-and-mcp.md)
- [Memory、State 与上下文管理](./memory-state-and-context.md)
- [Loop、Workflow 与 Human-in-the-Loop](./loop-workflow-and-human-review.md)
- [Harness、Eval 与观测](./harness-eval-and-observability.md)
- [Safety、权限边界与产品化](./safety-and-productization.md)
- [主流 Agent 框架与平台](./frameworks-and-platforms.md)
- [真实业务里的 Agent 模式](./real-world-agent-patterns.md)
