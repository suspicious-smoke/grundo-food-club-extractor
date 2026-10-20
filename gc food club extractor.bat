@echo off
cd /d "%~dp0"

".venv\Scripts\python.exe" "food_club_extractor.py" >> "%~dp0task_scheduler.log" 2>&1

echo Exit code: %errorlevel% >> "%~dp0task_scheduler.log"