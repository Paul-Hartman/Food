const puppeteer = require('puppeteer');

(async () => {
  console.log('🚀 Launching browser...');
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1920, height: 1080 }
  });

  const page = await browser.newPage();

  console.log('📱 Opening Apple Developer account page...');
  await page.goto('https://developer.apple.com/account', { waitUntil: 'networkidle2' });

  console.log('\n⏳ PLEASE LOG IN NOW with your Apple ID: paul.hartman222@gmail.com');
  console.log('   I will wait up to 5 minutes for you to complete login...\n');

  // Wait for login - check every 5 seconds for up to 5 minutes
  let loggedIn = false;
  let attempts = 0;
  const maxAttempts = 60; // 5 minutes

  while (!loggedIn && attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 5000));
    attempts++;

    try {
      const pageText = await page.evaluate(() => document.body.innerText);

      // Check if we're logged in by looking for common post-login text
      if (pageText.includes('Team ID') ||
          pageText.includes('Membership') ||
          pageText.includes('Certificates') ||
          pageText.includes('Account Holder')) {
        loggedIn = true;
        console.log('✅ Detected you\'re logged in!');
        break;
      } else {
        process.stdout.write(`\rWaiting... (${attempts * 5} seconds elapsed)`);
      }
    } catch (e) {
      // Page might be navigating, continue waiting
    }
  }

  if (!loggedIn) {
    console.log('\n\n❌ Timeout - You didn\'t log in within 5 minutes');
    console.log('Please run this script again and log in faster');
    await browser.close();
    return;
  }

  console.log('\n\n🔍 Searching for Team ID...');
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Take screenshot of account page
  await page.screenshot({ path: 'logged-in-account.png', fullPage: true });
  console.log('📸 Screenshot saved: logged-in-account.png');

  // Get all text from the page
  const pageText = await page.evaluate(() => document.body.innerText);

  // Look for Team ID in various formats
  let teamId = null;
  const patterns = [
    /Team ID[:\s]+([A-Z0-9]{10})/i,
    /Team[:\s]+([A-Z0-9]{10})/i,
    /\(([A-Z0-9]{10})\)/,  // Sometimes shown in parentheses
  ];

  for (const pattern of patterns) {
    const match = pageText.match(pattern);
    if (match && match[1]) {
      teamId = match[1];
      break;
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('APPLE DEVELOPER ACCOUNT STATUS');
  console.log('='.repeat(60));

  if (teamId) {
    console.log('✅ SUCCESS! Team ID Found: ' + teamId);
    console.log('\n🎉 Your Apple Developer team is ready!');
    console.log('\n📝 NEXT STEP: Run this command to build your app:');
    console.log('\ncd "C:\\Users\\paulh\\Documents\\Lotus-Eater Machine\\Food\\mobile"');
    console.log('npx eas build --platform ios --profile altstore\n');
  } else {
    console.log('⏳ Team ID not found yet');
    console.log('\nPossible reasons:');
    console.log('1. Apple is still creating your Personal Team (wait 10-30 more minutes)');
    console.log('2. You need to complete enrollment steps');
    console.log('\nCheck the screenshot: logged-in-account.png');
    console.log('Look for any prompts or agreements you need to accept\n');
  }

  console.log('='.repeat(60));
  console.log('\n⏸️  Browser will stay open for 30 seconds so you can review...');
  await new Promise(resolve => setTimeout(resolve, 30000));

  await browser.close();
  console.log('✅ Done!');
})();
