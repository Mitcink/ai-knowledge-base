# AI Knowledge Base

一个适合个人长期维护的 AI 知识库项目骨架，支持：

- 文档导入与增量索引
- 基于 RAG 的问答
- 简单 Web 界面
- Docker Compose 部署到服务器
- GitHub 单仓库维护

## 1. 项目结构

```text
ai-knowledge-base/
├─ app/                   # FastAPI API 和 RAG 逻辑
├─ ui/                    # Streamlit 页面
├─ scripts/               # 批量导入脚本
├─ data/
│  ├─ raw/                # 待导入的原始文档
│  └─ processed/          # 预留给后续处理结果
├─ docs/
│  ├─ architecture.md
│  ├─ deployment.md
│  └─ github-workflow.md
├─ docker-compose.yml
├─ Dockerfile.api
├─ Dockerfile.ui
└─ .env.example
```

## 2. 当前版本能力

- 支持导入 `Markdown`、`TXT`、`PDF`
- 支持目录批量导入和单文件上传导入
- 支持向量检索
- 支持基于关键词重排的轻量混合检索
- 支持回答时返回引用片段

注意：
当前版本的“混合检索”是 `向量召回 + 关键词加权重排`，已经足够作为第一版上线；如果你后续需要更强的精确召回，可以再升级成 Qdrant 的原生稀疏向量或 BM25 方案。

## 3. 本地启动

1. 复制环境变量文件

```powershell
Copy-Item .env.example .env
```

2. 填入你的模型配置，至少要改：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_MODEL`

3. 启动服务

```powershell
docker compose up --build
```

4. 打开页面

- Web UI: [http://localhost:8501](http://localhost:8501)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Qdrant: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

## 4. 首次导入文档

把你的资料放到 `data/raw/`，然后执行：

```powershell
docker compose exec api python scripts/ingest.py
```

你也可以直接在 Web UI 里上传文件。

## 5. 推荐的第一批资料

- 你自己的 Markdown 笔记
- 项目复盘文档
- PDF 电子书摘录
- 技术方案文档
- 常用命令备忘

第一次不要一次塞太多源，先用 20 到 50 份核心资料验证效果最好。

## 6. 下一步迭代建议

- 增加登录鉴权
- 增加定时增量更新
- 增加网页抓取导入
- 增加 Notion 或 Obsidian 同步
- 增加真正的 reranker

详细说明见：

- [技术架构](./docs/architecture.md)
- [服务器部署](./docs/deployment.md)
- [GitHub 工作流](./docs/github-workflow.md)

