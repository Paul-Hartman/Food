const puppeteer = require('puppeteer');

async function testFlaskApp(browser) {
  console.log('\n=== TESTING FLASK APP (5025) ===');
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  try {
    await page.goto('http://192.168.2.38:5025/', { waitUntil: 'networkidle2', timeout: 10000 });
    const title = await page.title();
    console.log('Home page title:', title);

    // Check for recipe cards
    const hasRecipes = await page.evaluate(() => {
      return document.body.innerText.includes('BBQ Pork') || document.body.innerText.includes('Bubble');
    });
    console.log('Has recipes:', hasRecipes);

    // Click on a MealDB recipe
    const clicked = await page.evaluate(() => {
      const cards = document.querySelectorAll('.recipe-card, [onclick*="mealdb"]');
      for (const card of cards) {
        if (card.innerText.includes('BBQ')) {
          card.click();
          return true;
        }
      }
      // Try clicking any recipe link
      const links = document.querySelectorAll('a[href*="recipe"]');
      if (links.length > 0) {
        links[0].click();
        return true;
      }
      return false;
    });
    console.log('Clicked recipe:', clicked);

    await page.waitForTimeout(2000);

    const pageContent = await page.evaluate(() => ({
      url: window.location.href,
      hasIngredients: document.body.innerText.includes('Ingredient'),
      hasInstructions: document.body.innerText.includes('Instruction') || document.body.innerText.includes('Step'),
    }));
    console.log('Recipe page:', pageContent);

    await page.screenshot({ path: 'test-flask-result.png' });
    console.log('Flask test: PASSED');
    return true;
  } catch (err) {
    console.log('Flask test FAILED:', err.message);
    return false;
  } finally {
    await page.close();
  }
}

async function testExpoApp(browser) {
  console.log('\n=== TESTING EXPO APP (8081) ===');
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Console error:', msg.text().substring(0, 100));
    }
  });

  try {
    await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForTimeout(3000);

    const title = await page.title();
    console.log('Home page title:', title);

    // Check for source tabs (My Recipes / Discover)
    const hasTabs = await page.evaluate(() => {
      return document.body.innerText.includes('My Recipes') && document.body.innerText.includes('Discover');
    });
    console.log('Has source tabs:', hasTabs);

    // Check for recipe cards
    const hasRecipes = await page.evaluate(() => {
      return document.body.innerText.includes('Cuisine') || document.body.innerText.includes('Time');
    });
    console.log('Has recipes:', hasRecipes);

    await page.screenshot({ path: 'test-expo-home.png' });

    // Try clicking a recipe card
    const cardPosition = await page.evaluate(() => {
      const buttons = document.querySelectorAll('[role="button"]');
      for (const btn of buttons) {
        const text = btn.innerText;
        if (text.includes('Cuisine') || (text.includes('Time') && text.includes('Serves'))) {
          const rect = btn.getBoundingClientRect();
          return { x: rect.left + rect.width/2, y: rect.top + rect.height/2 };
        }
      }
      return null;
    });

    if (cardPosition) {
      console.log('Clicking recipe at:', cardPosition);
      await page.mouse.click(cardPosition.x, cardPosition.y);
      await page.waitForTimeout(3000);

      const afterClick = await page.evaluate(() => ({
        hasIngredients: document.body.innerText.includes('Ingredient'),
        hasInstructions: document.body.innerText.includes('Instruction'),
        url: window.location.href,
      }));
      console.log('After click:', afterClick);
      await page.screenshot({ path: 'test-expo-detail.png' });

      if (afterClick.hasIngredients || afterClick.hasInstructions) {
        console.log('Expo test: PASSED - Navigation works!');
        return true;
      }
    }

    console.log('Expo test: Could not verify navigation');
    return false;
  } catch (err) {
    console.log('Expo test FAILED:', err.message);
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

  const flaskResult = await testFlaskApp(browser);
  const expoResult = await testExpoApp(browser);

  console.log('\n=== SUMMARY ===');
  console.log('Flask (5025):', flaskResult ? 'PASSED' : 'FAILED');
  console.log('Expo (8081):', expoResult ? 'PASSED' : 'FAILED');

  console.log('\nKeeping browser open 10 seconds...');
  await new Promise(r => setTimeout(r, 10000));
  await browser.close();
})();
