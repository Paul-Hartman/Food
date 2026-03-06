# Integration Report: Food App

## Source
`Lotus-Eater Machine/food-app/` + `food-app-mobile/`

## What Was Copied
- Flask backend with recipe engine
- SQLite DB (food.db) with recipe/nutrition data
- Pantry tracker
- Barcode scanner
- React frontend
- React Native mobile app (in ../food-app-mobile/)

## What Was Skipped
- `node_modules/`
- iOS/Android build artifacts

## Integration Steps Needed
1. **Merge with existing Food/ backend**: Check if Food/ already has a backend — merge or replace as appropriate.
2. **Register recipes as domain cards**: Each recipe becomes a card in the universal card system.
3. **Wire nutrition data to wellness tracking**: Connect to Wellness domain for health tracking.
4. **Barcode scanner**: Useful utility — could share with Skincare scanner.
5. **Mobile app**: Connect to Food API once running. Update API base URL.
6. **Port assignment**: Register Flask app port in manifest.

## Dependencies
- Existing Food/ project
- Universal card system
- Wellness tracking
- Skincare scanner (shared barcode logic)

## Priority
MEDIUM - Standalone domain with good existing functionality.
