# 微信 HTML 兼容规范

微信公众号图文编辑器基于 **ProseMirror**，会对粘贴进来的 HTML 做清洗：剥离不可用的样式、改写部分节点。下面是一线实战（含今天两次翻车）验证过的规范。

---

## 一、允许的标签 / 样式

- 结构标签：`<section>`（卡片容器，**替代 `<div>`**）、`<p>`、`<h2>`、`<h3>`、`<table>/<tr>/<td>/<th>`、`<ul>/<li>`、`<img>`
- 行内样式可用：`color`、`background-color`、`font-weight`、`text-align`、`border-radius`、`padding`（写在 section 上）、`border`（写在 section 上）
- 图片内联样式（**必须**）：`max-width:100%;height:auto;display:block;margin:6px auto 14px`

## 二、禁止的写法（附后果）

| 写法 | 后果 |
|------|------|
| `<div style="background/border/padding">` | ProseMirror 剥离 div 的 bg/border/padding，彩色卡片变裸文本 |
| CSS 变量 `var(--x)` | 不支持，整段样式失效 |
| `display:grid` / `display:flex` | 不支持，子元素塌陷重叠 |
| `position:absolute` / `position:fixed` | 不支持，元素飘出或被裁切重叠 |
| `conic-gradient` / 复杂 `linear-gradient` | 不支持或表现异常 |
| 大图（>750px 宽） | 即便 `width:100%` 仍可能横向溢出截断，留大片白边 |
| CSS 语法错误（如 `:` 误用 `;`） | 后续样式整体失效 |

> 用 `<section>` 而不是 `<div>` 承载卡片，是今天的头号教训：同一段样式写在 `<section>` 上微信能保留，写在 `<div>` 上会被剥光。

## 三、配图规范

- **宽度统一 750px**（微信公众号标准手机宽度），用 PIL `LANCZOS` resize
- 所有 `<img>` 必须带内联样式：`max-width:100%;height:auto;display:block;margin:6px auto 14px`
- 复杂关系图用 **matplotlib 生成**（750px 宽，中文字体 PingFang SC），**不要截图网页**——截图会丢字

## 四、发布前自检（必跑）

```bash
H=content/drafts/<slug>.html
echo "div 容器: $(grep -c '<div' $H)"
echo "CSS变量: $(grep -c 'var(' $H)"
echo "grid:    $(grep -c 'display:grid' $H)"
echo "absolute:$(grep -c 'position:absolute' $H)"
# 以上四项必须全为 0
```

## 五、复杂报告处理决策树

1. **源是 Markdown / 简单网页** → 用 gzh-design 排版后直接发
2. **源是宽屏复杂报告**（含 grid / absolute / conic-gradient）→ **禁止截图转图**
   - 用正则去标签提取全部文字（保真不漏字，约 5k 字分析报告可完整承载）
   - 八条主线 / 龙头分层 / 伪对标 / 个股观察 → `<section>` 卡片
   - 多列对照数据 → 真 `<table>`
   - 仅"象限矩阵 / 梯队"类二维关系 → matplotlib 画干净图
3. 生成内联预览（`data:image/png;base64` 内联全部图片）自检后再跑 `publish.py`

## 六、发布后核验（不可省）

读 `wechat-publish/screenshots/after_save.png`：

- 卡片 / 表格样式保留 ✓
- 图片无截断、无溢出白边 ✓
- 正文布局未错乱 ✓

> 预览面板正确 ≠ 微信编辑器正确。今天的午盘稿在预览面板正常，发到微信后布局全乱——唯独 `after_save.png` 能暴露真实渲染。
