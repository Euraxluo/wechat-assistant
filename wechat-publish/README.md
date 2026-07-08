# WeChat Publish - 微信公众号自动发布

通过 Playwright 浏览器自动化，实现微信公众号文章的一键排版、封面上传、草稿保存和群发。

## 目录结构

```
wechat-publish/
├── auto_publish.py          # 主发布脚本（v9）
├── draft_url.json           # 草稿缓存（运行时自动生成/删除）
├── README.md                # 本文件
├── articles/                # 文章 HTML 文件
│   ├── article_ai_invest_v3.html   # 最新版（研报风格）
│   ├── article_ai_invest_v2.html   # 旧版
│   └── article_ai_invest.html      # 初版
├── covers/                  # 封面图片
│   └── latest_cover_v3.png
├── screenshots/             # 运行时截图
├── diagnostics/             # 诊断/调试脚本（开发参考）
│   ├── diag_cover_set.py
│   ├── diag_cover_save.py
│   ├── diag_cover_api2.py
│   ├── diag_draftbox_v2.py
│   ├── diag_editor_v2.py
│   └── diag_editor_publish_final.py
├── utils/                   # 辅助工具
│   ├── republish.py         # 从草稿箱重新发表
│   ├── verify_publish.py    # 验证文章是否已发表
│   ├── publish_final.py     # 最终发布脚本
│   └── check_draftbox.py    # 检查草稿箱状态
└── .browser_profile/        # Playwright 持久化浏览器会话（运行后自动生成）
```

## 运行

```bash
cd wechat-publish
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python auto_publish.py
```

## Skill

配套 skill 位于 `.agents/skills/wechat-auto-publish/`（Cursor 通过 `.cursor/skills` 软链读取），可通过 Agent 对话直接调用。
