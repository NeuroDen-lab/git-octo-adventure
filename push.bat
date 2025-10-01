@echo off
chcp 65001 >nul
echo 🚀 Быстрый пуш в GitHub
echo.

REM Проверяем, есть ли Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Используем Python скрипт...
    python git_push.py %*
) else (
    echo Используем PowerShell скрипт...
    powershell -ExecutionPolicy Bypass -File git_push.ps1 %*
)

echo.
pause
