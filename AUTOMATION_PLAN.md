# Food App - Automation & Offline Strategy

## Goals

1. **Auto-start Flask backend** when PC boots
2. **Offline-first mobile app** - works without WiFi/server
3. **One-click deployments** with version bumping
4. **Automatic server detection** from mobile app

---

## Priority 1: Offline-First Mobile App

### Current Behavior (Requires Server)

- ❌ App loads recipes from Flask backend at http://192.168.2.38:5025
- ❌ No internet = no recipes
- ❌ Server must be running on PC
- ❌ iPhone must be on same WiFi

### Target Behavior (Offline-First)

- ✅ Recipes cached locally using SQLite (expo-sqlite)
- ✅ Works 100% offline after first sync
- ✅ Syncs with server when available
- ✅ Graceful degradation when offline

### Implementation Plan

#### Phase 1: Local Database (SQLite)

**What:** Store all recipes, ingredients, timers locally on iPhone

**Benefits:**
- App works completely offline
- Instant loading (no network delay)
- Server becomes optional sync mechanism

**Files to modify:**
- `mobile/src/database/` - New SQLite database layer
- `mobile/src/services/api.ts` - Add offline fallback
- `mobile/src/hooks/useRecipes.ts` - Check local DB first

**Code Pattern:**
```typescript
// 1. Try to load from local database (instant)
const localRecipes = await db.getRecipes()
setRecipes(localRecipes)

// 2. Try to sync from server (background)
try {
  const serverRecipes = await api.getRecipes()
  await db.syncRecipes(serverRecipes)
  setRecipes(serverRecipes)
} catch {
  // Server unavailable - use local data (already loaded)
}
```

#### Phase 2: Smart Sync

**When to sync with server:**
- App opens (background sync)
- User pulls to refresh
- Periodic background sync (when app is open)

**What to sync:**
- New recipes from MealDB API
- User's saved recipes
- Shopping lists
- Cooking timers

**Conflict resolution:**
- Local changes always win (user's device is source of truth)
- Server provides new community recipes

#### Phase 3: Server Detection

**Auto-detect server availability:**
```typescript
const API_URL = await detectServer() || 'http://192.168.2.38:5025'

async function detectServer() {
  const possibleIPs = [
    'http://192.168.2.38:5025',  // Home WiFi
    'http://172.20.10.2:5025',   // Mobile hotspot
  ]

  for (const ip of possibleIPs) {
    try {
      await fetch(`${ip}/api/health`, { timeout: 1000 })
      return ip  // Server found!
    } catch {
      continue
    }
  }

  return null  // No server available (use offline mode)
}
```

---

## Priority 2: Auto-Start Flask Backend

### Option A: Windows Task Scheduler (Recommended)

**Pros:**
- Built into Windows
- Runs on PC boot
- No extra software

**Setup:**

1. Create batch file: `Food/backend/start_server.bat`
```batch
@echo off
cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\backend"
python app.py
pause
```

2. Open Task Scheduler:
   - Win + R → `taskschd.msc`
   - Create Basic Task
   - Name: "Food App Backend"
   - Trigger: "When I log on"
   - Action: Start program `start_server.bat`
   - ✅ "Run whether user is logged in or not"

### Option B: PM2 (if Node.js installed)

```bash
# Install PM2 globally
npm install -g pm2

# Create ecosystem file
pm2 ecosystem
```

**ecosystem.config.js:**
```javascript
module.exports = {
  apps: [{
    name: 'food-backend',
    script: 'python',
    args: 'app.py',
    cwd: 'C:/Users/paulh/Documents/Lotus-Eater Machine/Food/backend',
    autorestart: true,
    watch: false
  }]
}
```

```bash
# Start backend
pm2 start ecosystem.config.js

# Auto-start on boot
pm2 startup
pm2 save
```

### Option C: Docker (Advanced)

**Pros:**
- Isolated environment
- Easy to deploy anywhere
- Cross-platform

**Cons:**
- Requires Docker Desktop
- More complex setup

---

## Priority 3: Deployment Automation

### Current Process

1. Edit `app.json` version manually
2. Run `npm run deploy`
3. Wait 30 minutes
4. Check email
5. Update TestFlight

### Automated Process

#### Quick Version Bump Script

**File:** `mobile/scripts/deploy.js`

```javascript
#!/usr/bin/env node
const fs = require('fs')
const { execSync } = require('child_process')

// Read current version
const appJson = JSON.parse(fs.readFileSync('app.json'))
const [major, minor, patch] = appJson.expo.version.split('.').map(Number)

// Increment patch version
const newVersion = `${major}.${minor}.${patch + 1}`
appJson.expo.version = newVersion

// Write back
fs.writeFileSync('app.json', JSON.stringify(appJson, null, 2))

console.log(`✅ Version bumped: ${appJson.expo.version} → ${newVersion}`)

// Deploy
console.log('🚀 Starting deployment...')
execSync('npm run deploy', { stdio: 'inherit' })
```

**Usage:**
```bash
cd mobile
node scripts/deploy.js  # Auto-increments version and deploys
```

**Update `package.json`:**
```json
{
  "scripts": {
    "deploy:auto": "node scripts/deploy.js"
  }
}
```

#### GitHub Actions (Advanced)

**Trigger deployment on git push:**

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to TestFlight

on:
  push:
    branches: [master]
    paths:
      - 'mobile/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        working-directory: mobile
        run: npm ci

      - name: Deploy to EAS
        working-directory: mobile
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}
        run: npm run deploy
```

**Setup:**
1. Get Expo token: `npx eas login && npx eas whoami --show-token`
2. Add to GitHub: Settings → Secrets → `EXPO_TOKEN`
3. Push to master → Auto-deploys!

---

## Priority 4: Better User Experience

### Server Status Indicator

**Show connection status in app:**

```typescript
// In App.tsx or StatusBar component
const [serverStatus, setServerStatus] = useState<'online' | 'offline'>('offline')

useEffect(() => {
  const checkServer = async () => {
    try {
      await fetch(`${API_URL}/api/health`, { timeout: 2000 })
      setServerStatus('online')
    } catch {
      setServerStatus('offline')
    }
  }

  checkServer()
  const interval = setInterval(checkServer, 30000) // Check every 30s
  return () => clearInterval(interval)
}, [])

// Show status badge
{serverStatus === 'offline' && (
  <View style={styles.offlineBanner}>
    <Text>📱 Offline Mode - Using cached data</Text>
  </View>
)}
```

### Smart Features by Connection Status

| Feature | Online | Offline |
|---------|--------|---------|
| Browse recipes | ✅ Latest from MealDB | ✅ Cached recipes |
| Search recipes | ✅ Server search | ✅ Local search |
| Barcode scan | ✅ Product lookup | ✅ Scan + queue for later |
| Shopping list | ✅ Sync across devices | ✅ Local only |
| Cooking timers | ✅ Always works | ✅ Always works |
| Recipe detail | ✅ Full info | ✅ Cached data |

---

## Implementation Roadmap

### Week 1: Offline Foundation
- [ ] Add SQLite schema for recipes
- [ ] Implement local database layer
- [ ] Migrate API calls to check local first
- [ ] Add initial data seeding (100 popular recipes)

### Week 2: Sync System
- [ ] Implement background sync
- [ ] Add pull-to-refresh
- [ ] Server auto-detection
- [ ] Connection status indicator

### Week 3: Backend Automation
- [ ] Windows Task Scheduler setup
- [ ] Create startup scripts
- [ ] Health check endpoint
- [ ] Auto-restart on crash

### Week 4: Deployment Automation
- [ ] Version bump script
- [ ] One-click deploy command
- [ ] GitHub Actions workflow
- [ ] Deployment documentation

---

## Quick Wins (Do First)

1. **Server Health Endpoint** (5 min)
   - Add `/api/health` to Flask
   - Returns `{"status": "ok", "version": "2.0"}`

2. **Startup Script** (10 min)
   - Create `backend/start_server.bat`
   - Add Task Scheduler task

3. **Deploy Script** (15 min)
   - Create `mobile/scripts/deploy.js`
   - Auto version bump

4. **Connection Indicator** (20 min)
   - Show "Online/Offline" badge
   - Try server, fall back gracefully

---

## Long-Term Vision

**The app should:**
- Work 100% offline after first use
- Sync silently in background when online
- Never block user waiting for server
- Auto-discover server on any network
- Deploy with one command

**The server should:**
- Auto-start with Windows
- Restart if crashed
- Provide new recipes/features
- Sync user data (optional)
- Not be required for core functionality
