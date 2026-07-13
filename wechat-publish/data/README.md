# 数据快照

财经/盘中类文章使用的 JSON 行情快照，与 HTML 正文分离存放。

| 文件 | 说明 |
|------|------|
| `snapshots/midday_data_0708.json` | 午盘数据 |
| `snapshots/afterhours_global_data_0708.json` | 盘后全球数据 |
| `snapshots/us_*_data.json` | 美股盘前/盘后 |

生成新快照时写入 `snapshots/<topic>-<date>.json`，文章 HTML 引用同一命名规范。
