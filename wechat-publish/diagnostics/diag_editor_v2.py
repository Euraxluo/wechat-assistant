#!/usr/bin/env python3
"""
诊断编辑器页面结构：检查 iframe、contenteditable 元素、封面上传区域
"""
import asyncio
import os
import re
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"
SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"
MP_URL = "https://mp.weixin.qq.com/"
COVER_IMAGE_PATH = "/Users/echo/project/wechat-skills/A_modern_minimalist_cover_imag_2026-07-07T09-17-27.png"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # 打开公众号后台
        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)

        # 提取 token
        token = None
        m = re.search(r'token=(\d+)', page.url)
        if m:
            token = m.group(1)
        else:
            token = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a[href*="token="]');
                    for (const link of links) {
                        const m = link.href.match(/token=(\\d+)/);
                        if (m) return m[1];
                    }
                    return '';
                }
            """)
        print(f"Token: {token}")

        # 直接用 URL 新建文章
        new_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN"
        await page.goto(new_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_new_article.png"))

        # 检查 iframe
        frames = page.frames
        print(f"\n=== 页面有 {len(frames)} 个 frame ===")
        for i, frame in enumerate(frames):
            print(f"  Frame {i}: url={frame.url}, name={frame.name}")

        # 检查 contenteditable 元素
        editables = await page.evaluate("""
            () => {
                const results = [];
                const elements = document.querySelectorAll('[contenteditable="true"], [contenteditable=""]'  );
                for (const el of elements) {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className?.toString()?.slice(0, 100),
                        contentEditable: el.contentEditable,
                        x: Math.round(rect.x), y: Math.round(rect.y),
                        w: Math.round(rect.width), h: Math.round(rect.height),
                        textLength: (el.innerText || '').length,
                        html: el.outerHTML.slice(0, 200),
                    });
                }
                return results;
            }
        """)
        print(f"\n=== Contenteditable 元素 ({len(editables)} 个) ===")
        for e in editables:
            print(f"  <{e['tag']}> id={e['id']} class={e['className']} ce={e['contentEditable']} pos=({e['x']},{e['y']}) size={e['w']}x{e['h']} textLen={e['textLength']}")
            print(f"    html: {e['html']}")

        # 检查编辑器容器（UEditor 等）
        editor_containers = await page.evaluate("""
            () => {
                const selectors = ['.edui-body-container', '#ueditor_0', '#ueditor', '.edui', 
                                  '[class*="rich-text"]', '[class*="editor"]', 'iframe'];
                const results = [];
                for (const sel of selectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 || rect.height > 0) {
                            results.push({
                                selector: sel,
                                tag: el.tagName,
                                id: el.id,
                                className: el.className?.toString()?.slice(0, 100),
                                x: Math.round(rect.x), y: Math.round(rect.y),
                                w: Math.round(rect.width), h: Math.round(rect.height),
                                textLength: (el.innerText || '').length,
                                src: el.src || '',
                            });
                        }
                    }
                }
                return results;
            }
        """)
        print(f"\n=== 编辑器容器 ({len(editor_containers)} 个) ===")
        for e in editor_containers:
            print(f"  {e['selector']}: <{e['tag']}> id={e['id']} class={e['className']} pos=({e['x']},{e['y']}) size={e['w']}x{e['h']} textLen={e['textLength']} src={e['src'][:80]}")

        # 检查封面区域
        cover_info = await page.evaluate("""
            () => {
                const coverArea = document.getElementById('js_cover_area');
                const coverBtn = document.querySelector('.js_cover_btn_area');
                const coverPreview = document.querySelector('.js_cover_preview_new, .select-cover__preview');
                const appmsgItem = document.querySelector('#appmsgItem');
                return {
                    coverAreaExists: !!coverArea,
                    coverAreaHTML: coverArea ? coverArea.outerHTML.slice(0, 500) : '',
                    coverBtnExists: !!coverBtn,
                    coverPreviewExists: !!coverPreview,
                    coverPreviewBg: coverPreview ? (coverPreview.style.backgroundImage || window.getComputedStyle(coverPreview).backgroundImage) : '',
                    appmsgItemExists: !!appmsgItem,
                    appmsgItemFileId: appmsgItem ? appmsgItem.getAttribute('data-fileid') : '',
                };
            }
        """)
        print(f"\n=== 封面区域 ===")
        print(f"  coverArea exists: {cover_info['coverAreaExists']}")
        print(f"  coverBtn exists: {cover_info['coverBtnExists']}")
        print(f"  coverPreview exists: {cover_info['coverPreviewExists']}")
        print(f"  coverPreview bg: {cover_info['coverPreviewBg']}")
        print(f"  appmsgItem exists: {cover_info['appmsgItemExists']}")
        print(f"  appmsgItem fileId: {cover_info['appmsgItemFileId']}")
        print(f"  coverArea HTML: {cover_info['coverAreaHTML'][:300]}")

        # 检查标题和作者
        title_info = await page.evaluate("""
            () => {
                const pm = document.querySelector('.title-editor-overlay .ProseMirror, .title-editor__input .ProseMirror');
                const hiddenTitle = document.getElementById('title');
                const authorInput = document.querySelector('[placeholder*="作者"], input[name="author"]');
                return {
                    pmExists: !!pm,
                    pmText: pm ? pm.innerText : '',
                    hiddenTitleExists: !!hiddenTitle,
                    hiddenTitleVal: hiddenTitle ? hiddenTitle.value : '',
                    authorExists: !!authorInput,
                    authorVal: authorInput ? authorInput.value : '',
                };
            }
        """)
        print(f"\n=== 标题和作者 ===")
        print(f"  ProseMirror: exists={title_info['pmExists']}, text='{title_info['pmText']}'")
        print(f"  Hidden title: exists={title_info['hiddenTitleExists']}, val='{title_info['hiddenTitleVal']}'")
        print(f"  Author: exists={title_info['authorExists']}, val='{title_info['authorVal']}'")

        # 检查摘要
        digest_info = await page.evaluate("""
            () => {
                const digest = document.querySelector('textarea[name="digest"], [placeholder*="摘要"], [class*="digest"] textarea, [class*="digest"] input');
                return {
                    exists: !!digest,
                    tag: digest ? digest.tagName : '',
                    val: digest ? digest.value : '',
                    placeholder: digest ? digest.placeholder : '',
                };
            }
        """)
        print(f"\n=== 摘要 ===")
        print(f"  exists={digest_info['exists']}, tag={digest_info['tag']}, val='{digest_info['val']}', placeholder='{digest_info['placeholder']}'")

        # 检查保存按钮
        save_btn_info = await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button, a, [role="button"]');
                const results = [];
                for (const btn of btns) {
                    const text = (btn.innerText || '').trim();
                    if (text.includes('保存') || text.includes('草稿')) {
                        const rect = btn.getBoundingClientRect();
                        results.push({
                            text: text,
                            tag: btn.tagName,
                            className: btn.className.slice(0, 80),
                            x: Math.round(rect.x), y: Math.round(rect.y),
                            w: Math.round(rect.width), h: Math.round(rect.height),
                        });
                    }
                }
                return results;
            }
        """)
        print(f"\n=== 保存按钮 ===")
        for b in save_btn_info:
            print(f"  <{b['tag']}> text='{b['text']}' class='{b['className']}' pos=({b['x']},{b['y']}) size={b['w']}x{b['h']}")

        print("\n诊断完成，浏览器保持打开 30 秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
