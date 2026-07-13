# 已发表归档

发表并 `verify_publish.py` 通过后，从 `drafts/` 复制终稿到此目录。

## 目录结构

```
published/
└── <slug>/
    ├── article.html      # 终稿 HTML（可选提交 Git）
    └── manifest.json     # 元数据（建议提交，体积极小）
```

## manifest.json 示例

```json
{
  "slug": "door-stabbing-0713",
  "topic": "hot-social",
  "title": "16岁少年拍门玩闹被捅死，母亲说：错不至死",
  "published_at": "2026-07-13",
  "wechat_appmsg_id": "100002658",
  "assets_dir": "content/assets/door-stabbing-0713",
  "note": "配图在本地 assets/，已上传微信 CDN，不提交 Git"
}
```

配图仍在本地 `content/assets/<slug>/`，不进入 Git。
