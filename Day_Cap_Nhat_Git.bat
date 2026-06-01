@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ====================================================
echo   DANG TU DONG DONG GOI VA DAY CODE LEN GIT...
echo ====================================================
echo.

python git_dev_push.py

if %errorlevel% neq 0 goto ERROR
goto END

:ERROR
echo.
echo ====================================================
echo   [LOI] Khong the day code len Git.
echo   Vui long chay truc tiep file bang cach go:
echo   python git_dev_push.py
echo   de xem chi tiet loi.
echo ====================================================
echo.
pause

:END
