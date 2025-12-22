const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  page.on('console', msg => console.log('Console:', msg.type(), msg.text().substring(0, 200)));
  page.on('pageerror', err => console.log('Page error:', err.message));
  page.on('requestfailed', req => console.log('Request failed:', req.url()));

  console.log('Loading Expo app...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(5000);

  // Get page content
  const content = await page.evaluate(() => {
    return {
      text: document.body.innerText.substring(0, 2000),
      buttons: Array.from(document.querySelectorAll('[role="button"]')).map(b => b.innerText.substring(0, 50)),
    };
  });

  console.log('\n=== PAGE TEXT ===');
  console.log(content.text);
  console.log('\n=== BUTTONS ===');
  content.buttons.forEach(b => console.log('-', b.replace(/\n/g, ' | ')));

  await page.screenshot({ path: 'expo-mealdb-debug.png', fullPage: true });
  console.log('\nScreenshot: expo-mealdb-debug.png');

  console.log('\nKeeping browser open 20 seconds...');
  await page.waitForTimeout(20000);
  await browser.close();
})();
