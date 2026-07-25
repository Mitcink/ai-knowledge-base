# AI Knowledge Base

一个面向个人长期维护的 AI 知识库项目。它不是一次性的 RAG demo，而是一个可持续导入、持续检索、持续清理和持续迭代的资料工作台。

当前版本聚焦三个目标：

- 把长期资料稳定导入知识库
- 用可解释的引用结果验证问答质量
- 把磁盘文件、向量索引和系统状态放在同一个工作台里管理

## 核心能力

- 批量同步 `data/raw/`，适合沉淀长期资料
- 单文件上传并即时索引，适合补充零散内容
- 基于 RAG 的问答与引用片段返回
- 文档总览：区分已索引、待索引、孤立索引、外部索引
- FastAPI + Streamlit 双端结构
- Docker Compose 一键启动本地工作环境

## 产品结构

- `app/`
  - FastAPI API
  - RAG 编排
  - 文档解析与向量存储访问
- `ui/`
  - Streamlit 工作台
  - 问答、导入、上传、文档管理和健康检查
- `scripts/`
  - 批量导入脚本

## 推荐使用流程

1. 把长期资料放进 `data/raw/`
2. 在工作台中执行“同步原始目录”
3. 用“上传单个文件”补充临时资料
4. 在“问答工作台”中验证召回质量与回答效果
5. 在“文档总览”中清理旧文件、孤立索引或外部索引

## 目录结构

```text
ai-knowledge-base/
├─ app/                   # FastAPI API 与 RAG 服务
├─ ui/                    # Streamlit 工作台
├─ scripts/               # 批量导入脚本
├─ docs/                  # 架构、部署与工作流文档
├─ data/
│  ├─ raw/                # 长期维护的原始资料
│  ├─ processed/          # 预留目录
│  └─ uploads/            # Web 上传文件
├─ docker-compose.yml
├─ Dockerfile.api
├─ Dockerfile.ui
└─ .env.example
```

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
- `QDRANT_URL`

默认 Docker Compose 环境中，Qdrant 地址已经配置为：

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

### 方案 A：批量同步 `data/raw/`

把资料放入 `data/raw/` 后，在 UI 中点击“同步原始目录”。

也可以直接执行脚本：

```powershell
docker compose exec api python scripts/ingest.py
```

### 方案 B：通过 Web 上传

适合补充单篇文档，上传后会立即解析并写入索引。

## 支持的文件类型

- `.md`
- `.markdown`
- `.txt`
- `.pdf`

文本文件优先按 `utf-8` 读取，并兼容常见中文编码回退。

## 系统管理能力

当前工作台支持：

- 查看 OpenAI 配置是否完整
- 查看 Qdrant 是否可达
- 查看文档总数、已索引数、待索引数、孤立索引数
- 查看分类、来源、文件类型和存储区域分布
- 按文件删除原文、删除索引或同时删除两者

## 下一步适合增强的方向

- 网页抓取与定时同步
- 更强的 reranker
- OCR PDF 支持
- 多轮会话与收藏回答
- 登录鉴权与多用户隔离

## 相关文档

- [架构说明](./docs/architecture.md)
- [部署说明](./docs/deployment.md)
- [GitHub 工作流](./docs/github-workflow.md)
