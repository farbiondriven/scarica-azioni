"""AWS Lambda handler for scarica-azioni."""

import json
import logging

from .fetcher import fetch_eod_data

# Setup logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda handler function.

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
