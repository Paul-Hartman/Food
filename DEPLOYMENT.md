# Food App - Deployment Guide

## Current Setup Status

✅ **GitHub Repository**: https://github.com/Paul-Hartman/Food
✅ **Apple Developer Account**: Active (Team ID: FQY22K9BK3)
✅ **App Store Connect**: App ID 6756897041
✅ **TestFlight**: Configured and working
✅ **Automated Build**: `npm run deploy` in `mobile/` directory

---

## Quick Deploy (One Command)

```bash
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\mobile"
npm run deploy
```

**What this does:**
- Builds iOS app on Expo's cloud servers (15-30 min)
- Automatically submits to TestFlight
- No Mac required!
- Email notification when ready

**After deployment:**
- Check email for Apple notification
- Open TestFlight on iPhone
- Update to new version

---

## Version Update Workflow

### 1. Make Changes to the App

Edit files in `Food/mobile/src/` as needed.

### 2. Update Version Number

Edit `mobile/app.json`:

```json
{
  "expo": {
    "version": "1.0.2"  // Increment this
  }
}
```

**Version Scheme:**
- `1.0.x` - Bug fixes, minor updates
- `1.x.0` - New features
- `x.0.0` - Major changes

### 3. Test Locally (Optional)

```bash
cd mobile
npm start
```

Scan QR code with Expo Go app on iPhone to test.

### 4. Deploy to TestFlight

```bash
npm run deploy
```

Wait 20-40 minutes for:
- Build to complete (~15-30 min)
- Apple processing (~5-10 min)
- Email notification

### 5. Update on iPhone

1. Open TestFlight app
2. Tap "Food App"
3. Tap "Update"
4. New version installs!

---

## Backend Server Management

### Starting the Flask Backend

```bash
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\backend"
python app.py
```

**Server runs on:**
- Local: http://127.0.0.1:5025
- Network: http://192.168.2.38:5025 (accessible from iPhone on same WiFi)

### Automatic Startup (TODO)

See `AUTOMATION_PLAN.md` for automatic backend startup options.

---

## Network Configuration

### Current Setup

**App Configuration** (`mobile/app.json`):
```json
"extra": {
  "apiUrl": "http://192.168.2.38:5025"
}
```

**Important:**
- iPhone must be on same WiFi network as PC
- If PC IP changes, update `apiUrl` and redeploy

### Checking Your PC's IP

```bash
ipconfig | findstr "IPv4"
```

Look for the `192.168.x.x` address.

---

## Automated Commands Reference

| Command | Purpose | Time |
|---------|---------|------|
| `npm run deploy` | Build & submit to TestFlight | 20-40 min |
| `npm run deploy:check` | Check recent build status | Instant |
| `npm run start` | Start Expo dev server | Instant |

---

## Common Issues

### Build Fails with Package Errors

**Fix:**
```bash
cd mobile
npm install
npm run deploy
```

### App Can't Connect to Backend

**Check:**
1. Is Flask running? (`netstat -ano | findstr :5025`)
2. Is iPhone on same WiFi?
3. Is PC IP correct in `mobile/app.json`?

**Start Flask:**
```bash
cd backend
python app.py
```

### TestFlight Shows Old Version

**Wait:**
- Apple processes builds in 5-10 minutes
- Email comes when ready
- Close and reopen TestFlight

---

## File Structure

```
Food/
├── mobile/               # React Native app
│   ├── src/             # App source code
│   ├── assets/          # Icons, images
│   ├── app.json         # Expo config (version, bundle ID)
│   ├── eas.json         # Build & submit config
│   └── package.json     # Dependencies & scripts
│
├── backend/             # Flask API server
│   ├── app.py           # Main server file
│   └── requirements.txt # Python dependencies
│
└── .gitignore          # Git ignore patterns
```

---

## Next Steps

See `AUTOMATION_PLAN.md` for:
- Auto-start Flask backend on PC boot
- Offline app functionality
- Automatic deployments
- GitHub Actions CI/CD
