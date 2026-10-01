@echo off
echo ========================================================
echo Starting CareVault AI - Patient-Controlled Health Wallet
echo Tagline: "Your Health. Your Records. Your Control."
echo ========================================================
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
