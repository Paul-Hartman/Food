# Testing Guide - How to Test Without Visual Access

## Overview

Since I cannot run visual testing tools (Puppeteer, emulators, etc.), I test by monitoring:

1. **Expo Metro Bundler logs** (frontend)
1. **Django Server logs** (backend API)

## Testing Commands

### Monitor Frontend Logs

```bash
# Filter for errors only
BashOutput bash_id=<expo_bash_id> filter="ERROR|error|Error|WARNING|Warning"

# Monitor specific screen
BashOutput bash_id=<expo_bash_id> filter="RecipeRecommendationsScreen"

# Watch for specific feature
BashOutput bash_id=<expo_bash_id> filter="swipe|Swipe"
```

### Monitor Backend Logs

```bash
# Filter for server errors
BashOutput bash_id=<django_bash_id> filter="error|Error|ERROR|Traceback"

# Watch specific API endpoint
BashOutput bash_id=<django_bash_id> filter="/api/recipes"
```

## Test Scenarios

### 1. Test Swipe Up (Add to Deck)

**What to test:** Swiping up should add recipe to cooking deck

**How to test via logs:**

1. Monitor: `BashOutput filter="RecipeRecommendationsScreen|swipe"`
1. Look for sequence:
   - "Adding to cooking deck: [Recipe Name]"
   - "Previous cooking deck size: X"
   - "New cooking deck size: X+1"
   - NO "No recipe at index" errors
   - NO "Total recipes: 0" errors

**Expected log output:**

```
LOG RecipeRecommendationsScreen: Adding to cooking deck: Scrambled Eggs
LOG RecipeRecommendationsScreen: Previous cooking deck size: 0
LOG RecipeRecommendationsScreen: New cooking deck size: 1
```

**Signs of failure:**

- "No recipe at index 0 Total recipes: 0"
- Recipe not added to state
- Card doesn't advance

### 2. Test Cook Mode Swipe Navigation

**What to test:** Left/right swipes should navigate between steps WITHOUT completing them

**How to test via logs:**

1. Monitor: `BashOutput filter="CookingAssistantScreen"`
1. Start cooking session
1. Look for navigation without completion:
   - Should see step changes
   - Should NOT see "Completed step" messages
   - Complete button should be the only way to complete steps

**Expected log output:**

```
LOG CookingAssistantScreen: Current step: 1
[after left swipe]
LOG CookingAssistantScreen: Current step: 2
[no completion messages]
```

### 3. Test Timer Functionality

**What to test:** Timers should be created and auto-advance to next step

**How to test via logs:**

1. Monitor: `BashOutput filter="timer|Timer"`
1. Create a timer from a step
1. Look for:
   - Timer creation success
   - Timer appears in active timers list
   - NO "Request failed with status code 500" on `/api/timers/`

**Expected log output:**

```
LOG Timer created successfully
LOG Active timers: 1
```

**Signs of failure:**

- "Internal Server Error: /api/timers/list/"
- "Internal Server Error: /api/timers/create/"

### 4. Test Recipe Loading

**What to test:** Recipes should load and persist

**How to test via logs:**

1. Monitor: `BashOutput filter="RecipeRecommendationsScreen.*recipes"`
1. Look for sequence:
   - "Fetching recipes from..."
   - "Got response" with recipe data
   - "Loaded X recipes"
   - "Found Y recommended recipes"

**Expected log output:**

```
LOG RecipeRecommendationsScreen: Fetching recipes from http://...
LOG RecipeRecommendationsScreen: Got response {"success": true, "recipes": [...]}
LOG RecipeRecommendationsScreen: Loaded 69 recipes
LOG RecipeRecommendationsScreen: Found 1 recommended recipes
```

**Signs of failure:**

- "Error fetching recipes"
- Component mounting multiple times rapidly
- "Loaded 0 recipes" or state reset to 0

### 5. Test Session Completion

**What to test:** Completing all steps should award rewards without errors

**How to test via logs:**

1. Monitor: `BashOutput filter="cooking.*complete|Complete"`
1. Complete final step
1. Look for:
   - "Completing cooking session"
   - Rewards data returned
   - NO "Cannot read property 'id' of null"
   - NO "TypeError" errors

**Expected log output:**

```
LOG Completing cooking session
LOG Rewards: {card: {...}, life_meter_boosts: {...}}
```

**Signs of failure:**

- "Error completing cooking session: [TypeError: Cannot read property 'id' of null]"
- "No session or session.id is null"

## Common Error Patterns

### State Reset Errors

**Symptoms:**

- "Total recipes: 0" after recipes were loaded
- Component mounting multiple times
- State not persisting

**Diagnosis:**

1. Check for multiple "Component mounted" messages
1. Look for useEffect dependency issues
1. Check navigation listeners that might refetch/reset

**Fix:**

- Remove problematic useEffect hooks
- Ensure state updates are functional: `setState(prev => ...)`
- Avoid navigation listeners that reset state

### Backend API Errors

**Symptoms:**

- "Request failed with status code 500"
- "Internal Server Error: /api/..."

**Diagnosis:**

1. Check Django logs for Traceback
1. Look for specific error type (TypeError, IntegrityError, etc.)
1. Identify which field/operation is failing

**Fix:**

- Add None checks for database aggregations
- Handle missing fields gracefully
- Add try/catch with proper error responses

### Race Conditions

**Symptoms:**

- "No recipe at index X"
- State accessed before it's set
- Async operations completing out of order

**Diagnosis:**

1. Check order of log messages
1. Look for async operations
1. Check if state is captured before async work

**Fix:**

- Capture state/values BEFORE starting animations
- Use functional state updates
- Add proper safety checks

## Pre-Deployment Checklist

Before marking features as "complete", verify via logs:

- [ ] No ERROR messages in frontend logs
- [ ] No Internal Server Error in backend logs
- [ ] All test scenarios pass (above sections)
- [ ] Component mount/unmount patterns are clean
- [ ] State updates are logged correctly
- [ ] API responses are successful (status 200)

## Log Monitoring Best Practices

1. **Always filter logs** - Don't read full output, use targeted filters
1. **Check both frontend and backend** - Many bugs span both layers
1. **Look for patterns** - Repeated errors indicate systemic issues
1. **Verify the sequence** - Order of operations matters
1. **Test the happy path** - Ensure basic flow works before edge cases
1. **Document findings** - Add new test scenarios to this guide

## Example Testing Session

```bash
# 1. Start by checking if servers are running
BashOutput bash_id=db1019 filter="Bundled|Failed"
BashOutput bash_id=2cf33e filter="Starting|Error"

# 2. Test specific feature (e.g., swipe up)
BashOutput bash_id=db1019 filter="RecipeRecommendationsScreen.*swipe|Adding to deck"

# 3. Check for any errors
BashOutput bash_id=db1019 filter="ERROR|Error"
BashOutput bash_id=2cf33e filter="ERROR|Error|Traceback"

# 4. Verify API responses
BashOutput bash_id=2cf33e filter="/api/recipes"

# 5. Confirm feature works by checking expected log messages
# (See test scenarios above for expected outputs)
```

## When Tests Fail

1. **Identify the exact error** from logs
1. **Find the code location** - logs usually include file:line
1. **Understand the root cause** - don't just fix symptoms
1. **Add safety checks** - prevent similar errors
1. **Re-test with logs** - verify fix works
1. **Update this guide** - document new patterns

## Remember

- I CANNOT see the visual UI
- I CAN see all log output
- Comprehensive logging is essential for testing
- Console.log statements are my eyes
- Good error messages make debugging possible
