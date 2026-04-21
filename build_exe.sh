#!/bin/bash
# Build Windows executable with PyInstaller (cross-platform script)

set -e

echo "Building Windows executable..."

uv run pyinstaller --onefile \
    --name scarica-azioni \
    --add-data "titoli_check.txt:." \
    --hidden-import yfinance \
    --hidden-import pandas \
    --hidden-import numpy \
    --hidden-import requests \
    --console \
    lambda_handler.py

echo ""
echo "✅ Build complete!"
echo "Executable: dist/scarica-azioni.exe (or scarica-azioni on Unix)"
echo ""
echo "To run:"
echo "  ./dist/scarica-azioni"
