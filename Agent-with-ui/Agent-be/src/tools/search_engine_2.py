import asyncio
import os
import uuid
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- CONFIGURATION ---
CONFIG = {
    "dynamicProxy": None,  # Example: "http://user:pass@host:port"
    "maxResults": 10,
    "delayBetweenRequests": (2.0, 4.0)  # Seconds
}

# --- HELPER FUNCTIONS ---
async def sleep(seconds):
    await asyncio.sleep(seconds)

# Ensure a directory exists to store the downloaded HTML files
DOWNLOAD_DIR = "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/raw_html"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

async def fetch_and_save(url, context, semaphore):
    """
    Opens a tab, scrapes the HTML, saves it to a file, and returns the path.
    """
    async with semaphore: # Limit concurrency (e.g. max 5 tabs at once)
        print(f"🕵️ [Playwright] scraping: {url}")
        page = await context.new_page()
        
        try:
            # Block heavy resources to speed up scraping
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,mp4,webp}", lambda route: route.abort())

            # Navigate
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await sleep(2.0) # Wait for JS execution

            content = await page.content()
            
            # Save HTML to a unique file
            filename = f"raw_{uuid.uuid4().hex[:8]}.html"
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"✅ Saved {url} -> {file_path}")
            return {
                "url": url,
                "file_store_path": file_path
            }

        except Exception as e:
            print(f"❌ Failed to load {url}: {e}")
            # Create an error file so the flow doesn't break
            err_filename = f"error_{uuid.uuid4().hex[:8]}.txt"
            err_path = os.path.join(DOWNLOAD_DIR, err_filename)
            with open(err_path, "w", encoding="utf-8") as f:
                f.write(f"Scrape failed for {url}\nError: {str(e)}")
            
            return {
                "url": url,
                "file_store_path": err_path
            }
        finally:
            await page.close()

async def i_search_engine_2(urls):
    """
    Takes a list of URLs, scrapes them in parallel (using a single browser instance),
    and returns a list of {url, file_store_path}.
    """
    async with async_playwright() as p:
        # Launch browser once
        browser_args = {"headless": False}
        if CONFIG.get("dynamicProxy"):
            browser_args["proxy"] = {"server": CONFIG["dynamicProxy"]}
            
        browser = await p.chromium.launch(**browser_args)
        context = await browser.new_context()
        
        # Apply stealth once to the context
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        
        # Semaphore to limit max open tabs (prevent crashing)
        semaphore = asyncio.Semaphore(5) 
        
        # Create tasks for all URLs
        tasks = [fetch_and_save(url, context, semaphore) for url in urls]
        
        # Run them all concurrently
        results = await asyncio.gather(*tasks)
        
        await context.close()
        await browser.close()
            
    return results