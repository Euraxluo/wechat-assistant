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

## 午盘/盘中研报提醒

用户要求“午盘研报 + 推文/公众号发送”时，必须按 `README.md` 的午盘/盘中研报自动发布 SOP 闭环执行：取数并落盘 → 生成 `wechat-publish/articles/*.html` → 更新 `auto_publish.py` 顶部发布参数 → 运行发布脚本 → `utils/verify_publish.py` 验证发表记录。不要只输出分析文本。
