"""
Scarica Azioni - AWS Lambda handler
Fetch End-of-Day stock data for Italian stocks
"""

import json
import logging

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
        f"Open: €{data['open']:.4f} - "
        f"High: €{data['high']:.4f} - "
        f"Low: €{data['low']:.4f} - "
        f"Close: €{data['close']:.4f}"
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
        event: Lambda event (can contain custom stock_file path)
        context: Lambda context

    Returns:
        Response with status and results
    """
    try:
        # Get stock file path from event or use default
        stock_file = event.get("stock_file", "titoli_check.txt")
        output_file = event.get("output_file", "/tmp/eod_data.csv")

        logger.info(f"Fetching EOD data from {stock_file}")

        # Fetch data
        results = fetch_eod_data(stock_file, output_file)

        # Count successes
        successful = sum(1 for r in results if r["data"] is not None)
        failed = len(results) - successful

        logger.info(f"Completed: {successful} successful, {failed} failed")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "EOD data fetched successfully",
                    "total_stocks": len(results),
                    "successful": successful,
                    "failed": failed,
                    "output_file": output_file,
                }
            ),
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
