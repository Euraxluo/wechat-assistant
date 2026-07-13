# 已废弃的发布脚本

2026-07-13 架构重构后，所有发布统一走：

```bash
python publish.py --run <slug>.json
```

本目录保留旧脚本仅供 diff 参考，**不要再运行或复制**。

| 文件 | 原用途 |
|------|--------|
| `publish_hot_article_v2.py` | 社会热点 v2（已迁入 `engine/publish_core.py`） |
| `publish_hot_article.py` | 社会热点 v1 |
| `publish_gender_article.py` | 性别信任议题 |
| `publish_finance_article.py` | 财经午盘 |
| `publish_tech_article.py` | 科技 AI |
| `publish_movie_article.py` | 影视 |
| `publish_lifework_article.py` | 职场生活 |
| `publish_kv_article.py` | KV 存储 |
| `auto_publish.py` | 旧通用入口 v9（封面-only，无正文图上传） |
