@echo off
chcp 65001 > nul
title Integrated Platform Frontend
cd /d "%~dp0"
echo Checking Vite version...
node node_modules\vite\bin\vite.js --version
echo Starting frontend dev server on port 3000...
node node_modules\vite\bin\vite.js --host 0.0.0.0 --port 3000 --strictPort
