@echo off
chcp 65001 > nul
title PlatformLauncher
cd /d %~dp0

echo ==========================================
echo   Starting Integrated Platform
echo ==========================================

:: 0. Clean up old processes to avoid port conflicts
echo [0/6] Cleaning up old processes...
taskkill /F /IM node.exe /T > nul 2>&1
taskkill /F /IM python.exe /T > nul 2>&1

:: 1. Check PostgreSQL Service
sc query postgresql-x64-18 | find "RUNNING" > nul
if errorlevel 1 (
    echo [1/6] Starting PostgreSQL service...
    net start postgresql-x64-18
) else (
    echo [1/6] PostgreSQL is already running
)

:: 2. Start Backend FastAPI (8000)
echo [2/6] Starting Version Management Backend...
start "Main Backend" cmd /k "cd backend && set "DATABASE_URL=postgresql://postgres:605678788@127.0.0.1:5000/model_db" && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 3. Start Monitor Server (5001) - Service Mode
echo [3/6] Starting Monitor Server...
start "Monitor Server" cmd /k "cd monitor_server && python app.py"

:: 4. Start Toolbox (5002)
echo [4/6] Starting Toolbox...
if exist "toolbox\analyzer" (
    start "Toolbox" cmd /k "cd toolbox\analyzer && streamlit run streamlit_app.py --server.port 5002 --server.address 0.0.0.0"
)

:: 5. Start Lab System Backend (8001)
echo [5/6] Starting Lab System Backend...
start "Lab Backend" cmd /k "cd lab_system\backend && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

:: Wait for backends to initialize
timeout /t 5 /nobreak > nul

:: 6. Start Main Frontend Vite (3000)
echo [6/6] Starting Main Frontend...
if exist "frontend" (
    start "Main Frontend" /D "%~dp0frontend" cmd /k "dev.bat"
)

echo.
echo ==========================================
echo All services started!
echo   主平台 (Main):         http://localhost:3000
echo   试验系统 (Lab):        http://localhost:3000/lab
echo   监测服务端 (Monitor):  http://localhost:5001
echo   工具箱 (Toolbox):       http://localhost:5002
echo.
echo   【重要】监测客户端 (sensor_monitor) 需要单独在采集主机上部署:
echo   - 客户端程序位于 sensor_monitor 目录
echo   - 服务端管理后台: http://localhost:5001/admin
echo   - 在各采集主机上运行 sensor_monitor/app.py 并配置正确的 server_url
echo ==========================================
echo Closing this window will NOT stop the services.
echo Please use Ctrl+C in each window to stop them.
pause
