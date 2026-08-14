@echo off
chcp 65001 > nul
title Integrated Platform Backend
cd /d "%~dp0"
echo Starting backend API server on port 8000...
set "DATABASE_URL=postgresql://postgres:605678788@127.0.0.1:5000/model_db"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
