@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Update failed with exit code %RC%.
pause
exit /b %RC%
