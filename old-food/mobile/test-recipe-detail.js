const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting Puppeteer test...');

  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1280, height: 800 }
  });

  const page = await browser.newPage();

  // Log console messages and errors
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  try {
    console.log('Navigating to app...');
    await page.goto('http://192.168.2.38:8081', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.screenshot({ path: 'screenshot-1-homepage.png' });
    console.log('Screenshot 1: Homepage saved');

    // Wait for recipes to load
    await page.waitForTimeout(2000);

    // Look for recipe cards
    console.log('Looking for recipe cards...');
    const cards = await page.$$('[data-testid="recipe-card"], .card, [style*="cursor"]');
    console.log(`Found ${cards.length} potential cards`);

    if (cards.length === 0) {
      // Try to find any clickable elements
      const clickables = await page.$$('div[role="button"], button, a');
      console.log(`Found ${clickables.length} clickable elements`);
      await page.screenshot({ path: 'screenshot-2-no-cards.png' });
    } else {
      await page.screenshot({ path: 'screenshot-2-cards-visible.png' });
      console.log('Screenshot 2: Cards visible');

      // Click the first card
      console.log('Clicking first recipe card...');
      await cards[0].click();
      await page.waitForTimeout(2000);

      await page.screenshot({ path: 'screenshot-3-after-click.png' });
      console.log('Screenshot 3: After clicking card');

      // Wait for detail screen to load
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'screenshot-4-detail-loaded.png' });
      console.log('Screenshot 4: Detail screen loaded');

      // Check for content
      const bodyText = await page.evaluate(() => document.body.innerText);
      console.log('Page text content:', bodyText.substring(0, 500));

      // Check for errors
      const errors = await page.evaluate(() => {
        const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
        return Array.from(errorElements).map(el => el.textContent);
      });
      if (errors.length > 0) {
        console.log('Errors found:', errors);
      }
    }

  } catch (error) {
    console.error('Test error:', error);
    await page.screenshot({ path: 'screenshot-error.png' });
  }

  console.log('Test complete. Keeping browser open for 10 seconds...');
  await page.waitForTimeout(10000);

  await browser.close();
})();
