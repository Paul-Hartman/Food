const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  // Listen to console messages
  page.on('console', msg => {
    console.log('BROWSER LOG:', msg.type(), msg.text());
  });

  // Listen to network requests
  page.on('requestfailed', request => {
    console.log('REQUEST FAILED:', request.url(), request.failure().errorText);
  });

  // Listen to errors
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });

  console.log('Navigating to http://localhost:19006...');
  await page.goto('http://localhost:19006', { waitUntil: 'networkidle2', timeout: 60000 });

  console.log('\nWaiting 10 seconds to see what loads...');
  await page.waitForTimeout(10000);

  // Get the page content to see what's rendered
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('\n=== PAGE CONTENT ===');
  console.log(bodyText.substring(0, 500));

  console.log('\nDone. Check the browser window.');
  // Don't close so you can inspect
  // await browser.close();
})();
