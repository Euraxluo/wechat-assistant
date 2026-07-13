#!/usr/bin/env python3
"""
微信公众号统一发布入口。

每次发布：
  1. 复制 runs/_example.json → runs/<slug>.json 并填写当次参数
  2. 阅读 config/topics/<topic>.md 获取题材差异与踩坑
  3. 运行本脚本

用法:
  python publish.py --run door-stabbing-0713.json
  python publish.py --run runs/door-stabbing-0713.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from engine.config import RUNS_DIR, load_run_config
from engine import publish_core


def main() -> int:
    parser = argparse.ArgumentParser(description="微信公众号文章发布")
    parser.add_argument(
        "--run",
        required=True,
        help="运行配置文件名（在 runs/ 下）或完整路径",
    )
    args = parser.parse_args()

    try:
        cfg = load_run_config(args.run)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"❌ 配置错误: {e}", file=sys.stderr)
        return 1

    print(f"题材: {cfg.topic} | slug: {cfg.slug}")
    print(f"标题: {cfg.title}")
    asyncio.run(publish_core.run(cfg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
