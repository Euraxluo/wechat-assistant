import asyncio, json, os
from playwright.async_api import async_playwright

DRAFT_URL_FILE = "/Users/echo/project/wechat-skills/draft_url.json"
SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"
USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"

def load_draft_url():
    if os.path.exists(DRAFT_URL_FILE):
        with open(DRAFT_URL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

async def main():
    draft = load_draft_url()
    if not draft or not draft.get("url"):
        print("❌ 没有找到草稿 URL")
        return

    print(f"继续发布草稿: {draft.get('appmsg_id')}")
    print("⚠️ 请准备好微信，二维码出现后请立即扫码！")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(draft["url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        print(f"  已打开编辑器: {page.url}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "republish_editor_open.png"))

        # 恢复封面（防止丢失）
        cover_restored = await page.evaluate("""
            () => {
                const preview = document.querySelector('.js_cover_preview_new');
                const item = document.querySelector('#appmsgItem');
                if (item) item.setAttribute('data-fileid', '100002622');
                if (preview) {
                    preview.style.backgroundImage = 'url(https://mmbiz.qpic.cn/mmbiz_png/XJTRLj5GGcBO1eVVpQam88PkLC10C8cz90Ric1KoKIrW5tNicbP9P37H4ayP89iaXJTLZia2E1OD5A5l6F5gSNf5Rw/0)';
                    preview.style.display = 'block';
                }
                return !!(preview && item);
            }
        """)
        print(f"  封面恢复: {cover_restored}")
        await page.wait_for_timeout(1000)

        # 点击 mass_send
        print("  点击 mass_send...")
        await page.evaluate("""
            () => {
                const btn = document.getElementById('mass_send') || document.querySelector('#js_submit a[onclick*="mass_send"], a[id*="mass_send"]');
                if (btn) { btn.click(); return true; }
                const links = document.querySelectorAll('a');
                for (const l of links) { if ((l.getAttribute('onclick') || '').includes('mass_send')) { l.click(); return true; } }
                return false;
            }
        """)
        await page.wait_for_timeout(2000)

        # 循环处理弹窗
        for i in range(20):
            await page.wait_for_timeout(1500)
            dialog_info = await page.evaluate("""
                () => {
                    const d = document.querySelector('.weui-desktop-dialog__wrp, .dialog_wrp');
                    if (!d || d.offsetHeight === 0) return { text: '', buttons: [] };
                    const text = (d.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 200);
                    const buttons = Array.from(d.querySelectorAll('button, a[btn]')).map(b => (b.innerText || '').trim()).filter(t => t);
                    return { text, buttons };
                }
            """)
            print(f"    第{i+1}轮: {dialog_info}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"republish_dialog{i+1}.png"))

            dialog_text = dialog_info.get("text", "")
            buttons = dialog_info.get("buttons", [])

            if not buttons:
                continue

            target = None
            if 'AI' in dialog_text or '声明' in dialog_text:
                for b in buttons:
                    if '无需声明并发表' in b or '无需声明' in b:
                        target = b
                        break
            elif '群发通知' in dialog_text or '定时发表' in dialog_text:
                for b in buttons:
                    if b == '发表':
                        target = b
                        break
            elif '未开启群发通知' in dialog_text or '继续发表' in dialog_text:
                for b in buttons:
                    if '继续发表' in b:
                        target = b
                        break
            elif '微信验证' in dialog_text or '扫码' in dialog_text:
                print("    ⚠️ 请立即用微信扫码验证！")
                # 继续等待
                continue

            if target:
                clicked = await page.evaluate("""
                    (targetText) => {
                        const d = document.querySelector('.weui-desktop-dialog__wrp, .dialog_wrp');
                        if (!d) return false;
                        const btns = d.querySelectorAll('button, a[btn]');
                        for (const b of btns) {
                            if ((b.innerText || '').trim() === targetText) { b.click(); return true; }
                        }
                        return false;
                    }
                """, target)
                print(f"    点击: {target} => {clicked}")

        # 最终验证
        await page.wait_for_timeout(5000)
        final_title = await page.evaluate("""
            () => {
                const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
                for (const pm of pms) {
                    if ((pm.getAttribute('data-placeholder') || '').includes('标题')) {
                        return (pm.innerText || '').trim().slice(0, 60);
                    }
                }
                return '';
            }
        """)
        print(f"  最终标题: {final_title}")

        # 检查发表记录
        await page.goto('https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=0&count=10', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "republish_final_record.png"))
        body_text = await page.inner_text('body')
        has_title = '全球半导体板块剧烈调整' in body_text
        print(f"  发表记录中是否包含文章: {has_title}")

        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
