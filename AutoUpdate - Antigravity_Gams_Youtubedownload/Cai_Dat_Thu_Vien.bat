@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ====================================================
echo   DANG TU DONG CAI DAT CAC THU VIEN BAT BUOC...
echo ====================================================
echo.

pip install -r requirements.txt

echo.
if %errorlevel% equ 0 goto SUCCESS
goto FAILURE

:SUCCESS
echo ====================================================
echo   CAI DAT THU VIEN THANH CONG!
echo   Bay gio ban co the mo Chay_Tool.bat de mo ung dung.
echo ====================================================
goto END

:FAILURE
echo ====================================================
echo   [LOI] Cai dat thu vien that bai.
echo   Vui long kiem tra Python da duoc cai dat va add PATH.
echo ====================================================

:END
echo.
pause
