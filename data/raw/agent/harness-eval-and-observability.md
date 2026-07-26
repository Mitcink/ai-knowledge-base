# Harness、Eval 与观测

能跑起来不算完成。对 Agent 来说，真正难的是确认它“稳定地跑、可解释地坏、可回归地修”。

最后核对日期：2026-07-26

## 1. 定义与边界

- Harness：用于批量执行、回放、对比、验收的测试与运行基座
- Eval：衡量 Agent 质量的指标、数据集和运行方法
- Observability：对运行轨迹、状态变化、工具调用和失败点的可观测能力

Harness 不等于单元测试，Eval 不等于人工感觉“这次回答不错”。

## 2. 为什么要先建 Harness

如果没有 Harness，Prompt、工具、workflow 每改一次，你都只能手工点一遍。这样会带来三类问题：

- 无法稳定复现问题
- 无法比较版本优劣
- 无法发现局部优化导致的整体退化

所以 Harness 的地位应该接近“Agent 的 CI 基座”。

## 3. Eval 应该评什么

最少要覆盖四类问题：

- 任务是否完成
- 工具是否调用正确
- 输出是否符合结构或事实要求
- 新版本是否回归

如果系统会执行外部动作，还要加：

- 是否触发了不该触发的动作
- 是否在阈值内完成审批

## 4. 推荐的评测分层

### 4.1 样例级回放

少量高价值 case，适合快速回归。

### 4.2 数据集级批跑

当你已经知道什么叫“好”，就应把这些标准固化为 dataset 与 eval run。这样才能比较 Prompt、工具或流程版本。

### 4.3 线上观测

离线全绿不代表线上安全。线上还要观察：

- 失败率
- 人工接管率
- 工具错误率
- 平均步数
- 平均时延
- 成本

## 5. Harness 的最小组成

一个实用最小集可以包括：

1. 固定输入样例集
2. 可重放的工具桩或沙箱
3. 输出断言
4. 运行日志与轨迹
5. 基线结果快照

如果支持 workflow 级中断恢复，还要能测试：

- 中途暂停
- 人工批准后恢复
- 超时重试
- 局部节点失败

## 6. 观测要看什么

至少记录这些数据：

- 用户目标
- 每一步决策
- 每次工具调用参数
- 工具返回值摘要
- 终止原因
- 失败原因
- 审批点

这些数据既服务调试，也服务后续做 eval dataset。

## 7. 常见错误与避坑

### 7.1 只评最终答案

最终答案对了，不代表过程对了。可能只是偶然答对，却走了危险路径。

### 7.2 样例全是 happy path

必须覆盖：

- 空结果
- 工具超时
- 部分数据缺失
- 审批拒绝
- 长上下文退化

### 7.3 没有基线快照

没有基线，后续任何优化都无法证明真的更好。

## 8. 最小实践建议

1. 先建 20 个固定高价值任务样例
2. 为每个样例定义“完成标准”
3. 记录每次版本变更前后的通过率与关键指标
4. 把线上失败样例持续回灌到离线 eval 集

## 9. 资料来源

- OpenAI Working with evals: <https://developers.openai.com/api/docs/guides/evals>
- OpenAI Evaluate agent workflows: <https://developers.openai.com/api/docs/guides/agent-evals>
- LangGraph Test: <https://docs.langchain.com/oss/python/langgraph/test>
- LangGraph Persistence: <https://docs.langchain.com/oss/python/langgraph/persistence>
- LangGraph Thinking in LangGraph: <https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph>
