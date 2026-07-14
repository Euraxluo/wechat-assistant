#!/usr/bin/env python3
"""兼容入口：转调统一发布 CLI（需提供 runs/*.json）。"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLISH = PROJECT_DIR / "publish.py"


def main() -> int:
    print("⚠️  publish_final.py 已废弃，请使用: python publish.py --run <slug>.json")
    if len(sys.argv) < 2:
        print("示例: python publish.py --run morning-outlook-0714.json")
        return 1
    return subprocess.call([sys.executable, str(PUBLISH), "--run", sys.argv[1]])


if __name__ == "__main__":
    raise SystemExit(main())
