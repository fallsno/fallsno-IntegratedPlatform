@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Running Alembic upgrade head...
alembic upgrade head
echo Done.
pause
