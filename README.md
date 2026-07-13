# 金融分析 · 公众号自动发布工作台

> **给 Agent 看的仓库说明书**：本 workspace 用于「金融研究 + 公众号文章生产与自动发布」的完整工作流。如果你是第一次进入这个 workspace，请先读本文件。

---

## 1. 这个仓库是做什么的

本仓库包含两个核心能力：

1. **金融分析能力**：一套股票/基金/宏观经济分析 skill（`.agents/skills/` 下）
2. **公众号自动发布能力**：通过浏览器自动化绕过 AppID/IP 白名单限制，直接登录公众号后台发布文章（`wechat-publish/`）

后续所有主题都会围绕**金融分析**展开，文章产出后通过自动化脚本发布到微信公众号。

---

## 2. 目录结构说明

```
wechat-assistant/
├── AGENTS.md                          # Agent 入口指引（精简版）
├── README.md                          # 本文件（Agent 必读）
├── .agents/
│   └── skills/                        # ✅ 项目级 Skill（随仓库一起提交）
│       ├── wechat-auto-publish/       # 公众号浏览器自动化发布 Skill
│       ├── 金融分析相关 skill（7个）
│       │   ├── akshare-stock/
│       │   ├── astock-report/
│       │   ├── china-stock-analysis/
│       │   ├── claw-stock/
│       │   ├── claw-stock-watcher-pro/
│       │   ├── stock-monitor-skill/
│       │   └── xiaodi-financial-analysis-team/
│       └── 辅助 skill（4个）
│           ├── data-analysis-skill/
│           ├── content-creator-cn/
│           ├── content-strategy/
│           └── web_search/
├── .cursor/
│   └── skills -> ../.agents/skills   # Cursor 软链，与 .agents/skills 同源
└── wechat-publish/                    # ✅ 公众号自动化项目代码
    ├── auto_publish.py                # 主发布脚本（v9），核心入口
    ├── draft_url.json                 # 运行时草稿缓存（自动生成/删除）
    ├── articles/                      # 文章 HTML 文件
    ├── covers/                        # 封面图片
    ├── screenshots/                   # 运行时截图与验证图
    ├── diagnostics/                   # 诊断/调试脚本（开发参考，生产勿用）
    └── utils/                         # 辅助工具
```

### 为什么用 `.agents/skills/`？

- 遵循 [Agent Skills](https://agentskills.io) 开放标准（`SKILL.md` 格式）
- 工具无关：Codex（`~/.agents/skills/`）、Cursor（`.cursor/skills/`）、Claude Code（`.claude/skills/`）均支持同一格式
- `.cursor/skills` 通过软链指向 `.agents/skills`，避免重复维护

---

## 3. 为什么有「wechat-publish」和「wechat-auto-publish」两个发布相关目录？

| 目录 | 类型 | 作用 | 说明 |
|------|------|------|------|
| `wechat-publish/` | Workspace | 发布引擎、题材配置、运行配置、memory | 执行 `publish.py --run <slug>.json` |
| `.agents/skills/wechat-auto-publish/` | Skill | Agent 操作手册（不复制代码） | 对话入口，指向 workspace |

**关系**：Skill 是手册，workspace 是代码与数据。详见 `wechat-publish/docs/ARCHITECTURE.md`。

**Agent 注意事项**：
- 发布文章 → `wechat-publish/publish.py --run runs/<slug>.json`
- 读题材差异 → `wechat-publish/config/topics/<type>.md`
- 读历史踩坑 → `wechat-publish/memory/lessons/<type>.md`
- **禁止**新建 `publish_*.py`

---

## 4. 核心工作流（Agent 执行流程）

金融分析文章从选题到发布的标准流程：

```
1. 选题/热点
   └─ 使用 wechat-viral-topic（用户级）或 content-strategy（项目级）

2. 金融数据获取
   └─ 使用 akshare-stock / claw-stock / china-stock-analysis / stock-monitor-skill

3. 深度分析
   └─ 使用 xiaodi-financial-analysis-team（多 Agent 团队）

4. 竞品/资讯调研
   └─ 使用 web_search / wechat-article-search（用户级）

5. 文章写作
   └─ 使用 content-creator-cn / wechat-article-pro（用户级）/ khazix-writer（用户级）

6. 数据可视化/报告
   └─ 使用 data-analysis-skill

7. 公众号排版
   └─ 使用 gzh-design（用户级）或 wechat-publisher（用户级）

8. 发布到公众号
   └─ 写 `wechat-publish/runs/<slug>.json`
   └─ 运行 `wechat-publish/publish.py --run <slug>.json`
   └─ 运行 `wechat-publish/utils/verify_publish.py`
   └─ 写 `wechat-publish/memory/journal/`
```

---

## 5. 午盘/盘中研报自动发布 SOP（Agent 必读）

当用户目标是“午盘研报 + 推文/公众号发送”时，不要只做文本分析，必须按下面链路闭环：

```text
1. 先读 README.md / AGENTS.md，确认当前仓库流程
2. 读取项目级 skill 文档：akshare-stock / astock-report / xiaodi-financial-analysis-team / content-creator-cn / wechat-auto-publish
3. 取数并落盘：行情、板块资金、龙头量价、涨停/炸板、港股/南向
4. 生成公众号 HTML → `wechat-publish/content/drafts/`（或过渡期 `articles/`）
5. 新建 `wechat-publish/runs/<slug>.json`
6. 运行 `wechat-publish/publish.py --run <slug>.json`
7. 运行 `utils/verify_publish.py` 验证发表记录
```

### 5.1 本次验证过的卡点与处理方式

- **不要直接用通用 deep-research 代替项目流程**：实时金融数字必须走项目数据源或可追溯快讯，无法核验时写“暂无可验证数据”。
- **项目级 skill 不一定出现在 Claude Code 的 Skill 列表里**：如果工具列表没有 `akshare-stock` 等项目 skill，就直接读取 `.agents/skills/<skill>/SKILL.md` 并按其中规则执行。
- **AkShare 可能未安装在当前 Python 环境**：先检查依赖；不可用时使用可追溯行情源兜底，并明确标注数据源、时间戳和核验状态。
- **东方财富 push2 接口可能拒绝连续请求**：成功取到的行情/板块资金要立即写入 JSON 快照，例如 `wechat-publish/articles/midday_data_YYYYMMDD.json`；后续文章生成用该快照，避免重复请求丢数。
- **个股/指数实时行情可用腾讯行情作兜底**：用于点位、涨跌幅、成交额、换手、盘口封单估算；必须标注取数时间。
- **发布脚本参数是硬编码入口**：发布前必须检查 `auto_publish.py` 顶部的文章路径、标题、作者、摘要和封面路径是否对应本次文章。
- **发表时微信验证是正常卡点**：脚本会等待“微信验证”弹窗，管理员/运营者扫码后继续；不要误判为失败。
- **成功后必须验证**：`auto_publish.py` 显示成功后，继续运行 `python utils/verify_publish.py`，以发表记录包含目标文章作为最终确认。
- **时点失效必须立刻废稿切题**：集合竞价稿只在竞价窗口有效；开盘稿只在开盘后短时间有效；午盘稿只在午盘窗口有效；收评稿只在收盘后有效。窗口一旦过去，不补发旧稿，直接改写当前时点内容。
- **验证失败不等于未发表**：先用修正后的 `utils/verify_publish.py` 检查，再决定是否使用 `utils/republish.py` 从当前仓库草稿继续发表；不要依赖旧 workspace 的脚本或标题。

---

## 6. 公众号发布脚本使用说明

### 6.1 前置条件

- 已安装 Playwright：`python -m playwright install chromium`
- 首次运行需要登录公众号后台，脚本会自动保存 cookie 到持久化浏览器 profile
- 后续运行复用 profile，无需重复登录

### 6.2 运行方式

```bash
cd wechat-publish
python auto_publish.py
```

### 6.3 脚本执行流程

1. 打开公众号后台图文编辑页
2. 粘贴文章 HTML 到编辑器
3. 通过编辑器工具栏上传封面图片
4. 提取 mmbiz.qpic.cn CDN 封面 URL
5. 保存草稿 → 重新加载 → 恢复封面 URL
6. 点击「发表」→ 处理弹窗 → 显示二维码
7. 用户扫码确认后发表成功

### 6.4 已知限制

- 首次登录需要手动扫码
- 微信会话会过期，长时间运行后可能出现 320003 错误，此时需要重新登录
- 每次群发会消耗公众号群发次数
- 文章 HTML 中不要使用 `<table>`、`<section>` 等复杂标签，移动端会错位；使用 `<div>`、`<p>`、`<br>` + 粗体即可

### 6.5 辅助脚本

| 脚本 | 作用 |
|------|------|
| `utils/republish.py` | 从草稿箱重新发表文章 |
| `utils/publish_final.py` | 最终稳定版发布脚本 |
| `utils/verify_publish.py` | 验证文章是否已出现在发表记录中 |
| `utils/check_draftbox.py` | 检查草稿箱状态 |
| `diagnostics/*.py` | 调试脚本，仅开发参考 |

---

## 7. Skill 使用优先级

金融分析主题下，优先使用以下 skill：

| 优先级 | Skill | 用途 |
|--------|-------|------|
| ⭐⭐⭐ | `xiaodi-financial-analysis-team` | 主力金融分析（多角色团队） |
| ⭐⭐⭐ | `akshare-stock` | A 股数据获取 |
| ⭐⭐⭐ | `claw-stock` | 个股打分与投资建议 |
| ⭐⭐ | `china-stock-analysis` | 中概/A 股/港股趋势分析 |
| ⭐⭐ | `claw-stock-watcher-pro` | 自选股监控与总结 |
| ⭐⭐ | `stock-monitor-skill` | 技术面预警监控 |
| ⭐⭐ | `data-analysis-skill` | 数据清洗与可视化报告 |
| ⭐⭐ | `web_search` | 实时财经资讯搜索 |
| ⭐ | `content-creator-cn` | 中文金融文章创作 |
| ⭐ | `content-strategy` | 内容选题策略 |
| ⭐ | `wechat-auto-publish` | 公众号发布 |

**用户级 skill**（安装在各工具的全局目录，不归本仓库管理）：

| 工具 | 路径 |
|------|------|
| Cursor | `~/.cursor/skills/` |
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |

常用用户级 skill：gzh-design、khazix-writer、wechat-article-pro、wechat-article-search、wechat-publisher、wechat-viral-topic。

---

## 8. 常见问题（FAQ for Agent）

### Q1：用户让我发布文章，但 skill 不工作？
A：市场安装的 `wechat-publisher` / `wechat-article-pro` 发布功能需要 `WECHAT_APP_ID` + `WECHAT_APP_SECRET` + IP 白名单。如果用户没有提供这些，改用 `wechat-publish/auto_publish.py` 浏览器自动化方案。

### Q2：文章在电脑上看起来正常，但手机排版错乱？
A：微信公众号移动端不支持 `<table>`、`<section>` 等复杂标签。应使用 `<div>` + `<p>` + `<br>` + 粗体。参考 `articles/article_ai_invest_v3.html`。

### Q3：封面无法显示？
A：不要直接通过 filetransfer 或 upload API 设置封面。正确流程：通过编辑器工具栏上传图片，获取插入图片的 `data-imgfileid`，提取 mmbiz.qpic.cn URL，再设回封面区域。`auto_publish.py` 已封装此逻辑。

### Q4：发表后提示「系统错误 (320003)」？
A：发表完成后微信会话会失效，属于正常现象。用 `verify_publish.py` 检查发表记录即可确认文章是否已发布。

### Q5：用户要新增 skill 到本仓库？
A：拷贝到 `.agents/skills/` 下，更新本 README 的 skill 列表，并在 `金融分析相关 skill` 或 `辅助 skill` 区域中正确归类。

---

## 9. 提交注意事项

本仓库中需要提交的内容：
- ✅ `wechat-publish/` 项目代码与文章
- ✅ `.agents/skills/` 下所有项目级 skill
- ✅ `AGENTS.md`、本 README.md

不需要提交/应由运行时生成的内容：
- ❌ `wechat-publish/.browser_profile/` — 浏览器 session 文件
- ❌ `wechat-publish/draft_url.json` — 运行时草稿缓存
- ❌ `wechat-publish/screenshots/` 中的运行时截图（除非用于文档）

---

## 10. 快速开始（Agent 速查）

```bash
# 1. 查看金融 skill
ls .agents/skills/

# 2. 运行公众号发布
cd wechat-publish
python auto_publish.py

# 3. 验证发布结果
python utils/verify_publish.py
```

---

*最后更新：2026-07-08*
