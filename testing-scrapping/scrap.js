/**
 * Safe Search & Scrape Tool (Full Stealth Mode)
 * - Uses Playwright Stealth for the Search (Bypasses DDG API blocks)
 * - Uses Axios + Random User Agents for scraping (Speed)
 * - Falls back to Playwright for scraping if Axios is blocked
 */

const fs = require('fs');
const axios = require('axios');
const cheerio = require('cheerio');
const { HttpsProxyAgent } = require('https-proxy-agent');
const UserAgent = require('user-agents'); 

// --- PLAYWRIGHT SETUP ---
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

// --- CONFIGURATION ---
const CONFIG = {
    outputFile: 'search_results.txt',
    // Add your proxy here like 'http://user:pass@1.2.3.4:8080' if you have one
    dynamicProxy: null, 
    axiosTimeout: 15000,
    maxResults: 5,
    delayBetweenRequests: [3000, 6000] // Increased slightly for safety
};

// --- HELPER FUNCTIONS ---
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const randomDelay = () => {
    const min = CONFIG.delayBetweenRequests[0];
    const max = CONFIG.delayBetweenRequests[1];
    return Math.floor(Math.random() * (max - min + 1) + min);
};

// Generates a random browser profile
const getRandomUserAgent = () => new UserAgent().toString();

// 1. SEARCH MODULE (NOW USING PLAYWRIGHT STEALTH)
// Replaces duck-duck-scrape to avoid "anomaly" errors
async function getDuckDuckGoResults(query) {
    console.log(`🔍 [Playwright] Searching DuckDuckGo for: "${query}"...`);
    
    let browser = null;
    try {
        browser = await chromium.launch({
            headless: true, // Set to false if you want to watch it work
            proxy: CONFIG.dynamicProxy ? { server: CONFIG.dynamicProxy } : undefined
        });

        const page = await browser.newPage();
        
        // 1. Go to DDG
        await page.goto('https://duckduckgo.com/', { waitUntil: 'networkidle' });
        
        // 2. Type Query and Search
        await page.fill('input[name="q"]', query);
        await page.press('input[name="q"]', 'Enter');
        
        // 3. Wait for results
        await page.waitForSelector('article', { timeout: 10000 });

        // 4. Extract Links
        // We select the anchor tags inside the result articles
        const urls = await page.evaluate((max) => {
            const anchors = Array.from(document.querySelectorAll('article h2 a'));
            return anchors.map(a => a.href).slice(0, max);
        }, CONFIG.maxResults);

        if (urls.length === 0) {
            console.log("❌ No results found via Playwright.");
            return [];
        }

        console.log(`✅ Found ${urls.length} URLs.`);
        return urls;

    } catch (error) {
        console.error(`❌ Search failed: ${error.message}`);
        return [];
    } finally {
        if (browser) await browser.close();
    }
}

// 2. AXIOS FETCH MODULE (With Random User Agents)
async function fetchWithAxios(url) {
    console.log(`🚀 [Axios] Attempting to fetch: ${url}`);
    
    const agent = CONFIG.dynamicProxy ? new HttpsProxyAgent(CONFIG.dynamicProxy) : undefined;
    const currentUA = getRandomUserAgent();

    try {
        const response = await axios.get(url, {
            headers: {
                'User-Agent': currentUA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://duckduckgo.com/'
            },
            httpsAgent: agent,
            timeout: CONFIG.axiosTimeout,
            validateStatus: (status) => status === 200
        });
        return response.data;
    } catch (error) {
        console.warn(`⚠️ [Axios] Failed (${error.message}). Switching to fallback...`);
        return null;
    }
}

// 3. PLAYWRIGHT FETCH MODULE (Fallback for scraping)
async function fetchWithPlaywright(url) {
    console.log(`🕵️ [Playwright] Launching Stealth Browser for: ${url}`);
    
    let browser = null;
    try {
        browser = await chromium.launch({
            headless: true,
            proxy: CONFIG.dynamicProxy ? { server: CONFIG.dynamicProxy } : undefined
        });

        const page = await browser.newPage();
        await page.setViewportSize({ width: 1920, height: 1080 });
        
        // Navigate
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        
        // Simulate a small scroll to trigger lazy loading
        await page.evaluate(() => window.scrollBy(0, 500));
        await sleep(2000); 

        const content = await page.content();
        return content;

    } catch (error) {
        console.error(`❌ [Playwright] Failed: ${error.message}`);
        return null;
    } finally {
        if (browser) await browser.close();
    }
}

// 4. CHEERIO PARSING MODULE
function parseAndCleanHtml(html, url) {
    if (!html) return null;

    const $ = cheerio.load(html);

    // Remove junk elements
    $('script, style, noscript, iframe, link, svg, footer, nav, header, aside, form, button').remove();

    let textContent = [];
    
    // Extract readable text
    $('body').find('p, h1, h2, h3, h4, h5, h6, li, article').each((i, el) => {
        const text = $(el).text().replace(/\s+/g, ' ').trim(); // Normalize whitespace
        // Filter empty or very short lines (garbage text)
        if (text.length > 40) { 
            textContent.push(text);
        }
    });

    // Deduplicate lines
    const uniqueText = [...new Set(textContent)];

    return `\n--- SOURCE: ${url} ---\n` + uniqueText.join('\n');
}

// 5. FILE SAVING MODULE
function saveToTxt(data) {
    fs.appendFileSync(CONFIG.outputFile, data + '\n\n', 'utf8');
    console.log(`💾 Saved data to ${CONFIG.outputFile}`);
}

// --- MAIN EXECUTION ---
async function run() {
    const query = process.argv[2] || "Future of AI in 2025";
    
    // Clear output file
    if (fs.existsSync(CONFIG.outputFile)) fs.unlinkSync(CONFIG.outputFile);

    // 1. Search (Using Playwright now)
    const urls = await getDuckDuckGoResults(query);

    // 2. Scrape loop
    for (const url of urls) {
        await sleep(randomDelay());

        // Try Axios first
        let html = await fetchWithAxios(url);

        // Fallback to Playwright if Axios fails
        if (!html) {
            html = await fetchWithPlaywright(url);
        }

        // Process
        if (html) {
            const cleanedText = parseAndCleanHtml(html, url);
            saveToTxt(cleanedText);
        } else {
            console.error(`❌ Could not retrieve content for ${url}`);
        }
    }
    
    console.log(`\n✨ Job Complete. Check ${CONFIG.outputFile}`);
}

run();