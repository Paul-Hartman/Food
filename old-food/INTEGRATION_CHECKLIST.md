# Food System Integration Checklist

**Status**: Ready for code when available
**Timeline**: Waiting for sister to push from home dev environment

## Pre-Integration (Complete ✓)

- [x] Create integration template
- [x] Design database schema migration
- [x] Plan shared module extraction
- [x] Create one-command integration script

## When Code Arrives

### Step 1: Code Transfer (5 min)
```bash
# On home computer (your sister runs this)
cd /path/to/Food
git add .
git commit -m "feat: Add Food system for integration"
git push origin food-system-branch

# On this computer (you run this)
git fetch origin
git checkout food-system-branch
```

### Step 2: Automated Integration (1 min)
```bash
# Run the one-command integration script
cd /Users/paul/IdeaProjects/Lotus-Eater-Machine
python3 ChiefSupervisor/integrate_food.py
```

**This script will automatically:**
1. ✅ Verify all Food code is present
2. ✅ Create/migrate database (food_database.db)
3. ✅ Extract shared modules (vision, photos, tagging)
4. ✅ Update Food to use shared modules
5. ✅ Run tests
6. ✅ Verify deployment readiness
7. ✅ Commit changes to knowledge base

### Step 3: Manual Verification (5 min)
```bash
# Verify Food app runs
cd Food
python3 manage.py runserver

# Check database
python3 manage.py shell
>>> from food.models import Recipe
>>> Recipe.objects.count()

# Run tests
python3 manage.py test
```

### Step 4: Integration Complete ✓
```bash
# Merge to master
git checkout master
git merge food-system-branch
git push

# Record integration in knowledge base
python3 ChiefSupervisor/smart_triggers.py << EOF
from smart_triggers import record_decision
record_decision(
    decision="Integrated Food system into main project",
    rationale="Unified all subsystems under Lotus-Eater Machine",
    project="Food"
)
EOF
```

---

## Database Migration Plan

### Current State (Home)
- SQLite: `db.sqlite3`
- Tables: Recipe, Ingredient, MealPlan, etc.

### Target State (Integrated)
- Database: `Food/food_database.db`
- Shared tables moved to: `shared/databases/common.db`
- Integration with: CardAnalysis, book-pathways, etc.

### Migration Script (Auto-generated)
```python
# Will be created by integrate_food.py
# Handles:
# - Schema compatibility
# - Data preservation
# - Foreign key updates
# - Index optimization
```

---

## Shared Module Extraction

### Vision Analysis
**From:** Food/vision/, CardAnalysis/vision/, book-pathways/vision/
**To:** `shared/vision_analysis/`

**Functions to unify:**
- Image classification
- Object detection
- OCR (for food labels)
- Color analysis

### Photo Storage
**From:** Multiple project-specific implementations
**To:** `shared/photo_storage/`

**Features:**
- Unified storage paths
- Automatic resizing
- Thumbnail generation
- Metadata extraction

### Tagging System
**From:** Food/tags/, CardAnalysis/tags/
**To:** `shared/tagging_system/`

**Features:**
- Hierarchical tags
- Tag suggestions
- Auto-tagging from AI
- Tag statistics

---

## Testing Strategy

### Unit Tests
```bash
# Run all Food tests
cd Food
python3 manage.py test

# Expected: 50+ tests pass
```

### Integration Tests
```bash
# Test shared module integration
python3 ChiefSupervisor/test_food_integration.py

# Expected: All shared modules work with Food
```

### Manual Test Checklist
- [ ] Create new recipe
- [ ] Upload food photo
- [ ] Search recipes by ingredient
- [ ] Generate meal plan
- [ ] Export shopping list
- [ ] Verify nutrition calculations
- [ ] Test mobile responsive UI

---

## Rollback Plan

If integration fails:

```bash
# 1. Restore from backup
cp Food/backup/db.sqlite3 Food/db.sqlite3

# 2. Revert shared module changes
git checkout HEAD -- shared/

# 3. Return to food-system-branch
git checkout food-system-branch

# 4. Debug and retry
python3 ChiefSupervisor/integrate_food.py --debug
```

---

## Success Criteria

✅ **Integration is successful when:**
1. Food app runs without errors
2. All existing features work (recipes, meal plans, etc.)
3. Shared modules are used (vision, photos, tags)
4. Tests pass (unit + integration)
5. Database size < 100 MB
6. No duplicate code with other projects
7. Deployment verification passes
8. Knowledge base updated with integration learnings

---

## Post-Integration

### Immediate (Day 1)
- [ ] Update main README with Food section
- [ ] Add Food to test orchestrator
- [ ] Configure CI/CD for Food
- [ ] Generate API documentation

### Short-term (Week 1)
- [ ] Extract additional reusable patterns
- [ ] Optimize database queries
- [ ] Add Food-specific slash commands
- [ ] Create Food usage guide

### Long-term (Month 1)
- [ ] AI meal planning improvements
- [ ] Integration with other subsystems
- [ ] Mobile app enhancements
- [ ] Advanced nutrition tracking

---

## Contact & Support

**Integration Issues?**
- Check: `ChiefSupervisor/integrate_food.log`
- Debug: `python3 integrate_food.py --verbose --debug`
- Ask Claude: "The Food integration failed at step X with error Y"

**Expected Integration Time:** 10-15 minutes (mostly automated)

🤖 *Generated with Lotus-Eater Machine - Progressive Intelligence*
