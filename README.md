# 微信公众号内容生产与自动发布工作台

> **给 Agent 看的仓库说明书**：本 workspace 负责「选题 → 写文 → 配图 → 发布到微信公众号」的完整闭环。第一次进入请先读本文件。

---

## 1. 这个仓库是做什么的

多题材公众号内容生产与自动发布工作台。

| 层 | 做什么 | 在哪 |
|----|--------|------|
| **发布能力** | Playwright 登录后台，一键发表图文 | `wechat-publish/` |
| **题材扩展** | 各题材差异用 profile 声明 | `config/topics/` |
| **内容生产 skill** | 按题材调用写作、搜索、取数等工具 | `.agents/skills/` |

发布走 **单引擎 + 配置驱动**：换题材只改 profile / `runs/*.json`，禁止再复制 `publish_*.py`。

---

## 2. 目录结构

```
wechat-assistant/
├── AGENTS.md                     # Agent 入口（精简）
├── README.md                     # 本文件
├── .agents/skills/               # 项目级 Skill（发布 + 内容工具）
│   ├── wechat-auto-publish/      # 发布操作手册（不复制代码）
│   ├── content-creator-cn/       # 中文写作
│   ├── web_search/               # 搜索
│   └── …（按题材按需挂接的其他 skill）
└── wechat-publish/               # 公众号 Workspace
    ├── publish.py                # 🚪 唯一发布入口
    ├── engine/                   # Playwright 引擎（不变代码）
    ├── config/topics/            # 题材 profile（差异声明）
    ├── runs/                     # 单次运行 JSON（本地，除 _example）
    ├── memory/                   # lessons(Git) + journal(本地)
    ├── content/                  # plans / drafts / published / assets(本地)
    ├── data/snapshots/           # 写稿用数据快照（按题材可选）
    └── docs/                     # ARCHITECTURE / GIT_POLICY / workflows
    ├── utils/                    # verify / republish / check_draftbox
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

题材只决定「第 2–4 步用什么工具、什么文风」；第 5–7 步永远是同一套发布引擎。

| 题材 `type` | profile |
|-------------|---------|
| `hot-social` | [hot-social.md](wechat-publish/config/topics/hot-social.md) |
| `finance-news` | [finance-news.md](wechat-publish/config/topics/finance-news.md) |
| `tech-ai` | [tech-ai.md](wechat-publish/config/topics/tech-ai.md) |
| `life-work` | [life-work.md](wechat-publish/config/topics/life-work.md) |
| `ent-movie` | [ent-movie.md](wechat-publish/config/topics/ent-movie.md) |

新增题材：复制 `config/topics/_template.md`，按需挂接 skill，不要改 `engine/`。  
题材专属 SOP / 卡点写在对应 profile 与 `memory/lessons/<topic>.md`，不堆在本 README。

---

## 5. 发布脚本使用说明

### 5.1 前置条件

```bash
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python -m playwright install chromium
```

首次运行需扫码登录，session 在 `.browser_profile/`（本地，不进 Git）。

### 5.2 运行方式

```bash
cd wechat-publish
cp runs/_example.json runs/my-article.json   # 编辑 title / html / cover / images_dir
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python publish.py --run my-article.json
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python utils/verify_publish.py
```

> `auto_publish.py` 已移除，统一使用 `publish.py --run <slug>.json`。

### 5.3 引擎流程（engine/publish_core.py）

1. 正文本地图 → 微信 CDN  
2. 填标题 / 作者 / 摘要 / 正文  
3. 上传封面 → 保存草稿 → 恢复封面预览  
4. 发表 → 弹窗链 → 等待微信扫码（~6min）

### 5.4 辅助脚本

| 脚本 | 作用 |
|------|------|
| `utils/verify_publish.py` | 验证发表记录 |
| `utils/republish.py` | 从草稿继续发表 |
| `utils/check_draftbox.py` | 检查草稿箱 |
| `diagnostics/*.py` | 开发调试，生产勿用 |

### 5.5 发布常见卡点

- 发表时微信扫码验证是正常卡点，脚本等待约 6 分钟
- 成功后必须跑 `verify_publish.py` 确认发表记录
- 验证失败可先 `utils/republish.py` 从草稿继续
- 封面/正文图须先上传微信 CDN（引擎会处理）

---

## 6. Skill 怎么用

| 场景 | 优先 Skill |
|------|------------|
| 发布到公众号 | `wechat-auto-publish` |
| 写作 / 选题 | `content-creator-cn`、`content-strategy` |
| 搜热搜 / 资讯 | `web_search` |
| 某题材专属取数 / 分析 | 见该题材 `config/topics/<type>.md` |

用户级 skill（gzh-design、wechat-viral-topic 等）见各工具全局目录。

---

## 7. FAQ

**Q：没有 WECHAT_APP_ID 怎么发？**  
A：用 `publish.py` 浏览器自动化，不需要 API 白名单。

**Q：封面/正文图显示不了？**  
A：本地图须先上传微信 CDN。HTML 里只写文件名，`images_dir` 指向 `content/assets/<slug>/`。

**Q：配图要 commit 吗？**  
A：不要。`content/assets/` 仅本地，见 GIT_POLICY.md。

**Q：新增题材？**  
A：加 `config/topics/<type>.md`，按需挂 skill；不要新建 publish 脚本。

**Q：发表后 320003 会话过期？**  
A：正常现象，用 `verify_publish.py` 确认即可。

---

## 8. Git 提交边界

| 提交 Git ✅ | 仅本地 ❌ |
|------------|----------|
| `engine/`、`publish.py`、`utils/` | `.browser_profile/` |
| `config/topics/`、`memory/lessons/` | `runs/<slug>.json` |
| `content/drafts/`、`content/plans/` | `content/assets/` |
| `content/published/` + manifest | `content/archive/` |
| `docs/`、`data/snapshots/` | `draft_url.json`、`screenshots/` |

全文：[wechat-publish/docs/GIT_POLICY.md](wechat-publish/docs/GIT_POLICY.md)

---

## 9. 快速开始

```bash
ls .agents/skills/
cd wechat-publish
cp runs/_example.json runs/test.json   # 编辑后
python publish.py --run test.json
python utils/verify_publish.py
```

---

*最后更新：2026-07-14 · workspace v2*
