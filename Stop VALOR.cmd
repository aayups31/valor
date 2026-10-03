@echo off
title VALOR
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-Valor.ps1" -Stop
if errorlevel 1 pause
