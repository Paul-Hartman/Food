const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 900 });

  // Go to recipes page first
  console.log('Loading recipes page...');
  await page.goto('http://localhost:5025/recipes', { waitUntil: 'networkidle2' });
  await page.screenshot({ path: 'test-1-recipes.png' });
  console.log('Screenshot 1: Recipes page');

  // Find "Beef and Oyster Pie" or any recipe with pinch
  console.log('Looking for Beef and Oyster Pie...');

  // Search for a recipe
  const searchInput = await page.$('input[type="search"], input[placeholder*="search" i], #search');
  if (searchInput) {
    await searchInput.type('Beef and Oyster');
    await page.waitForTimeout(1000);
  }

  await page.screenshot({ path: 'test-2-search.png' });
  console.log('Screenshot 2: After search');

  // Click on first recipe card
  const recipeLink = await page.$('a[href*="/recipe/"]');
  if (recipeLink) {
    await recipeLink.click();
    await page.waitForNavigation({ waitUntil: 'networkidle2' });
  } else {
    // Try direct URL for a recipe
    console.log('No recipe link found, trying direct URL...');
    await page.goto('http://localhost:5025/recipe/1', { waitUntil: 'networkidle2' });
  }

  await page.screenshot({ path: 'test-3-recipe-detail.png' });
  console.log('Screenshot 3: Recipe detail page');

  // Check the page content
  const pageContent = await page.content();

  // Look for servings selector
  const hasServingsSelector = pageContent.includes('serving') || pageContent.includes('Serving');
  console.log('Has servings mention:', hasServingsSelector);

  // Look for pinch
  const hasPinch = pageContent.includes('pinch');
  console.log('Has pinch mention:', hasPinch);

  // Look for ingredients
  const ingredients = await page.$$eval('.ingredient, [class*="ingredient"], li', els =>
    els.slice(0, 10).map(e => e.textContent?.trim()).filter(t => t && t.length < 100)
  );
  console.log('Sample ingredients found:', ingredients.slice(0, 5));

  // Check if there's a scaling UI
  const scalingButtons = await page.$$('button, [role="button"]');
  console.log('Number of buttons found:', scalingButtons.length);

  // Try to find serving adjustment
  const servingText = await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent && el.textContent.toLowerCase().includes('serving') && el.children.length === 0) {
        return el.textContent;
      }
    }
    return null;
  });
  console.log('Serving text found:', servingText);

  // Check for nutrition data
  const nutritionText = await page.evaluate(() => {
    const elements = document.querySelectorAll('*');
    for (const el of elements) {
      if (el.textContent && (el.textContent.includes('Protein') || el.textContent.includes('protein'))) {
        return el.parentElement?.textContent?.substring(0, 200);
      }
    }
    return null;
  });
  console.log('Nutrition text:', nutritionText?.substring(0, 100));

  // Wait for user to see
  console.log('\nBrowser will stay open for 30 seconds...');
  await page.waitForTimeout(30000);

  await browser.close();
  console.log('Done!');
})();
