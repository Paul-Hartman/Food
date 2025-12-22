const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console Error:', msg.text());
    }
  });

  page.on('pageerror', error => {
    console.log('Page Error:', error.message);
  });

  console.log('Loading Expo web app...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);

  console.log('Looking for recipe cards...');

  // Find and click the first recipe card
  const clicked = await page.evaluate(() => {
    // Find clickable elements that contain recipe names
    const allText = document.body.innerText;
    const hasRecipes = allText.includes('Bubble');

    // Try to find a touchable/clickable element
    const touchables = document.querySelectorAll('[role="button"]');
    if (touchables.length > 0) {
      console.log('Found', touchables.length, 'touchable elements');
      // Click the first recipe card (skip filter buttons)
      for (let i = 0; i < touchables.length; i++) {
        const text = touchables[i].innerText;
        if (text.includes('Time') && text.includes('Serves')) {
          touchables[i].click();
          return { clicked: true, text: text.substring(0, 100) };
        }
      }
    }
    return { clicked: false, count: touchables.length };
  });

  console.log('Click result:', clicked);
  await page.waitForTimeout(5000);

  // Take screenshot and get content
  const info = await page.evaluate(() => {
    return {
      url: window.location.href,
      title: document.title,
      bodyHeight: document.body.scrollHeight,
      bodyText: document.body.innerText.substring(0, 2000),
    };
  });

  console.log('\n=== AFTER CLICKING RECIPE ===');
  console.log('URL:', info.url);
  console.log('Title:', info.title);
  console.log('Body height:', info.bodyHeight);
  console.log('Body text:', info.bodyText);

  await page.screenshot({ path: 'expo-detail-test.png', fullPage: true });
  console.log('\nScreenshot saved: expo-detail-test.png');

  console.log('\nBrowser open 15 seconds...');
  await page.waitForTimeout(15000);
  await browser.close();
})();