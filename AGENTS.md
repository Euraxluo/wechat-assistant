# Agent 指引

本仓库用于「金融研究 + 公众号文章生产与自动发布」。完整说明见 [README.md](README.md)。

## 项目级 Skill

Skill 存放在 `.agents/skills/`（Cursor 通过 `.cursor/skills` 软链读取同一目录）。

| 类别 | Skill |
|------|-------|
| 金融分析 | `xiaodi-financial-analysis-team`, `akshare-stock`, `claw-stock`, `china-stock-analysis`, `claw-stock-watcher-pro`, `stock-monitor-skill`, `astock-report` |
| 辅助 | `data-analysis-skill`, `web_search`, `content-creator-cn`, `content-strategy` |
| 发布 | `wechat-auto-publish` |

## 快速入口

- 发布脚本：`wechat-publish/auto_publish.py`
- 发布 Skill：`.agents/skills/wechat-auto-publish/`
