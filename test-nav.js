const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 900 });

  // Check recipes list page
  console.log('Checking recipes list...');
  await page.goto('http://localhost:5025/', { waitUntil: 'networkidle2' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'test-recipes-list.png' });

  // Click on first recipe
  console.log('Clicking first recipe...');
  const clicked = await page.evaluate(() => {
    const link = document.querySelector('a[href*="/recipe/"]');
    if (link) {
      link.click();
      return link.href;
    }
    return null;
  });
  console.log('Clicked:', clicked);

  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'test-recipe-detail.png' });
  console.log('Current URL:', page.url());

  console.log('Browser open for 10 seconds...');
  await page.waitForTimeout(10000);

  await browser.close();
})();
