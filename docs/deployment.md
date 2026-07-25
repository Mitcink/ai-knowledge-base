# 服务器部署指南

本文默认你已经有：

- 一台 Linux 服务器
- 一个 GitHub 仓库
- Docker 和 Docker Compose 环境
- 一个可用域名或服务器公网 IP

## 1. 服务器准备

建议配置：

- 最低：`2C4G`
- 更稳妥：`4C8G`

推荐系统：

- Ubuntu 24.04 LTS

如果 Docker 还没安装，可参考官方文档：

- [Docker Engine Docs](https://docs.docker.com/engine/)
- [Docker Compose Docs](https://docs.docker.com/compose/)

## 2. 拉取代码

```bash
git clone <your-github-repo-url>
cd ai-knowledge-base
```

## 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少改这些：

```env
OPENAI_API_KEY=your_real_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
QDRANT_URL=http://qdrant:6333
```

如果你用的是兼容 OpenAI 协议的供应商，主要修改 `OPENAI_BASE_URL` 和模型名即可。

## 4. 启动服务

```bash
docker compose up -d --build
```

检查状态：

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f ui
```

## 5. 首次导入资料

先把资料放入：

```text
data/raw/
```

然后执行：

```bash
docker compose exec api python scripts/ingest.py
```

如果你更希望走产品工作台，也可以直接打开 UI，在“导入与同步”页执行“同步原始目录”。

## 6. 对外访问

默认端口：

- `8000`：API
- `8501`：Web UI
- `6333`：Qdrant

如果直接暴露到公网，安全性较弱。更推荐使用反向代理和 HTTPS。

## 7. Nginx 示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

## 8. HTTPS

推荐方案：

- `certbot`
- 或直接使用 `Caddy`

如果你希望维护更省心，后续可以把 Nginx 替换成 Caddy。

## 9. 持久化与备份

必须备份这两个目录：

- `qdrant_storage/`
- `data/raw/`

建议至少每天备份一次。

## 10. 部署后的检查清单

1. `docker compose ps` 全部正常
2. `http://your-domain/` 能打开 UI
3. `http://your-domain/health` 返回正常
4. 至少成功导入 1 份文档
5. 至少成功回答 3 个你能验证的问题
6. 文档总览里没有异常增长的孤立索引
