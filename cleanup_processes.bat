@echo off
chcp 65001 > nul

echo ==========================================
echo   Cleaning up lingering processes...
echo ==========================================

:: Kill Node.js (Vite)
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM esbuild.exe /T >nul 2>&1

:: Kill Python (FastAPI/Flask)
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1

:: Clear Vite Cache
echo [C] Clearing Vite cache...
if exist "frontend\.vite" rmdir /s /q "frontend\.vite"
if exist "frontend\node_modules\.vite" rmdir /s /q "frontend\node_modules\.vite"

:: Kill Java (Old backend if any)
taskkill /F /IM java.exe /T >nul 2>&1

:: Kill any process on port 8000 and 3000 using PowerShell
powershell -Command "Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo.
echo Cleanup complete! Please press F5 in VS Code to restart.
pause