from playwright.async_api import async_playwright
# FIXED: Import Stealth class instead of removed function
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from Agent.tools.complete_search_engine import sleep, random_delay, CONFIG

async def fetch_with_playwright(url, context):
    print(f"🕵️ [Playwright] scraping: {url}")
    page = await context.new_page()
    
    try:
        # Block images/fonts/media to save bandwidth/speed
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,webp}", lambda route: route.abort())

        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await sleep(2.0) # Wait for JS

        content = await page.content()
        return content
    except Exception as e:
        print(f"❌ Failed to load {url}: {e}")
        return None
    finally:
        await page.close()

async def search_engine_2(url):
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
            html = await fetch_with_playwright(url, context)
        finally:
            print("🛑 Closing Browser Engine...")
            await context.close()
            await browser.close()
            
    return html