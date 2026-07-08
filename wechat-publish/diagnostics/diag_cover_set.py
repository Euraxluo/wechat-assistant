#!/usr/bin/env python3
"""
诊断封面设置机制：
1. 上传图片到 CDN (filetransfer API)
2. 检查封面区域所有 hidden inputs
3. 搜索页面 JS 中封面相关的函数/对象
4. 尝试调用内部函数设置封面
5. 检查 Vue/React 内部数据模型
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

        # 提取 token
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

        # 打开新文章编辑器
        new_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN"
        await page.goto(new_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        # 滚动到封面区
        await page.evaluate("() => document.getElementById('js_cover_area')?.scrollIntoView({block:'center'})")
        await page.wait_for_timeout(1000)

        # ===== 1. 检查封面区域完整 HTML 结构 =====
        print("\n===== 1. 封面区域 HTML 结构 =====")
        cover_html = await page.evaluate("""
            () => {
                const area = document.getElementById('js_cover_area');
                if (!area) return 'NOT FOUND';
                return area.outerHTML.slice(0, 3000);
            }
        """)
        print(cover_html[:2000])

        # ===== 2. 检查所有 hidden inputs =====
        print("\n===== 2. 所有 hidden inputs =====")
        hidden_inputs = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input[type="hidden"], input[name*="file"], input[name*="cover"], input[name*="thumb"], input.js_file_id');
                return Array.from(inputs).map(i => ({
                    id: i.id,
                    name: i.name,
                    className: i.className.slice(0, 60),
                    value: (i.value || '').slice(0, 50),
                    type: i.type,
                }));
            }
        """)
        for hi in hidden_inputs:
            print(f"  {hi}")

        # ===== 3. 检查 #appmsgItem 的 data 属性 =====
        print("\n===== 3. #appmsgItem data 属性 =====")
        appmsg_data = await page.evaluate("""
            () => {
                const item = document.querySelector('#appmsgItem, .appmsg_item, [data-fileid]');
                if (!item) return 'NOT FOUND';
                return {
                    id: item.id,
                    className: item.className,
                    dataAttrs: Array.from(item.attributes).filter(a => a.name.startsWith('data-')).map(a => a.name + '=' + a.value.slice(0, 50)),
                };
            }
        """)
        print(f"  {appmsg_data}")

        # ===== 4. 搜索 window 上封面相关对象/函数 =====
        print("\n===== 4. window 上的封面相关对象/函数 =====")
        cover_globals = await page.evaluate("""
            () => {
                const results = [];
                const keywords = ['cover', 'Cover', 'fileid', 'fileId', 'thumb', 'Thumb', 'media', 'Media'];
                for (const key of Object.keys(window)) {
                    if (keywords.some(kw => key.toLowerCase().includes(kw.toLowerCase()))) {
                        const val = window[key];
                        const type = typeof val;
                        let info = type;
                        if (type === 'object' && val) {
                            info += ' keys: ' + Object.keys(val).slice(0, 10).join(',');
                        } else if (type === 'function') {
                            info += ' ' + (val.toString().match(/function\\s*\\(([^)]*)\\)/) || ['',''])[1];
                        }
                        results.push(key + ' (' + info + ')');
                    }
                }
                return results;
            }
        """)
        for g in cover_globals:
            print(f"  {g}")

        # ===== 5. 检查 wx 对象 / pageData / cgiData =====
        print("\n===== 5. wx/cgiData/pageData =====")
        wx_data = await page.evaluate("""
            () => {
                const result = {};
                if (window.wx) {
                    result.wx_keys = Object.keys(window.wx).slice(0, 20);
                    if (window.wx.cgiData) {
                        result.cgiData_keys = Object.keys(window.wx.cgiData).slice(0, 30);
                        // 找封面相关的
                        for (const k of Object.keys(window.wx.cgiData)) {
                            const v = window.wx.cgiData[k];
                            if (typeof v === 'string' && (k.includes('file') || k.includes('cover') || k.includes('thumb') || k.includes('media'))) {
                                result['cgiData.' + k] = v.slice(0, 80);
                            }
                        }
                    }
                }
                // 也检查 pageData
                if (window.pageData) result.pageData_keys = Object.keys(window.pageData).slice(0, 20);
                // 检查 wx.data
                if (window.wx && window.wx.data) result.wx_data_keys = Object.keys(window.wx.data).slice(0, 20);
                return result;
            }
        """)
        print(f"  {json.dumps(wx_data, ensure_ascii=False, indent=2)}")

        # ===== 6. 上传图片到 CDN =====
        print("\n===== 6. 上传图片到 CDN =====")
        with open(COVER_IMAGE_PATH, 'rb') as f:
            file_base64 = base64.b64encode(f.read()).decode()

        upload_result = await page.evaluate("""
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
                    try {
                        const json = JSON.parse(text);
                        return { status: response.status, json: json };
                    } catch {
                        return { status: response.status, text: text.slice(0, 500) };
                    }
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64, "token": token})
        print(f"  上传结果: {json.dumps(upload_result, ensure_ascii=False)[:300]}")

        file_id = None
        if upload_result.get('json', {}).get('base_resp', {}).get('ret') == 0:
            file_id = upload_result['json'].get('content', '')
            print(f"  ✅ file_id: {file_id}")

        if not file_id:
            print("  ❌ 上传失败，退出")
            await page.wait_for_timeout(10000)
            await context.close()
            return

        # ===== 7. 尝试获取 CDN URL =====
        print("\n===== 7. 获取 CDN URL =====")
        cdn_url = await page.evaluate("""
            (fileId) => {
                // 尝试多种方式获取 CDN URL
                const results = {};

                // 方法1: Upload.mediaFileUrl
                if (window.Upload && typeof Upload.mediaFileUrl === 'function') {
                    try { results.mediaFileUrl = Upload.mediaFileUrl(fileId); } catch(e) { results.mediaFileUrl_err = e.message; }
                }

                // 方法2: 检查 wx.cgiData 中有没有 URL 构造方法
                if (window.wx && window.wx.cgiData) {
                    results.bizmediaid = window.wx.cgiData.bizmediaid;
                }

                // 方法3: 直接构造 URL (常见的微信 CDN URL 格式)
                // 通常需要从 upload 响应中获取，或者通过另一个 API

                // 方法4: 检查 Upload 对象的方法
                if (window.Upload) {
                    results.upload_methods = Object.keys(Upload).filter(k => typeof Upload[k] === 'function').join(', ');
                }

                return results;
            }
        """, file_id)
        print(f"  CDN URL 信息: {json.dumps(cdn_url, ensure_ascii=False, indent=2)}")

        # ===== 8. 尝试获取图片 URL via API =====
        print("\n===== 8. 获取图片 URL via getmaterial API =====")
        material_url = await page.evaluate("""
            async (params) => {
                try {
                    // 尝试获取素材信息
                    const url = '/cgi-bin/filetransfer?action=get_material_info&f=json&token=' + params.token + '&lang=zh_CN';
                    const formData = new FormData();
                    formData.append('file_id', params.fileId);
                    const response = await fetch(url, { method: 'POST', body: formData });
                    const text = await response.text();
                    return { status: response.status, text: text.slice(0, 500) };
                } catch(e) { return { error: e.message }; }
            }
        """, {"fileId": file_id, "token": token})
        print(f"  素材信息: {material_url}")

        # ===== 9. 尝试设置封面 — 方法1: 调用 page.data 的 set 方法 =====
        print("\n===== 9. 尝试设置封面 =====")

        # 方法1: 直接设置 DOM hidden inputs + trigger
        print("  方法1: 设置 hidden inputs...")
        set_result1 = await page.evaluate("""
            (fileId) => {
                const results = [];

                // 设置所有可能的 file_id 输入
                const selectors = [
                    '.js_file_id',
                    'input[name="file_id"]',
                    'input[name="fileid"]',
                    'input[name="thumb_file_id"]',
                    'input[name="thumb_media_id"]',
                    '#file_id',
                    '#thumb_file_id',
                ];

                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        el.value = fileId;
                        el.setAttribute('value', fileId);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        results.push('set ' + sel);
                    }
                }

                // 设置 #appmsgItem data-fileid
                const item = document.querySelector('#appmsgItem');
                if (item) {
                    item.setAttribute('data-fileid', fileId);
                    results.push('set data-fileid on #appmsgItem');
                }

                // 设置封面预览的 background-image
                // 先尝试从 Upload 获取 URL
                let coverUrl = '';
                if (window.Upload && typeof Upload.mediaFileUrl === 'function') {
                    try { coverUrl = Upload.mediaFileUrl(fileId); } catch {}
                }

                if (coverUrl) {
                    const preview = document.querySelector('.js_cover_preview_new, .select-cover__preview');
                    if (preview) {
                        preview.style.backgroundImage = `url("${coverUrl}")`;
                        preview.style.display = 'block';
                        results.push('set preview bg to ' + coverUrl.slice(0, 50));
                    }
                }

                return results;
            }
        """, file_id)
        print(f"  方法1结果: {set_result1}")

        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_set_method1.png"))

        # 检查封面状态
        cover_status1 = await page.evaluate("""
            () => {
                const p = document.querySelector('.js_cover_preview_new');
                const bg = p ? (p.style.backgroundImage || window.getComputedStyle(p).backgroundImage) : '';
                const item = document.querySelector('#appmsgItem');
                return {
                    bg: bg.slice(0, 100),
                    display: p ? p.style.display : 'none',
                    fileId: item?.getAttribute('data-fileid'),
                };
            }
        """)
        print(f"  封面状态: {cover_status1}")

        # 方法2: 模拟从图片库选择图片的完整流程
        print("\n  方法2: 模拟图片库选择流程...")
        # 点击封面区域
        await page.locator("#js_cover_area .select-cover__btn").first.click()
        await page.wait_for_timeout(2000)

        # 点击"从图片库选择"
        await page.evaluate("() => document.querySelector('.js_imagedialog')?.click()")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_set_method2_imglib.png"))

        # 检查图片库对话框中的内容
        imglib_info = await page.evaluate("""
            () => {
                const dialog = document.querySelector('.weui-desktop-dialog__bd, .img_picker_dialog, [class*="img-picker"]');
                if (!dialog) return { found: false };
                const text = (dialog.innerText || '').slice(0, 200);
                const imgs = dialog.querySelectorAll('img, [style*="background-image"]');
                const items = dialog.querySelectorAll('[data-id], [data-fileid], .img_item, [class*="img-item"]');
                return {
                    found: true,
                    text: text,
                    imgCount: imgs.length,
                    itemCount: items.length,
                    itemDetails: Array.from(items).slice(0, 5).map(i => ({
                        className: i.className.slice(0, 40),
                        dataId: i.getAttribute('data-id'),
                        dataFileId: i.getAttribute('data-fileid'),
                    })),
                };
            }
        """)
        print(f"  图片库: {json.dumps(imglib_info, ensure_ascii=False)[:400]}")

        # 关闭对话框
        await page.evaluate("() => { const btn = document.querySelector('.weui-desktop-dialog__close-btn, [class*=\"close\"]'); if (btn) btn.click(); }")
        await page.wait_for_timeout(2000)

        # 方法3: 使用 Upload.uploadCdnFile 回调方式
        print("\n  方法3: Upload.uploadCdnFile 回调方式...")
        set_result3 = await page.evaluate("""
            async (params) => {
                try {
                    // 重新上传，但这次通过 Upload 对象的上传方法
                    // 让 Upload 对象自己处理 file_id 设置
                    const resp = await fetch('data:image/png;base64,' + params.base64);
                    const blob = await resp.blob();
                    const file = new File([blob], 'cover.png', { type: 'image/png' });

                    // 检查 Upload 对象的方法签名
                    const methods = [];
                    for (const key of Object.keys(Upload)) {
                        if (typeof Upload[key] === 'function') {
                            const src = Upload[key].toString().slice(0, 200);
                            methods.push(key + ': ' + src);
                        }
                    }

                    return { methods: methods };
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64})
        print(f"  Upload 方法:")
        for m in set_result3.get('methods', []):
            print(f"    {m[:120]}")

        # 方法4: 检查 page 对象的内部数据结构
        print("\n  方法4: 检查内部数据结构...")
        internal_data = await page.evaluate("""
            () => {
                const results = {};

                // 检查是否有 Vue 实例
                const appmsgItem = document.querySelector('#appmsgItem');
                if (appmsgItem && appmsgItem.__vue__) {
                    results.vue_data = Object.keys(appmsgItem.__vue__.$data || {}).join(', ');
                }

                // 检查 wx_main / page_main 等
                for (const key of ['page_main', 'wx_main', 'main', 'appmsg', 'editor', 'Editor']) {
                    if (window[key]) {
                        results[key] = typeof window[key];
                        if (typeof window[key] === 'object') {
                            results[key + '_keys'] = Object.keys(window[key]).slice(0, 15).join(', ');
                        }
                    }
                }

                // 检查所有 script 标签中是否有 setCover / updateCover 函数
                const scripts = document.querySelectorAll('script');
                let coverFuncs = [];
                for (const s of scripts) {
                    const text = s.textContent || '';
                    if (text.includes('cover') || text.includes('fileid') || text.includes('thumb_file')) {
                        // 提取函数名
                        const matches = text.match(/function\s+(\w*[Cc]over\w*)|(\w*[Cc]over\w*)\s*[:=]\s*function/g);
                        if (matches) coverFuncs.push(...matches);
                    }
                }
                results.coverFunctions = coverFuncs.slice(0, 10);

                return results;
            }
        """)
        print(f"  内部数据: {json.dumps(internal_data, ensure_ascii=False, indent=2)}")

        # 方法5: 尝试通过 formData 方式提交保存，看保存时需要什么参数
        print("\n  方法5: 检查保存时的网络请求格式...")
        # 先点击保存按钮看请求
        save_request_data = await page.evaluate("""
            () => {
                // 检查页面上是否有 form 或保存函数
                const forms = document.querySelectorAll('form');
                const result = [];
                for (const f of forms) {
                    result.push({
                        id: f.id,
                        action: f.action,
                        inputs: Array.from(f.querySelectorAll('input, textarea, select')).map(i => ({
                            name: i.name,
                            type: i.type,
                            value: (i.value || '').slice(0, 30),
                        })).filter(i => i.name),
                    });
                }
                return result;
            }
        """)
        print(f"  表单: {json.dumps(save_request_data, ensure_ascii=False)[:500]}")

        # 最终截图
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_set_final.png"))
        print("\n保持30秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
