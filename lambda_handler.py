"""
Scarica Azioni - AWS Lambda handler
Fetch End-of-Day stock data for Italian stocks
"""

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import yfinance as yf

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_stock_list(file_path: str) -> dict:
    """
    Parse the stock list file.

    Args:
        file_path: Path to the stock list file

    Returns:
        Dictionary mapping ticker to stock name
    """
    stocks = {}

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse format: stock-name-TICKER,filename.txt
            parts = line.split(",")
            if len(parts) >= 1:
                info = parts[0].split("-")
                if len(info) >= 2:
                    ticker = info[-1]
                    name = "-".join(info[:-1])
                    stocks[ticker] = name

    return stocks


def get_eod_data(ticker: str) -> dict | None:
    """
    Get end-of-day OHLC data for a stock.

    Args:
        ticker: Stock ticker (will add .MI suffix for Milan exchange)

    Returns:
        Dictionary with EOD data or None if error
    """
    full_ticker = f"{ticker}.MI" if not ticker.endswith(".MI") else ticker

    try:
        stock = yf.Ticker(full_ticker)
        hist = stock.history(period="2d")

        if hist.empty:
            return None

        latest = hist.iloc[-1]

        return {
            "ticker": ticker,
            "date": latest.name.strftime("%Y-%m-%d"),
            "open": latest["Open"],
            "high": latest["High"],
            "low": latest["Low"],
            "close": latest["Close"],
        }

    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None


def format_eod_data(data: dict) -> str:
    """Format EOD data as a string."""
    if not data:
        return "No data"

    return (
        f"{data['date']} - "
        f"Open: {data['open']:.4f} - "
        f"High: {data['high']:.4f} - "
        f"Low: {data['low']:.4f} - "
        f"Close: {data['close']:.4f}"
    )


def save_to_csv(results: list, filename: str) -> None:
    """
    Save results to CSV file.

    Args:
        results: List of result dictionaries
        filename: Output filename
    """
    with open(filename, "w") as f:
        # Header
        f.write("Ticker,Name,Date,Open,High,Low,Close\n")

        # Data rows
        for result in results:
            if result["data"]:
                d = result["data"]
                f.write(
                    f"{result['ticker']},{result['name']},{d['date']},"
                    f"{d['open']:.4f},{d['high']:.4f},{d['low']:.4f},{d['close']:.4f}\n"
                )


def load_smtp_config(config_file: str = "smtp_config.json") -> dict | None:
    """
    Load SMTP configuration from JSON file.

    Args:
        config_file: Path to SMTP config file

    Returns:
        Dictionary with SMTP config or None if file doesn't exist
    """
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            logger.warning(f"SMTP config file not found: {config_file}")
            return None

        with open(config_file) as f:
            config = json.load(f)

        required_keys = ["smtp_server", "smtp_port", "username", "password", "recipients"]
        if not all(key in config for key in required_keys):
            logger.error(f"SMTP config missing required keys: {required_keys}")
            return None

        return config

    except Exception as e:
        logger.error(f"Error loading SMTP config: {e}")
        return None


def format_email_body(results: list) -> str:
    """
    Format results as HTML email body.

    Args:
        results: List of stock results

    Returns:
        HTML formatted string
    """
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h2 { color: #333; }
            .stock { margin: 20px 0; padding: 10px; background-color: #f5f5f5; border-left: 4px solid #4CAF50; }
            .stock-name { font-weight: bold; font-size: 1.1em; color: #2c3e50; }
            .data { margin: 5px 0; font-family: 'Courier New', monospace; }
            .header { color: #666; font-weight: bold; }
            .no-data { color: #e74c3c; }
        </style>
    </head>
    <body>
        <h2>📊 Italian Stock Market - End-of-Day Report</h2>
        <p class="header">Date, Open, High, Low, Close</p>
    """

    for result in results:
        ticker = result["ticker"]
        name = result["name"]
        data = result["data"]

        html += '<div class="stock">'
        html += f'<div class="stock-name">{ticker} - {name}</div>'

        if data:
            html += '<div class="data">'
            html += f"{data['date']}, "
            html += f"Open: {data['open']:.4f}, "
            html += f"High: {data['high']:.4f}, "
            html += f"Low: {data['low']:.4f}, "
            html += f"Close: {data['close']:.4f}"
            html += "</div>"
        else:
            html += '<div class="data no-data">No data available</div>'

        html += "</div>"

    html += """
    </body>
    </html>
    """

    return html


def send_email(
    smtp_config: dict, subject: str, body_html: str, body_text: str | None = None
) -> bool:
    """
    Send email via SMTP.

    Args:
        smtp_config: SMTP configuration dictionary
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text fallback (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_config["username"]
        msg["To"] = ", ".join(smtp_config["recipients"])

        # Add plain text version if provided
        if body_text:
            part1 = MIMEText(body_text, "plain")
            msg.attach(part1)

        # Add HTML version
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

        # Send email
        logger.info(
            f"Connecting to SMTP server: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}"
        )

        # Determine if we should use TLS or SSL
        use_ssl = smtp_config.get("use_ssl", False)

        if use_ssl:
            # Use SSL (port 465 typically)
            server = smtplib.SMTP_SSL(smtp_config["smtp_server"], smtp_config["smtp_port"])
        else:
            # Use TLS (port 587 typically)
            server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
            server.starttls()

        server.login(smtp_config["username"], smtp_config["password"])
        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent successfully to: {', '.join(smtp_config['recipients'])}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return False


def fetch_eod_data(stock_file: str, output_file: str = "eod_data.csv") -> list:
    """
    Fetch EOD data for all stocks in the file.

    Args:
        stock_file: Path to stock list file
        output_file: Output CSV filename

    Returns:
        List of results
    """
    stocks = parse_stock_list(stock_file)

    logger.info("=" * 80)
    logger.info("End-of-Day Stock Data")
    logger.info("=" * 80)

    results = []

    for ticker, name in stocks.items():
        logger.info(f"{ticker:8} ({name})")
        data = get_eod_data(ticker)

        results.append({"ticker": ticker, "name": name, "data": data})

        if data:
            logger.info(f"         {format_eod_data(data)}")
        else:
            logger.warning(f"         No data available for {ticker}")

    # Save to CSV
    save_to_csv(results, output_file)
    logger.info("=" * 80)
    logger.info(f"Data saved to: {output_file}")

    return results


def handler(event, context):
    """
    AWS Lambda handler function.

    Args:
        event: Lambda event (can contain custom stock_file path, send_email flag, smtp_config_file)
        context: Lambda context

    Returns:
        Response with status and results
    """
    try:
        # Get stock file path from event or use default
        stock_file = event.get("stock_file", "titoli_check.txt")
        output_file = event.get("output_file", "/tmp/eod_data.csv")
        send_email_flag = event.get("send_email", False)
        smtp_config_file = event.get("smtp_config_file", "smtp_config.json")

        logger.info(f"Fetching EOD data from {stock_file}")

        # Fetch data
        results = fetch_eod_data(stock_file, output_file)

        # Count successes
        successful = sum(1 for r in results if r["data"] is not None)
        failed = len(results) - successful

        logger.info(f"Completed: {successful} successful, {failed} failed")

        response_body = {
            "message": "EOD data fetched successfully",
            "total_stocks": len(results),
            "successful": successful,
            "failed": failed,
            "output_file": output_file,
        }

        # Send email if requested
        if send_email_flag:
            smtp_config = load_smtp_config(smtp_config_file)

            if smtp_config:
                subject = smtp_config.get("subject", "MAIL AUTOM CHECK ADVFN")
                html_body = format_email_body(results)

                email_sent = send_email(smtp_config, subject, html_body)
                response_body["email_sent"] = email_sent

                if email_sent:
                    response_body["message"] += " and email sent"
            else:
                response_body["email_sent"] = False
                response_body["email_error"] = "SMTP configuration not found or invalid"
                logger.warning("Email requested but SMTP config not available")

        return {
            "statusCode": 200,
            "body": json.dumps(response_body),
        }

    except Exception as e:
        logger.error(f"Error in Lambda handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


# CLI entry point for local testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Simulate Lambda event
    event = {"stock_file": "titoli_check.txt", "output_file": "eod_data.csv"}
    context = None

    response = handler(event, context)
    print(json.dumps(response, indent=2))
