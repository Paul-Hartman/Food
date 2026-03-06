# TestFlight Deployment from PC - Complete Guide

Now that you have an Apple Developer account, you can deploy directly from your PC!

______________________________________________________________________

## Step 1: Verify Your Developer Account is Active

1. Go to https://developer.apple.com
1. Sign in with your Apple ID (`p...2@gmail.com`)
1. You should see "Account" and "Certificates, Identifiers & Profiles"
1. If you see those, **you're active!**

**If not yet active:** Wait 24-48 hours for Apple to process your membership.

______________________________________________________________________

## Step 2: Create App Store Connect Access

1. Go to https://appstoreconnect.apple.com
1. Sign in with your Apple ID
1. Click **Apps** (you'll see "No apps available")
1. This confirms your access is ready!

______________________________________________________________________

## Step 3: Configure Your App for Production

Update `eas.json` to use your Apple Developer credentials:

```json
{
  "build": {
    "production": {
      "distribution": "internal",
      "ios": {
        "simulator": false,
        "bundleIdentifier": "com.paulhartman.foodapp"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "YOUR_APPLE_ID@gmail.com",
        "ascAppId": "placeholder",
        "appleTeamId": "YOUR_TEAM_ID"
      }
    }
  }
}
```

______________________________________________________________________

## Step 4: Find Your Apple Team ID

### Option A: Via Apple Developer Portal

1. Go to https://developer.apple.com/account
1. Click **Membership** in sidebar
1. Your **Team ID** is shown (format: `ABC123DEFG`)

### Option B: Via Command Line

```bash
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\mobile"
npx eas credentials
```

______________________________________________________________________

## Step 5: Register Your App in App Store Connect

1. Go to https://appstoreconnect.apple.com

1. Click **Apps** → **+ (Add App)**

1. Fill in:

   - **Platform:** iOS
   - **Name:** Food App
   - **Primary Language:** English
   - **Bundle ID:** Select "com.paulhartman.foodapp" (or create new)
   - **SKU:** food-app-001 (can be anything unique)
   - **User Access:** Full Access

1. Click **Create**

1. Copy the **App ID** (10-digit number like `1234567890`)

______________________________________________________________________

## Step 6: Build from Your PC

```bash
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\mobile"

# Login to Expo (first time only)
npx eas login

# Build for production
npx eas build --platform ios --profile production
```

**What happens:**

- ✅ Code uploads to Expo servers
- ✅ Builds iOS .ipa file in the cloud
- ✅ Takes 15-30 minutes
- ✅ No Mac needed!

**When prompted for credentials:**

- Enter your Apple ID email
- Enter app-specific password (create at https://appleid.apple.com)
- EAS will configure everything automatically

______________________________________________________________________

## Step 7: Submit to TestFlight

**After build completes:**

```bash
# Submit to App Store Connect
npx eas submit --platform ios --profile production

# Or submit the specific build
npx eas submit --platform ios --latest
```

**What happens:**

- ✅ Uploads .ipa to App Store Connect
- ✅ Processes for TestFlight (5-10 minutes)
- ✅ Sends you email when ready

______________________________________________________________________

## Step 8: Install via TestFlight (iPhone)

1. **Install TestFlight** from App Store (free app by Apple)
1. **Get your test link:**
   - Go to https://appstoreconnect.apple.com
   - Click **Apps** → **Food App**
   - Click **TestFlight** tab
   - Click on the build under "iOS"
   - Copy the **TestFlight Public Link**
1. **Open link on iPhone** → Opens TestFlight → Click **Install**

**That's it!** App installs and stays for **90 days** (not 7 days like AltStore).

______________________________________________________________________

## Update the App (Push New Version)

```bash
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\mobile"

# Update version in app.json
# Change "version": "1.0.0" to "1.0.1"

# Build and submit
npx eas build --platform ios --profile production --auto-submit
```

**On iPhone:**

- TestFlight shows "Update Available"
- Tap **Update**
- New version installs

______________________________________________________________________

## Troubleshooting

### "No valid Apple Developer account"

**Fix:** Your membership might not be active yet. Wait 24-48 hours after payment.

**Check status:**

```bash
npx eas credentials
```

### "Bundle identifier is already in use"

**Fix:** Someone else registered `com.paulhartman.foodapp`. Change it:

In `mobile/app.json`:

```json
"ios": {
  "bundleIdentifier": "com.paulhartman.foodapp.v2"
}
```

### "Missing compliance" when submitting

**Fix:** Add export compliance to `app.json`:

```json
"ios": {
  "infoPlist": {
    "ITSAppUsesNonExemptEncryption": false
  }
}
```

### Build fails: "Provisioning profile error"

**Fix:** Let EAS manage credentials:

```bash
npx eas credentials
# Select: "Set up new credentials"
```

______________________________________________________________________

## TestFlight vs AltStore Comparison

| Feature            | TestFlight (With Developer Account) | AltStore (Free)     |
| ------------------ | ----------------------------------- | ------------------- |
| **Cost**           | $99/year                            | Free                |
| **Build from PC**  | ✅ Yes                              | ❌ No (need Mac)    |
| **Expiration**     | 90 days                             | 7 days              |
| **Re-signing**     | Every 90 days                       | Every 7 days        |
| **Install method** | TestFlight app                      | AltServer + Mac     |
| **Max devices**    | 100 devices                         | 3 apps total        |
| **Updates**        | Push from PC                        | Rebuild + reinstall |

______________________________________________________________________

## Quick Reference Commands

```bash
# Login to Expo
npx eas login

# Build for TestFlight
npx eas build --platform ios --profile production

# Submit to TestFlight
npx eas submit --platform ios --latest

# Build AND submit in one command
npx eas build --platform ios --profile production --auto-submit

# Check build status
npx eas build:list

# View build details
npx eas build:view [BUILD_ID]

# Configure credentials
npx eas credentials
```

______________________________________________________________________

## Complete Workflow Summary

```bash
# 1. Build from PC (15-30 min)
cd Food/mobile
npx eas build --platform ios --profile production

# 2. Submit to TestFlight (auto or manual)
npx eas submit --platform ios --latest

# 3. On iPhone - Install TestFlight from App Store

# 4. Open TestFlight link → Install Food App

# 5. App stays installed for 90 days!

# 6. To update: Change version in app.json, rebuild, resubmit
```

______________________________________________________________________

## Next Steps

1. ✅ Wait for Apple Developer membership to activate (check https://developer.apple.com)
1. ✅ Register app in App Store Connect
1. ✅ Run `npx eas build --platform ios --profile production`
1. ✅ Submit to TestFlight
1. ✅ Install via TestFlight on iPhone
1. ✅ Enjoy not re-signing every 7 days!

______________________________________________________________________

## Getting Help

**Build issues:**

```bash
npx eas build:list
npx eas build:view [BUILD_ID]
```

**Credential issues:**

```bash
npx eas credentials
```

**Expo docs:**

- https://docs.expo.dev/build/setup/
- https://docs.expo.dev/submit/ios/

**Apple docs:**

- https://developer.apple.com/testflight/

______________________________________________________________________

You're now set up for professional iOS deployment from your PC! 🚀
