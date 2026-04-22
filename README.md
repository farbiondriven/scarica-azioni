# Scarica Azioni

Italian Stock Market End-of-Day (EOD) data fetcher using Yahoo Finance API.

## Features

- Fetch end-of-day OHLC (Open, High, Low, Close) data for Italian stocks
- Export data to CSV format
- Optional email reports via SMTP
- Single config file for all settings
- Works as: Python script, AWS Lambda, or Windows .exe

## Installation

```bash
git clone https://github.com/USERNAME/scarica-azioni.git
cd scarica-azioni
uv sync
```

## Configuration

Create `config.json` (optional - uses defaults if missing):

```json
{
  "send_email": false,
  "stock_file": "titoli_check.txt",
  "output_file": "eod_data.csv",
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_ssl": false,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "recipients": ["recipient@example.com"],
    "subject": "MAIL AUTOM CHECK ADVFN"
  }
}
```

**Email:** Set `"send_email": true` to enable email reports.

Copy from example:
```bash
cp config.example.json config.json
# Edit config.json with your settings
```

## Usage

### Command Line

```bash
uv run python lambda_handler.py
```

Reads `config.json` and:
- Fetches stock data from `titoli_check.txt`
- Saves to `eod_data.csv`
- Sends email if enabled

**Output CSV:**
```csv
Ticker,Name,Date,Open,High,Low,Close
ENI,eni,2026-04-22,22.4800,23.1800,22.3700,22.9650
A2A,a2a,2026-04-22,2.3920,2.3940,2.3690,2.3850
```

### Windows .exe

**1. Build:**
```bash
uv run pyinstaller scarica-azioni.spec
```

**2. Distribute:**
```
folder/
├── scarica-azioni.exe
├── titoli_check.txt
└── config.json      ← Optional: for email
```

**3. Run:**
```cmd
scarica-azioni.exe
```

### AWS Lambda

**Deploy:**
```bash
./deploy_lambda.sh

aws lambda update-function-code \
  --function-name scarica-azioni \
  --zip-file fileb://lambda-deployment.zip
```

**Handler:** `lambda_handler.handler`

**Event (optional overrides):**
```json
{
  "stock_file": "titoli_check.txt",
  "output_file": "/tmp/eod_data.csv",
  "send_email": true
}
```

## Email Setup (Gmail)

1. Enable 2FA in Google Account
2. Create App Password: https://myaccount.google.com/apppasswords
3. Update `config.json`:
```json
{
  "send_email": true,
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "you@gmail.com",
    "password": "app-password-here",
    "recipients": ["recipient@example.com"]
  }
}
```

## Development

**Tests:**
```bash
uv run pytest
```

**Format & Lint:**
```bash
uv run ruff check --fix . && uv run ruff format .
```

## Project Structure

```
scarica-azioni/
├── lambda_handler.py          # Single file with all code
├── titoli_check.txt           # Stock list
├── config.example.json        # Example config
├── config.json                # Your config (gitignored)
├── scarica-azioni.spec        # PyInstaller spec
├── deploy_lambda.sh           # Lambda deployment
├── requirements.txt           # Dependencies
└── tests/                     # Pytest tests
```

## License

MIT License
