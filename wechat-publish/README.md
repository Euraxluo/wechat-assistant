# wechat-publish — 公众号 Workspace

> 微信公众号内容生产与自动发布工作区。  
> 架构：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · Git 策略：[docs/GIT_POLICY.md](docs/GIT_POLICY.md)

## 快速开始

```bash
# 1. 读题材 profile
cat config/topics/hot-social.md

# 2. 复制运行配置
cp runs/_example.json runs/my-article.json
# 编辑 title / html / cover ...

# 3. 发布
python publish.py --run my-article.json

# 4. 验证
python utils/verify_publish.py
```

## 目录一览

| 目录 | 职责 | Git |
|------|------|-----|
| `engine/` | Playwright 发布引擎（勿为单次选题修改） | ✅ |
| `config/topics/` | 题材 profile（差异声明） | ✅ |
| `runs/` | 单次运行 JSON（发一篇加一个文件） | 仅 `_example.json` ✅ |
| `memory/lessons/` | 跨次踩坑沉淀 | ✅ |
| `memory/journal/` | 单次复盘 | ❌ 本地 |
| `content/` | 文章、配图、选题计划 | ⚖️ 见 [docs/GIT_POLICY.md](docs/GIT_POLICY.md) |
| `data/` | 写稿用数据快照（按题材可选） | ⚖️ |
| `utils/` | verify / republish / check_draftbox | ✅ |

**Git 策略全文**：[docs/GIT_POLICY.md](docs/GIT_POLICY.md)

## Python 环境

```bash
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python publish.py --run ...
```

## 工作流 SOP

- 社会热点：[docs/workflows/hot-social-sop.md](docs/workflows/hot-social-sop.md)
- **Git vs 本地**：[docs/GIT_POLICY.md](docs/GIT_POLICY.md) ← 什么该提交、什么留本机
