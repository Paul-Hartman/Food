const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('ERROR:', msg.text());
    }
  });

  console.log('Loading Expo web app...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);

  console.log('Taking screenshot of recipes page...');
  await page.screenshot({ path: 'expo-recipes.png' });

  // Get the position of the first recipe card (Bubble & Squeak)
  const cardPosition = await page.evaluate(() => {
    const allElements = document.querySelectorAll('*');
    for (const el of allElements) {
      if (el.innerText && el.innerText.includes('Bubble & Squeak') && el.innerText.includes('Time')) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 100 && rect.height > 100) {
          return { x: rect.left + rect.width/2, y: rect.top + rect.height/2, w: rect.width, h: rect.height };
        }
      }
    }
    return null;
  });

  console.log('Card position:', cardPosition);

  if (cardPosition) {
    // Use Puppeteer's native click
    console.log('Clicking at', cardPosition.x, cardPosition.y);
    await page.mouse.click(cardPosition.x, cardPosition.y);
    await page.waitForTimeout(3000);
  }

  const afterClick = await page.evaluate(() => {
    return {
      url: window.location.href,
      title: document.title,
      text: document.body.innerText.substring(0, 1000)
    };
  });

  console.log('\n=== AFTER CLICK ===');
  console.log('Title:', afterClick.title);
  console.log('Text preview:', afterClick.text.substring(0, 500));

  await page.screenshot({ path: 'expo-after-click.png', fullPage: true });
  console.log('\nScreenshot saved: expo-after-click.png');

  console.log('\nKeeping browser open 20 seconds...');
  await page.waitForTimeout(20000);
  await browser.close();
})();
