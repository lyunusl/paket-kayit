@echo off
rem Paket Kayit kurulumu - Developed by AugeLab. MIT License (see LICENSE).
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kurulum\kurulum.ps1" %*
echo.
pause
