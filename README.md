# AI Knowledge Base

一个适合个人长期维护的 AI 知识库项目，目标不是做一次性 demo，而是做成可以持续导入、持续检索、持续使用的资料工作台。

当前版本提供：

- 文档上传与批量同步
- Markdown、TXT、PDF 入库
- 基于 RAG 的问答与引用返回
- 文档管理与索引状态查看
- FastAPI + Streamlit 双端结构
- Docker Compose 一键启动

## 产品形态

项目分成两层：

- `app/`：FastAPI API、RAG 编排、文档解析、向量存储访问
- `ui/`：Streamlit 工作台，负责问答、同步、上传和文档管理

知识库的推荐使用流程：

1. 把长期资料放到 `data/raw/`
2. 用“一键同步原始目录”建立索引
3. 用上传入口补充零散文件
4. 通过问答页验证召回与回答质量
5. 在文档管理页清理旧文件或孤立索引

## 项目结构

```text
ai-knowledge-base/
├─ app/                   # FastAPI API 与 RAG 服务
├─ ui/                    # Streamlit 工作台
├─ scripts/               # 批量导入脚本
├─ data/
│  ├─ raw/                # 长期维护的原始资料
│  ├─ processed/          # 预留目录
│  └─ uploads/            # Web 上传文件
├─ docs/
├─ docker-compose.yml
├─ Dockerfile.api
├─ Dockerfile.ui
└─ .env.example
```

## 核心能力

### 1. 智能问答

- 输入问题后进行向量召回
- 使用轻量关键词重排提升相关性
- 返回回答时附带引用片段
- 展示召回候选数与引用数，便于调试效果

### 2. 同步与上传

- 支持一键同步 `data/raw/`
- 支持单文件上传后即时入库
- 重复导入同一文件时会先清理旧索引，避免重复片段

### 3. 文档管理

- 查看文档总数、已索引数量、孤立索引
- 按分类、存储区域、索引状态筛选
- 删除原文件、删除索引，或两者同时删除

### 4. 系统概览

- 展示 OpenAI 配置是否完整
- 展示 Qdrant 是否可达
- 展示知识库文档数、索引数、片段数

## 本地启动

### 1. 准备环境变量

```powershell
Copy-Item .env.example .env
```

至少需要确认这些配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_MODEL`

默认情况下，Docker 内的 Qdrant 地址已经配置为：

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

## 首次导入资料

### 方案 A：放入原始目录后批量同步

把资料放到 `data/raw/`，然后在 UI 中点击“一键同步原始目录”。

也可以直接执行脚本：

```powershell
docker compose exec api python scripts/ingest.py
```

### 方案 B：通过 Web 上传

适合少量补充文档，上传后会立即写入索引。

## 支持的文件类型

- `.md`
- `.markdown`
- `.txt`
- `.pdf`

文本文件优先按 `utf-8` 读取，也兼容常见中文编码回退。

## 环境变量

`.env.example` 中已经包含默认值，常用项如下：

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=knowledge_base
RAW_DATA_DIR=./data/raw
UPLOAD_DIR=./data/uploads
MAX_CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=6
AUTO_INGEST_ON_STARTUP=true
AUTO_INGEST_SOURCE_LABEL=raw
```

## 下一步可继续增强的方向

- 增加网页抓取与定时同步
- 增加多轮会话与收藏回答
- 增加更强的 reranker
- 增加 OCR PDF 支持
- 增加登录鉴权与多用户隔离

## 相关文档

- [架构说明](./docs/architecture.md)
- [部署说明](./docs/deployment.md)
- [GitHub 工作流](./docs/github-workflow.md)
