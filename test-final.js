const puppeteer = require('puppeteer');

async function testExpoNavigation(browser) {
  console.log('\n=== TESTING EXPO APP NAVIGATION ===');
  const page = await browser.newPage();
  await page.setViewport({ width: 500, height: 800 });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Error:', msg.text().substring(0, 100));
    }
  });

  try {
    await page.goto('http://localhost:8081/', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForTimeout(5000);

    // Check for recipes
    const hasRecipes = await page.evaluate(() => {
      return document.body.innerText.includes('Cuisine');
    });
    console.log('1. Recipes loaded:', hasRecipes);

    if (!hasRecipes) {
      console.log('FAILED: No recipes loaded');
      return false;
    }

    await page.screenshot({ path: 'final-1-recipes.png' });

    // Find and click a recipe card
    const cardPosition = await page.evaluate(() => {
      const cards = document.querySelectorAll('[role="button"]');
      for (const card of cards) {
        const text = card.innerText;
        if (text.includes('Cuisine') && !text.includes('What are')) {
          const rect = card.getBoundingClientRect();
          if (rect.width > 100 && rect.height > 100) {
            return { x: rect.left + rect.width/2, y: rect.top + rect.height/2, text: text.substring(0, 50) };
          }
        }
      }
      return null;
    });

    if (!cardPosition) {
      console.log('FAILED: Could not find recipe card to click');
      return false;
    }

    console.log('2. Found recipe card:', cardPosition.text);
    console.log('3. Clicking at:', cardPosition.x, cardPosition.y);

    await page.mouse.click(cardPosition.x, cardPosition.y);
    await page.waitForTimeout(3000);

    // Check if we navigated to detail
    const detailContent = await page.evaluate(() => ({
      hasIngredients: document.body.innerText.includes('Ingredient'),
      hasInstructions: document.body.innerText.includes('Instruction'),
      hasCategory: document.body.innerText.includes('Category'),
      text: document.body.innerText.substring(0, 1000),
    }));

    console.log('4. Detail page content:');
    console.log('   - Has Ingredients:', detailContent.hasIngredients);
    console.log('   - Has Instructions:', detailContent.hasInstructions);
    console.log('   - Has Category:', detailContent.hasCategory);

    await page.screenshot({ path: 'final-2-detail.png' });

    const success = detailContent.hasIngredients || detailContent.hasInstructions;
    console.log('\n5. Navigation test:', success ? 'PASSED' : 'FAILED');

    if (!success) {
      console.log('\nPage content:', detailContent.text);
    }

    return success;
  } catch (err) {
    console.log('Test FAILED:', err.message);
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

  const result = await testExpoNavigation(browser);

  console.log('\n=== FINAL RESULT ===');
  console.log('Expo App Navigation:', result ? 'PASSED' : 'FAILED');

  console.log('\nKeeping browser open 15 seconds...');
  await new Promise(r => setTimeout(r, 15000));
  await browser.close();
})();
