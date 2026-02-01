import logging
import time
from functools import wraps

# ----------------------------------------------------------------------
# Logging configuration (run once when this module is imported)
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_advisor.log'),
        logging.StreamHandler()
    ]
)


# ----------------------------------------------------------------------
# Performance‑logging decorator
# ----------------------------------------------------------------------
def log_performance(func):
    """Decorator to log async function execution time."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            logging.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logging.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise

    return wrapper
