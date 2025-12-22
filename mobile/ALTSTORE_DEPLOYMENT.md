# AltStore Deployment Guide for Food App

Complete guide to build and install the Food app on your iPhone via AltStore.

---

## Prerequisites

### On Your Mac:
1. **Node.js and npm** installed
2. **Xcode** installed (from Mac App Store)
3. **AltServer** installed (https://altstore.io)
4. **Apple ID** (free account works)

### On Your iPhone:
1. **AltStore** installed (follow https://altstore.io installation guide)
2. Same WiFi network as your Mac

---

## Step 1: Clone and Setup (Mac)

```bash
# Clone the repo
git clone https://github.com/Paul-Hartman/Food.git
cd Food/mobile

# Install dependencies
npm install

# Login to Expo (first time only)
npx eas login
```

---

## Step 2: Build the IPA File

### Option A: Local Build on Mac (Recommended)

```bash
npm run build:altstore
```

**What this does:**
- Builds the iOS app on your Mac
- Creates an `.ipa` file
- Signs it with your Apple ID credentials
- Outputs: `Food/mobile/build-[timestamp].ipa`

**If prompted for credentials:**
- Enter your Apple ID email
- Enter app-specific password (see below how to create)

### Option B: Cloud Build (If Local Fails)

```bash
npm run build:altstore:cloud
```

**What this does:**
- Uploads code to Expo's servers
- Builds in the cloud
- Downloads the `.ipa` when complete

---

## Step 3: Create App-Specific Password

**Required for signing the IPA with your Apple ID:**

1. Go to https://appleid.apple.com
2. Sign in with your Apple ID
3. Go to **Security** section
4. Click **App-Specific Passwords**
5. Click **Generate an app-specific password**
6. Name it: "Food App Build"
7. Copy the password (format: `xxxx-xxxx-xxxx-xxxx`)
8. Save it - you'll need this when building

---

## Step 4: Install via AltStore

### Method 1: WiFi Installation (Easiest)

1. **On Mac:** Make sure AltServer is running (menu bar icon)
2. **On iPhone:**
   - Open AltStore
   - Tap **My Apps**
   - Tap **+** icon (top left)
   - Tap **Install .ipa**
3. **On Mac:**
   - AltServer will show a file picker
   - Select the `.ipa` file from `Food/mobile/`
   - Wait for installation (1-2 minutes)

### Method 2: Manual Copy via Finder

1. Connect iPhone to Mac via USB
2. Open **Finder**
3. Select your iPhone in sidebar
4. Drag the `.ipa` file to the iPhone
5. Open **AltStore** on iPhone
6. Tap **My Apps**
7. Find "Food App" and tap **Install**

---

## Step 5: Trust the App

**First time launching:**

1. Open the Food app
2. You'll see: "Untrusted Developer"
3. Go to **Settings** > **General** > **VPN & Device Management**
4. Find your Apple ID
5. Tap **Trust "Your Name"**
6. Confirm **Trust**
7. Return to home screen and launch Food app

---

## Troubleshooting

### Build Fails: "No valid code signing identity"

**Fix:**
```bash
# Install Xcode command line tools
xcode-select --install

# Open Xcode and agree to license
sudo xcodebuild -license accept
```

### Build Fails: "Provisioning profile error"

**Fix:** The app is configured for local signing. Make sure you're using:
```bash
npm run build:altstore  # Uses local signing
```

NOT:
```bash
npm run build:altstore:cloud  # Requires Expo credentials
```

### App Crashes on Launch

**Fix:** Rebuild with simulator disabled (already configured):
```bash
# This is already in eas.json:
"simulator": false
```

### AltStore Says "App Already Installed"

**Fix:**
1. Delete the existing Food app from iPhone
2. Reinstall via AltStore

### "Unable to Verify App" on iPhone

**Fix:**
1. Go to **Settings** > **General** > **Date & Time**
2. Turn OFF **Set Automatically**
3. Set date to 1-2 days in the past
4. Launch the app
5. Turn **Set Automatically** back ON

---

## Re-signing (Every 7 Days)

**Free Apple IDs expire after 7 days.** To keep using the app:

### Option 1: Auto-Refresh (Recommended)

1. Keep AltServer running on your Mac
2. Keep iPhone on same WiFi
3. AltStore will auto-refresh in the background

### Option 2: Manual Refresh

1. Open AltStore on iPhone
2. Go to **My Apps**
3. Find Food App
4. Tap **Refresh**

### Option 3: Rebuild

```bash
cd Food/mobile
npm run build:altstore
# Then reinstall via AltStore
```

---

## Quick Reference

| Command | What It Does |
|---------|-------------|
| `npm install` | Install dependencies |
| `npm run build:altstore` | Build IPA locally on Mac |
| `npm run build:altstore:cloud` | Build IPA in Expo cloud |
| `npx eas login` | Login to Expo account |
| `npx eas build:list` | Show build history |

---

## Configuration Details

**Bundle ID:** `com.paulhartman.foodapp`
**App Name:** Food App
**Version:** 1.0.0
**Signing:** Internal distribution (no App Store)

---

## Next Steps After Installation

1. **Backend Setup:** Make sure Flask backend is running on your network
2. **API URL:** App is configured to connect to `http://192.168.2.38:5025`
3. **Update API URL:** If your Mac has a different IP, update in `mobile/app.json`:
   ```json
   "extra": {
     "apiUrl": "http://YOUR_MAC_IP:5025"
   }
   ```
4. **Rebuild** if you change the API URL

---

## Tips

- **Keep AltServer running** for auto-refresh
- **Builds take 10-30 minutes** depending on method
- **Free Apple ID = 7 day limit**, paid Apple Developer = 1 year
- **3 app limit** on free Apple ID (delete old apps if needed)
- **Use WiFi installation** - faster than USB

---

## Getting Help

**Build issues?**
```bash
# Check EAS status
npx eas build:list

# View build logs
npx eas build:view [BUILD_ID]
```

**AltStore issues?**
- Visit https://altstore.io/faq
- Check AltServer is running on Mac
- Verify iPhone and Mac on same WiFi

---

## Summary

```bash
# On Mac:
git clone https://github.com/Paul-Hartman/Food.git
cd Food/mobile
npm install
npm run build:altstore

# On iPhone via AltStore:
My Apps > + > Install .ipa > Select the .ipa file

# Trust the app:
Settings > General > VPN & Device Management > Trust
```

That's it! You now have the Food app running on your iPhone via AltStore.
