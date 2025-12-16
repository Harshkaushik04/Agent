import asyncio
import random
from playwright.async_api import async_playwright
# UPDATED: Import the class instead of the function
from playwright_stealth import Stealth 
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
CONFIG = {
    "dynamicProxy": None,  # Example: "http://user:pass@host:port"
    "maxResults": 10,
    "delayBetweenRequests": (2.0, 4.0)  # Seconds
}

# --- HELPER FUNCTIONS ---
async def sleep(seconds):
    await asyncio.sleep(seconds)

def random_delay():
    min_delay, max_delay = CONFIG["delayBetweenRequests"]
    return random.uniform(min_delay, max_delay)

# 1. SEARCH MODULE
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

# 2. SCRAPE MODULE
async def fetch_with_playwright(url, context):
    print(f"🕵️ [Playwright] scraping: {url}")
    page = await context.new_page()
    
    try:
        # Block images/fonts/media to save bandwidth/speed
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,webp}", lambda route: route.abort())

        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await sleep(1.5) # Wait for JS

        content = await page.content()
        return content
    except Exception as e:
        print(f"❌ Failed to load {url}: {e}")
        return None
    finally:
        await page.close()

# 3. CLEANING MODULE
def parse_and_clean_html(html, url):
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted tags
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'link', 'svg', 'footer', 'nav', 'header', 'aside', 'form', 'button']):
        tag.decompose()

    text_content = []
    # Find relevant text elements
    targets = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'article'])
    
    for el in targets:
        text = el.get_text(separator=' ', strip=True)
        if len(text) > 40:
            text_content.append(text)

    # Remove duplicates while preserving order
    seen = set()
    unique_content = [x for x in text_content if not (x in seen or seen.add(x))]
    
    if not unique_content:
        return ""
        
    return f"\n--- SOURCE: {url} ---\n" + "\n".join(unique_content)

# --- MAIN ---
async def complete_search(search_query, top_k):
    CONFIG["maxResults"] = top_k
    print("🔥 Launching Browser Engine...")
    final_ans = ""
    
    async with async_playwright() as p:
        # Launch browser
        browser_args = {"headless": False}
        if CONFIG["dynamicProxy"]:
            browser_args["proxy"] = {"server": CONFIG["dynamicProxy"]}
            
        browser = await p.chromium.launch(**browser_args)
        
        # Create a context
        context = await browser.new_context()
        
        # --- FIXED STEALTH LOGIC ---
        # 1. Instantiate the class
        stealth = Stealth() 
        # 2. Apply it to the context
        await stealth.apply_stealth_async(context) 
        # ---------------------------

        try:
            # 1. Search
            urls = await get_duckduckgo_results(search_query, context)

            # 2. Scrape
            for url in urls:
                delay = random_delay()
                await sleep(delay)
                
                html = await fetch_with_playwright(url, context)
                if html:
                    cleaned_text = parse_and_clean_html(html, url)
                    if cleaned_text:
                        final_ans += cleaned_text
                        final_ans += "\n"
        
        finally:
            print("🛑 Closing Browser Engine...")
            await context.close()
            await browser.close()
            
    print(f"\n✨ Job Complete. Captured {len(final_ans)} chars.")
    return final_ans

# s_query = input("search query: ")
# t_k_input = input("top k: ")
# t_k = int(t_k_input) if t_k_input.strip() else 3

# result = asyncio.run(complete_search(s_query, t_k))
# print("\n--- FINAL OUTPUT SAMPLE ---\n")
# print("first 1000 words:",result[:1000])