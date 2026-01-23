"""Pytest configuration and fixtures for StockAdvisor tests."""
import pytest

import sys
from pathlib import Path
from unittest import mock

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

stub = mock.MagicMock()
stub.perform_tech_analysis = mock.MagicMock()
sys.modules["stock_adv_technical_analysis"] = stub
import src.stock_adv_user_interface as user_interface




@pytest.fixture
def sample_stock_symbol():
    """Provide a sample stock symbol for testing."""
    return "IBM"

@pytest.fixture
def invalid_stock_symbol():
    """Provide an invalid stock symbol for testing."""
    return "INVALIDSTOCK"

@pytest.fixture
def invalid_char_stock_symbol():
    """Provide an invalid stock symbol for testing."""
    return "IN1"


@pytest.fixture
def mock_st():
    """Patch streamlit functions used by get_user_input."""
    with mock.patch("src.stock_adv_user_interface.st") as mock_st:
        # Provide a dummy placeholder for the current_stock variable that the
        # function expects to exist in the module’s global scope.
        user_interface.current_stock = "AAPL"
        yield mock_st

