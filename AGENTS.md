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
| 辅助 | `content-creator-cn`, `web_search`, `content-strategy` |
| 金融（财经题材用） | `akshare-stock`, `xiaodi-financial-analysis-team`, … |

## 标准发布闭环

```text
1. 读 config/topics/<topic>.md + memory/lessons/<topic>.md
2. 选题 → content/plans/（或过渡期 articles/topic-plan-*.md）
3. 写文 + 配图 → content/drafts/ + content/assets/<slug>/
4. 新建 runs/<slug>.json
5. python wechat-publish/publish.py --run <slug>.json
6. python wechat-publish/utils/verify_publish.py
7. 写 memory/journal/<date>-<slug>.md
```

## 题材示例（财经不是主线）

写财经稿时：用 `finance-news` profile + 金融取数 skill；数据快照落 `data/snapshots/`。  
写热点/科技/职场/影视时：用对应 profile + 搜索/写作 skill。发布步骤相同。

## 反模式

- ❌ 把本仓库当成「金融分析产品」（金融 skill 只是财经题材的内容工具）
- ❌ 复制 `publish_*.py` 发新题材
- ❌ 把踩坑写进脚本顶部注释
- ❌ ImageGen 超时后复用其他题材旧图
