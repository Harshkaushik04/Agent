from playwright.async_api import async_playwright
# FIXED: Import Stealth class instead of removed function
from playwright_stealth import Stealth 
from bs4 import BeautifulSoup
from Agent.tools.complete_search_engine import sleep, random_delay, CONFIG

async def get_duckduckgo_results(query, context):
    print(f"🔍 Searching DuckDuckGo for: \"{query}\"...")
    page = await context.new_page()
    
    try:
        await page.goto('https://duckduckgo.com/', wait_until='networkidle')
        await page.fill('input[name="q"]', query)
        await page.press('input[name="q"]', 'Enter')
        
        # Wait for results to appear
        await page.wait_for_selector('article', timeout=15000)

        # Extract URLs
        urls = await page.evaluate(f"""
            (max) => {{
                const anchors = Array.from(document.querySelectorAll('article h2 a'));
                return anchors.map(a => a.href).slice(0, max);
            }}
        """, CONFIG["maxResults"])

        print(f"✅ Found {len(urls)} URLs.")
        return urls
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []
    finally:
        await page.close()

async def search_engine_1(search_query, top_k):
    CONFIG["maxResults"] = top_k
    async with async_playwright() as p:
        # Launch browser
        browser_args = {"headless": True}
        if CONFIG["dynamicProxy"]:
            browser_args["proxy"] = {"server": CONFIG["dynamicProxy"]}
            
        browser = await p.chromium.launch(**browser_args)
        
        # Create a context
        context = await browser.new_context()
        
        # FIXED: Apply stealth correctly
        stealth = Stealth()
        await stealth.apply_stealth_async(context) 

        try:
            # 1. Search
            urls = await get_duckduckgo_results(search_query, context)
        finally:
            print("🛑 Closing Browser Engine...")
            await context.close()
            await browser.close()
            
    return urls