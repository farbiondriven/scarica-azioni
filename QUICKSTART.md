# Quick Start Guide

## 3 Ways to Use Scarica Azioni

### 1️⃣ Windows Executable (No Python Required!)

**For users without Python:**

```cmd
# Build once (requires Python on build machine)
build_windows.bat

# Distribute to users
# Copy: dist\scarica-azioni.exe + titoli_check.txt

# Run on any Windows PC (no Python needed!)
scarica-azioni.exe
```

Output: `eod_data.csv` with stock data

---

### 2️⃣ AWS Lambda (Serverless)

**For automated cloud execution:**

```bash
# Deploy
./deploy_lambda.sh

# Configure Lambda
Handler: lambda_handler.handler
Timeout: 60+ seconds
Memory: 256+ MB

# Invoke
aws lambda invoke --function-name scarica-azioni output.json
```

---

### 3️⃣ Direct Python (Development)

**For development and testing:**

```bash
# Run locally
uv run python lambda_handler.py

# Or
python lambda_handler.py
```

---

## What Each Method Does

All methods:
1. Read `titoli_check.txt` (15 Italian stocks)
2. Fetch end-of-day prices from Yahoo Finance
3. Save to CSV with: Date, Open, High, Low, Close
4. Display progress/results

## Which Method Should I Use?

| Use Case | Method |
|----------|--------|
| Give to non-technical users | ✅ Windows `.exe` |
| Run on schedule (cron) | ✅ Lambda |
| Quick local testing | ✅ Direct Python |
| CI/CD pipeline | ✅ Lambda |

---

## File Sizes

- **Python script**: 5.4 KB
- **Windows executable**: ~120 MB (includes Python + dependencies)
- **Lambda package**: ~50 MB (zipped dependencies)

---

## Building for Distribution

### Windows Executable
```bash
# On Windows
build_windows.bat

# On Mac/Linux (using UV)
./build_exe.sh

# Output: dist/scarica-azioni.exe
```

### Lambda Package
```bash
./deploy_lambda.sh
# Output: lambda-deployment.zip
```

---

## Automatic Builds (GitHub Actions)

Push a tag to trigger automatic builds:
```bash
git tag v1.0.0
git push --tags
```

GitHub Actions will:
- ✅ Run tests
- ✅ Build Windows `.exe`
- ✅ Create GitHub Release
- ✅ Attach `.exe` to release

Download from: **Releases** page

---

## Troubleshooting

### Windows Executable

**Problem:** "File not found" error
**Solution:** Make sure `titoli_check.txt` is in the same folder as `.exe`

**Problem:** Antivirus blocks the `.exe`
**Solution:** This is normal for PyInstaller executables. Add exception or rebuild with code signing.

### Lambda

**Problem:** Timeout error
**Solution:** Increase timeout (API calls can take 30-60 seconds)

**Problem:** Import errors
**Solution:** Make sure all dependencies are in `requirements.txt`

### Python

**Problem:** `ModuleNotFoundError`
**Solution:** Run `uv sync` to install dependencies

---

## Next Steps

1. ✅ Test locally: `python lambda_handler.py`
2. ✅ Build Windows exe: `./build_exe.sh`
3. ✅ Deploy to Lambda: `./deploy_lambda.sh`
4. ✅ Push to GitHub for automatic builds

For detailed instructions, see:
- `BUILD_INSTRUCTIONS.md` - Detailed build guide
- `README.md` - Full documentation
