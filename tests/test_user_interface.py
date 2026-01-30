import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import src.ui.stock_adv_user_interface as user_interface


def test_get_user_input_valid_stock_symbol(mock_st, sample_stock_symbol):
    mock_st.text_input.return_value = sample_stock_symbol

    result = user_interface.get_user_input()

    assert result == sample_stock_symbol
    mock_st.text_input.assert_called_once()


def test_get_user_input_strips_and_uppercases(mock_st, sample_stock_symbol):
    # Simulate the user typing a mixed‑case string with surrounding spaces
    mock_st.text_input.return_value = "  ibm  "

    result = user_interface.get_user_input()

    # The function should strip whitespace and convert to upper case
    assert result == sample_stock_symbol
    mock_st.text_input.assert_called_once()


def test_get_user_input_empty_string(mock_st):
    # Simulate the user leaving the input blank
    mock_st.text_input.return_value = "   "

    result = user_interface.get_user_input()

    # After stripping, an empty string remains; upper‑casing has no effect
    assert result == ""
    mock_st.text_input.assert_called_once()


def test_get_user_input_long_stock_symbol(mock_st, invalid_stock_symbol):
    mock_st.text_input.return_value = invalid_stock_symbol
    result = user_interface.get_user_input()

    assert result == ""
    mock_st.text_input.assert_called_once()


def test_get_user_input_invalid_stock_symbol(mock_st, invalid_char_stock_symbol):
    mock_st.text_input.return_value = invalid_char_stock_symbol
    result = user_interface.get_user_input()

    assert result == ""
    mock_st.text_input.assert_called_once()

