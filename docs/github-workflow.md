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

建议按功能提交，而不是把大量无关改动混在一起：

- `init project scaffold`
- `add ingestion pipeline`
- `improve query workflow and citations`
- `refine document management experience`
- `add deployment docs`

## 3. 推荐分支策略

- `main`：可部署版本
- `dev`：日常开发
- 功能分支：`feature/*`

如果你是个人维护，也可以简化成：

- `main`
- `feature/*`

## 4. README 需要长期同步的内容

每次功能升级后，记得同步 README：

- 当前支持哪些文档类型
- 当前部署方式
- 当前环境变量
- 当前核心能力
- 已知限制
- 下一步计划

## 5. 推荐增加的 GitHub Actions

当前最值得保留的检查是：

- Python 语法和导入检查
- 基础 CI smoke check

后续可以继续增加：

- 单元测试
- lint
- Docker Compose 配置校验
- 自动构建镜像

## 6. 适合这个项目的维护习惯

因为这个项目是你自己的知识库，最重要的不是“代码看起来多高级”，而是：

- 资料能持续进入
- 搜索体验能持续变好
- 部署不要太脆弱
- 出问题时你自己能快速定位和修复

所以建议每次迭代只改一层：

- 要么改导入
- 要么改检索
- 要么改前端体验
- 要么改部署和运维

这样最稳，也更方便回滚。
