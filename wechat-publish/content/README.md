# Content 目录

```
content/
├── plans/              # 选题方案 topic-plan-*          [Git ✅]
├── drafts/             # 待发布 HTML                    [Git ⚖️ 终稿可留]
├── published/          # 已发表归档 + manifest.json     [Git ✅ 小文件]
├── archive/            # 预览/排版实验/旧版             [本地 ❌]
└── assets/
    └── <slug>/         # 当次配图，发表后可删            [本地 ❌]
```

## 当前资产索引

| slug | 正文（Git） | 配图（本地） |
|------|------------|-------------|
| `door-stabbing-0713` | `drafts/article_door_stabbing_0713_v2.html` | `assets/door-stabbing-0713/` |
| `finance-0713` | `drafts/article_finance_0713_midday.html` | `assets/finance-0713/` |
| `tech-gpt56-0713` | `drafts/article_tech_gpt56_0713.html` | `assets/tech-gpt56-0713/` |
| `movie-kungfu-0713` | `drafts/article_movie_kungfu_girls_0713.html` | `assets/movie-kungfu-0713/` |
| `lifework-fourday-0713` | `drafts/article_lifework_fourday_week_0713.html` | `assets/lifework-fourday-0713/` |
| `kv-storage-0713` | `drafts/article_kv_storage_2026_0713.html` | `assets/kv-storage-0713/` |
| `gender-trust-0709` | `drafts/article_gender_trust_v3_极简.html` | `assets/gender-trust-0709/` |

配图目录不进 Git，见 [docs/GIT_POLICY.md](../docs/GIT_POLICY.md)。

## runs.json 路径示例

```json
{
  "html": "content/drafts/article_door_stabbing_0713_v2.html",
  "cover": "content/assets/door-stabbing-0713/Editorial_illustration_cover___....png",
  "images_dir": "content/assets/door-stabbing-0713"
}
```

HTML 内 `<img src="文件名.png">` 只写文件名，`images_dir` 指向所在目录即可。
