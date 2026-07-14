# 公众号 Workspace 架构

> 设计原则：**代码只写一次，差异用配置表达，经验用 memory 沉淀，产物按生命周期分目录。**

## 问题诊断（2026-07-13）

起步阶段已出现：
- 8 份几乎相同的 `publish_*.py`（~6000 行重复）
- `articles/` 混放终稿、预览稿、选题计划、JSON 快照、35 张 PNG
- 题材差异写在脚本顶部，topic profile 只供人读、机器不读
- 无统一 memory，踩坑散落在 commit message 和 markdown 各处

## 目标架构

```
wechat-publish/                    # 公众号专用 workspace
│
├── publish.py                     # 🚪 唯一发布入口（CLI）
├── engine/                        # 🔧 不变代码（Playwright 自动化）
│   ├── config.py                  #    加载 runs/*.json
│   └── publish_core.py            #    13 步发表流程
│
├── config/                        # 📋 稳定配置（低频变更）
│   └── topics/                    #    题材 profile（选题/文风/配图/SOP 差异）
│
├── runs/                          # 🏃 单次运行输入（高频，不膨胀代码）
│   ├── _example.json              #    模板（提交）
│   └── <slug>.json                #    当次标题/正文/封面（gitignore）
│
├── memory/                        # 🧠 长期记忆（越用越好用）
│   ├── lessons/<topic>.md         #    跨次踩坑合集
│   └── journal/<date>-<slug>.md   #    单次复盘
│
├── content/                       # 📄 内容资产（按生命周期，逐步迁移）
│   ├── plans/                     #    选题方案 topic-plan-*
│   ├── drafts/                    #    进行中 HTML
│   ├── published/                 #    已发表终稿（可选归档）
│   └── assets/<slug>/             #    当次配图（替代 articles/images 大杂烩）
│
├── data/                          # 📊 数据快照（财经 JSON 等）
├── tools/                         # 🔨 辅助工具（verify / republish / check_draftbox）
│   └── (当前仍为 utils/，兼容旧路径)
│
├── diagnostics/                   # 🧪 开发调试（不用于生产）
```

## 扩展点（膨胀控制）

| 你想加什么 | 应该加在哪 | 不应该加什么 |
|-----------|-----------|-------------|
| 新题材（影视/财经/科技） | `config/topics/<type>.md` | 新的 `publish_xxx.py` |
| 发一篇文章 | `runs/<slug>.json` | 改 `engine/` |
| 本次踩坑 | `memory/journal/` → `memory/lessons/` | 写进 Python 注释 |
| 发布引擎 bugfix | `engine/publish_core.py` | 复制整份脚本 |
| 财经专属取数 | `tools/finance_chart.py` 或 skill | 塞进 publish 引擎 |
| 排版/HTML 规则 | topic profile `文章.style` | 新一套 publish 脚本 |

## 标准工作流

```
1. 读 config/topics/<topic>.md     # 题材差异
2. 读 memory/lessons/<topic>.md    # 历史坑
3. 选题 → content/plans/
4. 写文 → content/drafts/ 或 articles/（过渡期）
5. 配图 → content/assets/<slug>/
6. 写 runs/<slug>.json
7. python publish.py --run <slug>.json
8. python utils/verify_publish.py
9. 写 memory/journal/<date>-<slug>.md
```

## 与 Skill 的关系

```
.agents/skills/wechat-auto-publish/SKILL.md   ← Agent 读的操作手册
         ↓ 指向
wechat-publish/publish.py                     ← 实际执行
         ↓ 读取
config/topics/ + runs/ + memory/              ← 差异与记忆
```

Skill **不复制** Python 代码；workspace **自包含**可执行逻辑。

## Git 与本地边界

哪些进 Git、哪些只留本机，见 **[GIT_POLICY.md](GIT_POLICY.md)**（发布前 Agent 必读）。

## 迁移计划（渐进，不一次性搬家）

| 阶段 | 动作 | 状态 |
|------|------|------|
| P0 | 单引擎 `publish.py` + `runs/` | ✅ 本次 |
| P0 | `topics/` → `config/topics/` | ✅ 本次 |
| P0 | 归档 8 个 `publish_*.py` | ✅ 本次 |
| P1 | `articles/` 逐步迁入 `content/` | ✅ 2026-07-13 |
| P1 | `utils/` 重命名为 `tools/` | 待做 |
| P2 | topic profile frontmatter 机器可读 | 待做 |
| P2 | journal 自动追加 hook | 待做 |

## 反模式清单

- ❌ 每发一篇就 commit 一个 750 行脚本
- ❌ 把预览稿、排版稿、终稿全放同一目录不加后缀规范
- ❌ ImageGen 超时后复用其他题材旧图
- ❌ 在 skill 里维护第二份 `auto_publish.py`
- ❌ 把所有 PNG 永久堆在 git 里（未来考虑 LFS 或 assets 外置）
- ❌ 把 `runs/<slug>.json`、`draft_url.json`、`.browser_profile/` 提交进 Git

## Git vs 本地

详见 **[docs/GIT_POLICY.md](GIT_POLICY.md)** — 能力/知识提交 Git，运行时仅本地，内容层按策略分级。
