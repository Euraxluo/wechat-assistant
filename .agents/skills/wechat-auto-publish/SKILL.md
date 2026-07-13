---
name: wechat-auto-publish
agent_created: true
description: 微信公众号文章自动化发布 workspace：Playwright 登录后台，填写标题/作者/摘要，粘贴 HTML，上传正文图与封面到微信 CDN，保存草稿并发表。题材差异见 config/topics/，单次参数见 runs/*.json，踩坑见 memory/lessons/。
version: 4.0.0
display_name: "公众号自动发布"
display_name_en: "WeChat Auto Publish"
---

# 公众号自动发布 Skill

> **架构**：一个引擎 + 题材 profile + 运行配置 + memory。详见 `wechat-publish/docs/ARCHITECTURE.md`

## 触发意图

- "发布到公众号" / "自动发表" / "群发这篇推文"

## 执行前必读

1. `wechat-publish/config/topics/<topic>.md` — 题材差异（选题源、文风、配图、SOP）
2. `wechat-publish/memory/lessons/<topic>.md` — 历史踩坑

## 标准闭环

```text
选题 → 写文/配图 → runs/<slug>.json → publish.py → verify_publish.py → memory/journal
```

### 1. 准备运行配置

复制 `wechat-publish/runs/_example.json` → `runs/<slug>.json`，填写：

- `topic`, `title`, `author`, `digest`
- `html`, `cover`, `images_dir`（路径相对 `wechat-publish/`）

### 2. 发布

```bash
cd wechat-publish
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python publish.py --run <slug>.json
```

### 3. 验证

```bash
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python utils/verify_publish.py
```

### 4. 写 memory

`memory/journal/<YYYY-MM-DD>-<slug>.md` — 记录 result / blocker / new_lesson

## 引擎能力（engine/publish_core.py）

- 持久化浏览器 session（`.browser_profile/`）
- 正文本地图 → 微信 CDN 替换
- 封面上传 + 保存后恢复预览 URL
- 发表弹窗链：AI声明 → 继续发表 → 发表 → 扫码（等待 ~6min）
- 保留 `draft_url.json` 供 verify 使用

## 禁止事项

- ❌ 新建 `publish_xxx.py`（用 `runs/*.json` 代替）
- ❌ 修改 `engine/` 来适配单次选题
- ❌ ImageGen 超时后复用其他题材旧图
- ❌ 维护 skill 目录下的脚本副本（唯一代码在 `wechat-publish/engine/`）

## 题材 profile 位置

`wechat-publish/config/topics/` — 新增题材只加一份 `.md`，从 `_template.md` 复制。

## 依赖

- Python 3.11+，playwright + chromium
- 公众号管理员/运营者微信（发表时需扫码验证）
