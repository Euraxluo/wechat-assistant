# Memory — 越用越好用

本目录是公众号工作区的**长期记忆层**，与单次运行的 `runs/*.json` 分离。

## 三层记忆

```
config/topics/<type>.md     ← 题材「说明书」（稳定、人工维护）
        ↑ 定期提炼
memory/lessons/<type>.md    ← 跨次运行的踩坑合集（append-only）
        ↑ 每次发布后写
memory/journal/<date>-<slug>.md  ← 单次运行复盘（可选，轻量）
```

| 层 | 更新频率 | 谁写 | 内容 |
|----|----------|------|------|
| **topic profile** | 题材新增/大改时 | 人 + Agent | 选题源、文风、配图策略、SOP 差异 |
| **lessons** | 每 3–5 次发布后合并 | Agent 提炼 | 可复用的坑与解法（≤10 条/题材） |
| **journal** | 每次发布后 | Agent | 本次标题、结果、耗时、新发现的坑 |

## 写入规则

1. **发布失败或验证失败** → 必须写 journal，记录卡在哪一步
2. **发现可复用坑** → journal 里标 `→ lesson`，下次合并进 `lessons/`
3. **lessons 超过 15 条** → 合并去重，沉淀进 `config/topics/*.md` 的「踩坑/经验」
4. **不要**把 memory 写进 `publish_*.py` 或 HTML 里

## Journal 模板

```markdown
# <date> <slug>

- topic: hot-social
- title: ...
- result: published | draft | failed
- blocker: 微信扫码超时 / 配图错配 / ...
- new_lesson: （如有）
- duration_min: 
```

## 与 Agent 的关系

Agent 启动任务时应：

1. 读 `config/topics/<topic>.md`（题材差异）
2. 读 `memory/lessons/<topic>.md`（历史坑）
3. 任务结束后写 `memory/journal/`（本次复盘）

这是「个人助手越用越好用」的落地点——**不靠隐式上下文，靠显式 markdown 沉淀**。
