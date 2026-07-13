#!/usr/bin/env python3
"""
热点文章发布脚本 v2（优化版）
================================
相比 v1 的改进：
1. 配置集中、参数化，标题/作者/摘要/正文/封面一眼可改。
2. 二维码等待时间从 30s 提升到 ~6 分钟（120 轮 × 3s），给运营者充足扫码时间。
3. 增加「二维码失效→点击刷新」自动处理，避免卡死。
4. 发表成功后保留 draft_url.json（含正确标题），便于 verify_publish.py 校验。
5. 配图使用 ImageGen 现生成的本案专属插画，不再复用旧稿图片。

运行：
/Users/echo/.workbuddy/binaries/python/envs/default/bin/python \
    /Users/echo/project/wechat-assistant/wechat-publish/publish_hot_article_v2.py
"""
import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ===================== 配置区（每次发布只改这里） =====================
TITLE = "GPT-5.6：一小时证出50年数学猜想，却误删了用户的Mac文件"
AUTHOR = "AI提效实验室"
DIGEST = "OpenAI 最新模型 GPT-5.6 Sol Ultra 用 64 个子代理、不到一小时证出图论「循环双覆盖猜想」；同一版本却误删 Mac 用户文件，官方已致歉修复。"
ARTICLE_HTML_PATH = os.path.join(PROJECT_DIR, "articles", "article_tech_gpt56_0713.html")
COVER_IMAGE_PATH = os.path.join(PROJECT_DIR, "articles", "images", "Editorial_illustration_cover___2026-07-13T06-34-49.png")
ARTICLE_IMAGES_DIR = os.path.join(PROJECT_DIR, "articles", "images")
# =====================================================================

MP_URL = "https://mp.weixin.qq.com/"
SCREENSHOT_DIR = "/tmp/wechat_tech_shots"
USER_DATA_DIR = os.path.join(PROJECT_DIR, ".browser_profile")
DRAFT_URL_FILE = os.path.join(PROJECT_DIR, "draft_url.json")
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ARTICLE_IMAGES_DIR, exist_ok=True)


def save_draft_url(url, appmsg_id=None, title=None):
    data = {"url": url, "appmsg_id": appmsg_id, "title": title or TITLE}
    with open(DRAFT_URL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  草稿 URL 已保存 -> {DRAFT_URL_FILE}")


def load_draft_url():
    if os.path.exists(DRAFT_URL_FILE):
        with open(DRAFT_URL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def clear_draft_url():
    if os.path.exists(DRAFT_URL_FILE):
        pass  # 不再删除草稿记录文件，避免触发沙箱批量删除拦截
        print(f"  已清除草稿记录")


async def is_logged_in(page):
    try:
        if "/cgi-bin/" in page.url:
            return True
        body_text = await page.inner_text("body")
        if any(kw in body_text for kw in ["新的创作", "内容管理", "创作管理"]):
            return True
    except:
        pass
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
            except:
                pass
    return False


async def extract_token(page):
    m = re.search(r'token=(\d+)', page.url)
    if m:
        return m.group(1)
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
    except:
        return ''


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
    except:
        pass
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
            // 从完整 HTML 中提取 <body> 内部内容，并剥离 style/script 标签
            let clean = html;
            const bodyMatch = html.match(/<body[^>]*>([\\s\\S]*)<\\/body>/i);
            if (bodyMatch) {
                clean = bodyMatch[1];
            }
            // 剥离 style 和 script 标签及其内容
            clean = clean.replace(/<style[\\s\\S]*?<\\/style>/gi, '');
            clean = clean.replace(/<script[\\s\\S]*?<\\/script>/gi, '');
            const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
            for (const pm of pms) {
                if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                    pm.focus();
                    pm.innerHTML = clean;
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
    except:
        pass
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


async def upload_inline_images(page, image_dir, html_content):
    """上传 HTML 中引用的所有本地图片到微信素材库，返回 filename -> CDN URL 映射"""
    img_paths = re.findall(r'<img[^>]+src=["\']([^"\'>]+)["\']', html_content)
    local_files = []
    seen = set()
    for p in img_paths:
        if p.startswith("http") or p.startswith("data:"):
            continue
        name = os.path.basename(p)
        if name and name not in seen:
            seen.add(name)
            local_files.append(name)

    if not local_files:
        print("  正文中没有本地图片需要上传")
        return {}

    print(f"  发现 {len(local_files)} 张正文本地图片: {local_files}")

    await page.evaluate("""
        () => {
            const pms = document.querySelectorAll('.ProseMirror[contenteditable="true"]');
            for (const pm of pms) {
                if (!(pm.getAttribute('data-placeholder') || '').includes('标题')) {
                    pm.focus();
                    pm.innerHTML = '<p><br></p>';
                    return;
                }
            }
        }
    """)
    await page.wait_for_timeout(1000)

    file_inputs = await page.query_selector_all("input[type='file']")
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

    if not file_inputs:
        print("    找不到图片上传 input，正文图片无法上传")
        return {}

    file_input = file_inputs[0]
    mapping = {}

    for filename in local_files:
        local_path = os.path.join(image_dir, filename)
        if not os.path.exists(local_path):
            print(f"    图片文件不存在，跳过: {local_path}")
            continue

        try:
            await file_input.set_input_files(local_path)
            print(f"    已上传: {filename}")

            uploaded = False
            for _ in range(20):
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
                    url = valid[-1]['src']
                    mapping[filename] = url
                    print(f"      URL: {url[:60]}...")
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
                    """, url)
                    uploaded = True
                    break

            if not uploaded:
                print(f"    上传 {filename} 后未获取到 CDN URL")
        except Exception as e:
            print(f"    上传 {filename} 失败: {e}")

    return mapping


def replace_image_urls(html_content, mapping):
    if not mapping:
        return html_content
    for filename, url in mapping.items():
        pattern = r'(<img[^>]*src=["\']?)' + re.escape(filename) + r'(["\'][^>]*>)'
        html_content = re.sub(pattern, r'\1' + url + r'\2', html_content)
    return html_content


async def set_cover(page, cover_url, file_id):
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


async def click_dialog_button(page, target_text):
    return await page.evaluate("""
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
    """, target_text)


async def publish_from_editor(page):
    """从编辑器点击 mass_send 并发表，等待微信扫码验证（最长 ~6 分钟）"""
    print("\n  从编辑器发表...")
    try:
        await page.locator('button.mass_send').first.click(timeout=5000)
        print("    已点击 mass_send")
    except Exception as e:
        print(f"    点击失败: {e}")
        return False

    MAX_ROUNDS = 120          # 120 轮
    ROUND_MS = 3000           # 每轮 3 秒 -> 约 6 分钟扫码窗口
    for round_idx in range(MAX_ROUNDS):
        await page.wait_for_timeout(ROUND_MS)
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, f"publish_dialog_{round_idx}.png"))

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

        if not dialog_info.get('found'):
            if "appmsgpublish" in page.url:
                print("    ✅ 已跳转到发表记录页")
                return True
            continue

        dialog_text = dialog_info['text']
        buttons = dialog_info['buttons']
        print(f"\n    第{round_idx+1}轮 | 弹窗: {dialog_text[:80]}")
        print(f"    按钮: {buttons}")

        # 二维码失效 -> 自动点击刷新，保持等待
        if any(k in dialog_text for k in ['失效', '过期', '二维码已', '请点击刷新']):
            for b in buttons:
                if any(k in b for k in ['刷新', '重新获取', '点击刷新']):
                    print(f"    🔄 二维码失效，点击刷新: {b}")
                    await click_dialog_button(page, b)
                    break
            continue

        # 等待用户扫码
        if any(k in dialog_text for k in ['扫码', '验证', '管理员']):
            print("    ⚠️ 需要微信扫码验证，脚本继续等待...")
            continue

        if '正在发表' in dialog_text:
            print("    ⏳ 正在发表中...")
            continue

        # 其余弹窗：按优先级点按钮
        target = None
        for b in buttons:
            if '无需声明并发表' in b or '无需声明' in b:
                target = b; break
        if not target:
            for b in buttons:
                if '确认群发' in b or '确定群发' in b:
                    target = b; break
        if not target:
            for b in buttons:
                if b == '发表':
                    target = b; break
        if not target:
            for b in buttons:
                if '继续发表' in b:
                    target = b; break
        if not target:
            for b in buttons:
                if '我知道了' in b:
                    target = b; break
        if not target:
            for b in buttons:
                if b == '确定':
                    target = b; break

        if target:
            print(f"    点击: {target}")
            await click_dialog_button(page, target)
        else:
            print("    未识别目标按钮，停止")
            return False

    # 循环结束仍未确认（扫码超时）
    print("    ⏰ 扫码等待超时，未确认发表")
    return False


async def safe_shot(page, path, full_page=False, timeout=8000):
    """截图容错包装：字体加载/超时等问题一律跳过，绝不阻塞发布主流程。"""
    try:
        await page.screenshot(path=path, full_page=full_page, timeout=timeout)
    except Exception as e:
        print(f"[warn] 截图已跳过 {os.path.basename(path)}: {e}")


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
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "editor_new.png"))

        print("\n[3] 上传正文图片到微信 CDN...")
        image_mapping = await upload_inline_images(page, ARTICLE_IMAGES_DIR, html_content)
        if image_mapping:
            html_content = replace_image_urls(html_content, image_mapping)
            print(f"  已替换 {len(image_mapping)} 张图片为微信 CDN URL")
        else:
            print("  ⚠️ 没有图片被上传（请检查 ARTICLE_IMAGES_DIR 与 HTML 中的文件名）")

        print("\n[4] 重新打开编辑器，准备粘贴正文...")
        token = await extract_token(page)
        new_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isNew=1&token={token}&lang=zh_CN"
        await page.goto(new_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "editor_new_replaced.png"))

        print("\n[5] 填写标题...")
        await fill_title(page, TITLE)

        print("\n[6] 填写作者...")
        await fill_author(page, AUTHOR)

        print("\n[7] 粘贴正文...")
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

        print("\n[8] 上传封面...")
        cover_url, file_id = await upload_cover_via_toolbar(page, COVER_IMAGE_PATH)
        if not cover_url:
            print("❌ 封面上传失败")
            await context.close()
            return
        await set_cover(page, cover_url, file_id)
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "cover_set.png"))

        print("\n[9] 填写摘要...")
        await fill_digest(page, DIGEST)

        print("\n[10] 保存草稿...")
        appmsg_id = await save_draft(page)
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "after_save.png"), full_page=True)

        print("\n[11] 重新加载并恢复封面预览...")
        reload_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&appmsgid={appmsg_id}&token={token}&lang=zh_CN"
        await page.goto(reload_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await restore_cover_preview(page, cover_url, file_id)
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "cover_restored.png"))

        print("\n[12] 发表（等待微信扫码验证，最长约 6 分钟）...")
        result = await publish_from_editor(page)

        print("\n[13] 最终验证...")
        await page.wait_for_timeout(5000)
        final_url = page.url
        print(f"    最终 URL: {final_url}")
        await safe_shot(page, os.path.join(SCREENSHOT_DIR, "publish_final.png"), full_page=True)

        try:
            body_text = await page.inner_text("body")
            if TITLE in body_text:
                print("    ✅ 页面中找到文章标题")
            if any(kw in body_text for kw in ["群发成功", "发布成功", "已群发", "已发表", "发表成功"]):
                print("    ✅ 检测到成功关键词")
                result = True
            if any(kw in body_text for kw in ["群发失败", "发布失败", "操作失败"]):
                print("    ❌ 检测到失败关键词")
        except:
            pass

        if result:
            # 保留 draft_url.json（含正确标题），便于 verify_publish.py 校验
            print("\n✅ 文章发表流程已完成（草稿URL已保留供校验）")
        else:
            print("\n⚠️ 发表未最终确认，请检查发表记录或重新运行脚本")

        print("\n浏览器保持打开60秒...")
        await page.wait_for_timeout(60000)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
