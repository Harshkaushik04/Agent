from playwright.async_api import async_playwright
from playwright_stealth import Stealth 
import asyncio

CONFIG = {
    "dynamicProxy": None,  # Example: "http://user:pass@host:port"
    "maxResults": 10,
    "delayBetweenRequests": (2.0, 4.0)  # Seconds
}

# 1. Update: Accept top_k as argument
async def get_duckduckgo_results(query, context, top_k):
    print(f"Searching DuckDuckGo for: \"{query}\" (Limit: {top_k})...")
    page = await context.new_page()
    
    try:
        await page.goto('https://duckduckgo.com/', wait_until='networkidle')
        await page.fill('input[name="q"]', query)
        await page.press('input[name="q"]', 'Enter')
        
        # Wait for results to appear
        await page.wait_for_selector('article', timeout=15000)

        # 2. Update: Use local 'top_k' variable in the f-string, NOT CONFIG global
        urls = await page.evaluate(f"""
            (max) => {{
                const anchors = Array.from(document.querySelectorAll('article h2 a'));
                return anchors.map(a => a.href).slice(0, {top_k});
            }}
        """)

        print(f" Found {len(urls)} URLs for \"{query}\".")
        return urls
    except Exception as e:
        print(f" Search failed for {query}: {e}")
        return []
    finally:
        await page.close()

async def f_search_engine_1(search_query, top_k):
    # REMOVED: CONFIG["maxResults"] = top_k (To prevent race condition)
    
    async with async_playwright() as p:
        browser_args = {"headless": False}
        if CONFIG.get("dynamicProxy"): # Use .get() for safety
            browser_args["proxy"] = {"server": CONFIG["dynamicProxy"]}
            
        browser = await p.chromium.launch(**browser_args)
        context = await browser.new_context()
        
        stealth = Stealth()
        await stealth.apply_stealth_async(context) 

        try:
            # Pass top_k down explicitly
            urls = await get_duckduckgo_results(search_query, context, top_k)
        finally:
            await context.close()
            await browser.close()
            
    return urls

async def i_search_engine_1(list_search_query_top_k):
    semaphore = asyncio.Semaphore(3) # Limit to 3 browsers

    # Wrapper to format the output correctly for the Agent
    async def safe_search(q, top_k):
        async with semaphore:
            urls = await f_search_engine_1(q, top_k)
            # Return the object structure expected by your Agent Prompt
            return {
                "search_query": q,
                "urls": urls
            }

    tasks = []
    for item in list_search_query_top_k:
        # Extract fields from the dict
        tasks.append(safe_search(item["search_query"], item["top_k"]))
    
    return await asyncio.gather(*tasks)