# 文档总览

这个仓库现在包含两类文档：

- 项目运行与维护文档：面向当前知识库系统本身
- AI Agent 知识文档：面向后续持续沉淀的 Agent 全链路知识体系

## 项目文档

- [架构说明](./architecture.md)
- [部署说明](./deployment.md)
- [GitHub 工作流](./github-workflow.md)

## AI Agent 知识库

以下正文已经迁到 `data/raw/agent/`，这样系统同步 `data/raw/` 时可以直接识别并入库：

- [Agent 知识库总览](../data/raw/agent/README.md)
- [建设路线图](../data/raw/agent/roadmap.md)
- [Agent 快速入门](../data/raw/agent/agent-basics.md)
- [核心术语表](../data/raw/agent/glossary.md)
- [资料筛选与沉淀原则](../data/raw/agent/curation-policy.md)

## 维护约定

- 优先沉淀可复用、可验证、可落地的内容
- 不直接堆原始材料，先筛选、纠错、重组，再入库
- 每篇文档尽量同时回答三个问题：
  - 这是什么
  - 为什么重要
  - 工程上怎么落地
- 每一批内容都尽量附带一个可执行的学习或搭建任务
