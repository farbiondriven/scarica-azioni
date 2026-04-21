# Scarica Azioni

Italian Stock Market End-of-Day (EOD) data fetcher using Yahoo Finance API.

[![CI](https://github.com/USERNAME/scarica-azioni/workflows/CI/badge.svg)](https://github.com/USERNAME/scarica-azioni/actions)

## Features

- Fetch end-of-day OHLC (Open, High, Low, Close) data for Italian stocks
- Read stock list from `titoli_check.txt`
- Export data to CSV format
- Logging support
- Type hints and clean code
- Full test coverage with pytest
- CI/CD with GitHub Actions (linting, formatting, testing)

## Installation

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/USERNAME/scarica-azioni.git
cd scarica-azioni

# Install dependencies
uv sync
```

## Usage

### Command Line

```bash
# Run directly
uv run python lambda_handler.py

# Or with custom event
python lambda_handler.py
```

### As a Python Module

```python
import lambda_handler

# Fetch EOD data for stocks in the list
results = lambda_handler.fetch_eod_data("titoli_check.txt", "output.csv")

# Process results
for result in results:
    if result['data']:
        print(f"{result['ticker']}: €{result['data']['close']:.2f}")
```

### Windows Standalone Executable

Build a standalone `.exe` that runs on Windows **without requiring Python or any dependencies installed**.

#### Building the executable:

**On Windows:**
```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
build_windows.bat
```

**On Mac/Linux (cross-compile for Windows):**
```bash
# Build using UV
./build_exe.sh

# Or manually
uv run pyinstaller scarica-azioni.spec
```

The executable will be created in `dist/scarica-azioni.exe` (~100-150MB, includes Python + all dependencies).

#### Running the executable:

1. Copy `scarica-azioni.exe` to your Windows PC
2. Make sure `titoli_check.txt` is in the same directory
3. Double-click `scarica-azioni.exe` or run from command prompt:
   ```cmd
   scarica-azioni.exe
   ```

The program will:
- Fetch EOD data for all stocks in `titoli_check.txt`
- Save results to `eod_data.csv` in the same directory
- Display progress in the console

#### GitHub Actions Auto-Build

The Windows executable is automatically built when you:
- Push a version tag (e.g., `v1.0.0`)
- Or manually trigger the "Build Windows Executable" workflow

Download the pre-built executable from GitHub Releases.

### AWS Lambda Deployment

#### Option 1: Using the deployment script

```bash
# Create Lambda deployment package
./deploy_lambda.sh

# Deploy using AWS CLI
aws lambda update-function-code \
  --function-name scarica-azioni \
  --zip-file fileb://lambda-deployment.zip
```

#### Option 2: Manual deployment

1. **Create the package:**
   ```bash
   pip install -r requirements.txt -t lambda-package/
   cp -r src/scarica_azioni lambda-package/
   cp titoli_check.txt lambda-package/
   cd lambda-package && zip -r ../lambda.zip . && cd ..
   ```

2. **Deploy via AWS Console:**
   - Upload `lambda.zip` to your Lambda function
   - Set handler to: `lambda_handler.handler`
   - Set timeout to at least 60 seconds (API calls can be slow)
   - Set memory to at least 256 MB

#### Lambda Event Format

```json
{
  "stock_file": "titoli_check.txt",
  "output_file": "/tmp/eod_data.csv"
}
```

Both parameters are optional and will use defaults if not provided.

#### Lambda Response

Success:
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"EOD data fetched successfully\", \"total_stocks\": 15, \"successful\": 15, \"failed\": 0}"
}
```

Error:
```json
{
  "statusCode": 500,
  "body": "{\"error\": \"Error message here\"}"
}
```

## Stock List Format

The `titoli_check.txt` file should have the following format:

```
stock-name-TICKER,filename.txt
azimut-AZM,azimut08.txt
eni-ENI,eni08.txt
```

Italian stocks use the `.MI` suffix (Milan Exchange), which is automatically added by the fetcher.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/scarica_azioni
```

### Linting and Formatting

```bash
# Check code style
uv run ruff check .

# Format code
uv run ruff format .

# Check formatting without modifying
uv run ruff format --check .
```

### Pre-commit Checks

Before committing, make sure to run:

```bash
uv run ruff check . && uv run ruff format . && uv run pytest
```

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Linting**: Runs `ruff check` and `ruff format --check`
- **Testing**: Runs pytest on Python 3.11, 3.12, and 3.13
- **Triggers**: On push to `main` and on pull requests

## Project Structure

```
scarica-azioni/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI: linting, formatting, testing
│       └── build-exe.yml       # Build Windows executable on release
├── tests/
│   ├── __init__.py
│   └── test_lambda_handler.py  # Unit tests
├── lambda_handler.py           # Single file with all code ⭐
├── titoli_check.txt            # Stock list file
├── scarica-azioni.spec         # PyInstaller spec for Windows exe
├── build_windows.bat           # Build script for Windows
├── build_exe.sh                # Build script for Unix
├── deploy_lambda.sh            # Lambda deployment script
├── requirements.txt            # Dependencies
├── pyproject.toml              # Project configuration
├── BUILD_INSTRUCTIONS.md       # Detailed build guide
└── README.md
```

**Simple single-file design** - Everything in `lambda_handler.py` for:
- ✅ Easy Lambda deployment
- ✅ Standalone Windows `.exe` (no Python required!)
- ✅ Direct Python execution

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
