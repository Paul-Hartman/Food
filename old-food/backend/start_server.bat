@echo off
echo ========================================
echo Starting Food App Backend Server
echo ========================================
echo.

cd /d "C:\Users\paulh\Documents\Lotus-Eater Machine\Food\backend"

echo Starting Flask server on port 5025...
echo.
echo Access URLs:
echo   Local:   http://localhost:5025
echo   Network: Check output below for IP
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python app.py

pause
