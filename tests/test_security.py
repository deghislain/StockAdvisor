import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import src.agents.stock_adv_security as security


def test_validate_stock_symbol_correct_stock_symbol(sample_stock_symbol):
    result, error_msg = security.validate_stock_symbol(sample_stock_symbol)
    assert result is True
    assert error_msg == None


def test_validate_stock_symbol_empty_stock_symbol(invalid_char_stock_symbol):
    # Simulate the user leaving the input blank
    result, error_msg = security.validate_stock_symbol("")

    assert result is False
    assert error_msg == "Stock symbol cannot be empty"


def test_validate_stock_symbol_long_stock_symbol(invalid_stock_symbol):
    result, error_msg = security.validate_stock_symbol(invalid_stock_symbol)

    assert result is False
    assert error_msg == "Stock symbol too long (max 5 characters)"


def test_validate_stock_symbol_non_letter_stock_symbol(invalid_char_stock_symbol):
    result, error_msg = security.validate_stock_symbol(invalid_char_stock_symbol)

    assert result is False
    assert error_msg == "Stock symbol must contain only letters (A-Z)"

