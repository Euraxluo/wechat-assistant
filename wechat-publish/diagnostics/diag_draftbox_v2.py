#!/usr/bin/env python3
"""
诊断脚本：检查草稿箱 DOM 结构，找到真正的「发表/群发」按钮
"""
import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

USER_DATA_DIR = "/Users/echo/project/wechat-skills/.browser_profile"
SCREENSHOT_DIR = "/Users/echo/project/wechat-skills"
MP_URL = "https://mp.weixin.qq.com/"

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
        try:
            m = re.search(r'token=(\d+)', page.url)
            if m:
                token = m.group(1)
            else:
                # 尝试从页面获取
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
        except: pass

        print(f"Token: {token}")

        # 导航到草稿箱
        draft_box_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_manage&action=list&type=77&token={token}&lang=zh_CN"
        await page.goto(draft_box_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_draftbox_v2.png"))

        # 检查草稿箱中的文章列表
        drafts_info = await page.evaluate("""
            () => {
                const data = window.wx?.cgiData || window.cgiData || {};
                const items = data.item || data.list || [];
                return items.map((item, i) => ({
                    index: i,
                    app_id: item.app_id || item.appmsgid || item.id,
                    title: item.title || '',
                    update_time: item.update_time || '',
                }));
            }
        """)
        print(f"\n草稿箱中有 {len(drafts_info)} 篇草稿:")
        for d in drafts_info:
            print(f"  [{d['index']}] appMsgId={d['app_id']}, title={d['title']}, update={d['update_time']}")

        # 详细检查页面中所有包含"发表"、"群发"、"发布"的元素
        print("\n=== 页面中包含'发表/群发/发布'的元素 ===")
        buttons_info = await page.evaluate("""
            () => {
                const results = [];
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const text = (el.innerText || el.textContent || '').trim();
                    if (text === '发表' || text === '群发' || text === '发布' || 
                        text === '发表文章' || text === '群发文章' || text.includes('发表') && text.length < 20) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            // 找到这个元素的完整 HTML 上下文
                            const parent = el.parentElement;
                            const grandparent = parent ? parent.parentElement : null;
                            results.push({
                                tag: el.tagName,
                                text: text,
                                className: el.className?.toString()?.slice(0, 150) || '',
                                id: el.id || '',
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                w: Math.round(rect.width),
                                h: Math.round(rect.height),
                                parentTag: parent?.tagName || '',
                                parentClass: parent?.className?.toString()?.slice(0, 100) || '',
                                parentText: (parent?.innerText || '').slice(0, 100),
                                grandparentTag: grandparent?.tagName || '',
                                grandparentClass: grandparent?.className?.toString()?.slice(0, 100) || '',
                                href: el.href || el.getAttribute('data-url') || '',
                                onclick: el.onclick ? 'has_onclick' : '',
                                outerHTML: el.outerHTML.slice(0, 300),
                            });
                        }
                    }
                }
                return results;
            }
        """)
        for i, b in enumerate(buttons_info):
            print(f"\n  [{i}] <{b['tag']}> text=\"{b['text']}\" class=\"{b['className']}\" id=\"{b['id']}\"")
            print(f"       position: ({b['x']},{b['y']}) size: {b['w']}x{b['h']}")
            print(f"       parent: <{b['parentTag']}> class=\"{b['parentClass']}\" text=\"{b['parentText'][:60]}\"")
            print(f"       grandparent: <{b['grandparentTag']}> class=\"{b['grandparentClass']}\"")
            print(f"       href: {b['href']}")
            print(f"       outerHTML: {b['outerHTML']}")

        # 检查草稿卡片的操作按钮区域
        print("\n=== 草稿卡片操作按钮区域 ===")
        card_buttons = await page.evaluate("""
            () => {
                const results = [];
                // 找所有可能的操作按钮容器
                const opContainers = document.querySelectorAll('[class*="oper"], [class*="action"], [class*="btn-group"], [class*="toolbar"], .weui-desktop-card__ft, .card_ft');
                for (const container of opContainers) {
                    const rect = container.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const text = (container.innerText || '').trim();
                        if (text.length < 200) {
                            results.push({
                                tag: container.tagName,
                                className: container.className?.toString()?.slice(0, 150) || '',
                                text: text,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                w: Math.round(rect.width),
                                h: Math.round(rect.height),
                                innerHTML: container.innerHTML.slice(0, 500),
                            });
                        }
                    }
                }
                return results;
            }
        """)
        for i, c in enumerate(card_buttons):
            print(f"\n  [{i}] <{c['tag']}> class=\"{c['className']}\"")
            print(f"       text: \"{c['text']}\"")
            print(f"       position: ({c['x']},{c['y']}) size: {c['w']}x{c['h']}")
            print(f"       innerHTML: {c['innerHTML'][:300]}")

        # 特别检查：是否有"发表记录"导航链接（可能被误点）
        print("\n=== 检查导航栏中的'发表'相关链接 ===")
        nav_links = await page.evaluate("""
            () => {
                const results = [];
                const links = document.querySelectorAll('a, [role="link"], [role="menuitem"], .weui-desktop-nav__item, [class*="nav"] *');
                for (const link of links) {
                    const text = (link.innerText || link.textContent || '').trim();
                    if ((text.includes('发表') || text.includes('群发') || text.includes('发布')) && text.length < 30) {
                        const rect = link.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            results.push({
                                tag: link.tagName,
                                text: text,
                                className: link.className?.toString()?.slice(0, 100) || '',
                                href: link.href || '',
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                            });
                        }
                    }
                }
                return results;
            }
        """)
        for i, l in enumerate(nav_links):
            print(f"  [{i}] <{l['tag']}> text=\"{l['text']}\" class=\"{l['className']}\" href=\"{l['href']}\" pos=({l['x']},{l['y']})")

        # 滚动到第一篇草稿卡片并截图
        await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.weui-desktop-card, [class*="appmsg"]');
                if (cards.length > 0) cards[0].scrollIntoView({ block: 'center' });
            }
        """)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "diag_draftbox_card1.png"))

        # 检查第一篇草稿卡片的完整 HTML
        first_card_html = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.weui-desktop-card');
                if (cards.length > 0) {
                    return cards[0].outerHTML.slice(0, 3000);
                }
                return 'no card found';
            }
        """)
        print(f"\n=== 第一篇草稿卡片 HTML (前3000字符) ===")
        print(first_card_html)

        print("\n诊断完成，浏览器保持打开 30 秒...")
        await page.wait_for_timeout(30000)
        await context.close()

asyncio.run(main())
