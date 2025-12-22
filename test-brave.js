const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  console.log('Testing in BRAVE browser...');
  await page.goto('http://localhost:5025/recipe/mealdb/52878', { waitUntil: 'networkidle2' });
  await page.waitForTimeout(3000);

  // Get what's actually visible
  const info = await page.evaluate(() => {
    const header = document.querySelector('.recipe-header');
    const grid = document.querySelector('.recipe-grid');
    return {
      url: window.location.href,
      title: document.title,
      hasHeader: header !== null,
      hasIngredients: grid !== null,
      headerHeight: header ? header.offsetHeight : 0,
      bodyText: document.body.innerText.substring(0, 400)
    };
  });

  console.log('URL:', info.url);
  console.log('Title:', info.title);
  console.log('Has header:', info.hasHeader);
  console.log('Has ingredients:', info.hasIngredients);
  console.log('Header height:', info.headerHeight);
  console.log('Body text:', info.bodyText);

  await page.screenshot({ path: 'brave-test.png', fullPage: true });
  console.log('\nScreenshot saved: brave-test.png');

  console.log('\nBrowser open 15 seconds - compare with your Brave window...');
  await page.waitForTimeout(15000);
  await browser.close();
})();