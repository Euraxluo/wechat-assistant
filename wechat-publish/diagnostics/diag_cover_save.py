#!/usr/bin/env python3
"""
聚焦：手动设置封面 + 保存 + 重新加载验证
1. 上传图片到 CDN (API)
2. 获取 CDN URL (Upload.mediaFileUrl)
3. 手动创建 hidden inputs + 设置预览 + 设置 data-fileid
4. 保存草稿
5. 重新加载验证封面是否持久化
6. 检查草稿箱发表按钮状态
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
                const m = window.location.href.match(/token=(\\d+)/);
                if (m) return m[1];
                const l = document.querySelector('a[href*="token="]');
                if (l) { const m2 = l.href.match(/token=(\\d+)/); return m2 ? m2[1] : ''; }
                return '';
            }
        """)
        print(f"Token: {token}")

        new_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN"
        await page.goto(new_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)

        # 滚动到封面区
        await page.evaluate("() => document.getElementById('js_cover_area')?.scrollIntoView({block:'center'})")
        await page.wait_for_timeout(1000)

        # ===== 1. 上传图片到 CDN =====
        print("===== 1. 上传图片到 CDN =====")
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
                    const json = await response.json();
                    return json;
                } catch(e) { return { error: e.message }; }
            }
        """, {"base64": file_base64, "token": token})
        print(f"  上传结果: {json.dumps(upload_result, ensure_ascii=False)[:200]}")

        file_id = upload_result.get('content', '')
        if not file_id:
            print("  ❌ 上传失败")
            await page.wait_for_timeout(10000)
            await context.close()
            return
        print(f"  ✅ file_id: {file_id}")

        # ===== 2. 获取 CDN URL =====
        print("\n===== 2. 获取 CDN URL =====")
        cdn_url = await page.evaluate("""
            (fileId) => {
                try { return Upload.mediaFileUrl(fileId); } catch(e) { return 'err:' + e.message; }
            }
        """, file_id)
        print(f"  CDN URL: {cdn_url[:100]}")

        # ===== 3. 设置封面 =====
        print("\n===== 3. 手动设置封面 =====")
        set_result = await page.evaluate("""
            (params) => {
                const preview = document.querySelector('.js_cover_preview_new');
                const item = document.querySelector('#appmsgItem');
                const results = [];

                // 设置 data-fileid
                if (item) {
                    item.setAttribute('data-fileid', params.fileId);
                    results.push('set data-fileid on #appmsgItem');
                }

                // 设置预览
                if (preview) {
                    preview.style.backgroundImage = `url("${params.cdnUrl}")`;
                    preview.style.display = 'block';
                    results.push('set preview bg + display');

                    // 创建 hidden inputs（如果不存在）
                    const inputs = [
                        { cls: 'js_file_id', name: 'file_id', value: params.fileId },
                        { cls: 'js_cdn_url', name: 'cdn_url', value: params.cdnUrl },
                        { cls: 'js_cdn_url_back', name: 'cdn_url_back', value: params.cdnUrl },
                        { cls: 'js_show_cover_pic', name: 'show_cover_pic', value: '0' },
                    ];
                    for (const inp of inputs) {
                        let el = preview.querySelector(`.${inp.cls}`) || document.querySelector(`input[name="${inp.name}"]`);
                        if (!el) {
                            el = document.createElement('input');
                            el.type = 'hidden';
                            el.className = 'js_field ' + inp.cls;
                            el.name = inp.name;
                            preview.appendChild(el);
                            results.push('created input.' + inp.cls);
                        }
                        el.value = inp.value;
                        el.setAttribute('value', inp.value);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }

                    // 添加修改/删除按钮区域（如果不存在）
                    if (!preview.querySelector('.js_cover_btn_area')) {
                        const modifyDiv = document.createElement('div');
                        modifyDiv.className = 'select-cover__icon__modify js_cover_btn_area';
                        modifyDiv.innerHTML = '<a href="javascript:;" class="icon18_common del_gray js_modifyCover" onclick="return false;">修改</a>';
                        preview.appendChild(modifyDiv);
                    }
                }

                return results;
            }
        """, {"fileId": file_id, "cdnUrl": cdn_url})
        print(f"  设置结果: {set_result}")

        await page.wait_for_timeout(2000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_manual_set.png"))

        # 验证
        verify = await page.evaluate("""
            () => {
                const preview = document.querySelector('.js_cover_preview_new');
                const bg = preview ? preview.style.backgroundImage : '';
                const fileIdInput = document.querySelector('.js_file_id, input[name="file_id"]');
                const cdnUrlInput = document.querySelector('.js_cdn_url, input[name="cdn_url"]');
                const item = document.querySelector('#appmsgItem');
                return {
                    bg: bg.slice(0, 80),
                    display: preview?.style.display,
                    fileId: item?.getAttribute('data-fileid'),
                    fileIdInput: fileIdInput?.value,
                    cdnUrlInput: cdnUrlInput?.value?.slice(0, 60),
                };
            }
        """)
        print(f"  验证: {json.dumps(verify, ensure_ascii=False)}")

        # ===== 4. 保存草稿 =====
        print("\n===== 4. 保存草稿 =====")
        # 填写标题（保存需要标题）
        await page.evaluate("""
            (text) => {
                const titlePm = document.querySelector('.ProseMirror[data-placeholder="请在这里输入标题"]');
                if (titlePm) {
                    titlePm.innerHTML = '<p>' + text + '</p>';
                    const overlay = document.querySelector('.title-editor-overlay');
                    if (overlay) overlay.classList.remove('is-empty');
                    titlePm.dispatchEvent(new InputEvent('input', { bubbles: true, data: text, inputType: 'insertText' }));
                    const hidden = document.getElementById('title');
                    if (hidden) { hidden.value = text; hidden.setAttribute('value', text); hidden.dispatchEvent(new Event('input', {bubbles:true})); hidden.dispatchEvent(new Event('change', {bubbles:true})); }
                }
            }
        """, "测试封面_自动删除")

        # 等待一下
        await page.wait_for_timeout(1000)

        # 点击保存
        await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.innerText.includes('保存为草稿') || b.innerText.includes('保存')) {
                        b.scrollIntoView({ block: 'center' });
                        b.click();
                        return;
                    }
                }
            }
        """)
        print("  点击保存...")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_after_save.png"))

        # 获取 appmsgid
        current_url = page.url
        m = re.search(r'appMsgId=(\d+)|appmsgid=(\d+)', current_url)
        appmsg_id = m.group(1) or m.group(2) if m else None
        print(f"  保存后 URL: {current_url}")
        print(f"  appMsgId: {appmsg_id}")

        # ===== 5. 重新加载页面验证封面是否持久化 =====
        print("\n===== 5. 重新加载验证 =====")
        if appmsg_id:
            edit_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&appmsgid={appmsg_id}&token={token}&lang=zh_CN"
            await page.goto(edit_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(5000)

            reload_cover = await page.evaluate("""
                () => {
                    const preview = document.querySelector('.js_cover_preview_new');
                    const bg = preview ? (preview.style.backgroundImage || window.getComputedStyle(preview).backgroundImage) : '';
                    const display = preview ? preview.style.display : '';
                    const item = document.querySelector('#appmsgItem');
                    const fileId = item?.getAttribute('data-fileid');
                    const fileIdInput = document.querySelector('.js_file_id, input[name="file_id"]');
                    return {
                        bg: bg.slice(0, 100),
                        display: display,
                        fileId: fileId,
                        hasFileIdInput: !!fileIdInput,
                        fileIdInputVal: fileIdInput?.value,
                    };
                }
            """)
            print(f"  重新加载后封面: {json.dumps(reload_cover, ensure_ascii=False)}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_reload_verify.png"))

            # ===== 6. 检查草稿箱发表按钮状态 =====
            print("\n===== 6. 检查草稿箱发表按钮 =====")
            draft_box_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_manage&action=list&type=77&token={token}&lang=zh_CN"
            await page.goto(draft_box_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(5000)

            btn_status = await page.evaluate("""
                (appmsgId) => {
                    const cards = document.querySelectorAll('.weui-desktop-card[data-appid]');
                    for (const card of cards) {
                        const aid = card.getAttribute('data-appid');
                        const publishBtn = card.querySelector('.weui-desktop-link_send-multi');
                        if (publishBtn) {
                            const isDisabled = publishBtn.classList.contains('weui-desktop-link_disable');
                            // 检查封面缩略图
                            const thumb = card.querySelector('.appmsg_thumb, [class*="thumb"]');
                            const thumbBg = thumb ? (thumb.style.backgroundImage || window.getComputedStyle(thumb).backgroundImage) : '';
                            return {
                                appId: aid,
                                isDisabled: isDisabled,
                                text: publishBtn.innerText.trim(),
                                thumbBg: thumbBg.slice(0, 80),
                                thumbEmpty: thumbBg.includes('url("")') || thumbBg.includes("url('')") || !thumbBg.includes('url'),
                                isMyArticle: String(aid) === String(appmsgId),
                            };
                        }
                    }
                    return { found: false };
                }
            """, appmsg_id)
            print(f"  发表按钮状态: {json.dumps(btn_status, ensure_ascii=False)}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_cover_draftbox.png"))

            # ===== 7. 清理：删除测试草稿 =====
            print(f"\n===== 7. 清理测试草稿 (appMsgId={appmsg_id}) =====")
            # 尝试删除草稿
            deleted = await page.evaluate("""
                async (params) => {
                    try {
                        const url = '/cgi-bin/appmsg?t=media/appmsg_manage&action=delete&type=77&appmsgid=' + params.appmsgId + '&token=' + params.token + '&lang=zh_CN&f=json';
                        const response = await fetch(url, { method: 'GET' });
                        const text = await response.text();
                        return { status: response.status, text: text.slice(0, 200) };
                    } catch(e) { return { error: e.message }; }
                }
            """, {"appmsgId": appmsg_id, "token": token})
            print(f"  删除结果: {deleted}")

        print("\n保持30秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
