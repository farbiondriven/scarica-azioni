# Building Windows Executable

This guide explains how to build a standalone Windows executable that can run without Python installed on the target machine.

## Prerequisites

**On Windows:**
- Python 3.11+ installed
- PyInstaller (`pip install pyinstaller`)

**On Mac/Linux:**
- UV installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Build Methods

### Method 1: Quick Build (Windows)

```cmd
build_windows.bat
```

This will create `dist\scarica-azioni.exe`.

### Method 2: UV Build (Mac/Linux/Windows)

```bash
./build_exe.sh
```

Or manually:
```bash
uv run pyinstaller scarica-azioni.spec
```

### Method 3: Manual Build

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
pyinstaller --onefile \
    --name scarica-azioni \
    --add-data "titoli_check.txt:." \
    --hidden-import yfinance \
    --hidden-import pandas \
    --hidden-import numpy \
    --hidden-import requests \
    --console \
    lambda_handler.py
```

## Output

The executable will be created in:
- `dist/scarica-azioni.exe` (Windows)
- `dist/scarica-azioni` (Mac/Linux)

## Size

The executable is typically **100-150 MB** because it includes:
- Python interpreter (embedded)
- All dependencies (yfinance, pandas, numpy, etc.)
- Your code

## Distribution

To distribute to Windows users:

1. **Option A: Simple Distribution**
   - Zip together:
     - `scarica-azioni.exe`
     - `titoli_check.txt`
   - Send to users
   - Users extract and double-click the `.exe`

2. **Option B: GitHub Releases**
   - Push a version tag: `git tag v1.0.0 && git push --tags`
   - GitHub Actions will automatically build and attach the `.exe` to the release
   - Users download from Releases page

## Testing

After building:

```cmd
cd dist
scarica-azioni.exe
```

Verify:
- Console output appears
- `eod_data.csv` is created
- No errors about missing modules

## Troubleshooting

### "Failed to execute script" error

This usually means a dependency is missing. Add it to `hiddenimports` in `scarica-azioni.spec`:

```python
hiddenimports=['yfinance', 'pandas', 'numpy', 'requests', 'certifi', 'YOUR_MISSING_MODULE'],
```

### "titoli_check.txt not found"

Make sure the file is in the same directory as the `.exe`.

### Large file size

This is normal. PyInstaller bundles everything. To reduce size:
- Remove unused dependencies from `requirements.txt`
- Use `upx=True` in the spec file (already enabled)
- Consider using Nuitka instead of PyInstaller for smaller binaries

## Cross-Platform Builds

**Note:** PyInstaller does NOT support cross-compilation. You must build on the target platform:
- Build Windows `.exe` on Windows
- Build Mac app on Mac
- Build Linux binary on Linux

However, you can use:
- **Wine** (run Windows Python on Linux/Mac)
- **GitHub Actions** (automatically build on all platforms)
- **Docker with Wine** (for CI/CD)

The included GitHub Actions workflow (`build-exe.yml`) handles Windows builds automatically.
