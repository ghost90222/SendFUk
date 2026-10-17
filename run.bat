@echo off
title ⚡ FUK FUK Sender
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org and tick "Add python.exe to PATH".
    pause
    exit /b 1
)

python fuk_fuk_sender.py
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Application closed with code %errorlevel%.
    pause
)
