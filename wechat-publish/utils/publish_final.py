#!/usr/bin/env python3
"""兼容入口：转调当前仓库的 auto_publish.py。"""
import runpy
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
AUTO_PUBLISH = PROJECT_DIR / "auto_publish.py"

if __name__ == "__main__":
    runpy.run_path(str(AUTO_PUBLISH), run_name="__main__")
