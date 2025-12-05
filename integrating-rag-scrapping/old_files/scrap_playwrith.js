/**
 * Safe Search & Scrape Tool (Playwright ONLY Edition)
 * * Advantages: Higher success rate, handles JS sites perfectly.
 * * Disadvantages: Slower, uses more RAM.
 */

const fs = require('fs');
const cheerio = require('cheerio');
// Removed Axios and User-Agents (Playwright handles this)
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

// --- CONFIGURATION ---
const CONFIG = {
    outputFile: 'context.txt',
    dynamicProxy: null, 
    maxResults: 5,
    delayBetweenRequests: [3000, 6000] 
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
        await page.close(); // Close tab, keep browser open
    }
}

// 2. SCRAPE MODULE (Playwright Only)
async function fetchWithPlaywright(url, browser) {
    console.log(`🕵️ [Playwright] scraping: ${url}`);
    const page = await browser.newPage();
    
    try {
        await page.route('**/*.{png,jpg,jpeg,gif,svg,woff,woff2}', route => route.abort());
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await sleep(2000);

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
    fs.appendFileSync(CONFIG.outputFile, data + '\n\n', 'utf8');
    console.log(`💾 Saved data.`);
}

// --- MAIN ---
// *** MODIFIED TO SUPPORT MULTIPLE QUERIES ***
async function run() {
    const queries = process.argv.slice(2);   // ← now supports multiple searches
    if (queries.length === 0) queries.push("Future of AI");

    if (fs.existsSync(CONFIG.outputFile)) fs.unlinkSync(CONFIG.outputFile);

    console.log("🔥 Launching Browser Engine...");
    const browser = await chromium.launch({
        headless: true,
        proxy: CONFIG.dynamicProxy ? { server: CONFIG.dynamicProxy } : undefined
    });

    try {
        // Loop through ALL queries
        for (const query of queries) {
            console.log(`\n==============================`);
            console.log(`🔎 QUERY: ${query}`);
            console.log(`==============================`);

            // 1. Search
            const urls = await getDuckDuckGoResults(query, browser);

            // 2. Scrape each result
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
    
    console.log(`\n✨ Job Complete. Check ${CONFIG.outputFile}`);
}

run();
