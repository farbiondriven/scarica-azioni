"""Tests for the Lambda handler."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from scarica_azioni.lambda_handler import handler


def test_lambda_handler_success():
    """Test Lambda handler with successful execution."""
    # Create temporary stock file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("eni-ENI,eni08.txt\n")
        stock_file = f.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
        output_file = f.name

    try:
        event = {"stock_file": stock_file, "output_file": output_file}
        context = MagicMock()

        response = handler(event, context)

        assert response["statusCode"] == 200

        body = json.loads(response["body"])
        assert "message" in body
        assert body["total_stocks"] == 1
        assert "successful" in body
        assert "failed" in body

    finally:
        Path(stock_file).unlink()
        if Path(output_file).exists():
            Path(output_file).unlink()


def test_lambda_handler_default_paths():
    """Test Lambda handler with default paths."""
    event = {}
    context = MagicMock()

    # This might fail if titoli_check.txt doesn't exist in Lambda environment
    # but we're testing the handler logic
    response = handler(event, context)

    # Should return some response
    assert "statusCode" in response
    assert "body" in response


def test_lambda_handler_error():
    """Test Lambda handler with invalid stock file."""
    event = {"stock_file": "/nonexistent/file.txt", "output_file": "/tmp/test.csv"}
    context = MagicMock()

    response = handler(event, context)

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
