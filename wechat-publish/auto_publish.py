#!/usr/bin/env python3
"""
微信公众号自动发布脚本 v9
核心修复（相比 v8）：
1. 封面上传改用编辑器工具栏图片上传，获取真实有效的 file_id 和 mmbiz CDN URL
   - 旧版 filetransfer API + Upload.mediaFileUrl() 返回的 URL 无法加载图片
   - 新版：通过工具栏 file input 上传 → 从 img[data-imgfileid] 取 file_id
2. 保存后封面预览 URL 会被微信重置为无效的 filetransfer URL，因此在保存后重新加载并恢复预览 URL
3. 发表改为从编辑器直接点击 mass_send，不再依赖草稿箱卡片点击
4. 处理发表弹窗：发表 → 继续发表 → 扫码验证/正在发表
"""
import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

# ========= 项目根目录 =========
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

ARTICLE_HTML_PATH = os.path.join(PROJECT_DIR, "articles", "article_ai_invest_v3.html")
TITLE = "全球半导体板块剧烈调整：产业周期与市场情绪的再定价"
AUTHOR = "AI提效实验室"
DIGEST = "【策略研究】SOX两日跌11%后二次探底，三星业绩暴增18倍股价反跌7%。资金面、技术面、产业面全维度分析。三条主线+杠铃策略，附7家机构最新观点。"
COVER_IMAGE_PATH = os.path.join(PROJECT_DIR, "covers", "latest_cover_v3.png")
MP_URL = "https://mp.weixin.qq.com/"
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots")
USER_DATA_DIR = os.path.join(PROJECT_DIR, ".browser_profile")
DRAFT_URL_FILE = os.path.join(PROJECT_DIR, "draft_url.json")
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def save_draft_url(url, appmsg_id=None, title=None):
    data = {"url": url, "appmsg_id": appmsg_id, "title": title or TITLE}
    with open(DRAFT_URL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  草稿 URL 已保存")


def load_draft_url():
    if os.path.exists(DRAFT_URL_FILE):
        with open(DRAFT_URL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def clear_draft_url():
    if os.path.exists(DRAFT_URL_FILE):
        os.remove(DRAFT_URL_FILE)
        print(f"  已清除草稿记录")


async def is_logged_in(page):
    try:
        if "/cgi-bin/" in page.url:
            return True
        body_text = await page.inner_text("body")
        if any(kw in body_text for kw in ["新的创作", "内容管理", "创作管理"]):
            return True
    except: pass
    return False


async def wait_for_login(page, max_seconds=300):
    for attempt in range(max_seconds):
        await page.wait_for_timeout(1000)
        if await is_logged_in(page):
            return True
        if attempt > 0 and attempt % 40 == 0:
            try:
                await page.reload(wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
            except: pass
    return False


async def extract_token(page):
    m = re.search(r'token=(\d+)', page.url)
    if m: return m.group(1)
    try:
        return await page.evaluate("""
            () => {
                const m = window.location.href.match(/token=(\\d+)/);
                if (m) return m[1];
                const l = document.querySelector('a[href*="token="]');
                if (l) { const m2 = l.href.match(/token=(\\d+)/); return m2 ? m2[1] : ''; }
                return '';
            }
        """)
    except: return ''


async def fill_title(page, title):
    print("  填写标题...")
    await page.evaluate("""
        (text) => {
            const pm = document.querySelector('.ProseMirror[data-placeholder*="标题"]');
            if (pm) {
                pm.innerHTML = '<p>' + text + '</p>';
                pm.dispatchEvent(new InputEvent('input', { bubbles: true, data: text, inputType: 'insertText' }));
                const hidden = document.getElementById('title');
                if (hidden) { hidden.value = text; hidden.setAttribute('value', text); hidden.dispatchEvent(new Event('input', {bubbles:true})); hidden.dispatchEvent(new Event('change', {bubbles:true})); }
            }
        }
    """, title)
    await page.wait_for_timeout(500)


async def fill_author(page, author):
    print("  填写作者...")
    try:
        loc = page.locator('input[name="author"], [placeholder*="作者"]').first
        if await loc.is_visible(timeout=3000):
            await loc.fill(author)
            await loc.press("Tab")
            return
    except: pass
    await page.evaluate("""
        (author) => {
            const input = document.querySelector('input[name="author"]');
            if (input) { input.value = author; input.dispatchEvent(new Event('input', {bubbles:true})); input.dispatchEvent(new Event('change', {bubbles:true})); }
        }
    """, author)
    await page.wait_for_timeout(500)


async def paste_content(page, html_content):
    print("  粘贴正文...")
    await page.evaluate("""
        (html) => {
            const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
            for (const pm of pms) {
                if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                    pm.focus();
                    pm.innerHTML = html;
                    pm.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertHTML' }));
                    return true;
                }
            }
            return false;
        }
    """, html_content)
    await page.wait_for_timeout(2000)


async def fill_digest(page, digest):
    print("  填写摘要...")
    try:
        loc = page.locator('textarea[name="digest"], [placeholder*="摘要"]').first
        if await loc.is_visible(timeout=3000):
            await loc.fill(digest)
            await loc.press("Tab")
            return
    except: pass
    await page.evaluate("""
        (digest) => {
            const ta = document.querySelector('textarea[name="digest"]');
            if (ta) { ta.value = digest; ta.dispatchEvent(new Event('input', {bubbles:true})); ta.dispatchEvent(new Event('change', {bubbles:true})); }
        }
    """, digest)
    await page.wait_for_timeout(500)


async def upload_cover_via_toolbar(page, cover_path):
    """通过编辑器工具栏上传封面图，返回 (cover_url, file_id)"""
    print("  通过工具栏上传封面...")
    await page.evaluate("""
        () => {
            const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
            for (const pm of pms) {
                if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                    pm.focus();
                    pm.innerHTML += '<p><br></p>';
                    return;
                }
            }
        }
    """)
    await page.wait_for_timeout(1000)

    file_inputs = await page.query_selector_all("input[type='file']")
    print(f"    file inputs: {len(file_inputs)}")

    if len(file_inputs) == 0:
        print("    尝试点击「图片」按钮触发 file input...")
        await page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if ((b.innerText || '').includes('图片')) { b.click(); return; }
                }
            }
        """)
        await page.wait_for_timeout(2000)
        file_inputs = await page.query_selector_all("input[type='file']")
        print(f"    再次 file inputs: {len(file_inputs)}")

    cover_url = None
    file_id = ''
    for fi in file_inputs:
        try:
            await fi.set_input_files(cover_path)
            print("    已上传文件")
            for _ in range(10):
                await page.wait_for_timeout(1000)
                imgs = await page.evaluate("""
                    () => {
                        const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
                        for (const pm of pms) {
                            if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                                return Array.from(pm.querySelectorAll('img')).map(img => ({
                                    src: img.src,
                                    fileId: img.getAttribute('data-imgfileid') || img.dataset.imgfileid,
                                }));
                            }
                        }
                        return [];
                    }
                """)
                valid = [img for img in imgs if img.get('src') and img['src'].startswith('http')]
                if valid:
                    cover_url = valid[-1]['src']
                    file_id = valid[-1].get('fileId') or ''
                    print(f"    URL: {cover_url[:60]}...")
                    print(f"    file_id: {file_id}")
                    break
            if cover_url:
                break
        except Exception as e:
            print(f"    上传失败: {e}")

    if not cover_url:
        return None, None

    # 删除正文中的临时图片
    await page.evaluate("""
        (url) => {
            const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
            for (const pm of pms) {
                if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                    const imgs = pm.querySelectorAll('img');
                    for (const img of imgs) {
                        if (img.src === url) {
                            const p = img.closest('p');
                            if (p) p.remove();
                            else img.remove();
                        }
                    }
                    return;
                }
            }
        }
    """, cover_url)
    await page.wait_for_timeout(500)

    return cover_url, file_id


async def set_cover(page, cover_url, file_id):
    """手动设置封面到编辑器"""
    print("  设置封面...")
    await page.evaluate("""
        (params) => {
            const preview = document.querySelector('.js_cover_preview_new');
            const item = document.querySelector('#appmsgItem');
            if (item) item.setAttribute('data-fileid', params.fileId);
            if (preview) {
                preview.style.backgroundImage = `url("${params.url}")`;
                preview.style.display = 'block';
                preview.style.backgroundSize = 'cover';
                preview.style.backgroundPosition = 'center';
                const area = document.getElementById('js_cover_area');
                if (area) {
                    const btn = area.querySelector('.select-cover__btn');
                    const loading = area.querySelector('.js_cover_loading');
                    if (btn) btn.style.display = 'none';
                    if (loading) loading.style.display = 'none';
                }
                const inputs = [
                    { cls: 'js_file_id', name: 'file_id', value: params.fileId },
                    { cls: 'js_cdn_url', name: 'cdn_url', value: params.url },
                    { cls: 'js_cdn_url_back', name: 'cdn_url_back', value: params.url },
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
                    }
                    el.value = inp.value;
                    el.setAttribute('value', inp.value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        }
    """, {"url": cover_url, "fileId": file_id})
    await page.wait_for_timeout(1000)


async def save_draft(page):
    """保存草稿并返回 appmsg_id"""
    print("  保存草稿...")
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
    await page.wait_for_timeout(6000)
    current_url = page.url
    m = re.search(r'appMsgId=(\d+)|appmsgid=(\d+)', current_url)
    appmsg_id = m.group(1) or m.group(2) if m else None
    save_draft_url(current_url, appmsg_id)
    print(f"    appMsgId: {appmsg_id}")
    return appmsg_id


async def restore_cover_preview(page, cover_url, file_id):
    """保存并重新加载后，恢复封面预览 URL（不保存）"""
    print("  恢复封面预览 URL...")
    await page.evaluate("""
        (params) => {
            const preview = document.querySelector('.js_cover_preview_new');
            const item = document.querySelector('#appmsgItem');
            if (preview) {
                preview.style.backgroundImage = `url("${params.url}")`;
                preview.style.display = 'block';
                preview.style.backgroundSize = 'cover';
                preview.style.backgroundPosition = 'center';
                const area = document.getElementById('js_cover_area');
                if (area) {
                    const btn = area.querySelector('.select-cover__btn');
                    const loading = area.querySelector('.js_cover_loading');
                    if (btn) btn.style.display = 'none';
                    if (loading) loading.style.display = 'none';
                }
            }
            if (item) item.setAttribute('data-fileid', params.fileId);
        }
    """, {"url": cover_url, "fileId": file_id})
    await page.wait_for_timeout(1000)


async def publish_from_editor(page):
    """从编辑器点击 mass_send 并发表"""
    print("\n  从编辑器发表...")
    try:
        await page.locator('button.mass_send').first.click(timeout=5000)
        print("    已点击 mass_send")
    except Exception as e:
        print(f"    点击失败: {e}")
        return False

    for round_idx in range(12):
        await page.wait_for_timeout(2500)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"publish_dialog_{round_idx}.png"))

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
                            buttons: Array.from(btns).map(b => (b.innerText || '').trim()).filter(t => t.length > 0 && t.length < 30),
                        };
                    }
                }
                return { found: false };
            }
        """)

        print(f"\n    第{round_idx+1}轮 URL={page.url}")
        if not dialog_info.get('found'):
            print("    无弹窗")
            if "appmsgpublish" in page.url:
                print("    ✅ 已跳转到发表记录页")
                return True
            continue

        print(f"    弹窗: {dialog_info['text'][:80]}")
        print(f"    按钮: {dialog_info['buttons']}")

        dialog_text = dialog_info['text']
        buttons = dialog_info['buttons']
        target = None

        # 微信验证：需要用户扫码，脚本继续等待
        if '扫码' in dialog_text or '验证' in dialog_text or '管理员' in dialog_text:
            print("    ⚠️ 需要微信扫码验证，脚本继续等待...")
            continue

        # 正在发表中
        if '正在发表' in dialog_text:
            print("    ⏳ 正在发表中...")
            continue

        if 'AI' in dialog_text or '声明' in dialog_text:
            for b in buttons:
                if '无需声明并发表' in b or '无需声明' in b:
                    target = b
                    break
        if not target:
            for b in buttons:
                if '确认群发' in b or '确定群发' in b:
                    target = b
                    break
        if not target:
            for b in buttons:
                if b == '发表':
                    target = b
                    break
        if not target:
            for b in buttons:
                if '继续发表' in b:
                    target = b
                    break
        if not target:
            for b in buttons:
                if '我知道了' in b:
                    target = b
                    break
        if not target:
            for b in buttons:
                if b == '确定':
                    target = b
                    break

        if target:
            print(f"    点击: {target}")
            await page.evaluate("""
                (targetText) => {
                    const dialogs = document.querySelectorAll('.weui-desktop-dialog, .weui-desktop-overlay, [class*="dialog"]');
                    for (const d of dialogs) {
                        if (d.offsetHeight === 0) continue;
                        const btns = d.querySelectorAll('button, a, [role="button"], .weui-desktop-btn');
                        for (const b of btns) {
                            if ((b.innerText || '').trim() === targetText) { b.click(); return true; }
                        }
                    }
                    const allBtns = document.querySelectorAll('button, a, [role="button"]');
                    for (const b of allBtns) {
                        if ((b.innerText || '').trim() === targetText && b.offsetHeight > 0) { b.click(); return true; }
                    }
                    return false;
                }
            """, target)
        else:
            print("    未识别目标按钮，停止")
            return False

    return False


async def main():
    existing_draft = load_draft_url()
    if existing_draft:
        print(f"  发现旧草稿记录 (appMsgId={existing_draft.get('appmsg_id')})，将创建新文章")
        clear_draft_url()

    with open(ARTICLE_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu"]
        )
        await context.grant_permissions(["clipboard-read", "clipboard-write"], origin=MP_URL)
        page = context.pages[0] if context.pages else await context.new_page()

        print("\n[1] 打开公众号后台...")
        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(3000)
        if not await is_logged_in(page):
            print("  请扫码登录")
            if not await wait_for_login(page):
                print("  登录超时")
                await context.close()
                return
            print("  登录成功")

        print("\n[2] 创建新文章...")
        token = await extract_token(page)
        new_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN"
        await page.goto(new_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "editor_new.png"))

        print("\n[3] 填写标题...")
        await fill_title(page, TITLE)

        print("\n[4] 填写作者...")
        await fill_author(page, AUTHOR)

        print("\n[5] 粘贴正文...")
        await paste_content(page, html_content)
        text_len = await page.evaluate("""
            () => {
                const allPm = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
                for (const pm of allPm) {
                    if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                        return (pm.innerText || '').length;
                    }
                }
                return 0;
            }
        """)
        print(f"    正文字数: {text_len}")

        print("\n[6] 上传封面...")
        cover_url, file_id = await upload_cover_via_toolbar(page, COVER_IMAGE_PATH)
        if not cover_url:
            print("❌ 封面上传失败")
            await context.close()
            return
        await set_cover(page, cover_url, file_id)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "cover_set.png"))

        print("\n[7] 填写摘要...")
        await fill_digest(page, DIGEST)

        print("\n[8] 保存草稿...")
        appmsg_id = await save_draft(page)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "after_save.png"), full_page=True)

        print("\n[9] 重新加载并恢复封面预览...")
        reload_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&appmsgid={appmsg_id}&token={token}&lang=zh_CN"
        await page.goto(reload_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await restore_cover_preview(page, cover_url, file_id)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "cover_restored.png"))

        print("\n[10] 发表...")
        result = await publish_from_editor(page)

        print("\n[11] 最终验证...")
        await page.wait_for_timeout(5000)
        final_url = page.url
        print(f"    最终 URL: {final_url}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "publish_final.png"), full_page=True)

        try:
            body_text = await page.inner_text("body")
            if TITLE in body_text:
                print("    ✅ 页面中找到文章标题")
            if any(kw in body_text for kw in ["群发成功", "发布成功", "已群发", "已发表", "发表成功"]):
                print("    ✅ 检测到成功关键词")
                result = True
            if any(kw in body_text for kw in ["群发失败", "发布失败", "操作失败"]):
                print("    ❌ 检测到失败关键词")
        except: pass

        if result:
            clear_draft_url()
            print("\n✅ 文章发表流程已完成")
        else:
            print("\n⚠️ 发表未最终确认，请检查发表记录")

        print("\n浏览器保持打开60秒...")
        await page.wait_for_timeout(60000)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
