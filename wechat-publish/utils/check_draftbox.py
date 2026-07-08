#!/usr/bin/env python3
"""
检查草稿箱状态。
"""
import asyncio, os, json
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"
MP_URL = "https://mp.weixin.qq.com/"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)

        token = await page.evaluate("""
            () => {
                const m = window.location.href.match(/token=(\\d+)/);
                if (m) return m[1];
                const l = document.querySelector('a[href*="token="]');
                if (l) { const m2 = l.href.match(/token=(\\d+)/); return m2 ? m2[1] : ''; }
                return '';
            }
        """)
        print(f"Token: {token}")

        draft_box_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_manage&action=list&type=77&token={token}&lang=zh_CN"
        await page.goto(draft_box_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        drafts = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.weui-desktop-card[data-appid]');
                return Array.from(cards).map(c => {
                    const titleEl = c.querySelector('.appmsg_title, .weui-desktop-card__title');
                    const thumb = c.querySelector('.appmsg_thumb, [class*="thumb"]');
                    const thumbBg = thumb ? (thumb.style.backgroundImage || window.getComputedStyle(thumb).backgroundImage) : '';
                    const btn = c.querySelector('.weui-desktop-link_send-multi');
                    return {
                        appId: c.getAttribute('data-appid'),
                        title: (titleEl?.innerText || c.innerText).slice(0, 80),
                        thumbBg: thumbBg.slice(0, 80),
                        hasThumb: thumbBg.includes('url') && !thumbBg.includes('url("")'),
                        btnDisabled: btn?.classList?.contains('weui-desktop-link_disable') || false,
                    };
                });
            }
        """)
        print(f"草稿数量: {len(drafts)}")
        print(json.dumps(drafts, ensure_ascii=False, indent=2))

        await page.screenshot(path="/Users/echo/project/wechat-skills/check_draftbox.png")
        print("\n截图已保存")

        await page.wait_for_timeout(10000)
        await context.close()

asyncio.run(main())
