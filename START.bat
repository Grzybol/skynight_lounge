@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title SkyJump
echo.
echo  SKYJUMP - czekaj, okno moze byc ciche przez minute...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-skyjump.ps1"
if errorlevel 1 (
  echo.
  echo Cos poszlo nie tak. To okno zostaw otwarte i zrob zrzut ekranu.
  echo Okno samo nie zniknie przez 2 minuty.
  timeout /t 120 >nul
  pause
  exit /b 1
)
endlocal
