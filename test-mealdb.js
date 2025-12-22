const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.setCacheEnabled(false);
  await page.setViewport({ width: 1200, height: 900 });

  // Go to the specific MealDB recipe (Beef and Oyster Pie)
  console.log('Loading Beef and Oyster Pie (MealDB recipe 52878)...');
  await page.goto('http://localhost:5025/recipe/mealdb/52878', { waitUntil: 'networkidle2', timeout: 15000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'mealdb-test-1-initial.png' });
  console.log('Screenshot 1: Initial page');

  // Check for serving controls
  const controls = await page.evaluate(() => {
    return {
      hasServingControl: document.querySelector('.serving-control') !== null,
      hasServingBtns: document.querySelectorAll('.serving-btn').length,
      servingValue: document.querySelector('.serving-value')?.textContent,
      allButtons: Array.from(document.querySelectorAll('button')).map(b => b.textContent?.trim()).filter(t => t)
    };
  });
  console.log('Serving controls:', controls);

  // Check for pinch ingredients
  const ingredients = await page.evaluate(() => {
    const amounts = document.querySelectorAll('.ingredient-amount');
    return Array.from(amounts).map(el => el.textContent?.trim()).filter(t => t);
  });
  console.log('All ingredient amounts:', ingredients);

  // Check current servings
  const currentServings = await page.evaluate(() => {
    const el = document.querySelector('.serving-value');
    return el?.textContent || 'not found';
  });
  console.log('Current servings:', currentServings);

  // Try to click + button if it exists
  const plusBtnExists = await page.evaluate(() => {
    const btns = document.querySelectorAll('.serving-btn');
    for (const btn of btns) {
      if (btn.textContent?.includes('+')) {
        btn.click();
        return true;
      }
    }
    return false;
  });

  if (plusBtnExists) {
    console.log('\nClicked + button, waiting...');
    await page.waitForTimeout(500);

    // Click 7 more times to go from 4 to 12 servings (3x multiplier)
    for (let i = 0; i < 7; i++) {
      await page.evaluate(() => {
        const btns = document.querySelectorAll('.serving-btn');
        for (const btn of btns) {
          if (btn.textContent?.includes('+')) {
            btn.click();
            return;
          }
        }
      });
      await page.waitForTimeout(200);
    }

    await page.screenshot({ path: 'mealdb-test-2-scaled.png' });
    console.log('Screenshot 2: After scaling');

    const scaledIngredients = await page.evaluate(() => {
      const amounts = document.querySelectorAll('.ingredient-amount');
      return Array.from(amounts).map(el => el.textContent?.trim()).filter(t => t);
    });
    console.log('Scaled ingredient amounts:', scaledIngredients);

    const newServings = await page.evaluate(() => {
      const el = document.querySelector('.serving-value');
      return el?.textContent || 'not found';
    });
    console.log('New servings:', newServings);
  } else {
    console.log('No + button found!');
  }

  console.log('\nBrowser open for 15 seconds...');
  await page.waitForTimeout(15000);

  await browser.close();
  console.log('Done!');
})();
