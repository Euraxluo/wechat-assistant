#!/usr/bin/env python3
"""
尝试多种方式上传封面到 CDN：
1. filetransfer API (带 f=json)
2. filetransfer upload_material API
3. 使用 Playwright expect_file_chooser
"""
import asyncio, os, base64, json, re
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"
SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"
MP_URL = "https://mp.weixin.qq.com/"
COVER_IMAGE_PATH = "/Users/echo/project/wechat-skills/A_modern_minimalist_cover_imag_2026-07-07T09-17-27.png"

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
                const l = document.querySelector('a[href*="token="]');
                if (!l) return '';
                const m = l.href.match(/token=(\\d+)/);
                return m ? m[1] : '';
            }
        """)
        print(f"Token: {token}")
        await page.goto(f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        with open(COVER_IMAGE_PATH, 'rb') as f:
            file_base64 = base64.b64encode(f.read()).decode()

        # 滚动到封面区
        await page.evaluate("() => document.getElementById('js_cover_area')?.scrollIntoView({block:'center'})")
        await page.wait_for_timeout(1000)

        # ===== 尝试1: filetransfer API 带 f=json =====
        print("=== 尝试1: filetransfer?action=upload&type=image&f=json ===")
        result1 = await page.evaluate("""
            async (params) => {
                try {
                    const resp = await fetch('data:image/png;base64,' + params.base64);
                    const blob = await resp.blob();
                    const file = new File([blob], 'cover.png', { type: 'image/png' });

                    const formData = new FormData();
                    formData.append('file', file);

                    const url = '/cgi-bin/filetransfer?action=upload&type=image&f=json&token=' + params.token + '&lang=zh_CN';
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const text = await response.text();
                    return { status: response.status, text: text };
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64, "token": token})
        print(f"  结果: {result1}")

        # ===== 尝试2: upload_material API =====
        print("\n=== 尝试2: filetransfer?action=upload_material&f=json ===")
        result2 = await page.evaluate("""
            async (params) => {
                try {
                    const resp = await fetch('data:image/png;base64,' + params.base64);
                    const blob = await resp.blob();
                    const file = new File([blob], 'cover.png', { type: 'image/png' });

                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('scene', '1');

                    const url = '/cgi-bin/filetransfer?action=upload_material&f=json&token=' + params.token + '&lang=zh_CN';
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const text = await response.text();
                    return { status: response.status, text: text };
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64, "token": token})
        print(f"  结果: {result2}")

        # ===== 尝试3: 用 Upload.uploadCdnFileWithCheck 配置对象 =====
        print("\n=== 尝试3: Upload.uploadCdnFileWithCheck ===")
        result3 = await page.evaluate("""
            async (params) => {
                try {
                    const resp = await fetch('data:image/png;base64,' + params.base64);
                    const blob = await resp.blob();
                    const file = new File([blob], 'cover.png', { type: 'image/png' });

                    // 尝试用 uploadCdnFileWithCheck
                    // 它需要配置对象，包含 file, container, success 回调等
                    const result = await new Promise((resolve, reject) => {
                        const config = {
                            file: file,
                            container: '#js_cover_area',
                            success: function(data) { resolve({ success: true, data: data }); },
                            error: function(err) { resolve({ success: false, error: 'callback_error' }); },
                        };
                        try {
                            const ret = Upload.uploadCdnFileWithCheck(config);
                            // 如果返回 Promise
                            if (ret && ret.then) {
                                ret.then(data => resolve({ success: true, data: data }))
                                   .catch(err => resolve({ success: false, error: err.message }));
                            }
                            // 5秒超时
                            setTimeout(() => resolve({ success: false, error: 'timeout' }), 5000);
                        } catch(e) { resolve({ success: false, error: e.message }); }
                    });
                    return result;
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64})
        print(f"  结果: {json.dumps(result3, ensure_ascii=False)[:300]}")

        # ===== 尝试4: expect_file_chooser 点击封面按钮 =====
        print("\n=== 尝试4: expect_file_chooser ===")
        try:
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                # 点击封面按钮
                await page.locator("#js_cover_area .select-cover__btn").first.click()
                # 也尝试点击 "拖拽或选择封面" 文字
                await page.wait_for_timeout(1000)
                # 如果没有 file chooser，尝试点击选项中的某个按钮
                try:
                    # 尝试点击 js_chooseCover 按钮如果存在
                    await page.evaluate("() => document.querySelector('.js_chooseCover')?.click()")
                except: pass

            file_chooser = await fc_info.value
            await file_chooser.set_files(COVER_IMAGE_PATH)
            print("  ✅ file chooser 触发并设置文件！")
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"  ❌ file chooser 未触发: {e}")

        # ===== 尝试5: 拦截网络请求看上传URL =====
        print("\n=== 尝试5: 监听网络请求 ===")
        # 先设置请求监听
        upload_requests = []
        def on_request(request):
            if 'filetransfer' in request.url or 'upload' in request.url.lower():
                upload_requests.append({
                    url: request.url,
                    method: request.method,
                    content_type: request.headers.get('content-type', ''),
                })
        page.on("request", on_request)

        # 尝试点击封面区域的不同按钮
        await page.evaluate("() => document.getElementById('js_cover_area')?.scrollIntoView({block:'center'})")
        await page.wait_for_timeout(500)

        # 重新点击封面按钮
        await page.locator("#js_cover_area .select-cover__btn").first.click()
        await page.wait_for_timeout(2000)

        # 尝试点击每个选项
        for btn_class in ['.js_selectCoverFromContent', '.js_imagedialog', '.js_imageScan', '.js_aiImage']:
            try:
                clicked = await page.evaluate(f"""
                    () => {{
                        const btn = document.querySelector('{btn_class}');
                        if (btn && btn.offsetHeight > 0) {{ btn.click(); return true; }}
                        return false;
                    }}
                """)
                if clicked:
                    print(f"  点击了 {btn_class}")
                    await page.wait_for_timeout(2000)
                    # 检查是否有 file input 出现
                    file_inputs = await page.query_selector_all("input[type='file']")
                    new_inputs = [fi for fi in file_inputs if await fi.evaluate("el => !el.closest('#edui1') && el.offsetHeight >= 0")]
                    print(f"    file inputs: {len(file_inputs)} (非编辑器: {len(new_inputs)})")
                    # 关闭可能打开的对话框
                    await page.evaluate("() => { const close = document.querySelector('.weui-desktop-dialog__close-btn'); if (close) close.click(); }")
                    await page.wait_for_timeout(1000)
            except: pass

        page.remove_listener("request", on_request)
        print(f"  拦截到 {len(upload_requests)} 个上传请求")
        for req in upload_requests:
            print(f"    {req}")

        # ===== 尝试6: 直接设置封面的 hidden inputs =====
        print("\n=== 尝试6: 从已上传的草稿中获取 file_id ===")
        # 之前已经上传了很多次到图片库，图片应该已经存在
        # 尝试从图片库获取已有的图片 file_id
        # 或者直接用一个已知的 file_id
        # 先检查 cgiData 中有没有有用的信息
        cgi_info = await page.evaluate("""
            () => {
                const data = window.wx?.cgiData || {};
                return {
                    app_id: data.app_id,
                    bizmediaid: data.bizmediaid,
                    multi_appmsg_data: data.multi_appmsg_data ? 'exists' : 'none',
                    appmsg_data: data.appmsg_data ? JSON.stringify(data.appmsg_data).slice(0, 200) : 'none',
                };
            }
        """)
        print(f"  cgiData: {cgi_info}")

        # 最终检查
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_api_final.png"))
        cover = await page.evaluate("""
            () => {
                const p = document.querySelector('.js_cover_preview_new');
                return p ? { bg: p.style.backgroundImage, display: p.style.display } : null;
            }
        """)
        print(f"\n最终封面: {cover}")

        print("\n保持30秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
