---
name: wechat-auto-publish
agent_created: true
description: 微信公众号文章自动化发布：通过 Playwright 浏览器自动化登录公众号后台，自动填写标题/作者/摘要，粘贴 gzh-design 或 wenyan 排版后的 HTML 正文，通过编辑器工具栏上传真实有效的封面图，保存草稿后从编辑器直接发表。首次扫码登录后，后续复用持久化会话免扫码。
version: 3.0.0
display_name: "公众号自动发布"
display_name_en: "WeChat Auto Publish"
---

# 公众号自动发布 Skill

微信公众号后台文章的自动化发布工作流。适合把已排版好的 HTML 长文一键推到公众号并发表。首次运行走完整流程，后续运行复用已登录的浏览器 session。

## 核心能力

- 持久化浏览器会话（首次扫码，之后免登录）
- 自动进入公众号编辑器并创建新图文
- 自动填写标题、作者、摘要
- 自动粘贴 HTML 正文（兼容 gzh-design 等微信合规排版）
- 自动上传封面图（通过编辑器工具栏，获取真实有效的 mmbiz CDN URL）
- 自动保存为草稿
- 自动记录草稿 URL / appMsgId
- **从编辑器直接发表**：点击 `button.mass_send` → 处理发表/继续发表/扫码验证弹窗
- **保存后恢复封面预览**：微信保存会重置封面 URL 为无效 filetransfer 链接，脚本在保存-重新加载后手动恢复为有效的 mmbiz URL

## 使用方式

### 前置条件

1. 已安装 Playwright + Chromium：
   ```bash
   /Users/echo/.workbuddy/binaries/python/envs/default/bin/pip install playwright
   /Users/echo/.workbuddy/binaries/python/envs/default/bin/playwright install chromium
   ```
2. 已准备公众号文章：
   - Markdown 原文：`article.md`
   - 排版后的 HTML：`article.html`（用 gzh-design 或 wenyan 生成）
   - 封面图：`cover.png`（建议 900×383 或 2.35:1）

### 直接调用

用户说类似以下意图时触发：

- "把这篇文章发布到公众号"
- "自动发布到微信公众号"
- "帮我发一下公众号"
- "用浏览器自动发布这篇推文"
- "把这篇推文群发出去"

### 执行流程

1. **确认素材**：检查文章 HTML 路径、标题、作者、摘要、封面路径。
2. **如果没有排版 HTML**：先调用 `gzh-design` skill 进行排版（摸鱼绿主题默认）。
3. **如果没有封面图**：用 ImageGen 生成一张 900×383 的封面。
4. **运行脚本**：
   ```bash
   cd wechat-publish
   /Users/echo/.workbuddy/binaries/python/envs/default/bin/python auto_publish.py
   ```
5. **首次登录**：用户在微信扫码；之后自动复用 session。
6. **脚本行为**：
   - 创建新文章 → 填写标题/作者/摘要/正文 → 上传封面 → 保存草稿 → 重新加载恢复封面预览 → 点击发表 → 处理弹窗 → 检测成功。
   - 发布成功后自动删除 `draft_url.json`。

### 脚本配置（运行前修改）

```python
# auto_publish.py 会自动使用项目目录下的子目录，通常只需改 TITLE/AUTHOR/DIGEST：
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLE_HTML_PATH = os.path.join(PROJECT_DIR, "articles", "article.html")
COVER_IMAGE_PATH = os.path.join(PROJECT_DIR, "covers", "cover.png")
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots")
USER_DATA_DIR = os.path.join(PROJECT_DIR, ".browser_profile")
DRAFT_URL_FILE = os.path.join(PROJECT_DIR, "draft_url.json")
```

## 脚本位置

- 主脚本：`scripts/auto_publish.py`
- 参考示例：`references/example-config.md`

## 关键实现细节

### 1. 封面图上传（v9 核心修复）

微信公众号封面区域没有标准 file input，且图片库/从正文选择对该账号可能报 "未授权使用切换账号能力"。v9 改为：

1. 聚焦正文 ProseMirror 编辑器
2. 找到编辑器工具栏的隐藏 `input[type=file]`
3. `set_input_files()` 上传封面图到正文
4. 从插入的 `<img data-imgfileid="...">` 读取真实 file_id
5. 读取 `img.src`（`mmbiz.qpic.cn` CDN URL）
6. 删除正文中的临时图片
7. 手动设置封面区域：
   - `#appmsgItem data-fileid`
   - `.js_cover_preview_new` 背景图
   - 隐藏占位按钮 `.select-cover__btn` 和 loading
   - 创建 `file_id` / `cdn_url` 等 hidden inputs

### 2. 标题填写（ProseMirror）

新版公众号编辑器标题是隐藏 `<textarea id="title">` + 可视化 ProseMirror 的组合。普通 `fill` 无效，脚本通过 JS 同时设置：
- `hiddenTitle.value`
- `ProseMirror.innerHTML`
- 触发 `input`/`change` 事件

### 3. 正文粘贴

正文编辑器是 `.ProseMirror[contenteditable="true"]`（不是旧版的 `.edui-body-container`）。脚本直接用 JS 设置 `innerHTML` 并触发 `input` 事件。

### 4. 发表流程

不再从草稿箱卡片点击发表（之前会误点导航栏"发表记录"）。改为从编辑器页面直接点击 `button.mass_send`，然后处理弹窗：

1. 发表弹窗（群发通知/定时发表）→ 点击「发表」
2. 二次确认弹窗 → 点击「继续发表」
3. 微信验证弹窗 → 等待用户扫码
4. "正在发表..." → 继续等待
5. 最终跳转首页或发表记录页 → 检测成功关键词

### 5. 发布成功检测

以页面跳转到首页/发表记录页，并检测「已发表」「发表成功」「群发成功」等关键词作为成功指标。

## 常见问题

- **草稿箱里出现多篇相同标题的文章**：这是调试过程中多次新建文章导致的，可手动删除旧草稿。
- **封面在编辑器里不显示**：微信保存后会重置封面预览 URL。脚本已加入保存后重新加载并恢复 URL 的步骤，编辑器中应能正常显示。
- **发表时弹出微信扫码验证**：这是公众号后台安全机制，需要管理员/运营者扫码。脚本会等待 60-120 秒，扫码后自动继续。
- **如果微信后台结构升级**：查看 `cover_set.png`、`after_save.png`、`cover_restored.png`、`publish_final.png` 等截图，调整 `auto_publish.py` 中的选择器。

## 依赖

- Python 3.11+
- playwright（Python 包 + Chromium 浏览器）
- 已登录的微信公众号后台（订阅号/服务号均可）
