---
type: ent-movie
name: 影视剧热点跟踪（国内外）
enabled: true
description: 国内外影视剧开播/收官/争议/奖项热点，点评与追剧指南，重版权规避
选题:
  sources:
    - 国内：豆瓣、微博、猫眼/灯塔、影视圈话题
    - 国外：IMDb、Rotten Tomatoes、Letterboxd、行业媒体
  filters: 热度 + 讨论度 + 可评点性；国内外分池跟踪
  priority_dims:
    - 热度（开播/收官/出圈名场面）
    - 争议/讨论空间
    - 评分变化（国内外用各自平台标准）
素材:
  methods:
    - 国内外评分平台数据 + 媒体评测 + 观众讨论
    - 区分「国内热」与「海外热」，分别标注
  verify:
    - 剧名/导演/主演/播出平台/日期准确
    - 评分注明平台与口径（豆瓣 X 分 / 烂番茄 Y%）
    - 不剧透关键结局（或明确标注「剧透预警」）
文章:
  style: 点评、追剧指南、争议梳理，可读性强
  word_count: 1200-2000
  title_template: "{剧名}：{核心看点或争议}"
  digest_template: "一句话定位 + 为什么值得看/聊"
配图:
  tool: ImageGen
  style: 影视感 editorial，胶片质感、戏剧光影
  prompt_template: "Editorial illustration, {场景}, cinematic film mood, dramatic lighting, no real faces, no text, concept art"
  count: 3正文 + 1封面
  notes: |
    版权红线：不用剧照/海报实景（版权），用 AI 生成影视感插画替代，或仅文字描述。
    不生成可识别真人面孔。
发布:
  author: AI提效实验室
  cover_ratio: 2.35:1
  special_sop:
    - 国内外分区：评分/热度用各自平台口径，不混用
    - 剧照/海报版权：一律 AI 生成替代，禁实景搬运
    - 关键结局加「剧透预警」
---

# 影视剧热点跟踪（国内外）题材说明

## 流程差异概述

与新闻线最大差异是**版权规避**：剧照、海报都有版权，配图一律用 ImageGen 生成
影视感插画，不搬实景；国内外评分/热度分池跟踪，不混用口径。

## 配图策略

胶片质感、戏剧光影的 editorial，抽象意象（放映机、座位、光斑），不出现可识别真人。

## 踩坑 / 经验（待实战补充）

- 待补：国内外数据源与评分口径对照。

## 标题 / 摘要示例（占位）

- 标题：`{剧名}：{看点/争议}`
- 摘要：`{定位}。{为什么值得看/聊}`
