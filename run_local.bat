@echo off
REM ============================================================
REM   اجرای ربات MrBiznes روی کامپیوتر خودتان (ویندوز)
REM   کافیست روی همین فایل دوبار کلیک کنید.
REM ============================================================

cd /d "%~dp0"

echo ==============================================
echo    MrBiznes - اجرای محلی (ویندوز)
echo ==============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [خطا] پایتون نصب نیست.
    echo از python.org نسخه 3.11 یا 3.12 را نصب کنید و
    echo در هنگام نصب گزینه "Add python.exe to PATH" را تیک بزنید.
    echo.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/4] ساخت محیط پایتون...
    python -m venv .venv
)

echo [2/4] نصب پیش نیازها (بار اول چند دقیقه طول می کشد)...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
.venv\Scripts\pip.exe install --quiet -r requirements.txt

if not exist ".env" (
    echo [3/4] ساخت فایل تنظیمات .env ...
    copy /y ".env.example" ".env" >nul
    echo.
    echo  توجه: فایل .env ساخته شد.
    echo  الان Notepad باز می شود؛ این دو خط را پر کنید:
    echo     BOT_TOKEN=توکن ربات از BotFather
    echo     ADMIN_IDS=1432178804
    echo  بعد ذخیره کنید و این پنجره را ببندید.
    echo.
    notepad .env
)

echo [4/4] چک کردن وضعیت...
.venv\Scripts\python.exe scripts\doctor.py
echo.
echo  روشن کردن ربات (برای توقف: Ctrl+C)
echo.
.venv\Scripts\python.exe main.py

pause
