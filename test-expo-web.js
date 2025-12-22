const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  console.log('Testing EXPO WEB app in Brave...');
  await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(5000); // Wait for React to render

  // Get what's actually visible
  const info = await page.evaluate(() => {
    return {
      url: window.location.href,
      title: document.title,
      bodyText: document.body.innerText.substring(0, 1000),
      hasRoot: document.getElementById('root') !== null,
      rootContent: document.getElementById('root')?.innerHTML?.substring(0, 500) || 'empty'
    };
  });

  console.log('URL:', info.url);
  console.log('Title:', info.title);
  console.log('Has root:', info.hasRoot);
  console.log('Body text:', info.bodyText);
  console.log('\nRoot content preview:', info.rootContent);

  await page.screenshot({ path: 'expo-web-test.png', fullPage: true });
  console.log('\nScreenshot saved: expo-web-test.png');

  // Check for errors in console
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console Error:', msg.text());
    }
  });

  console.log('\nBrowser open 15 seconds...');
  await page.waitForTimeout(15000);
  await browser.close();
})();
