# Memory、State 与上下文管理

很多 Agent 项目不是死在模型能力上，而是死在“状态不知道放哪、放多久、什么时候取回”。

最后核对日期：2026-07-26

## 1. 定义与边界

- Context：本轮推理时实际送进模型的内容
- State：执行流程当前可读写的运行态
- Short-term memory：线程级、会话级、任务级记忆
- Long-term memory：跨会话、跨任务、跨线程的持久信息

这四者不能混为一谈。

最常见误区是：把 memory 等于“把历史对话都塞给模型”。这既贵，也不稳。

## 2. 推荐分层

### 2.1 短期记忆

存：

- 当前任务目标
- 最近几步动作
- 最近工具结果
- 当前草稿或中间产物

用途是支撑“这一次流程”跑完。

### 2.2 长期记忆

存：

- 用户偏好
- 常用配置
- 历史稳定事实
- 可跨任务复用的知识片段

用途是支撑“下次还记得你是谁、之前发生过什么”。

### 2.3 检索型外部知识

这不一定是 memory，更接近 knowledge retrieval。比如产品文档、工单库、代码仓库、运行手册。

不要把知识库和记忆库混成一套概念。

## 3. 核心原理

LangGraph 当前文档把短期记忆明确建模为 thread-scoped state，把长期记忆建模为跨线程 namespace 下的存储。这种分层很适合 Agent 工程实现。

工程上可以照着抽象：

- `thread_state`
- `user_memory`
- `workspace_memory`
- `retrieval_corpus`

然后为每层分别定义：

- 写入时机
- 读取时机
- 生命周期
- 删除策略

## 4. 状态应该存什么

适合放进 state 的内容：

- 后续步骤还会用到
- 重新计算成本高
- 需要审计或回放
- 需要跨节点传递

不适合直接存的内容：

- 可以即时推导出来的文本
- 大量重复日志
- 全量原始文档
- 已经过期的上下文

一个实用判断标准是：如果某信息不存，下一个节点还能廉价重建吗？能，就别存。

## 5. 记忆写入策略

### 5.1 先记录事实，再记录总结

长期记忆优先保存结构化事实，例如：

- 用户偏好的语言是中文
- 审批阈值为 1000 元
- 常用项目仓库是某地址

摘要型“印象”应谨慎写入，因为它最容易把偶发行为误当成长期偏好。

### 5.2 记忆写入要有触发条件

不要每轮都写长期记忆。常见触发条件：

- 用户显式声明偏好
- 人工确认保存
- 某事实在多次任务中重复出现
- 某结果已经通过验证

### 5.3 检索前先压缩上下文

长上下文会拖慢模型、抬高成本、降低专注度。应在每个关键节点前做：

- 截断
- 摘要
- 去重
- 只保留当前节点所需字段

## 6. 工程落地方式

一个最小但实用的状态模型可以分四层：

1. `session`
2. `working_state`
3. `memory_store`
4. `knowledge_store`

其中：

- `session` 管消息与会话元信息
- `working_state` 管任务执行过程
- `memory_store` 管跨任务持久信息
- `knowledge_store` 管可检索资料

## 7. 常见错误与避坑

### 7.1 把消息历史当成唯一状态

这样做的后果是：

- 解析成本越来越高
- 调试困难
- 很难局部恢复

### 7.2 长期记忆没有淘汰和纠错

长期记忆一旦写错，会持续污染后续任务。必须有：

- 更新规则
- 置信度
- 人工修正入口

### 7.3 用向量库存一切

并不是所有状态都适合向量检索。流程状态、布尔标记、审批结果更适合结构化存储。

## 8. 最小实践建议

1. 先把“当前任务状态”从聊天历史里拆出来
2. 再定义一个长期记忆表，只存少量高价值事实
3. 检索知识库与长期记忆分开维护
4. 每次回归测试都覆盖“旧状态恢复”和“长对话退化”

## 9. 资料来源

- LangGraph Memory Overview: <https://docs.langchain.com/oss/python/concepts/memory>
- LangGraph Thinking in LangGraph: <https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph>
- OpenAI Results and state: <https://developers.openai.com/api/docs/guides/agents/results>
- Dify Customer Service Bot With Knowledge Base: <https://docs.dify.ai/en/learn/tutorials/customer-service-bot>
