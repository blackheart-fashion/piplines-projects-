// Optional instructor export: install Playwright and its Chromium browser to reuse.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.WORKSHOP_PLAYWRIGHT || 'playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const output = path.join(root, 'output', 'pdf');
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true, executablePath: process.env.WORKSHOP_BROWSER || undefined,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 1000 } });
    await page.goto(pathToFileURL(path.join(root, 'dist', 'workshop-days-1-2.html')).href);
    await page.evaluate(() => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        walker.currentNode.textContent = walker.currentNode.textContent.replace(/[\u2011\u2013\u2014]/g, '-');
      }
    });
    await page.pdf({
      path: path.join(output, 'workshop-days-1-2.pdf'),
      format: 'A4', preferCSSPageSize: true, printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: '<div style="font-size:9px;width:100%;text-align:center;color:#64748b">Jenkins + Python | Days 1 and 2 | <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
    });
    console.log(path.join(output, 'workshop-days-1-2.pdf'));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exit(1); });
