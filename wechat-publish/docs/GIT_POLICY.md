# Git vs 本地：什么该提交，什么留本地

> 一句话：**Git 存「能力和知识」，本地存「运行时状态和个人操作痕迹」。内容资产（文章/图片）按策略分级。**

---

## 三层分类

| 层级 | 含义 | 是否 push Git | 典型路径 |
|------|------|:-------------:|----------|
| **A. 能力层** | 代码、工具、模板、架构文档 | ✅ 必须 | `engine/`, `publish.py`, `utils/`, `docs/` |
| **B. 知识层** | 题材差异、跨次踩坑、工作流 SOP | ✅ 必须 | `config/topics/`, `memory/lessons/`, `docs/workflows/` |
| **C. 运行时层** | 登录态、草稿缓存、调试截图、当次配置 | ❌ 仅本地 | `.browser_profile/`, `draft_url.json`, `screenshots/`, `runs/<slug>.json` |
| **D. 内容层** | 文章 HTML、配图、行情快照 | ⚖️ 可选 | `content/`, `data/snapshots/` |

---

## A. 必须提交 Git（能力层）

这些是 workspace 的「操作系统」——换机器、换 Agent 都要能复现。

```
wechat-publish/
├── publish.py              # 发布入口
├── engine/                 # Playwright 引擎
├── utils/                  # verify / republish / check_draftbox
├── config/topics/          # 题材 profile（含 _template.md）
├── runs/_example.json      # 运行配置模板
├── runs/README.md
├── memory/README.md
├── memory/lessons/         # 跨次踩坑（团队共享记忆）
├── docs/                   # ARCHITECTURE.md、workflows/
├── content/README.md       # 目录规范（不是内容本身）
├── data/README.md
└── _archive/               # 废弃脚本（只读参考）

.agents/skills/wechat-auto-publish/   # Agent 操作手册
AGENTS.md、README.md                  # 仓库级指引
```

**原则**：改这里 = 改「怎么发」，不是「发哪一篇」。

---

## B. 必须提交 Git（知识层）

| 路径 | 为什么提交 |
|------|-----------|
| `config/topics/*.md` | 题材差异是长期资产，新 Agent 必须先读 |
| `memory/lessons/*.md` | 踩坑沉淀 = 「越用越好用」的核心，应跨会话共享 |
| `docs/workflows/*.md` | SOP 是流程知识，不是单次产出 |
| `content/plans/topic-plan-*.md` | 选题方案有复盘价值，体量小 |

**原则**：提交后，任何 Agent 读仓库就能避开已知坑。

---

## C. 仅本地管理（运行时层）

已在 `.gitignore` 中，**永远不要 commit**：

| 路径 | 内容 | 原因 |
|------|------|------|
| `.browser_profile/` | 微信登录 cookie / session | 私密；换机器需重新扫码 |
| `draft_url.json` | 当前草稿 appMsgId、URL | 单次发布临时状态 |
| `screenshots/` | Playwright 调试截图 | 体积大、无长期价值 |
| `runs/<slug>.json` | 当次标题/正文/封面路径 | 高频、一次性；模板 `_example.json` 除外 |
| `memory/journal/*` | 单次发布复盘 | 个人操作日志，默认本地 |
| `backup/` | 手动备份 | 临时 |
| `.workbuddy/` | Cursor/本地工具缓存 | 环境相关 |
| `__pycache__/`, `.DS_Store` | 系统垃圾 | — |

**原则**：丢了可以重来，不该污染 git history。

---

## D. 内容层（可选，需你定策略）

当前状态：**全部在 Git 里**（历史迁移时提交的）。这是仓库膨胀的主因。

### 推荐策略（未来目标）

| 路径 | 推荐 | 理由 |
|------|------|------|
| `content/drafts/*.html` | ⚖️ **已发表的可提交，进行中可本地** | 终稿是资产；草稿迭代频繁 |
| `content/published/` | ✅ 提交 | 已验证发表的终稿归档 |
| `content/archive/` | ❌ 不提交 | 预览稿/排版实验/旧版，无长期价值 |
| `content/assets/<slug>/*.png` | ❌ 不提交（或 Git LFS） | 单张 1–2MB，35 张 ≈ 40MB+ |
| `data/snapshots/*.json` | ⚖️ 盘中稿提交，过期可删 | 保证文章数字可复现；时效过后是垃圾 |

### 当前 vs 目标

```
                    当前 Git    目标策略
content/drafts/       ✅ 在 Git   已发表 ✅ / 草稿中 ❌
content/archive/      ❌ 已移出   ❌ 仅本地
content/assets/       ❌ 已移出   ❌ 仅本地
content/published/    ✅ 结构在   终稿 HTML + manifest ✅
data/snapshots/       ✅ 在 Git   按时效清理
```

> **2026-07-13 更新**：`content/assets/` 与 `content/archive/` 已从 Git 跟踪移除，文件仍保留在本地。

---

## 决策流程图

```
新增/修改了一个文件
        │
        ▼
  是 Python/配置模板/文档吗？ ──是──→ ✅ 提交 Git
        │否
        ▼
  是登录态/截图/当次 runs.json 吗？ ──是──→ ❌ 仅本地
        │否
        ▼
  是 memory/journal 复盘吗？ ──是──→ ❌ 默认本地（精华提炼后写入 lessons/ 再提交）
        │否
        ▼
  是文章 HTML / PNG / JSON 快照吗？ ──是──→ 见下方内容层规则
        │否
        ▼
  不确定 → 先本地，确认有价值再提交
```

---

## 各操作对应的 Git 行为

| 你做了什么 | 该提交什么 | 不该提交什么 |
|-----------|-----------|-------------|
| 新发一篇热点文 | `content/drafts/` 终稿 HTML（可选）、`memory/lessons/` 若发现新坑 | `runs/foo.json`、`draft_url.json`、`screenshots/` |
| 新增题材线 | `config/topics/new-topic.md` | — |
| 修复发布引擎 bug | `engine/publish_core.py` | 调试截图 |
| 发布成功复盘 | 提炼进 `memory/lessons/<topic>.md` | 原始 `memory/journal/`（默认本地） |
| 财经午盘取数 | `data/snapshots/`（若要复现）、`content/drafts/` HTML | 盘中临时 runs.json |
| ImageGen 配图 | 目标：`content/assets/<slug>/` 本地 | 当前：仍在 Git（待改） |

---

## Memory 专项规则

```
memory/
├── lessons/<topic>.md     ✅ Git — 团队共享的长期记忆
└── journal/<date>-<slug>.md   ❌ 本地 — 单次操作流水账
```

**流转**：`journal`（本地草稿）→ 提炼精华 → `lessons`（提交 Git）→ 稳定后合并进 `config/topics/*.md`

---

## 仓库体积控制

| 风险 | 现状 | 对策 |
|------|------|------|
| PNG 撑大 `.git`（~44MB） | `content/assets/` 全在 Git | P2：gitignore assets，或 Git LFS |
| 重复草稿 HTML | `content/archive/` 在 Git | 删除或移出仓库 |
| 过期行情 JSON | 4 个 snapshot 在 Git | 发完后归档或删除过期文件 |
| 重复 publish 脚本 | 已解决 | `_archive/` 保留一份即可 |

---

## 快速自查命令

```bash
# 看哪些大文件在 Git 里
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '/^blob/ {print $3, $4}' | sort -rn | head -10

# 看某文件是否被 ignore
git check-ignore -v wechat-publish/runs/my-article.json

# 看工作区有没有误提交的运行时文件
git status
```

---

## 相关文件

- 忽略规则：仓库根 `.gitignore`
- 架构总览：`docs/ARCHITECTURE.md`
- 内容目录：`content/README.md`
