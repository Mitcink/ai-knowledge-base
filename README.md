# AI Knowledge Base

这是一个长期维护的 AI 知识库项目。当前仓库一方面承载 RAG 知识库系统本身，另一方面开始沉淀面向 Agent 开发全链路的知识文档。

这次已经完成第一批 Agent 文档落库，后续会按主题持续扩充，不做“资料堆积”，而是做筛选、纠错、重组后的可维护知识库。

## 当前重点

- 维护这个知识库系统本身的架构、部署和工作流文档
- 系统化沉淀 Agent 开发全链路知识
- 一边整理资料，一边形成一条从 0 到 1 搭建 Agent 的学习与实践路径

## 文档入口

- [文档总览](./docs/README.md)
- [Agent 知识库总览](./docs/agent/README.md)
- [建设路线图](./docs/agent/roadmap.md)
- [Agent 快速入门](./docs/agent/agent-basics.md)
- [核心术语表](./docs/agent/glossary.md)
- [资料筛选与沉淀原则](./docs/agent/curation-policy.md)

## 项目结构

```text
ai-knowledge-base/
|-- app/                     # FastAPI API 与 RAG 服务
|-- ui/                      # Streamlit 工作台
|-- scripts/                 # 导入与运维脚本
|-- docs/                    # 项目文档与 Agent 知识文档
|-- data/
|   |-- raw/                 # 原始资料
|   |-- processed/           # 预留目录
|   `-- uploads/             # Web 上传文件
|-- tests/
|-- docker-compose.yml
|-- Dockerfile.api
|-- Dockerfile.ui
`-- .env.example
```

## 本地启动

### 1. 准备环境变量

```powershell
Copy-Item .env.example .env
```

至少确认这些配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_MODEL`
- `QDRANT_URL`

默认 Docker Compose 环境中：

```env
QDRANT_URL=http://qdrant:6333
```

### 2. 启动服务

```powershell
docker compose up --build
```

启动后可访问：

- UI: [http://localhost:8501](http://localhost:8501)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Qdrant: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

## 导入资料

### 方案 A：同步 `data/raw/`

把长期维护的资料放入 `data/raw/`，然后通过 UI 执行同步，或直接运行：

```powershell
docker compose exec api python scripts/ingest.py
```

### 方案 B：通过 Web 上传

适合补充零散文档，上传后即时解析并写入索引。

当前支持：

- `.md`
- `.markdown`
- `.txt`
- `.pdf`

## 已有项目文档

- [架构说明](./docs/architecture.md)
- [部署说明](./docs/deployment.md)
- [GitHub 工作流](./docs/github-workflow.md)

## 下一步

接下来会按批次继续补充这些主题：

- Prompt
- Tool / Skill / Loop
- Memory / Workflow / Hook
- Harness / Eval
- 主流 Agent 框架与真实业务案例
