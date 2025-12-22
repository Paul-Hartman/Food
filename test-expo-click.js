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
      console.log('ERROR:', msg.text());
    }
  });

  console.log('Loading Expo web app...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);

  console.log('Scrolling to find BBQ Pork Sloppy Joes...');

  // Scroll down to find BBQ Pork
  for (let i = 0; i < 5; i++) {
    await page.evaluate(() => window.scrollBy(0, 500));
    await page.waitForTimeout(500);
  }

  console.log('Looking for BBQ Pork Sloppy Joes...');

  // Click on the text directly
  const clicked = await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('*'));
    for (const el of elements) {
      if (el.innerText && el.innerText.includes('BBQ Pork Sloppy Joes') && !el.innerText.includes('What are we')) {
        // Find the closest clickable parent
        let current = el;
        for (let i = 0; i < 10; i++) {
          if (current.onclick || current.tagName === 'A' || current.getAttribute('data-testid')) {
            current.click();
            return { clicked: true, tag: current.tagName, text: current.innerText?.substring(0, 50) };
          }
          current = current.parentElement;
          if (!current) break;
        }
        // Just click the element directly
        el.click();
        return { clicked: true, tag: el.tagName, text: el.innerText?.substring(0, 50) };
      }
    }
    return { clicked: false };
  });

  console.log('Click result:', clicked);
  await page.waitForTimeout(5000);

  // Check what we see now
  const info = await page.evaluate(() => {
    return {
      url: window.location.href,
      title: document.title,
      bodyHeight: document.body.scrollHeight,
      bodyText: document.body.innerText.substring(0, 2500),
    };
  });

  console.log('\n=== AFTER CLICKING ===');
  console.log('URL:', info.url);
  console.log('Title:', info.title);
  console.log('Body height:', info.bodyHeight);
  console.log('\nBody text:\n', info.bodyText);

  await page.screenshot({ path: 'expo-click-test.png', fullPage: true });
  console.log('\nScreenshot saved: expo-click-test.png');

  console.log('\nBrowser open 15 seconds...');
  await page.waitForTimeout(15000);
  await browser.close();
})();
