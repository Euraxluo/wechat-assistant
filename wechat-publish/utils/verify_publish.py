#!/usr/bin/env python3
"""验证最新公众号发表记录。

可选参数：
  --title "文章标题"   显式指定要核对的目标标题（推荐，避免读到旧脚本标题）
"""
import argparse
import asyncio
import os
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = PROJECT_DIR / "screenshots"
USER_DATA_DIR = PROJECT_DIR / ".browser_profile"
DRAFT_URL_FILE = PROJECT_DIR / "draft_url.json"
RUNS_DIR = PROJECT_DIR / "runs"
MP_URL = "https://mp.weixin.qq.com/"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def load_expected_title(cli_title: str | None = None):
    if cli_title:
        return cli_title
    if DRAFT_URL_FILE.exists():
        text = DRAFT_URL_FILE.read_text(encoding="utf-8")
        m = re.search(r'"title"\s*:\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    # 回退：最近修改的 runs/*.json（排除 _example）
    runs = sorted(
        [p for p in RUNS_DIR.glob("*.json") if p.name != "_example.json"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in runs:
        try:
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("title"):
                return data["title"]
        except Exception:
            continue
    return ""


async def extract_token(page):
    return await page.evaluate(
        """
        () => {
            const m = window.location.href.match(/token=(\d+)/);
            if (m) return m[1];
            const l = document.querySelector('a[href*="token="]');
            if (l) {
                const m2 = l.href.match(/token=(\d+)/);
                return m2 ? m2[1] : '';
            }
            return '';
        }
        """
    )


async def main():
    parser = argparse.ArgumentParser(description="验证公众号发表记录")
    parser.add_argument("--title", default=None, help="显式指定要核对的目标标题")
    args = parser.parse_args()

    expected_title = args.title or load_expected_title()
    print(f"目标标题: {expected_title or '（未解析到）'}")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("[1] 访问公众号主页...")
        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOT_DIR / "verify_home.png"))

        body_text = await page.inner_text("body")
        is_login_page = (
            ("扫码" in body_text and "公众号" in body_text)
            or "请重新登录" in body_text
            or "二维码" in body_text
        )
        print(f"  是否登录页: {is_login_page}")
        if is_login_page:
            print("  ⚠️ 浏览器已退出登录，请先扫码登录后重试")
            await context.close()
            return

        token = await extract_token(page)
        if not token:
            print("  ❌ 未提取到 token")
            await context.close()
            return

        print("[2] 检查发表记录...")
        pub_url = f"https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=20&token={token}&lang=zh_CN"
        await page.goto(pub_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(SCREENSHOT_DIR / "verify_publish_record.png"), full_page=True)

        body_text = await page.inner_text("body")
        page_content = await page.content()
        has_title = expected_title in body_text if expected_title else False
        has_title2 = expected_title in page_content if expected_title else False
        print(f"  发表记录包含目标文章(inner_text): {has_title}")
        print(f"  发表记录包含目标文章(content): {has_title2}")

        articles = await page.evaluate(
            """
            () => {
                const cards = document.querySelectorAll('.weui-desktop-card');
                return Array.from(cards).map(card => {
                    const title = card.querySelector('.weui-desktop-card__title, .publish_title, .appmsg_title')?.innerText || '';
                    const time = card.querySelector('.weui-desktop-card__time, .publish_time')?.innerText || '';
                    const status = card.querySelector('.publish_status')?.innerText || '';
                    return { title: title.trim().slice(0, 80), time: time.trim(), status: status.trim() };
                }).filter(x => x.title);
            }
            """
        )
        print(f"  找到 {len(articles)} 篇文章:")
        for a in articles[:10]:
            print(f"    - {a['title']} | {a['time']} | {a['status']}")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
