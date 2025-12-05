/**
 * scrap_playwrith1.js
 * modified to accept output filename as argument
 */

const fs = require('fs');
const cheerio = require('cheerio');
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

// --- CLI ARGUMENT PARSING ---
// Usage: node scrap_playwrith1.js <output_filename> <query1> <query2> ...
const args = process.argv.slice(2);

if (args.length < 1) {
    console.error("Usage: node scrap_playwrith1.js <output_filename> <query1> [query2] ...");
    process.exit(1);
}

const TARGET_FILE = args[0];
const SEARCH_QUERIES = args.slice(1);

// --- CONFIGURATION ---
const CONFIG = {
    outputFile: TARGET_FILE, // Set dynamically from args
    dynamicProxy: null, 
    maxResults: 3,           // Reduced slightly for speed since we do multiple queries
    delayBetweenRequests: [2000, 4000] 
};

// --- HELPER FUNCTIONS ---
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
const randomDelay = () => {
    const min = CONFIG.delayBetweenRequests[0];
    const max = CONFIG.delayBetweenRequests[1];
    return Math.floor(Math.random() * (max - min + 1) + min);
};

// 1. SEARCH MODULE
async function getDuckDuckGoResults(query, browser) {
    console.log(`🔍 Searching DuckDuckGo for: "${query}"...`);
    const page = await browser.newPage();
    
    try {
        await page.goto('https://duckduckgo.com/', { waitUntil: 'networkidle' });
        await page.fill('input[name="q"]', query);
        await page.press('input[name="q"]', 'Enter');
        await page.waitForSelector('article', { timeout: 15000 });

        const urls = await page.evaluate((max) => {
            const anchors = Array.from(document.querySelectorAll('article h2 a'));
            return anchors.map(a => a.href).slice(0, max);
        }, CONFIG.maxResults);

        console.log(`✅ Found ${urls.length} URLs.`);
        return urls;
    } catch (error) {
        console.error(`❌ Search failed: ${error.message}`);
        return [];
    } finally {
        await page.close(); 
    }
}

// 2. SCRAPE MODULE
async function fetchWithPlaywright(url, browser) {
    console.log(`🕵️ [Playwright] scraping: ${url}`);
    const page = await browser.newPage();
    
    try {
        await page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2}', route => route.abort());
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 }); // Reduced timeout
        await sleep(1500);

        const content = await page.content();
        return content;
    } catch (error) {
        console.error(`❌ Failed to load ${url}: ${error.message}`);
        return null;
    } finally {
        await page.close();
    }
}

// 3. CLEANING MODULE
function parseAndCleanHtml(html, url) {
    if (!html) return null;
    const $ = cheerio.load(html);
    $('script, style, noscript, iframe, link, svg, footer, nav, header, aside, form, button').remove();
    
    let textContent = [];
    $('body').find('p, h1, h2, h3, h4, h5, h6, li, article').each((i, el) => {
        const text = $(el).text().replace(/\s+/g, ' ').trim();
        if (text.length > 40) textContent.push(text);
    });
    return `\n--- SOURCE: ${url} ---\n` + [...new Set(textContent)].join('\n');
}

function saveToTxt(data) {
    // Ensure directory exists if path contains folders
    const dir = CONFIG.outputFile.substring(0, CONFIG.outputFile.lastIndexOf('/'));
    if (dir && !fs.existsSync(dir)){
        fs.mkdirSync(dir, { recursive: true });
    }

    fs.appendFileSync(CONFIG.outputFile, data + '\n\n', 'utf8');
    console.log(`💾 Saved data to ${CONFIG.outputFile}`);
}

// --- MAIN ---
async function run() {
    // Fallback if no queries passed
    if (SEARCH_QUERIES.length === 0) {
        console.log("⚠️ No queries provided. Exiting.");
        return;
    }

    // Reset file
    if (fs.existsSync(CONFIG.outputFile)) {
        fs.unlinkSync(CONFIG.outputFile);
    }

    console.log("🔥 Launching Browser Engine...");
    const browser = await chromium.launch({
        headless: true,
        proxy: CONFIG.dynamicProxy ? { server: CONFIG.dynamicProxy } : undefined
    });

    try {
        for (const query of SEARCH_QUERIES) {
            console.log(`\n==============================`);
            console.log(`🔎 QUERY: ${query}`);
            console.log(`==============================`);

            const urls = await getDuckDuckGoResults(query, browser);

            for (const url of urls) {
                await sleep(randomDelay());
                const html = await fetchWithPlaywright(url, browser);
                if (html) {
                    const cleanedText = parseAndCleanHtml(html, url);
                    saveToTxt(cleanedText);
                }
            }
        }
    } finally {
        console.log("🛑 Closing Browser Engine...");
        await browser.close();
    }
    
    console.log(`\n✨ Job Complete. Context saved to: ${CONFIG.outputFile}`);
}

run();