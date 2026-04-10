"""Command-line interface for scarica-azioni."""

import logging
import sys
from pathlib import Path

from .fetcher import fetch_eod_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    """Main CLI entry point."""
    # Default stock file path
    stock_file = Path(__file__).parent.parent.parent / "titoli_check.txt"

    if not stock_file.exists():
        logging.error(f"Stock file not found: {stock_file}")
        sys.exit(1)

    # Fetch EOD data
    fetch_eod_data(str(stock_file))


if __name__ == "__main__":
    main()
