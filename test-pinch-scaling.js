const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  // Disable cache
  await page.setCacheEnabled(false);
  await page.setViewport({ width: 1200, height: 900 });

  // Go directly to recipe 15 which has pinch ingredients
  console.log('Loading recipe 15 (with cache disabled)...');
  await page.goto('http://localhost:5025/recipe/15', { waitUntil: 'networkidle2', timeout: 10000 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'pinch-test-1-initial.png' });
  console.log('Screenshot 1: Initial recipe page');

  // Check if + button exists
  const hasButtons = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    return {
      total: buttons.length,
      texts: buttons.map(b => b.textContent?.trim()).filter(t => t),
      hasPlus: buttons.some(b => b.textContent?.trim() === '+'),
      hasMinus: buttons.some(b => b.textContent?.trim() === '-')
    };
  });
  console.log('Buttons found:', hasButtons);

  // Find pinch ingredients
  const initialPinch = await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('.ingredient-card-amount'));
    return elements.map(el => el.textContent?.trim());
  });
  console.log('Initial ingredient amounts:', initialPinch);

  // Find current servings
  const initialServings = await page.evaluate(() => {
    const statValue = document.querySelector('.stat-value span');
    return statValue?.textContent || document.body.innerText.match(/(\d+)\s*Servings/)?.[1] || 'not found';
  });
  console.log('Initial servings:', initialServings);

  if (hasButtons.hasPlus) {
    // Click + button 4 times
    console.log('\nClicking + button 4 times...');
    for (let i = 0; i < 4; i++) {
      await page.click('button:has-text("+")').catch(async () => {
        await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const plusBtn = buttons.find(b => b.textContent?.trim() === '+');
          if (plusBtn) plusBtn.click();
        });
      });
      await page.waitForTimeout(500);
    }

    await page.screenshot({ path: 'pinch-test-2-after-scaling.png' });
    console.log('Screenshot 2: After scaling up');

    // Check scaled values
    const scaledPinch = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('.ingredient-card-amount'));
      return elements.map(el => el.textContent?.trim());
    });
    console.log('Scaled ingredient amounts:', scaledPinch);

    const scaledServings = await page.evaluate(() => {
      const statValue = document.querySelector('.stat-value span');
      return statValue?.textContent || 'not found';
    });
    console.log('Scaled servings:', scaledServings);

    // Check if values changed
    if (initialPinch.join() !== scaledPinch.join()) {
      console.log('\n SUCCESS: Ingredient values changed after scaling!');
    } else {
      console.log('\n ISSUE: Ingredient values did NOT change');
    }
  } else {
    console.log('\n ISSUE: No + button found - template may not be updated');
  }

  console.log('\nBrowser staying open for 15 seconds...');
  await page.waitForTimeout(15000);

  await browser.close();
  console.log('Done!');
})();
