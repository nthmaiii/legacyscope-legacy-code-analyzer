@echo off
cd /d "%~dp0"
echo Dang cai dat thu vien (neu can)...
python -m pip install -r requirements.txt
echo.
echo Dang khoi dong LegacyScope tai http://127.0.0.1:8000
start "" /b cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8000"
python app.py
pause
