const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  // Capture ALL console messages
  page.on('console', msg => console.log('CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url(), req.failure()?.errorText));

  console.log('Loading Expo...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(5000);

  console.log('\n=== BEFORE CLICK ===');
  await page.screenshot({ path: 'debug-1-before.png' });

  // Find and click the first recipe card
  const card = await page.evaluate(() => {
    const all = document.querySelectorAll('div');
    for (const el of all) {
      const rect = el.getBoundingClientRect();
      if (rect.width > 170 && rect.width < 190 && rect.height > 260 && rect.height < 280) {
        if (el.innerText?.includes('Cuisine')) {
          return {
            x: rect.left + rect.width/2,
            y: rect.top + rect.height/2,
            text: el.innerText.substring(0, 100)
          };
        }
      }
    }
    return null;
  });

  console.log('Card found:', card?.text);

  if (card) {
    console.log('\nClicking at', card.x, card.y);
    await page.mouse.click(card.x, card.y);

    // Wait and check for navigation
    await page.waitForTimeout(5000);

    console.log('\n=== AFTER CLICK ===');
    const afterContent = await page.evaluate(() => ({
      url: window.location.href,
      bodyText: document.body.innerText.substring(0, 1500),
      hasImage: !!document.querySelector('img'),
      imageCount: document.querySelectorAll('img').length,
    }));

    console.log('URL:', afterContent.url);
    console.log('Image count:', afterContent.imageCount);
    console.log('Body text:', afterContent.bodyText);

    await page.screenshot({ path: 'debug-2-after.png', fullPage: true });
  }

  console.log('\nBrowser open 30 seconds for manual inspection...');
  await page.waitForTimeout(30000);
  await browser.close();
})();
