# 真实业务里的 Agent 模式

比起“行业案例合集”，更值得沉淀的是可重复套用的任务模式。

最后核对日期：2026-07-26

## 1. 知识问答与客服 Agent

目标：

- 从知识库检索事实
- 结合上下文组织回答
- 降低人工客服压力

关键组件：

- 检索
- 引用或证据传递
- 人工兜底
- 长文档分块质量控制

适用边界：

- 事实性问题多
- 业务规则相对稳定
- 容忍“答不上来”，不能容忍“编错”

## 2. 浏览器与操作型 Agent

目标：

- 在真实系统里执行步骤
- 读取页面状态
- 根据反馈继续操作

关键组件：

- 工具权限边界
- 步数上限
- 审批与回滚
- 过程日志

适用边界：

- 步骤有反馈闭环
- 动作可审计
- 失败代价可控

## 3. 代码与仓库协作 Agent

目标：

- 阅读代码
- 修改文件
- 跑测试
- 提交或生成 review

关键组件：

- 工具约束
- 文件 diff 审计
- 测试 harness
- Git 工作流

适用边界：

- 仓库结构清晰
- 任务可拆分
- 能通过测试或 review 验收

## 4. 多 Agent 研究与报告生成

目标：

- 把复杂研究任务拆给不同角色
- 汇总和审校结果

关键组件：

- 明确角色分工
- 共享状态
- 汇总与冲突消解
- 终稿验收

适用边界：

- 存在天然分工
- 单个 Agent 上下文压力过大

## 5. 业务流程自动化 Agent

目标：

- 接事件
- 做判断
- 调用企业系统
- 触发后续流程

关键组件：

- workflow 编排
- 结构化状态
- 权限模型
- 审批和失败恢复

适用边界：

- 流程清晰
- 需要系统集成
- 对稳定性和审计要求高

## 6. 模式选择建议

如果你当前项目主要是知识库与 Agent 方法论沉淀，最值得优先补实践的其实是这三类：

1. 知识问答 Agent
2. 代码协作 Agent
3. 业务流程自动化 Agent

因为它们刚好覆盖：

- 检索
- 工具调用
- 状态管理
- 审批
- 评测

## 7. 常见错误与避坑

### 7.1 先做“通用万能 Agent”

真实落地几乎都从垂直任务开始。任务边界越清晰，成功率越高。

### 7.2 案例只记结果，不记失败机制

知识库里最有价值的部分不是“它能做什么”，而是“它为什么不会轻易失控”。

## 8. 资料来源

- OpenAI Multi-agent guide: <https://developers.openai.com/api/docs/guides/responses-multi-agent>
- OpenAI Guardrails and human review: <https://developers.openai.com/api/docs/guides/agents/guardrails-approvals>
- AutoGen Examples: <https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/examples/index.html>
- Dify Customer Service Bot With Knowledge Base: <https://docs.dify.ai/en/learn/tutorials/customer-service-bot>
