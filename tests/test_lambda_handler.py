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
def temp_json_file(tmp_path):
    """Create a temporary JSON file path."""
    return tmp_path / "output.json"


@pytest.fixture
def temp_smtp_config(tmp_path):
    """Create a temporary SMTP config file."""
    config_file = tmp_path / "smtp_config.json"
    config_data = {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "username": "test@example.com",
        "password": "password123",
        "recipients": ["recipient@example.com"],
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
        assert stocks["A2A"] == "a2a"
        assert stocks["AZM"] == "azimut"
        assert stocks["ENI"] == "eni"

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
        assert "23.5000" in result
        assert "24.0000" in result
        assert "23.2500" in result
        assert "23.7500" in result
        # No euro sign
        assert "€" not in result

    def test_format_eod_data_none(self):
        """Test formatting None data."""
        result = lambda_handler.format_eod_data(None)
        assert result == "No data"


class TestJSONOperations:
    """Tests for JSON operations."""

    def test_format_data_string(self, sample_eod_data):
        """Test formatting data as comma-separated string."""
        result = lambda_handler.format_data_string(sample_eod_data)

        # Should be: "date,open,high,low,close"
        assert result == "2024-01-15,23.5000,24.0000,23.2500,23.7500"

    def test_save_to_json(self, sample_results, temp_json_file):
        """Test saving results to JSON."""
        lambda_handler.save_to_json(sample_results, str(temp_json_file))

        # Read and verify JSON
        data = json.loads(temp_json_file.read_text())

        assert "ENI" in data
        assert data["ENI"] == "2024-01-15,23.5000,24.0000,23.2500,23.7500"

        assert "INVALID" in data
        assert data["INVALID"] is None


class TestLambdaHandler:
    """Tests for Lambda handler."""

    def test_lambda_handler_success(self, temp_single_stock_file, temp_json_file, mock_context):
        """Test Lambda handler with successful execution."""
        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_json_file),
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


class TestSMTPConfiguration:
    """Tests for SMTP configuration."""

    def test_load_smtp_config_missing_file(self):
        """Test loading SMTP config when file doesn't exist."""
        config = lambda_handler.load_smtp_config("/nonexistent/smtp_config.json")
        assert config is None

    def test_load_smtp_config_valid(self, temp_smtp_config):
        """Test loading valid SMTP config."""
        config = lambda_handler.load_smtp_config(str(temp_smtp_config))

        assert config is not None
        assert config["smtp_server"] == "smtp.example.com"
        assert config["smtp_port"] == 587
        assert "recipients" in config
        assert config["recipients"] == ["recipient@example.com"]

    def test_load_smtp_config_invalid_json(self, tmp_path):
        """Test loading invalid JSON config."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json{")

        config = lambda_handler.load_smtp_config(str(config_file))
        assert config is None


class TestEmailFormatting:
    """Tests for email formatting."""

    def test_format_email_body(self, sample_results):
        """Test formatting email body."""
        html = lambda_handler.format_email_body(sample_results)

        assert "ENI" in html
        assert "eni" in html
        assert "2024-01-15" in html
        assert "23.5000" in html
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

    def test_lambda_handler_with_email_no_config(
        self, temp_single_stock_file, temp_json_file, mock_context
    ):
        """Test Lambda handler with email enabled but no config file."""
        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_json_file),
            "send_email": True,
            "smtp_config_file": "/nonexistent/smtp_config.json",
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["email_sent"] is False
        assert "email_error" in body

    def test_lambda_handler_without_email_flag(
        self, temp_single_stock_file, temp_json_file, mock_context
    ):
        """Test Lambda handler without email flag (default behavior)."""
        event = {
            "stock_file": str(temp_single_stock_file),
            "output_file": str(temp_json_file),
        }

        response = lambda_handler.handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        # email_sent should not be in response if email not requested
        assert "email_sent" not in body
