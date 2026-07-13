# 运行配置（runs/）

每次发布**只新增一个 JSON 文件**，不要改 Python 代码。

## 用法

```bash
# 1. 复制模板
cp runs/_example.json runs/my-article.json

# 2. 填写 title / html / cover / images_dir 等

# 3. 发布
python publish.py --run my-article.json
```

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `topic` | ✅ | 题材标识，对应 `config/topics/<topic>.md` |
| `slug` | 建议 | 本次运行唯一名，写入 `draft_url.json` 和 memory journal |
| `title` | ✅ | 文章标题 |
| `author` | ✅ | 作者署名（可被 topic profile 覆盖习惯） |
| `digest` | ✅ | 摘要 |
| `html` | ✅ | 正文 HTML 路径（相对 wechat-publish/） |
| `cover` | ✅ | 封面图路径 |
| `images_dir` | 可选 | 正文本地图片目录；无内嵌图可省略 |

## Git 策略

- `runs/_example.json` — 提交（模板）
- `runs/*.json`（除 `_example`）— **不提交**（见根 `.gitignore`）
- 已发表的运行可归档到 `memory/journal/` 做记录
