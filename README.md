# 金融分析 · 公众号自动发布工作台

> **给 Agent 看的仓库说明书**：本 workspace 用于「金融研究 + 公众号文章生产与自动发布」。第一次进入请先读本文件。

---

## 1. 这个仓库是做什么的

两个核心能力：

1. **金融分析**：股票/基金/宏观分析 skill（`.agents/skills/`）
2. **公众号发布**：浏览器自动化登录后台发文（`wechat-publish/`）

文章产出后，通过 **单引擎 + 配置驱动** 流程发布到微信公众号，支持多题材扩展。

---

## 2. 目录结构

```
wechat-assistant/
├── AGENTS.md                     # Agent 入口（精简）
├── README.md                     # 本文件
├── .agents/skills/               # 项目级 Skill
│   ├── wechat-auto-publish/      # 发布操作手册（不复制代码）
│   ├── xiaodi-financial-analysis-team/  … 等金融 skill
│   └── web_search/ content-creator-cn/ …
└── wechat-publish/               # 公众号 Workspace
    ├── publish.py                # 🚪 唯一发布入口
    ├── engine/                   # Playwright 引擎（不变代码）
    ├── config/topics/            # 题材 profile（差异声明）
    ├── runs/                     # 单次运行 JSON（本地，除 _example）
    ├── memory/                   # lessons(Git) + journal(本地)
    ├── content/                  # plans / drafts / published / assets(本地)
    ├── data/snapshots/           # 行情 JSON 快照
    ├── docs/                     # ARCHITECTURE.md / GIT_POLICY.md / workflows/
    ├── utils/                    # verify / republish / check_draftbox
    └── _archive/                   # 废弃脚本（只读参考）
```

详细架构：[wechat-publish/docs/ARCHITECTURE.md](wechat-publish/docs/ARCHITECTURE.md)  
Git vs 本地：[wechat-publish/docs/GIT_POLICY.md](wechat-publish/docs/GIT_POLICY.md)

---

## 3. wechat-publish vs wechat-auto-publish

| 目录 | 类型 | 作用 |
|------|------|------|
| `wechat-publish/` | Workspace | 代码、配置、内容、memory |
| `.agents/skills/wechat-auto-publish/` | Skill | Agent 操作手册，指向 workspace |

**Agent 必记**：
- 发布 → `publish.py --run runs/<slug>.json`
- 题材差异 → `config/topics/<type>.md`
- 历史踩坑 → `memory/lessons/<type>.md`
- ❌ 禁止新建 `publish_*.py`

---

## 4. 核心工作流

### 通用选题 → 发布

```text
1. 读 config/topics/<topic>.md + memory/lessons/<topic>.md
2. 选题 → content/plans/
3. 写文 → content/drafts/
4. 配图 → content/assets/<slug>/（本地，不进 Git）
5. 配置 → runs/<slug>.json（本地）
6. 发布 → python publish.py --run <slug>.json
7. 验证 → python utils/verify_publish.py
8. 复盘 → memory/journal/（本地）→ 提炼进 memory/lessons/（Git）
```

### 金融分析链路

```
选题 → 取数(akshare-stock) → 分析(xiaodi-financial-analysis-team)
     → 写作(content-creator-cn) → 排版(gzh-design) → 发布(publish.py)
```

题材 profile 已覆盖：`hot-social` / `finance-news` / `tech-ai` / `life-work` / `ent-movie`

---

## 5. 午盘/盘中研报 SOP（Agent 必读）

```text
1. 读 README.md / AGENTS.md / 相关 skill
2. 取数落盘 → data/snapshots/midday_data_YYYYMMDD.json
3. 生成 HTML → content/drafts/
4. 新建 runs/<slug>.json
5. python publish.py --run <slug>.json
6. python utils/verify_publish.py
```

### 5.1 验证过的卡点

- 金融数字必须可追溯，无法核验时写「暂无可验证数据」
- 行情数据立即写入 `data/snapshots/`，避免重复请求丢数
- 发表时微信扫码验证是正常卡点，脚本等待约 6 分钟
- 成功后必须跑 `verify_publish.py` 确认发表记录
- 时点失效立刻废稿切题（竞价稿/午盘稿/收评稿各有窗口）
- 验证失败可先 `utils/republish.py` 从草稿继续

---

## 6. 发布脚本使用说明

### 6.1 前置条件

```bash
# Playwright（推荐 workbuddy venv）
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python -m playwright install chromium
```

首次运行需扫码登录，session 保存在 `.browser_profile/`（本地，不进 Git）。

### 6.2 运行方式

```bash
cd wechat-publish

# 1. 复制运行配置
cp runs/_example.json runs/my-article.json
# 编辑 title / html / cover / images_dir

# 2. 发布
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python publish.py --run my-article.json

# 3. 验证
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python utils/verify_publish.py
```

> `auto_publish.py` 已废弃，会自动转发到 `publish.py`，请勿直接改其逻辑。

### 6.3 引擎流程（engine/publish_core.py）

1. 上传正文本地图 → 微信 CDN 替换
2. 填写标题/作者/摘要/正文
3. 上传封面 → 保存草稿 → 恢复封面预览
4. 发表 → 处理弹窗链 → 等待微信扫码（~6min）

### 6.4 辅助脚本

| 脚本 | 作用 |
|------|------|
| `utils/verify_publish.py` | 验证发表记录 |
| `utils/republish.py` | 从草稿继续发表 |
| `utils/check_draftbox.py` | 检查草稿箱 |
| `diagnostics/*.py` | 开发调试，生产勿用 |

---

## 7. Skill 优先级

| 优先级 | Skill | 用途 |
|--------|-------|------|
| ⭐⭐⭐ | `xiaodi-financial-analysis-team` | 金融分析团队 |
| ⭐⭐⭐ | `akshare-stock` | A 股数据 |
| ⭐⭐⭐ | `wechat-auto-publish` | 公众号发布 |
| ⭐⭐ | `claw-stock` / `china-stock-analysis` | 个股/趋势 |
| ⭐⭐ | `data-analysis-skill` / `web_search` | 数据/资讯 |
| ⭐ | `content-creator-cn` / `content-strategy` | 写作/选题 |

用户级 skill（gzh-design、wechat-viral-topic 等）见各工具全局目录。

---

## 8. FAQ

**Q：没有 WECHAT_APP_ID 怎么发？**  
A：用 `wechat-publish/publish.py` 浏览器自动化，不需要 API 白名单。

**Q：封面/正文图显示不了？**  
A：本地图必须先上传到微信 CDN。`publish.py` 会自动处理；HTML 里只写文件名，`images_dir` 指向 `content/assets/<slug>/`。

**Q：配图要 commit 吗？**  
A：不要。`content/assets/` 仅本地，见 GIT_POLICY.md。

**Q：新增一个题材线？**  
A：复制 `config/topics/_template.md`，不要新建 publish 脚本。

**Q：发表后 320003 会话过期？**  
A：正常现象，用 `verify_publish.py` 确认即可。

---

## 9. Git 提交边界

| 提交 Git ✅ | 仅本地 ❌ |
|------------|----------|
| `engine/`、`publish.py`、`utils/` | `.browser_profile/` |
| `config/topics/`、`memory/lessons/` | `runs/<slug>.json` |
| `content/drafts/`、`content/plans/` | `content/assets/` |
| `content/published/` + manifest | `content/archive/` |
| `docs/`、`data/snapshots/` | `draft_url.json`、`screenshots/` |

全文：[wechat-publish/docs/GIT_POLICY.md](wechat-publish/docs/GIT_POLICY.md)

---

## 10. 快速开始

```bash
# 查看 skill
ls .agents/skills/

# 发布一篇文章
cd wechat-publish
cp runs/_example.json runs/test.json   # 编辑后
python publish.py --run test.json
python utils/verify_publish.py
```

---

*最后更新：2026-07-13 · workspace v2*
