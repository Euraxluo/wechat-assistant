# 公众号自动发布配置示例

## 文件结构示例

```
~/project/my-gzh-article/
├── article.md              # Markdown 原文
├── article.html            # gzh-design 排版后的 HTML
├── cover.png               # 封面图（900×383 或 2.35:1）
├── .browser_profile/       # 持久化浏览器会话（脚本自动生成）
└── auto_publish.py         # 复制 scripts/auto_publish.py 并修改配置
```

## 最小配置修改

编辑 `auto_publish.py` 顶部的配置变量：

```python
ARTICLE_HTML_PATH = "/Users/echo/project/my-gzh-article/article.html"
TITLE = "你的文章标题"
AUTHOR = "你的公众号名"
DIGEST = "一句话摘要，会在转发时显示"
COVER_IMAGE_PATH = "/Users/echo/project/my-gzh-article/cover.png"
USER_DATA_DIR = "/Users/echo/project/my-gzh-article/.browser_profile"
```

## 运行

```bash
cd /Users/echo/project/my-gzh-article
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python auto_publish.py
```

首次运行会弹出浏览器让你扫码，之后自动保存 session。

## 封面图生成提示词模板

```
A modern minimalist cover image for a WeChat article about [主题]. 
Green-themed. Style: clean, professional, abstract geometric patterns. 
No text overlay. Soft gradient background.
```
