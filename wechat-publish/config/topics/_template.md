---
type: <题材标识，如 my-topic>
name: <中文展示名>
enabled: true
description: <一句话说明这条线做什么>
选题:
  sources:
    - <去哪找选题 1>
    - <去哪找选题 2>
  filters: <筛选标准，如 热度阈值 / 影响面 / 时效性>
  priority_dims:
    - <优先级维度 1>
    - <优先级维度 2>
素材:
  methods:
    - <怎么挖素材 1>
    - <怎么挖素材 2>
  verify:
    - <核实要求 1>
    - <核实要求 2>
文章:
  style: <文风，如 麦杰逊极简 / 数据驱动 / 共鸣>
  word_count: <目标字数，如 1200-1500>
  title_template: "<标题模板，含 {占位}>"
  digest_template: "<摘要模板>"
配图:
  tool: ImageGen
  style: <视觉风格关键词>
  prompt_template: "Editorial illustration, {场景}, <风格关键词>, no text, concept art"
  count: <如 4正文+1封面>
  notes: <约束/坑，如 不用真人照片、禁止跨题材复用>
发布:
  author: <作者署名>
  cover_ratio: 2.35:1
  special_sop:
    - <该题材特有步骤/坑 1>
    - <该题材特有步骤/坑 2>
---

# <中文展示名> 题材说明

> 本文件是 `_template.md` 的副本。删除本段，填写下方「踩坑/经验」，把通用流程在该题材下的
> **特殊之处**沉淀下来，供下次直接复用。

## 流程差异概述

（相对于通用 skill 流程，这条线哪里不一样？）

## 配图策略

（场景清单 + prompt 要点；本条线的配图最容易踩什么坑？）

## 踩坑 / 经验

- （例）事实必须核实，原稿曾把日期写错
- （例）配图必须题材专属，禁止复用其他题材的旧图
- （例）发表弹窗链顺序：声明 → 继续发表 → 发表 → 确认 → 扫码

## 标题 / 摘要示例

- 标题：`<示例>`
- 摘要：`<示例>`
