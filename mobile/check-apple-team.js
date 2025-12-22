const puppeteer = require('puppeteer');

(async () => {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1920, height: 1080 }
  });

  const page = await browser.newPage();

  console.log('Navigating to Apple Developer account page...');
  await page.goto('https://developer.apple.com/account', { waitUntil: 'networkidle2' });

  // Wait a bit for any redirects or page loads
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Take screenshot of current page
  console.log('Taking screenshot...');
  await page.screenshot({ path: 'apple-account-status.png', fullPage: true });
  console.log('Screenshot saved as: apple-account-status.png');

  // Try to find Team ID on the page
  const pageText = await page.evaluate(() => document.body.innerText);

  // Look for Team ID pattern (usually 10 uppercase alphanumeric characters)
  const teamIdMatch = pageText.match(/Team ID[:\s]+([A-Z0-9]{10})/i);
  const personalTeamMatch = pageText.match(/Personal Team/i);
  const membershipMatch = pageText.match(/Membership/i);

  console.log('\n=== Apple Developer Account Status ===');

  if (teamIdMatch) {
    console.log('✅ TEAM ID FOUND:', teamIdMatch[1]);
    console.log('\nYou can now run the build command!');
  } else if (personalTeamMatch || membershipMatch) {
    console.log('⏳ Account page loaded, but Team ID not found yet');
    console.log('   This is normal - Apple is still creating your team');
    console.log('   Check the screenshot to see current status');
  } else {
    console.log('⏳ Waiting for login or account setup...');
    console.log('   The browser is still open - please log in manually');
    console.log('   Check the screenshot after logging in');
  }

  console.log('\nBrowser will stay open for 60 seconds so you can check manually...');
  await new Promise(resolve => setTimeout(resolve, 60000));

  // Take another screenshot before closing
  await page.screenshot({ path: 'apple-account-final.png', fullPage: true });
  console.log('Final screenshot saved as: apple-account-final.png');

  await browser.close();
  console.log('\nDone! Check the screenshots in Food/mobile/ folder');
})();
