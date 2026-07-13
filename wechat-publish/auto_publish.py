#!/usr/bin/env python3
"""[已废弃] 请使用 publish.py --run <slug>.json

本文件保留为兼容入口，自动转发到统一发布引擎。
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def main():
    print("⚠️  auto_publish.py 已废弃，请改用: python publish.py --run <slug>.json")
    print("    参见 wechat-publish/docs/ARCHITECTURE.md")
    example = PROJECT_DIR / "runs" / "_example.json"
    if not example.exists():
        print("❌ 未找到 runs/_example.json，请先创建运行配置")
        return 1
    cmd = [sys.executable, str(PROJECT_DIR / "publish.py"), "--run", str(example)]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
