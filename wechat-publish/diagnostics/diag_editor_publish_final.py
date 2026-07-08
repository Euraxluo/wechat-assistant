#!/usr/bin/env python3
"""
测试从编辑器页面直接点击 mass_send 按钮，完成整个发表流程。
"""
import asyncio, os, json
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"
SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"
MP_URL = "https://mp.weixin.qq.com/"
TARGET_TITLE = "同事用AI 2小时干完你1天的工作"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR, headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))

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

        draft_url_file = "/Users/echo/project/wechat-skills/draft_url.json"
        if os.path.exists(draft_url_file):
            with open(draft_url_file, "r", encoding="utf-8") as f:
                draft_info = json.load(f)
            appmsg_id = draft_info.get('appmsg_id')
        else:
            appmsg_id = "100002578"
        print(f"草稿 appMsgId: {appmsg_id}")

        edit_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&appmsgid={appmsg_id}&token={token}&lang=zh_CN"
        await page.goto(edit_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        # 检查当前状态
        status = await page.evaluate("""
            () => {
                const allPm = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
                let contentLen = 0;
                for (const pm of allPm) {
                    if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                        contentLen = (pm.innerText || '').length;
                    }
                }
                const item = document.querySelector('#appmsgItem');
                const massBtn = document.querySelector('button.mass_send');
                return {
                    contentLen,
                    fileId: item?.getAttribute('data-fileid'),
                    massBtnText: massBtn?.innerText?.trim(),
                    massBtnDisabled: massBtn?.disabled,
                    massBtnClass: massBtn?.className?.slice(0, 100),
                };
            }
        """)
        print(f"编辑器状态: {json.dumps(status, ensure_ascii=False)}")

        # 点击 mass_send
        print("\n===== 点击 mass_send =====")
        try:
            await page.locator('button.mass_send').first.click(timeout=5000)
            print("已点击 mass_send")
        except Exception as e:
            print(f"点击失败: {e}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_final_error.png"))
            await context.close()
            return

        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_final_dialog1.png"))

        # 处理弹窗循环
        for round_idx in range(8):
            await page.wait_for_timeout(2000)
            dialog_info = await page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('.weui-desktop-dialog, .weui-desktop-overlay, [class*="dialog"]:not([style*="display:none"])');
                    for (const d of dialogs) {
                        if (d.offsetHeight === 0) continue;
                        const text = (d.innerText || '').trim();
                        if (text.length > 0) {
                            const btns = d.querySelectorAll('button, a, [role="button"], .weui-desktop-btn');
                            return {
                                found: true,
                                text: text.substring(0, 300),
                                buttons: Array.from(btns).map(b => ({
                                    text: (b.innerText || '').trim(),
                                    className: b.className?.slice(0, 100) || '',
                                    disabled: b.disabled,
                                })).filter(x => x.text.length > 0 && x.text.length < 30),
                            };
                        }
                    }
                    return { found: false };
                }
            """)

            print(f"\n第{round_idx+1}轮")
            print(f"URL: {page.url}")

            if not dialog_info.get('found'):
                print("无弹窗")
                if "appmsgpublish" in page.url:
                    print("已跳转到发表记录页")
                    break
                continue

            print(f"弹窗文本: {dialog_info['text'][:100]}")
            print(f"按钮: {json.dumps(dialog_info['buttons'], ensure_ascii=False)}")

            # 决定点击哪个按钮
            dialog_text = dialog_info['text']
            buttons = dialog_info['buttons']

            # 优先级：
            # 1. AI声明："无需声明并发表"
            # 2. 群发确认："确认群发"
            # 3. 发表对话框："发表" (绿色按钮)
            # 4. 我知道了
            target = None
            if 'AI' in dialog_text or '声明' in dialog_text:
                for b in buttons:
                    if '无需声明并发表' in b['text'] or '无需声明' in b['text']:
                        target = b['text']
                        break
            elif '群发' in dialog_text or '确认' in dialog_text:
                for b in buttons:
                    if '确认群发' in b['text'] or '确定' in b['text']:
                        target = b['text']
                        break
            else:
                # 发表对话框，找"发表"按钮
                for b in buttons:
                    if b['text'] == '发表':
                        target = '发表'
                        break
                # 如果没有精确匹配，找"我知道了"
                if not target:
                    for b in buttons:
                        if '我知道了' in b['text']:
                            target = b['text']
                            break

            if target:
                print(f"将点击: {target}")
                clicked = await page.evaluate("""
                    (targetText) => {
                        const dialogs = document.querySelectorAll('.weui-desktop-dialog, .weui-desktop-overlay, [class*="dialog"]');
                        for (const d of dialogs) {
                            if (d.offsetHeight === 0) continue;
                            const btns = d.querySelectorAll('button, a, [role="button"], .weui-desktop-btn');
                            for (const b of btns) {
                                if ((b.innerText || '').trim() === targetText) {
                                    b.click();
                                    return true;
                                }
                            }
                        }
                        // 全局搜索
                        const allBtns = document.querySelectorAll('button, a, [role="button"]');
                        for (const b of allBtns) {
                            if ((b.innerText || '').trim() === targetText && b.offsetHeight > 0) {
                                b.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """, target)
                print(f"点击结果: {clicked}")
            else:
                print("未找到目标按钮")
                await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"diag_final_round_{round_idx}_no_target.png"))

            await page.wait_for_timeout(2000)
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"diag_final_round_{round_idx}.png"))

        # 最终验证
        print("\n===== 最终验证 =====")
        await page.wait_for_timeout(5000)
        final_url = page.url
        print(f"最终 URL: {final_url}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_final_result.png"), full_page=True)

        try:
            body_text = await page.inner_text("body")
            if TARGET_TITLE in body_text:
                print("✅ 页面中找到文章标题")
            if any(kw in body_text for kw in ["群发成功", "发布成功", "已群发", "已发布", "发表成功"]):
                print("✅ 检测到成功关键词")
            if any(kw in body_text for kw in ["群发失败", "发布失败", "操作失败"]):
                print("❌ 检测到失败关键词")
        except Exception as e:
            print(f"读取页面文本失败: {e}")

        print("\n保持30秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
