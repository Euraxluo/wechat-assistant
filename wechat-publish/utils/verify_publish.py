import asyncio, os, json
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='/Users/echo/project/wechat-skills/.browser_profile',
            headless=False,
            viewport={'width': 1280, 'height': 900},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 先访问首页获取token
        print("[1] 访问公众号主页...")
        await page.goto('https://mp.weixin.qq.com/', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "verify_home.png"))
        
        # 检查是否已登录
        body_text = await page.inner_text('body')
        is_login_page = ('扫码' in body_text and '公众号' in body_text) or '请重新登录' in body_text or '二维码' in body_text
        print(f"  是否登录页: {is_login_page}")
        
        if is_login_page:
            print("  ⚠️ 浏览器已退出登录，需要你重新扫码登录")
            print("  请查看浏览器窗口，用微信扫码登录")
            await page.wait_for_timeout(60000)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "verify_after_login.png"))
        
        # 提取token
        token = await page.evaluate("""
            () => {
                const m = window.location.href.match(/token=(\\d+)/);
                if (m) return m[1];
                const l = document.querySelector('a[href*=\"token=\"]');
                if (l) { const m2 = l.href.match(/token=(\\d+)/); return m2 ? m2[1] : ''; }
                return '';
            }
        """)
        print(f"  token: {token}")
        
        if token:
            # 检查发表记录
            print("[2] 检查发表记录...")
            pub_url = f'https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=10&token={token}&lang=zh_CN'
            await page.goto(pub_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "verify_publish_record.png"))
            
            body_text = await page.inner_text('body')
            has_title = '全球半导体板块剧烈调整' in body_text
            has_title2 = '全球半导体板块剧烈调整' in await page.content()
            print(f"  发表记录包含目标文章(inner_text): {has_title}")
            print(f"  发表记录包含目标文章(content): {has_title2}")
            
            # 提取文章列表
            articles = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('.publish_status');
                    const items = [];
                    rows.forEach(r => {
                        const card = r.closest('.weui-desktop-card');
                        const title = card ? (card.querySelector('.weui-desktop-card__title')?.innerText || '') : '';
                        const time = (card?.querySelector('.weui-desktop-card__time')?.innerText || '');
                        const status = (card?.querySelector('.publish_status')?.innerText || '');
                        if (title) items.push({title: title.slice(0, 80), time, status});
                    });
                    return items;
                }
            """)
            print(f"  找到 {len(articles)} 篇文章:")
            for a in articles[:5]:
                print(f"    - {a['title']} | {a['time']} | {a['status']}")
        
        await page.wait_for_timeout(3000)
        await context.close()

asyncio.run(main())
