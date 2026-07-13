# 选题库（题材 Profile）

本目录声明**各题材线与通用发布流程之间的差异**。完整架构见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)。

## 核心思路

```
通用流程（engine/publish_core.py）  ← 不变
        +
题材 profile（本目录 *.md）        ← 选题/文风/配图/SOP 差异
        +
单次运行（runs/<slug>.json）       ← 当次标题/正文/封面
        +
长期记忆（memory/lessons/）        ← 踩坑沉淀
```

**新增题材**：复制 `_template.md` → 登记下方表格。**禁止**新建 `publish_*.py`。

## 发布方式

```bash
# 1. 读 config/topics/<topic>.md
# 2. 写 runs/<slug>.json
python publish.py --run <slug>.json
```

## Frontmatter 字段表（所有 profile 统一）

| 字段 | 含义 |
|------|------|
| `type` | 题材唯一标识（脚本/命令引用用，如 `hot-social`） |
| `name` | 中文展示名 |
| `enabled` | 是否启用（`true`/`false`） |
| `description` | 一句话说明这条线做什么 |
| `选题.sources` | 去哪找选题（热搜/行情/媒体…） |
| `选题.filters` | 筛选标准（热度阈值、影响面…） |
| `选题.priority_dims` | 优先级排序维度 |
| `素材.methods` | 怎么挖素材（搜索/API/公告…） |
| `素材.verify` | 素材核实要求（事实/数字/来源） |
| `文章.style` | 文风（麦杰逊极简 / 数据驱动 / 共鸣…） |
| `文章.word_count` | 目标字数区间 |
| `文章.title_template` | 标题模板（含 `{占位}`） |
| `文章.digest_template` | 摘要模板 |
| `配图.tool` | 配图工具（默认 `ImageGen`） |
| `配图.style` | 配图视觉风格关键词 |
| `配图.prompt_template` | ImageGen prompt 模板（含 `{场景}` 占位） |
| `配图.count` | 配图数量（如 `4正文+1封面`） |
| `配图.notes` | 配图约束/坑（版权、禁止复用等） |
| `发布.author` | 作者署名 |
| `发布.cover_ratio` | 封面比例（默认 `2.35:1`） |
| `发布.special_sop` | 该题材特有的流程步骤/坑（列表） |

## 如何新增一条题材

1. 复制 `_template.md` 为 `topics/<type>.md`
2. 填 frontmatter + 正文「踩坑/经验」章节
3. 在下方登记一行
4. 可选：创建 `memory/lessons/<type>.md`

## 与发布引擎的关系

`publish.py` + `runs/<slug>.json` 驱动 `engine/publish_core.py`。本目录供 Agent 阅读；机器可读 frontmatter 解析为 P2 任务。

## 题材登记

| type | name | profile |
|------|------|---------|
| `hot-social` | 实时热点·社会新闻 | [hot-social.md](hot-social.md) |
| `finance-news` | 实时财经新闻 | [finance-news.md](finance-news.md) |
| `tech-ai` | 科技/AI 资讯 | [tech-ai.md](tech-ai.md) |
| `life-work` | 泛生活/职场 | [life-work.md](life-work.md) |
| `ent-movie` | 影视剧热点跟踪（国内外） | [ent-movie.md](ent-movie.md) |
