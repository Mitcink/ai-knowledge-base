# GitHub 上传与维护指南

## 1. 初始化仓库

如果这个项目要作为你现有仓库里的一个子目录，直接提交这个目录即可。

如果它要作为独立仓库：

```bash
git init
git add .
git commit -m "init ai knowledge base"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## 2. 推荐提交节奏

建议按功能提交，而不是一次性混在一起：

- `init project scaffold`
- `add ingestion pipeline`
- `add query api and ui`
- `add deployment docs`

## 3. 推荐分支策略

- `main`：可部署版本
- `dev`：日常开发
- 功能分支：`feature/*`

如果你是个人维护，也可以简化成：

- `main`
- `feature/*`

## 4. 推荐 README 长期维护内容

每次功能升级后，记得同步 README：

- 当前支持哪些文档类型
- 当前部署方式
- 当前环境变量
- 已知限制
- 下一步计划

## 5. 推荐增加的 GitHub Actions

第一版建议只做最基础检查：

- Python 语法检查
- Docker Compose 配置检查

后续可以再加：

- 单元测试
- lint
- 自动构建镜像

## 6. 适合你的维护习惯

因为这个项目是你自己的知识库，最重要的不是“代码看起来多高级”，而是：

- 资料持续进入
- 搜索体验持续变好
- 部署不要太脆弱
- 出问题时你自己能修

所以建议你每次迭代只改一层：

- 要么改导入
- 要么改检索
- 要么改前端
- 要么改部署

这样最稳。
