@echo off
cd /d C:\Users\ELZAHBIA\Vs_code\personal_AI_Assistant\ASK_SONA\sonna-ai
start "" /min "C:\Users\ELZAHBIA\anaconda3\python.exe" main.py
timeout /t 4 /nobreak >nul
start "" msedge --app=http://127.0.0.1:8000