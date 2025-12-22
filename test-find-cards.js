const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(5000);

  // Find all elements with dimensions that could be cards
  const elements = await page.evaluate(() => {
    const results = [];
    const all = document.querySelectorAll('*');
    for (const el of all) {
      const rect = el.getBoundingClientRect();
      if (rect.width > 140 && rect.width < 200 && rect.height > 200 && rect.height < 300) {
        results.push({
          tag: el.tagName,
          role: el.getAttribute('role'),
          classes: el.className,
          x: rect.left + rect.width/2,
          y: rect.top + rect.height/2,
          w: rect.width,
          h: rect.height,
          text: el.innerText?.substring(0, 60),
          hasOnClick: !!el.onclick,
        });
      }
    }
    return results;
  });

  console.log('Found', elements.length, 'potential card elements:');
  elements.forEach((el, i) => {
    console.log(`${i}: ${el.tag} role=${el.role} ${el.w}x${el.h} at (${Math.round(el.x)}, ${Math.round(el.y)})`);
    console.log(`   text: ${el.text?.replace(/\n/g, ' | ')}`);
  });

  if (elements.length > 0) {
    const card = elements.find(e => e.text?.includes('Cuisine')) || elements[0];
    console.log('\nClicking card at:', card.x, card.y);
    await page.mouse.click(card.x, card.y);
    await page.waitForTimeout(3000);

    const after = await page.evaluate(() => document.body.innerText.substring(0, 500));
    console.log('\nAfter click:', after);
  }

  await page.screenshot({ path: 'find-cards-result.png', fullPage: true });
  console.log('\nScreenshot: find-cards-result.png');

  await page.waitForTimeout(15000);
  await browser.close();
})();
