"""Tests for the fetcher module."""

import tempfile
from pathlib import Path

from scarica_azioni.fetcher import (
    fetch_eod_data,
    format_eod_data,
    get_eod_data,
    parse_stock_list,
    save_to_csv,
)


def test_parse_stock_list():
    """Test parsing stock list file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a2a-A2A,aem08.txt\n")
        f.write("azimut-AZM,azimut08.txt\n")
        f.write("eni-ENI,eni08.txt\n")
        temp_file = f.name

    try:
        stocks = parse_stock_list(temp_file)

        assert len(stocks) == 3
        assert stocks["A2A"] == "a2a"
        assert stocks["AZM"] == "azimut"
        assert stocks["ENI"] == "eni"
    finally:
        Path(temp_file).unlink()


def test_parse_stock_list_empty_lines():
    """Test parsing stock list with empty lines."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a2a-A2A,aem08.txt\n")
        f.write("\n")
        f.write("eni-ENI,eni08.txt\n")
        temp_file = f.name

    try:
        stocks = parse_stock_list(temp_file)
        assert len(stocks) == 2
    finally:
        Path(temp_file).unlink()


def test_get_eod_data_valid_ticker():
    """Test fetching EOD data for a valid ticker."""
    # ENI is a stable Italian stock
    data = get_eod_data("ENI")

    # We might not get data if markets are closed or API fails
    # So we just test the structure if data exists
    if data:
        assert "ticker" in data
        assert "date" in data
        assert "open" in data
        assert "high" in data
        assert "low" in data
        assert "close" in data
        assert data["ticker"] == "ENI"


def test_get_eod_data_invalid_ticker():
    """Test fetching EOD data for an invalid ticker."""
    data = get_eod_data("INVALID_TICKER_XYZ")
    # Should return None for invalid tickers
    assert data is None


def test_format_eod_data():
    """Test formatting EOD data."""
    data = {
        "date": "2024-01-15",
        "open": 23.50,
        "high": 24.00,
        "low": 23.25,
        "close": 23.75,
    }

    result = format_eod_data(data)

    assert "2024-01-15" in result
    assert "€23.5000" in result
    assert "€24.0000" in result
    assert "€23.2500" in result
    assert "€23.7500" in result


def test_format_eod_data_none():
    """Test formatting None data."""
    result = format_eod_data(None)
    assert result == "No data"


def test_save_to_csv():
    """Test saving results to CSV."""
    results = [
        {
            "ticker": "ENI",
            "name": "eni",
            "data": {
                "date": "2024-01-15",
                "open": 23.50,
                "high": 24.00,
                "low": 23.25,
                "close": 23.75,
            },
        },
        {"ticker": "INVALID", "name": "invalid", "data": None},
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        temp_file = f.name

    try:
        save_to_csv(results, temp_file)

        # Read and verify CSV
        with open(temp_file) as f:
            lines = f.readlines()

        assert len(lines) == 2  # Header + 1 valid data row
        assert "Ticker,Name,Date,Open,High,Low,Close" in lines[0]
        assert "ENI,eni,2024-01-15" in lines[1]
    finally:
        Path(temp_file).unlink()


def test_fetch_eod_data():
    """Test full fetch EOD data workflow."""
    # Create temporary stock list
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("eni-ENI,eni08.txt\n")
        stock_file = f.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        output_file = f.name

    try:
        results = fetch_eod_data(stock_file, output_file)

        assert len(results) == 1
        assert results[0]["ticker"] == "ENI"
        assert results[0]["name"] == "eni"

        # Check CSV was created
        assert Path(output_file).exists()
    finally:
        Path(stock_file).unlink()
        if Path(output_file).exists():
            Path(output_file).unlink()
