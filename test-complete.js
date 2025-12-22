const puppeteer = require('puppeteer');

async function testFlask(browser) {
  console.log('\n=== FLASK APP (5025) ===');
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  try {
    await page.goto('http://192.168.2.38:5025/', { waitUntil: 'networkidle2', timeout: 15000 });
    const hasRecipes = await page.evaluate(() => document.body.innerText.includes('Recipe'));
    console.log('Home page loads:', hasRecipes ? 'OK' : 'FAIL');

    // Click a recipe
    await page.evaluate(() => {
      const links = document.querySelectorAll('a[href*="recipe"]');
      if (links.length > 0) links[0].click();
    });
    await page.waitForTimeout(2000);

    const hasDetail = await page.evaluate(() =>
      document.body.innerText.includes('Ingredient') || document.body.innerText.includes('Step')
    );
    console.log('Recipe detail:', hasDetail ? 'OK' : 'FAIL');

    return hasRecipes && hasDetail;
  } catch (e) {
    console.log('Flask FAILED:', e.message);
    return false;
  } finally {
    await page.close();
  }
}

async function testExpo(browser) {
  console.log('\n=== EXPO APP (8081) ===');
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  try {
    await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Check home page
    const hasTabs = await page.evaluate(() =>
      document.body.innerText.includes('My Recipes') && document.body.innerText.includes('Discover')
    );
    console.log('Source tabs:', hasTabs ? 'OK' : 'FAIL');

    const hasRecipes = await page.evaluate(() => document.body.innerText.includes('Cuisine'));
    console.log('MealDB recipes:', hasRecipes ? 'OK' : 'FAIL');

    // Click a recipe card
    const card = await page.evaluate(() => {
      const all = document.querySelectorAll('div');
      for (const el of all) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 170 && rect.width < 190 && rect.height > 260 && rect.height < 280) {
          if (el.innerText?.includes('Cuisine')) {
            return { x: rect.left + rect.width/2, y: rect.top + rect.height/2 };
          }
        }
      }
      return null;
    });

    if (card) {
      await page.mouse.click(card.x, card.y);
      await page.waitForTimeout(3000);

      const hasDetail = await page.evaluate(() =>
        document.body.innerText.includes('Ingredient') && document.body.innerText.includes('Instruction')
      );
      console.log('Recipe navigation:', hasDetail ? 'OK' : 'FAIL');

      return hasTabs && hasRecipes && hasDetail;
    }

    console.log('Recipe navigation: Could not find card');
    return false;
  } catch (e) {
    console.log('Expo FAILED:', e.message);
    return false;
  } finally {
    await page.close();
  }
}

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
  });

  const flask = await testFlask(browser);
  const expo = await testExpo(browser);

  console.log('\n========== SUMMARY ==========');
  console.log('Flask (5025):', flask ? 'PASSED' : 'FAILED');
  console.log('Expo (8081):', expo ? 'PASSED' : 'FAILED');
  console.log('Feature parity:', (flask && expo) ? 'ACHIEVED' : 'NOT YET');
  console.log('==============================');

  await new Promise(r => setTimeout(r, 5000));
  await browser.close();
})();
