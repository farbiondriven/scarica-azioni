"""Tests for the Lambda handler using pytest fixtures."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory to path to import lambda_handler
sys.path.insert(0, str(Path(__file__).parent.parent))

import lambda_handler


# Fixtures
@pytest.fixture
def sample_eod_data():
    """Sample EOD data for testing."""
    return {
        "date": "2024-01-15",
        "date_full": "15-Jan-24",
        "open": 23.50,
        "high": 24.00,
        "low": 23.25,
        "close": 23.75,
    }


@pytest.fixture
def sample_results(sample_eod_data):
    """Sample results list with valid and invalid data."""
    return [
        {
            "ticker": "ENI",
            "name": "eni",
            "data": sample_eod_data,
        },
        {"ticker": "INVALID", "name": "invalid", "data": None},
    ]


@pytest.fixture
def temp_stock_file(tmp_path):
    """Create a temporary stock list file."""
    stock_file = tmp_path / "stocks.txt"
    stock_file.write_text("a2a-A2A,aem08.txt\nazimut-AZM,azimut08.txt\neni-ENI,eni08.txt\n")
    return stock_file


@pytest.fixture
def temp_single_stock_file(tmp_path):
    """Create a temporary stock list file with single stock."""
    stock_file = tmp_path / "single_stock.txt"
    stock_file.write_text("eni-ENI,eni08.txt\n")
    return stock_file


@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file path."""
    return tmp_path / "output.csv"


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.json"
    config_data = {
        "send_email": True,
        "stock_file": "titoli_check.txt",
        "output_file": "eod_data.csv",
        "smtp": {
            "server": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password123",
            "recipients": ["recipient@example.com"],
            "subject": "Test Subject",
        },
    }
    config_file.write_text(json.dumps(config_data))
    return config_file


@pytest.fixture
def mock_context():
    """Create a mock Lambda context."""
    return MagicMock()


# Tests
class TestStockListParsing:
    """Tests for stock list parsing."""

    def test_parse_stock_list(self, temp_stock_file):
        """Test parsing stock list file."""
        stocks = lambda_handler.parse_stock_list(str(temp_stock_file))

        assert len(stocks) == 3
        assert stocks["A2A"] == ("a2a", "aem08.txt")
        assert stocks["AZM"] == ("azimut", "azimut08.txt")
        assert stocks["ENI"] == ("eni", "eni08.txt")

    def test_parse_stock_list_with_empty_lines(self, tmp_path):
        """Test parsing stock list with empty lines."""
        stock_file = tmp_path / "stocks_with_empty.txt"
        stock_file.write_text("a2a-A2A,aem08.txt\n\n\neni-ENI,eni08.txt\n")

        stocks = lambda_handler.parse_stock_list(str(stock_file))
        assert len(stocks) == 2


class TestEODDataFetching:
    """Tests for EOD data fetching."""

    def test_get_eod_data_valid_ticker(self):
        """Test fetching EOD data for a valid ticker."""
        data = lambda_handler.get_eod_data("ENI")

        if data:
            assert "ticker" in data
            assert "date" in data
            assert "open" in data
            assert "high" in data
            assert "low" in data
            assert "close" in data
            assert data["ticker"] == "ENI"

    def test_get_eod_data_invalid_ticker(self):
        """Test fetching EOD data for an invalid ticker."""
        data = lambda_handler.get_eod_data("INVALID_TICKER_XYZ")
        assert data is None


class TestDataFormatting:
    """Tests for data formatting."""

    def test_format_eod_data(self, sample_eod_data):
        """Test formatting EOD data."""
        result = lambda_handler.format_eod_data(sample_eod_data)

        assert "2024-01-15" in result
        assert "23.500" in result
        assert "24.000" in result
        assert "23.250" in result
        assert "23.750" in result
        # No euro sign
        assert "€" not in result

    def test_format_eod_data_none(self):
        """Test formatting None data."""
        result = lambda_handler.format_eod_data(None)
        assert result == "No data"


class TestCSVOperations:
    """Tests for CSV operations."""

    def test_save_to_csv(self, sample_results, temp_csv_file):
        """Test saving results to CSV."""
        lambda_handler.save_to_csv(sample_results, str(temp_csv_file))

        # Read and verify CSV
        lines = temp_csv_file.read_text().splitlines()

        assert len(lines) == 2  # Header + 1 valid data row
        assert "Ticker,Name,Date,Open,High,Low,Close" in lines[0]
        assert "ENI,eni,2024-01-15" in lines[1]
        assert "23.500,24.000,23.250,23.750" in lines[1]


class TestRollFile:
    """Tests for roll_file function."""

    def test_roll_file_inserts_at_line_2(self, tmp_path, sample_eod_data):
        """Test roll_file inserts new data at line 2 (after header)."""
        stock_file = tmp_path / "stock.txt"
        stock_file.write_text(
            "Date,Open,High,Low,Close,,Close\n"
            "14-Jan-24,22.000,22.500,21.500,22.250,,22.250\n"
            "13-Jan-24,21.000,21.500,20.500,21.250,,21.250\n"
        )

        lambda_handler.roll_file(stock_file, sample_eod_data)

        lines = stock_file.read_text().splitlines()
        assert len(lines) == 4  # Header + 3 data lines
        assert lines[0] == "Date,Open,High,Low,Close,,Close"
        assert lines[1] == "15-Jan-24,23.500,24.000,23.250,23.750,,23.750"
        assert lines[2] == "14-Jan-24,22.000,22.500,21.500,22.250,,22.250"
        assert lines[3] == "13-Jan-24,21.000,21.500,20.500,21.250,,21.250"

    def test_roll_file_preserves_header(self, tmp_path, sample_eod_data):
        """Test roll_file always preserves the header."""
        stock_file = tmp_path / "stock.txt"
        stock_file.write_text("Date,Open,High,Low,Close,,Close\n")

        lambda_handler.roll_file(stock_file, sample_eod_data)

        lines = stock_file.read_text().splitlines()
        assert lines[0] == "Date,Open,High,Low,Close,,Close"
        assert lines[1] == "15-Jan-24,23.500,24.000,23.250,23.750,,23.750"

    def test_roll_file_trims_at_max_lines_with_3_decimals(
        self, tmp_path, sample_eod_data, monkeypatch
    ):
        """Test roll_file trims at MAX_LINES and uses 3 decimal places."""
        # Mock MAX_LINES to 5 (header + 4 data lines)
        monkeypatch.setattr(lambda_handler, "MAX_LINES", 5)

        stock_file = tmp_path / "stock.txt"
        # Create file with header + 4 data lines = 5 lines total
        stock_file.write_text(
            "Date,Open,High,Low,Close,,Close\n"
            "14-Jan-24,22.000,22.500,21.500,22.250,,22.250\n"
            "13-Jan-24,21.000,21.500,20.500,21.250,,21.250\n"
            "12-Jan-24,20.000,20.500,19.500,20.250,,20.250\n"
            "11-Jan-24,19.000,19.500,18.500,19.250,,19.250\n"
        )

        lambda_handler.roll_file(stock_file, sample_eod_data)

        lines = stock_file.read_text().splitlines()
        # Should have header + 4 data lines (last line "11-Jan-24" removed)
        assert len(lines) == 5
        assert lines[0] == "Date,Open,High,Low,Close,,Close"
        # Check 3 decimal places are used
        assert lines[1] == "15-Jan-24,23.500,24.000,23.250,23.750,,23.750"
        assert lines[2] == "14-Jan-24,22.000,22.500,21.500,22.250,,22.250"
        assert lines[3] == "13-Jan-24,21.000,21.500,20.500,21.250,,21.250"
        assert lines[4] == "12-Jan-24,20.000,20.500,19.500,20.250,,20.250"
        # Line "11-Jan-24" should be removed


class TestLambdaHandler:
    """Tests for Lambda handler."""

    def test_lambda_handler_success(
        self, temp_single_stock_file, temp_csv_file, tmp_path, mock_context
    ):
        """Test Lambda handler with successful execution."""
        # Create the stock file that roll_file expects
        stock_data_file = tmp_path / "eni08.txt"
        stock_data_file.write_text("Date,Open,High,Low,Close,,Close\n")

        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_csv_file),
            "stock_folder": str(tmp_path),
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert "message" in body
        assert body["total_stocks"] == 1
        assert "successful" in body
        assert "failed" in body

    def test_lambda_handler_error(self, mock_context):
        """Test Lambda handler with invalid stock file."""
        event = {
            "stock_file": "/nonexistent/file.txt",
            "output_file": "/tmp/test.csv",
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


class TestConfiguration:
    """Tests for configuration loading."""

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist (returns defaults)."""
        config = lambda_handler.load_config("/nonexistent/config.json")
        assert config["send_email"] is False
        assert config["stock_file"] == "titoli_check.txt"

    def test_load_config_valid(self, temp_config):
        """Test loading valid config."""
        config = lambda_handler.load_config(str(temp_config))

        assert config is not None
        assert config["send_email"] is True
        assert config["smtp"]["server"] == "smtp.example.com"
        assert config["smtp"]["port"] == 587
        assert config["smtp"]["recipients"] == ["recipient@example.com"]

    def test_load_config_invalid_json(self, tmp_path):
        """Test loading invalid JSON config (returns defaults)."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json{")

        config = lambda_handler.load_config(str(config_file))
        assert config["send_email"] is False  # Returns defaults


class TestEmailFormatting:
    """Tests for email formatting."""

    def test_format_email_body(self, sample_results):
        """Test formatting email body."""
        html = lambda_handler.format_email_body(sample_results)

        assert "ENI" in html
        assert "eni" in html
        assert "2024-01-15" in html
        assert "23.500" in html
        assert "INVALID" in html
        assert "No data available" in html
        assert "<html>" in html
        assert "</html>" in html
        # No euro sign
        assert "€" not in html

    def test_format_email_body_empty_results(self):
        """Test formatting email body with empty results."""
        html = lambda_handler.format_email_body([])

        assert "<html>" in html
        assert "</html>" in html
        assert "Date, Open, High, Low, Close" in html


class TestLambdaHandlerWithEmail:
    """Tests for Lambda handler with email functionality."""

    def test_lambda_handler_with_email_no_smtp(
        self, temp_single_stock_file, temp_csv_file, tmp_path, mock_context
    ):
        """Test Lambda handler with email enabled but no SMTP config."""
        # Create the stock file that roll_file expects
        stock_data_file = tmp_path / "eni08.txt"
        stock_data_file.write_text("Date,Open,High,Low,Close,,Close\n")

        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_csv_file),
            "send_email": True,
            "stock_folder": str(tmp_path),
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["email_sent"] is False
        assert "email_error" in body

    def test_lambda_handler_without_email_flag(
        self, temp_single_stock_file, temp_csv_file, tmp_path, mock_context
    ):
        """Test Lambda handler without email flag (default behavior)."""
        # Create the stock file that roll_file expects
        stock_data_file = tmp_path / "eni08.txt"
        stock_data_file.write_text("Date,Open,High,Low,Close,,Close\n")

        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_csv_file),
            "stock_folder": str(tmp_path),
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        # email_sent should not be in response if email not requested
        assert "email_sent" not in body
