#!/usr/bin/env python3
"""从当前仓库 draft_url.json 恢复并继续发表草稿。"""
import asyncio
import json
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_DIR = Path(__file__).resolve().parents[1]
DRAFT_URL_FILE = PROJECT_DIR / "draft_url.json"
SCREENSHOT_DIR = PROJECT_DIR / "screenshots"
USER_DATA_DIR = PROJECT_DIR / ".browser_profile"
MP_URL = "https://mp.weixin.qq.com/"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def load_draft():
    if not DRAFT_URL_FILE.exists():
        return None
    return json.loads(DRAFT_URL_FILE.read_text(encoding="utf-8"))


def load_expected_title():
    draft = load_draft()
    if draft and draft.get("title"):
        return draft["title"]
    runs_dir = PROJECT_DIR / "runs"
    for path in sorted(runs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.name == "_example.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("title"):
                return data["title"]
        except Exception:
            continue
    return ""


async def is_logged_in(page):
    try:
        if "/cgi-bin/" in page.url:
            return True
        body_text = await page.inner_text("body")
        return any(kw in body_text for kw in ["新的创作", "内容管理", "创作管理"])
    except Exception:
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
            except Exception:
                pass
    return False


async def extract_token(page):
    return await page.evaluate(
        """
        () => {
            const m = window.location.href.match(/token=(\d+)/);
            if (m) return m[1];
            const l = document.querySelector('a[href*="token="]');
            if (l) { const m2 = l.href.match(/token=(\d+)/); return m2 ? m2[1] : ''; }
            return '';
        }
        """
    )


async def get_current_cover(page):
    return await page.evaluate(
        """
        () => {
            const item = document.querySelector('#appmsgItem');
            const preview = document.querySelector('.js_cover_preview_new');
            const fileId = item?.getAttribute('data-fileid') || preview?.querySelector('input[name="file_id"]')?.value || '';
            let url = '';
            if (preview) {
                const bg = preview.style.backgroundImage || window.getComputedStyle(preview).backgroundImage || '';
                const m = bg.match(/url\(["']?(.*?)["']?\)/);
                if (m) url = m[1];
            }
            url = url || preview?.querySelector('input[name="cdn_url"]')?.value || '';
            return { fileId, url };
        }
        """
    )


async def ensure_cover_preview(page, cover):
    if not cover.get("fileId") or not cover.get("url"):
        return False
    return await page.evaluate(
        """
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
                return true;
            }
            return false;
        }
        """,
        cover,
    )


async def click_dialog_button(page, target_text):
    return await page.evaluate(
        """
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
        """,
        target_text,
    )


async def publish_from_editor(page):
    try:
        await page.locator('button.mass_send').first.click(timeout=5000)
        print("  已点击 mass_send")
    except Exception:
        clicked = await page.evaluate(
            """
            () => {
                const btn = document.getElementById('mass_send') || document.querySelector('button.mass_send');
                if (btn) { btn.click(); return true; }
                return false;
            }
            """
        )
        if not clicked:
            print("  ❌ 未找到发表按钮")
            return False

    for i in range(120):
        await page.wait_for_timeout(3000)
        info = await page.evaluate(
            """
            () => {
                const dialogs = document.querySelectorAll('.weui-desktop-dialog, .weui-desktop-overlay, [class*="dialog"]');
                for (const d of dialogs) {
                    if (d.offsetHeight === 0) continue;
                    const text = (d.innerText || '').trim();
                    if (!text) continue;
                    const buttons = Array.from(d.querySelectorAll('button, a, [role="button"], .weui-desktop-btn')).map(b => (b.innerText || '').trim()).filter(Boolean);
                    return { found: true, text: text.slice(0, 260), buttons };
                }
                return { found: false, text: '', buttons: [] };
            }
            """
        )
        body_text = ""
        try:
            body_text = await page.inner_text("body")
        except Exception:
            pass
        if any(kw in body_text for kw in ["群发成功", "发布成功", "已群发", "已发表", "发表成功"]) or "appmsgpublish" in page.url or "home?t=home" in page.url:
            return True
        if not info.get("found"):
            continue
        text = info.get("text", "")
        buttons = info.get("buttons", [])
        target = None
        if "扫码" in text or "验证" in text or "管理员" in text:
            print("  ⚠️ 等待微信扫码/管理员验证...")
            continue
        if "正在发表" in text:
            print("  ⏳ 正在发表中...")
            continue
        if "AI" in text or "声明" in text:
            target = next((b for b in buttons if "无需声明并发表" in b or "无需声明" in b), None)
        if not target:
            target = next((b for b in buttons if b == "发表"), None)
        if not target:
            target = next((b for b in buttons if "继续发表" in b), None)
        if not target:
            target = next((b for b in buttons if b in ["确定", "我知道了"] or "确认群发" in b or "确定群发" in b), None)
        if target:
            print(f"  点击: {target}")
            await click_dialog_button(page, target)
    return False


async def main():
    draft = load_draft()
    if not draft or not draft.get("url"):
        print("❌ 没有找到当前仓库草稿 URL")
        return

    expected_title = load_expected_title()
    print(f"继续发布草稿: {draft.get('appmsg_id')}")
    print(f"目标标题: {expected_title}")
    print("⚠️ 如出现微信验证，请尽快扫码")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(MP_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        if not await is_logged_in(page):
            print("⚠️ 公众号后台未登录，请扫码登录后重试")
            if not await wait_for_login(page):
                await context.close()
                return

        token = await extract_token(page)
        edit_url = draft["url"]
        if token and draft.get("appmsg_id"):
            edit_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&appmsgid={draft['appmsg_id']}&token={token}&lang=zh_CN"
        await page.goto(edit_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(SCREENSHOT_DIR / "republish_editor_open.png"), full_page=True)

        cover = await get_current_cover(page)
        restored = await ensure_cover_preview(page, cover)
        print(f"封面恢复: {restored}")

        result = await publish_from_editor(page)
        print(f"发表结果: {result}")
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
