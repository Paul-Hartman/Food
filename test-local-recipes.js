const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  page.on('console', msg => console.log('CONSOLE:', msg.type(), msg.text().substring(0, 150)));

  console.log('Loading Expo...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(4000);

  // Click on "My Recipes" tab
  console.log('\n=== CLICKING "MY RECIPES" TAB ===');
  await page.evaluate(() => {
    const all = document.querySelectorAll('*');
    for (const el of all) {
      if (el.innerText === 'My Recipes') {
        el.click();
        return true;
      }
    }
  });
  await page.waitForTimeout(2000);

  // Check what's visible now
  const content = await page.evaluate(() => document.body.innerText.substring(0, 800));
  console.log('After clicking My Recipes:', content);

  await page.screenshot({ path: 'local-recipes-1.png' });

  // Try to find and click a local recipe card
  const card = await page.evaluate(() => {
    const all = document.querySelectorAll('div');
    for (const el of all) {
      const rect = el.getBoundingClientRect();
      if (rect.width > 170 && rect.width < 190 && rect.height > 260 && rect.height < 280) {
        const text = el.innerText;
        if (text.includes('Time') && text.includes('Serves')) {
          return { x: rect.left + rect.width/2, y: rect.top + rect.height/2, text: text.substring(0, 80) };
        }
      }
    }
    return null;
  });

  console.log('\nFound local recipe card:', card);

  if (card) {
    console.log('Clicking at', card.x, card.y);
    await page.mouse.click(card.x, card.y);
    await page.waitForTimeout(3000);

    const after = await page.evaluate(() => document.body.innerText.substring(0, 1200));
    console.log('\n=== AFTER CLICKING LOCAL RECIPE ===');
    console.log(after);

    await page.screenshot({ path: 'local-recipes-2.png' });
  } else {
    console.log('No local recipes found');
  }

  await page.waitForTimeout(20000);
  await browser.close();
})();
