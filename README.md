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
# Run the CLI
uv run python -m scarica_azioni.cli

# Or use the entry point (if installed)
uv run scarica-azioni
```

### As a Library

```python
from scarica_azioni import fetch_eod_data

# Fetch EOD data for stocks in the list
results = fetch_eod_data("titoli_check.txt", "output.csv")

# Process results
for result in results:
    if result['data']:
        print(f"{result['ticker']}: €{result['data']['close']:.2f}")
```

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
   - Set handler to: `scarica_azioni.lambda_handler.handler`
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
│       └── ci.yml           # GitHub Actions CI workflow
├── src/
│   └── scarica_azioni/
│       ├── __init__.py      # Package initialization
│       ├── fetcher.py       # Core fetching logic
│       └── cli.py           # Command-line interface
├── tests/
│   ├── __init__.py
│   └── test_fetcher.py      # Unit tests
├── titoli_check.txt         # Stock list file
├── pyproject.toml           # Project configuration
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
