"""Scarica Azioni - Italian Stock Market EOD Data Fetcher."""

from .fetcher import fetch_eod_data, get_eod_data, parse_stock_list

__version__ = "0.1.0"
__all__ = ["fetch_eod_data", "parse_stock_list", "get_eod_data"]
