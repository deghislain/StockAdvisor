
LARGE_MODEL = "ollama:llama3.1:8b"
SMALL_MODEL = "ollama:granite4:micro-h"

from enum import Enum


class DataType(str, Enum):
    """
    Enumeration of data categories used within the application.

    Attributes
    ----------
    FUNDAMENTAL_DATA : str
        Represents fundamental financial data (e.g., earnings, balance sheets).
    TECHNICAL_DATA : str
        Represents technical market data (e.g., price patterns, indicators).
    NON_FINANCIAL_DATA : str
        Represents non‑financial data sources (e.g., news sentiment, ESG scores).
    """
    FUNDAMENTAL_DATA = "FFD"
    TECHNICAL_DATA = "TMD"
    NON_FINANCIAL_DATA = "NFD"
