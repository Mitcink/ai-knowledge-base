# Loop、Workflow 与 Human-in-the-Loop

Agent 能否真正落地，关键不在“会不会调工具”，而在“如何循环、何时暂停、怎么恢复、谁来兜底”。

最后核对日期：2026-07-26

## 1. 定义与边界

- Loop：单个 Agent 的感知、决策、执行、观察、更新循环
- Workflow：把多个步骤、分支、状态迁移明确建模出来
- Human-in-the-Loop：在关键节点引入人工确认、补充输入或直接接管

Loop 更像控制核心，Workflow 更像外层编排。

## 2. 什么时候用 Loop，什么时候上 Workflow

### 2.1 只用 Loop

适合：

- 任务短
- 工具少
- 分支有限
- 失败代价低

### 2.2 上 Workflow

适合：

- 步骤明确
- 分支条件多
- 需要重试和回放
- 需要人工审批
- 需要多个子 Agent 协作

LangGraph 官方文档把二者区分得很清楚：workflow 更偏预设路径，agent 更偏动态路径。真实系统经常是二者混合。

## 3. 推荐的控制闭环

一个稳妥的最小闭环通常是：

1. 读取状态
2. 判断当前阶段
3. 决定直接回答、调工具或请求人工输入
4. 执行动作
5. 写回结果
6. 判断是否继续、重试或终止

其中必须显式定义：

- `max_steps`
- `timeout`
- `retry_policy`
- `termination_condition`

## 4. Human-in-the-Loop 应该放在哪

最常见的人工介入点有三类：

- 高风险动作前
- 不确定性过高时
- 最终结果出站前

OpenAI 当前 guardrails 文档把 approvals 作为敏感工具调用前的暂停机制；LangGraph 则把 `interrupt()` 作为可持久化暂停点。这两种设计都说明：人工介入不是补丁，而应是主流程的一部分。

## 5. Workflow 的推荐拆法

### 5.1 按节点职责拆

- 读取输入
- 分类或路由
- 检索
- 动作执行
- 结果整合
- 审批
- 输出

### 5.2 按失败恢复点拆

如果某一步失败后需要独立重试、单独观察或人工恢复，它就应该是独立节点。

### 5.3 按状态边界拆

只要某一步产出的状态会被后续多处复用，就不要把它埋在一个大节点内部。

## 6. 多 Agent 放进 Workflow 的原则

多 Agent 不是越多越好。只有当存在清晰分工时才值得引入，例如：

- Planner 负责拆解
- Researcher 负责找资料
- Executor 负责动作执行
- Reviewer 负责验收

OpenAI 的多智能体与编排文档、AutoGen 的 AgentChat / Teams 模型，都体现了同一个结论：多 Agent 的核心价值是分工，而不是“让更多模型一起想”。

## 7. 常见错误与避坑

### 7.1 把所有逻辑塞进一个 while 循环

初期能跑，后期会很难：

- 定位问题
- 做局部重试
- 插人工节点
- 观察成本

### 7.2 没有恢复点

如果流程中断后只能重跑全部步骤，说明你的 workflow 粒度太粗。

### 7.3 审批只做 UI，不做状态保存

审批节点必须保存可恢复快照，否则人工确认之后很难无损续跑。

## 8. 最小实践建议

1. 单 Agent 阶段先做显式状态机，而不是无限自由循环
2. 对高风险工具加审批节点
3. 给每个可失败节点定义重试上限
4. 让暂停、恢复和终止都能从状态层面解释

## 9. 资料来源

- LangGraph Workflows and agents: <https://docs.langchain.com/oss/python/langgraph/workflows-agents>
- LangGraph Thinking in LangGraph: <https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph>
- LangGraph Interrupts: <https://docs.langchain.com/oss/python/langgraph/interrupts>
- OpenAI Orchestration and handoffs: <https://developers.openai.com/api/docs/guides/agents/orchestration>
- OpenAI Guardrails and human review: <https://developers.openai.com/api/docs/guides/agents/guardrails-approvals>
- OpenAI Multi-agent guide: <https://developers.openai.com/api/docs/guides/responses-multi-agent>
- AutoGen AgentChat: <https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html>
