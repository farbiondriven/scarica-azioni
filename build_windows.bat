@echo off
REM Build Windows executable with PyInstaller

echo Building Windows executable...

pyinstaller --onefile ^
    --name scarica-azioni ^
    --add-data "titoli_check.txt;." ^
    --hidden-import yfinance ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import requests ^
    --console ^
    lambda_handler.py

echo.
echo ✅ Build complete!
echo Executable: dist\scarica-azioni.exe
echo.
echo To run:
echo   dist\scarica-azioni.exe
