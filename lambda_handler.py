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

MAX_LINES = 202


def parse_stock_list(file_path: str) -> dict[str, tuple[str, str]]:
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
                    stocks[ticker] = name, parts[1]

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
            "date_full": latest.name.strftime("%d-%b-%y"),
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
        f"Open: {data['open']:.3f} - "
        f"High: {data['high']:.3f} - "
        f"Low: {data['low']:.3f} - "
        f"Close: {data['close']:.3f}"
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
                    f"{d['open']:.3f},{d['high']:.3f},{d['low']:.3f},{d['close']:.3f}\n"
                )


def load_config(config_file: str = "config.json") -> dict:
    """
    Load configuration from JSON file.

    Args:
        config_file: Path to config file

    Returns:
        Dictionary with config (returns defaults if file doesn't exist)
    """
    defaults = {
        "send_email": False,
        "stock_file": "titoli_check.txt",
        "output_file": "eod_data.csv",
        "smtp": {},
    }

    try:
        config_path = Path(config_file)
        if not config_path.exists():
            logger.info(f"Config file not found: {config_file}, using defaults")
            return defaults

        with open(config_path) as f:
            config = json.load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return defaults


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
            html += f"Open: {data['open']:.3f}, "
            html += f"High: {data['high']:.3f}, "
            html += f"Low: {data['low']:.3f}, "
            html += f"Close: {data['close']:.3f}"
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
        logger.info(f"Connecting to SMTP server: {smtp_config['server']}:{smtp_config['port']}")

        # Determine if we should use TLS or SSL
        use_ssl = smtp_config.get("use_ssl", False)

        if use_ssl:
            # Use SSL (port 465 typically)
            server = smtplib.SMTP_SSL(smtp_config["server"], smtp_config["port"])
        else:
            # Use TLS (port 587 typically)
            server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
            server.starttls()

        server.login(smtp_config["username"], smtp_config["password"])
        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent successfully to: {', '.join(smtp_config['recipients'])}")
        return True

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        return False


def roll_file(stock_file_path: Path, data: dict):
    """
    Update stock file with new data.

    Inserts new data at line 2 (after header) and trims file to MAX_LINES.

    Args:
        stock_file_path: Path to the stock data file
        data: Dictionary with EOD data including date_full
    """
    new_line = (
        ",".join(
            [
                data["date_full"],
                f"{data['open']:.3f}",
                f"{data['high']:.3f}",
                f"{data['low']:.3f}",
                f"{data['close']:.3f}",
                "",
                f"{data['close']:.3f}",
            ]
        )
        + "\n"
    )

    with stock_file_path.open("r") as file:
        lines = file.readlines()

    # Reconstruct file: header + new line + old lines (trimmed to MAX_LINES)
    data_file = [lines[0]]  # header
    data_file.append(new_line)  # new data at line 2
    data_file.extend(lines[1 : MAX_LINES - 1])  # old data, trimmed

    with stock_file_path.open("w") as file:
        file.writelines(data_file)


def fetch_eod_data(
    stock_file: str,
    output_file: str,
    single_stock_base_path: str,
) -> list:
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

    for ticker, value in stocks.items():
        name, stock_filename = value
        logger.info(f"{ticker:8} ({name})")
        data = get_eod_data(ticker)

        results.append({"ticker": ticker, "name": name, "data": data})

        if data:
            logger.info(f"         {format_eod_data(data)}")
            # add to file
            stock_file_path = Path(single_stock_base_path) / stock_filename
            logger.info("Appending to stock file %s", stock_file_path)
            roll_file(stock_file_path, data)
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
        event: Lambda event (optional overrides for config)
        context: Lambda context

    Returns:
        Response with status and results
    """
    try:
        # Load config
        config = load_config()

        # Event can override config
        stock_file = event.get("stock_file", config.get("stock_file", "titoli_check.txt"))
        output_file = event.get("output_file", config.get("output_file", "eod_data.csv"))
        send_email_flag = event.get("send_email", config.get("send_email", False))
        stock_folder = event.get("stock_folder", config.get("stock_folder", None))
        if not stock_folder:
            raise Exception("Missing stock folder from config, exiting")

        logger.info(f"Fetching EOD data from {stock_file}")

        # Fetch data
        results = fetch_eod_data(stock_file, output_file, stock_folder)

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

        # Send email if enabled
        if send_email_flag and config.get("smtp"):
            smtp_config = config["smtp"]
            subject = smtp_config.get("subject", "MAIL AUTOM CHECK ADVFN")
            html_body = format_email_body(results)

            email_sent = send_email(smtp_config, subject, html_body)
            response_body["email_sent"] = email_sent

            if email_sent:
                response_body["message"] += " and email sent"
        elif send_email_flag:
            response_body["email_sent"] = False
            response_body["email_error"] = "SMTP not configured"
            logger.warning("Email requested but SMTP not configured")

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


# CLI entry point
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Load config and run
    response = handler({}, None)
    print(json.dumps(response, indent=2))
