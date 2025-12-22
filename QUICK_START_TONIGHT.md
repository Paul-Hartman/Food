# Quick Start Guide - Tonight's Porterhouse Steak Dinner

**Production Test Timeline: 2-3 hours until cooking**

## Prerequisites Checklist

- [ ] Porterhouse steak (1.5-2 inches thick)
- [ ] MEATER thermometer inserted in Home Assistant
- [ ] Home Assistant running at http://jungledirector.local:8123
- [ ] Ingredients for dinner (see recipe details below)

______________________________________________________________________

## Step 1: Get Home Assistant Long-Lived Access Token

**You MUST complete this step first for MEATER integration to work.**

1. **Open Home Assistant in your browser:**

   ```
   http://jungledirector.local:8123
   ```

1. **Navigate to your profile:**

   - Click your username/profile icon in the bottom left sidebar
   - Scroll down to the **"Long-Lived Access Tokens"** section

1. **Create a new token:**

   - Click **"Create Token"**
   - Give it a name: `Food App - MEATER Integration`
   - Click **"OK"**
   - **IMPORTANT:** Copy the token immediately - it will only be shown once!

1. **Add token to your local environment file:**

   Create or edit the file `.env.local` in the Food project directory:

   ```bash
   # Location: C:\Users\paulh\Documents\Lotus-Eater Machine\Food\.env.local
   HOME_ASSISTANT_URL=http://jungledirector.local:8123
   HOME_ASSISTANT_TOKEN=your_long_lived_token_here
   ```

   Replace `your_long_lived_token_here` with the token you just copied.

______________________________________________________________________

## Step 2: Start the Django Backend Server

1. **Open a terminal in the Food directory:**

   ```bash
   cd "C:\Users\paulh\Documents\Lotus-Eater Machine\Food"
   ```

1. **Activate the virtual environment and start the server:**

   ```bash
   venv\Scripts\python.exe manage.py runserver
   ```

1. **Verify the server is running:**

   - You should see: `Starting development server at http://127.0.0.1:8000/`
   - Keep this terminal window open

______________________________________________________________________

## Step 3: Test MEATER Connection

**Open a new terminal** and run this test:

```bash
curl http://localhost:8000/api/meater/test-connection/
```

**Expected responses:**

### If token is NOT configured:

```json
{
  "connected": false,
  "error": "Home Assistant token not configured",
  "message": "Home Assistant token not configured. Create token at: http://jungledirector.local:8123/profile"
}
```

**Action:** Go back to Step 1 and configure your token.

### If token IS configured and working:

```json
{
  "connected": true,
  "url": "http://jungledirector.local:8123",
  "token_configured": true,
  "message": "Connection successful!"
}
```

**Great!** MEATER integration is ready.

______________________________________________________________________

## Step 4: Access Your Recipes

### Option A: Django Admin Interface

1. Navigate to: http://localhost:8000/admin/
1. Login with your admin credentials
1. Go to **Recipes** > **Recipes**
1. You'll see three recipes created by the seed command:
   - **Perfect Porterhouse Steak (Medium-Rare)** - Main dish
   - **Creamy Garlic Mashed Potatoes** - Side dish
   - **Roasted Asparagus with Lemon** - Vegetable

### Option B: API Endpoints

**List all recipes:**

```bash
curl http://localhost:8000/api/recipes/all/
```

**Get steak recipe details (ID 67):**

```bash
curl http://localhost:8000/api/recipes/67/detail/
```

______________________________________________________________________

## Step 5: Cooking Timeline

### T-60 minutes (1 hour before cooking)

1. **Remove steak from refrigerator**
   - Let it come to room temperature
   - Pat completely dry with paper towels

### T-30 minutes

1. **Preheat oven to 275°F (135°C)**
1. **Season steak:**
   - 2 tsp kosher salt
   - 1 tsp freshly ground black pepper
   - Season all sides generously
   - Let sit for 10 minutes

### T-20 minutes

1. **Insert MEATER probe:**

   - Place steak on wire rack over baking sheet
   - Insert probe into thickest part (avoid bone)
   - Set MEATER app target: 120°F (49°C)

1. **Place in oven:**

   - Monitor temperature via MEATER app
   - Cook for 20-30 minutes until 120°F internal

### T-5 minutes (when MEATER alerts)

1. **Remove steak from oven**
1. **Heat cast iron skillet:**
   - High heat until smoking hot (5 minutes)

### Final Sear

1. **Add 1 tbsp butter to hot pan**

1. **Sear steak:**

   - 60-90 seconds per side without moving

1. **Baste with herbs:**

   - Add: 1 tbsp butter, 4 smashed garlic cloves, 2 sprigs rosemary, 3 sprigs thyme
   - Tilt pan and baste for 30 seconds per side
   - Check MEATER: should read 130-135°F

1. **Rest:**

   - Transfer to cutting board
   - Tent loosely with foil
   - Rest 10 minutes (temp will rise to 135°F)

1. **Serve:**

   - Slice against the grain
   - Drizzle with herb butter from pan

______________________________________________________________________

## Wine Pairing Suggestions

Perfect companions for porterhouse steak:

### Red Wines (Recommended)

- **Cabernet Sauvignon** - Bold, tannic, pairs with fatty beef
- **Malbec** - Rich, fruity, complements char from searing
- **Syrah/Shiraz** - Peppery notes enhance seasoned crust
- **Bordeaux Blend** - Classic pairing with premium steak
- **Tempranillo (Rioja)** - Earthy notes work with herbs

### Temperature

- Serve red wine at 60-65°F (slightly below room temp)
- Open 30 minutes before dinner to let it breathe

______________________________________________________________________

## Side Dishes from Seed Data

### Creamy Garlic Mashed Potatoes

**Ingredients:**

- 2 lbs russet potatoes (peeled, quartered)
- 4 tbsp butter
- 1/2 cup heavy cream (warmed)
- 6 cloves roasted garlic
- Salt to taste

**Quick Steps:**

1. Boil potatoes in salted water until fork-tender (15-20 min)
1. Drain and return to pot
1. Add butter, warm cream, roasted garlic
1. Mash until smooth, season with salt

### Roasted Asparagus with Lemon

**Ingredients:**

- 1 lb asparagus (trimmed)
- 2 tbsp olive oil
- 2 cloves garlic (minced)
- 1/2 tsp salt, 1/4 tsp pepper
- 1/2 lemon (zest + juice)

**Quick Steps:**

1. Preheat oven to 425°F (220°C)
1. Toss asparagus with oil, garlic, salt, pepper
1. Spread on baking sheet
1. Roast 10-12 minutes until tender
1. Drizzle with lemon juice and zest

______________________________________________________________________

## Troubleshooting

### MEATER not showing in Home Assistant

1. Check MEATER is powered on and connected via Bluetooth
1. Verify MEATER integration is installed in Home Assistant
1. Check entity ID: `sensor.meater_*` should appear in HA

### Django server won't start

```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Use a different port if needed
venv\Scripts\python.exe manage.py runserver 8001
```

### Recipes not showing

```bash
# Re-run the seed command
venv\Scripts\python.exe manage.py seed_steak_dinner

# Check database
venv\Scripts\python.exe manage.py shell -c "from recipes.models import Recipe; print(f'Recipes: {Recipe.objects.count()}')"
```

### Can't connect to Home Assistant

1. Verify HA is running: http://jungledirector.local:8123
1. Check token is in `.env.local`
1. Test connection endpoint: `curl http://localhost:8000/api/meater/test-connection/`

______________________________________________________________________

## MEATER Temperature Targets

| Doneness    | Pull Temp (oven) | Final Temp (after rest) | MEATER Target |
| ----------- | ---------------- | ----------------------- | ------------- |
| Rare        | 115°F            | 125°F                   | 115°F         |
| Medium-Rare | 120°F            | 130-135°F               | 120°F         |
| Medium      | 130°F            | 140°F                   | 130°F         |
| Medium-Well | 140°F            | 150°F                   | 140°F         |

**For tonight: We're targeting Medium-Rare (120°F → 135°F final)**

______________________________________________________________________

## Additional API Endpoints

### List MEATER sensors

```bash
curl http://localhost:8000/api/meater/sensors/
```

### Get current MEATER status

```bash
curl http://localhost:8000/api/meater/status/
```

### Get recipe recommendations

```bash
curl http://localhost:8000/api/recipes/recommendations/
```

______________________________________________________________________

## Notes for Production Test

- **Take photos** of each stage for documentation
- **Monitor MEATER closely** during oven phase
- **Don't skip the rest** - it's critical for even cooking
- **Timing side dishes** - Start potatoes first, asparagus last
- **Cast iron must be HOT** - wait for visible smoke before searing

**Enjoy your dinner!**
