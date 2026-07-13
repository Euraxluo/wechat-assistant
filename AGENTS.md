# Agent 指引

本仓库是**微信公众号内容生产与自动发布 workspace**。完整架构见 [wechat-publish/docs/ARCHITECTURE.md](wechat-publish/docs/ARCHITECTURE.md)。

## 核心原则

- **一个发布引擎**：`wechat-publish/publish.py`（禁止新建 `publish_*.py`）
- **题材差异**：读 `wechat-publish/config/topics/<type>.md`
- **单次参数**：写 `wechat-publish/runs/<slug>.json`（不改编译器）
- **长期记忆**：读/写 `wechat-publish/memory/lessons/` 与 `journal/`

## 项目级 Skill

| 类别 | Skill |
|------|-------|
| 发布 | `wechat-auto-publish` |
| 通用内容 | `content-creator-cn`, `web_search`, `content-strategy` |
| 题材专属 | 见对应 `config/topics/<type>.md`（按需挂接） |

## 标准发布闭环

```text
1. 读 config/topics/<topic>.md + memory/lessons/<topic>.md
2. 选题 → content/plans/
3. 写文 + 配图 → content/drafts/ + content/assets/<slug>/
4. 新建 runs/<slug>.json
5. python wechat-publish/publish.py --run <slug>.json
6. python wechat-publish/utils/verify_publish.py
7. 写 memory/journal/<date>-<slug>.md
```

## 反模式

- ❌ 复制 `publish_*.py` 发新题材
- ❌ 把踩坑写进脚本顶部注释
- ❌ ImageGen 超时后复用其他题材旧图
