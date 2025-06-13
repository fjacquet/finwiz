import logging
import os
import warnings
from datetime import datetime

from dotenv import load_dotenv

from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger, setup_logging

# Setup logging configuration
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
setup_logging(log_level=logging.INFO, log_dir=log_dir)
logger = get_logger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", message="No path_separator found in configuration")

logger.info("Loading environment variables for test run.")
load_dotenv()

# Initialize LLM retry mechanism
logger.info("Initializing LLM retry mechanism.")
initialize_retry_mechanism(max_retries=5, timeout=300)

def run_test():
    """Run a single crew for validation."""
    logger.info("Starting single crew validation run for StockCrew.")
    try:
        # Prepare inputs
        today = datetime.now()
        inputs = {
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
        }
        logger.debug(f"Test inputs prepared: {inputs}")

        # Instantiate and run the StockCrew
        stock_crew_instance = StockCrew().crew()
        result = stock_crew_instance.kickoff(inputs=inputs)

        logger.info("StockCrew validation run completed.")
        print("--- Stock Crew Output ---")
        print(result)
        print("-------------------------")

    except Exception as e:
        logger.critical(f"Single crew validation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_test()
