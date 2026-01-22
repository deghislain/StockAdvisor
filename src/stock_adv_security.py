"""Security and validation utilities for StockAdvisor application."""
import re
import logging
from typing import Optional, Tuple
from collections import defaultdict
from time import time

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_stock_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate stock ticker symbol format.
    
    Args:
        symbol: The stock ticker symbol to validate
    
    Returns:
        (is_valid, error_message): Tuple with validation result and error message if invalid
    """
    if not symbol:
        return False, "Stock symbol cannot be empty"
    
    # Remove whitespace
    symbol = symbol.strip()
    
    if len(symbol) > 5:
        return False, "Stock symbol too long (max 5 characters)"
    
    if len(symbol) < 1:
        return False, "Stock symbol too short (min 1 character)"
    
    # Check if symbol contains only letters
    if not re.match(r'^[A-Z]{1,5}$', symbol.upper()):
        return False, "Stock symbol must contain only letters (A-Z)"
    
    logging.info(f"Stock symbol '{symbol}' validated successfully")
    return True, None


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        user_input: Raw user input string
    
    Returns:
        Sanitized string with potentially dangerous characters removed
    """
    if not user_input:
        return ""
    
    # Remove potentially dangerous characters, keep only alphanumeric, spaces, hyphens, and dots
    sanitized = re.sub(r'[^\w\s\-\.]', '', user_input)
    sanitized = sanitized.strip()
    
    logging.debug(f"Input sanitized: '{user_input}' -> '{sanitized}'")
    return sanitized


class RateLimiter:
    """
    Rate limiter to prevent abuse by limiting requests per user/session.
    
    Attributes:
        max_requests: Maximum number of requests allowed in the time window
        time_window: Time window in seconds for rate limiting
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed (default: 10)
            time_window: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        logging.info(f"RateLimiter initialized: {max_requests} requests per {time_window}s")
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if a request from the user is allowed.
        
        Args:
            user_id: Unique identifier for the user/session
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time()
        
        # Clean old requests outside the time window
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[user_id]) >= self.max_requests:
            logging.warning(f"Rate limit exceeded for user: {user_id}")
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        logging.debug(f"Request allowed for user: {user_id} ({len(self.requests[user_id])}/{self.max_requests})")
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get the number of remaining requests for a user.
        
        Args:
            user_id: Unique identifier for the user/session
        
        Returns:
            Number of remaining requests in current time window
        """
        now = time()
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]
        
        remaining = self.max_requests - len(self.requests[user_id])
        return max(0, remaining)
    
    def reset_user(self, user_id: str) -> None:
        """
        Reset rate limit for a specific user.
        
        Args:
            user_id: Unique identifier for the user/session
        """
        if user_id in self.requests:
            del self.requests[user_id]
            logging.info(f"Rate limit reset for user: {user_id}")


# Global rate limiter instance
# 10 report generations per 5 minutes (300 seconds)
report_rate_limiter = RateLimiter(max_requests=10, time_window=300)

# 30 chat questions per minute
chat_rate_limiter = RateLimiter(max_requests=30, time_window=60)


if __name__ == "__main__":
    # Test validation
    logging.info("Testing stock symbol validation:")
    test_symbols = ["AAPL", "IBM", "GOOGL", "A", "TOOLONG", "123", "AA-PL", "", "  MSFT  "]
    for symbol in test_symbols:
        is_valid, error = validate_stock_symbol(symbol)
        logging.info(f"  {symbol!r:15} -> Valid: {is_valid:5} {f'Error: {error}' if error else ''}")

    logging.info("\nTesting input sanitization:")
    test_inputs = ["AAPL", "IBM; DROP TABLE", "<script>alert('xss')</script>", "Normal text 123"]
    for inp in test_inputs:
        sanitized = sanitize_input(inp)
        logging.info(f"  {inp!r:40} -> {sanitized!r}")

    logging.info("\nTesting rate limiter:")
    limiter = RateLimiter(max_requests=3, time_window=10)
    user = "test_user"
    for i in range(5):
        allowed = limiter.is_allowed(user)
        remaining = limiter.get_remaining_requests(user)
        logging.info(f"  Request {i+1}: Allowed={allowed}, Remaining={remaining}")
