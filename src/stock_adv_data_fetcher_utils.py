import pandas as pd

from typing import Dict, Any, List
import logging

LARGE_MODEL = "ollama:llama3.1:8b"
SMALL_MODEL = "ollama:granite4:micro-h"
FIN_MODEL = "0xroyce/plutus:latest"
DATA_DATES = ['2024-12-31', '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31']

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for the keys (optional, but helps avoid hardcoding strings)
ADDITIONAL_INFO_KEYS = {
    "currentPrice", "previousClose", "marketCap", "fiftyTwoWeekLow", "fiftyTwoWeekHigh",
    "dividendYield", "payoutRatio", "trailingPE", "forwardPE", "priceToSalesTrailing12Months",
    "priceToBook", "grossMargins", "ebitdaMargins", "operatingMargins", "earningsGrowth",
    "revenueGrowth", "totalRevenue", "freeCashflow", "operatingCashflow", "quickRatio",
    "currentRatio", "returnOnAssets", "returnOnEquity", "totalDebt", "enterpriseValue",
    "enterpriseToRevenue", "beta", "bookValue", "sharesOutstanding", "floatShares"
}

INCOME_STATEMENT_DATA_KEYS = [
    'Normalized EBITDA',
    'EBITDA',
    'EBIT',
    'Normalized Income'
    'Net Income From Continuing And Discontinued Operation',
    'Total Expenses',
    'Diluted EPS',
    'Basic EPS',
    'Net Income',
    'Net Income Including Noncontrolling Interests',
    'Operating Income',
    'Gross Profit',
    'Cost Of Revenue',
    'Total Revenue',
    'Operating Revenue',
    'Total Unusual Items'

]

BALANCE_SHEET_DATA_KEYS = [
    'Total Assets',
    'Total Liabilities',
    'Total Equity',
    'Total Debt',
    'Net Debt',
    'Total Capitalization',
    'Total Non Current Assets',
    'Current Assets',
    'Current Liabilities',
    'Long Term Debt',
    'Current Debt',
    'Total Non Current Liabilities Net Minority Interes',
    'Total Current Liabilities',
    'Total Current Assets',
    'Stockholders Equity',
    'Retained Earnings',
    'Working Capital',
    'Net PPE',
    'Cash and Cash Equivalents',
    'Total Cash',
    'Total Current Assets',
    'Total Current Liabilities',
    'Total Non Current Assets',
    'Total Non Current Liabilities',
    'Total Liabilities',
    'Total Equity',
    'Total Debt',
    'Net Debt',
    'Total Capitalization',
    'Total Assets'
]

CASH_FLOW_DATA_KEYS = [
    'Operating Cash Flow',
    'Cash Flow From Continuing Operating Activities',
    'Free Cash Flow',
    'Capital Expenditure',
    'Net Income From Continuing Operations',
    'Depreciation Amortization Depletion',
    'Depreciation And Amortization',
    'Depreciation',
    'Cash Dividends Paid',
    'Common Stock Dividend Paid',
    'Issuance Of Debt',
    'Repayment Of Debt',
    'Long Term Debt Issuance',
    'Long Term Debt Payments',
    'Change In Other Working Capital',
    'Change In Inventory',
    'Change In Receivables',
    'Change In Payables And Accrued Expense',
    'Change In Account Payable'

]


def filter_necessary_additional_info_data(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter essential fundamental analysis data from the provided additional info.

    Args:
        data (Dict[str, Any]): A dictionary containing stock data, where the keys are data
        field names and the values are corresponding financial metrics.

    Returns:
        pd.DataFrame: A DataFrame containing the fundamental analysis data extracted.
    """

    # Extract the relevant fields using a dictionary comprehension
    filtered_stock_data = {key: data.get(key) for key in ADDITIONAL_INFO_KEYS}

    # Check for missing required data and raise a ValueError if needed (optional)
    #if any(value is None for value in filtered_stock_data.values()):
        #raise ValueError("Some required fundamental data is missing.")

    # Convert the dictionary to a pandas DataFrame
    filtered_additional_info = pd.DataFrame({'Additional Information': filtered_stock_data})

    return filtered_additional_info


def filter_by_year(stock_data: pd.DataFrame, keys: List[str], data_type: str) -> pd.DataFrame:
    logging.info(f"-----------------------------filter_by_year START")
    filtered_stock_data = pd.DataFrame({})
    pd.set_option('display.max_columns', None)  # Display all columns
    pd.set_option('display.width', 1000)  # Adjust width to show more content
    pd.set_option('display.max_rows', None)  # Display all rows (if more than one)
    for year in DATA_DATES:
        try:
            logging.info(f"-----------------------------filtering year = {stock_data[year]}")
            current_stock_data = get_filtered_stock_data(stock_data[year], keys)
            if current_stock_data:
                filtered_stock_data[data_type + year] = current_stock_data
        except Exception as err:
            logging.error(f"Error: {err}")

    logging.info(f"-----------------------------filter_by_year END with output = {filtered_stock_data}")
    return filtered_stock_data


def get_filtered_stock_data(stock_data, necessary_keys):
    """
    This function filters the income statement data and returns only the necessary data for fundamental analysis.

    Parameters:
        stock_data (dict): A dictionary where keys are the data labels and values are the corresponding data points.
        param necessary_keys: data labels needed to retrieve the necessary data

    Returns:
        dict: A filtered dictionary containing only the necessary data for fundamental analysis.

    """

    # Filter the income statement data to include only necessary keys
    filtered_data = {
        key: value for key, value in stock_data.items()
        if key in necessary_keys and value is not None
    }

    return filtered_data


def filter_necessary_fundamental_data(stock_data: pd.DataFrame, keys: List[str], data_type: str) -> pd.DataFrame:
    logging.info(f"-----------------------------filter_necessary_fundamental_data START")
    return filter_by_year(stock_data, keys, data_type)
