---
type: tech-ai
name: 科技/AI 资讯
enabled: true
description: 科技产品发布、AI 模型/研究动态、行业事件，清晰可解释、重事实与原始来源
选题:
  sources:
    - 科技媒体（36氪、机器之心、量子位、The Verge 等）
    - 官方博客 / 发布页、GitHub、arXiv
    - 社交平台上的技术圈热点
  filters: 影响力 + 新奇度 + 可解释性；回避未证实爆料
  priority_dims:
    - 技术影响力
    - 读者新颖度
    - 可解释性（能否讲清楚）
素材:
  methods:
    - 读官方公告/论文摘要/发布说明原文
    - WebSearch 交叉，优先一手来源
  verify:
    - 版本号、发布日期、参数指标逐字核对
    - 引用原始链接（论文/官网/仓库）
    - 不夸大能力，区分「官方宣称」与「实测」
文章:
  style: 清晰、带技术解释、不堆术语，复杂概念用类比
  word_count: 1200-2000
  title_template: "{产品/模型}：{核心能力或事件}"
  digest_template: "一句话能力/事件 + 为什么重要"
配图:
  tool: ImageGen
  style: 科技感 editorial，冷蓝/线条/几何，未来感但克制
  prompt_template: "Editorial illustration, {场景}, tech futuristic mood, cool blue palette, clean geometry, no text, concept art"
  count: 3正文 + 1封面
  notes: 不用未授权产品截图/Logo 实景；用 AI 生成抽象科技感插画替代
发布:
  author: AI提效实验室
  cover_ratio: 2.35:1
  special_sop:
    - 技术事实核实：版本号/日期/指标准确
    - 链接原始来源（论文/官网/仓库）
    - 区分官方宣称与第三方实测
---

# 科技/AI 资讯 题材说明

## 流程差异概述

与社会新闻相比，技术线重「一手来源 + 可解释」。选题来自科技媒体与官方发布，
文章要把技术讲明白，配图走科技感而非暗调社会新闻风。

## 配图策略

冷蓝未来感 editorial，避免直接搬产品 Logo/截图（版权），用抽象科技意象。

## 踩坑 / 经验（待实战补充）

- 待补：首篇跑通后记录常用一手来源与核实清单。

## 标题 / 摘要示例（占位）

- 标题：`{产品/模型}：{核心能力}`
- 摘要：`{能力/事件}。{为什么重要}`
