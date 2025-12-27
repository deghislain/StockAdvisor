from beeai_framework.errors import FrameworkError
from enum import Enum
import pandas as pd

from typing import Dict, Any, List
import logging

LARGE_MODEL = "ollama:llama3.1:8b"
SMALL_MODEL = "ollama:granite4:micro-h"
FIN_MODEL = "ollama:0xroyce/Plutus-3B:latest"
DATA_DATES = ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31']

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
