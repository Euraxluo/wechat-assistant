#!/usr/bin/env python3
"""检查当前仓库草稿箱状态。"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_DIR = Path(__file__).resolve().parents[1]
USER_DATA_DIR = PROJECT_DIR / ".browser_profile"
SCREENSHOT_DIR = PROJECT_DIR / "screenshots"
MP_URL = "https://mp.weixin.qq.com/"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


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
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)

        token = await extract_token(page)
        print(f"Token extracted: {bool(token)}")
        if not token:
            await context.close()
            return

        draft_box_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_manage&action=list&type=77&token={token}&lang=zh_CN"
        await page.goto(draft_box_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        drafts = await page.evaluate(
            """
            () => {
                const cards = document.querySelectorAll('.weui-desktop-card[data-appid], .weui-desktop-card');
                return Array.from(cards).map(c => {
                    const titleEl = c.querySelector('.appmsg_title, .weui-desktop-card__title');
                    const thumb = c.querySelector('.appmsg_thumb, [class*="thumb"]');
                    const thumbBg = thumb ? (thumb.style.backgroundImage || window.getComputedStyle(thumb).backgroundImage) : '';
                    const btn = c.querySelector('.weui-desktop-link_send-multi');
                    return {
                        appId: c.getAttribute('data-appid') || '',
                        title: ((titleEl?.innerText || c.innerText || '').trim()).slice(0, 80),
                        thumbBg: thumbBg.slice(0, 120),
                        hasThumb: thumbBg.includes('url') && !thumbBg.includes('url(\"\")'),
                        btnDisabled: btn?.classList?.contains('weui-desktop-link_disable') || false,
                    };
                }).filter(x => x.title);
            }
            """
        )
        print(f"草稿数量: {len(drafts)}")
        print(json.dumps(drafts, ensure_ascii=False, indent=2))

        await page.screenshot(path=str(SCREENSHOT_DIR / "check_draftbox.png"), full_page=True)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
