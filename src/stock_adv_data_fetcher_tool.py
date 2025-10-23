from pandas import DataFrame
import yfinance as yf
from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from beeai_framework.emitter import Emitter
from beeai_framework.tools import Tool, ToolRunOptions
from beeai_framework.context import RunContext
from beeai_framework.tools.search import SearchToolOutput, SearchToolResult
from stock_adv_utils import DataType
import asyncio
import logging
from stock_adv_data_fetcher_utils import (
    filter_necessary_additional_info_data,
    filter_necessary_fundamental_data,
    INCOME_STATEMENT_DATA_KEYS,
    BALANCE_SHEET_DATA_KEYS,
    CASH_FLOW_DATA_KEYS
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DataFetcherToolInput(BaseModel):
    stock_symbol: str = Field(description="Stock symbol of the data to fetch.")
    data_type: DataType = Field(description="Type of stock data to fetch.. eg. Fundamental data")


class DataFetcherToolResult(SearchToolResult):
    title: str
    description: str
    url: str
    income_statement: Optional[DataFrame] = None
    balance_sheet: Optional[DataFrame] = None
    cash_flow: Optional[DataFrame] = None
    additional_info: Optional[DataFrame] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DataFetcherToolOutput(SearchToolOutput):
    pass


class DataFetcherTool(Tool[DataFetcherToolInput, ToolRunOptions, DataFetcherToolOutput]):
    name = "DataFetcher"
    description = """This tool fetch data from Yahoo Finance websites based on a given stock symbol,
     providing users with up-to-date financial information and insights"""
    input_schema = DataFetcherToolInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "data_fetcher", "DataFetcher"],
            creator=self,
        )

    def _get_fundamental_data(self, input: DataFetcherToolInput) -> DataFetcherToolResult:
        logging.info(f"_get_fundamental_data START with input {input}")
        result = None
        try:
                stock_data = yf.Ticker(input.stock_symbol)

                income_statement = getattr(stock_data, "income_stmt", None)
                filtered_income_statement = filter_necessary_fundamental_data(income_statement, INCOME_STATEMENT_DATA_KEYS, '#### Income Statement: ')
                balance_sheet = getattr(stock_data, "balance_sheet", None)
                filtered_balance_sheet = filter_necessary_fundamental_data(balance_sheet, BALANCE_SHEET_DATA_KEYS, '#### Balance Sheet: ')
                cash_flow = getattr(stock_data, "cash_flow", None)
                filtered_cash_flow = filter_necessary_fundamental_data(cash_flow, CASH_FLOW_DATA_KEYS, '#### Cash Flow: ')
                info = yf.Ticker(input.stock_symbol).info
                filtered_necessary_additional_info= filter_necessary_additional_info_data(info)
            #pd.set_option('display.max_columns', None)  # Display all columns
            #pd.set_option('display.width', 1000)  # Adjust width to show more content
            #pd.set_option('display.max_rows', None)  # Display all rows (if more than one)

                logging.info(f"**********************************************filtered_income_statement= {filtered_income_statement} *************")
                logging.info(f"**********************************************filtered_balance_sheet= {filtered_balance_sheet} *************")
                logging.info(f"**********************************************filtered_cash_flow= {filtered_cash_flow} *************")

                logging.info(f"**********************************************filtered_necessary_additional_info= {filtered_necessary_additional_info} *************")

                result = DataFetcherToolResult(
                    title=f"Financial statements for {input.stock_symbol}",
                    description="""Income statement, balance sheet, cash‑flow data and company's attributes 
                    such as ratios e.g P/E fetched via yfinance.""",
                    url=f"https://finance.yahoo.com/quote/{input.stock_symbol}",
                    income_statement=filtered_income_statement,
                    balance_sheet=filtered_balance_sheet,
                    cash_flow=filtered_cash_flow,
                    additional_info=filtered_necessary_additional_info
                )
                logging.info(f"***********************************_get_fundamental_data END with output {result}")
        except Exception as ex:
            logging.error(ex)

        return result

    #def _get_technical_data(self, stock_symbol: str, start_date: str, end_date : str)-> DataFetcherToolResult:

    async def _run(
            self,
            input: DataFetcherToolInput,
            options: ToolRunOptions | None,
            context: RunContext,
    ) -> DataFetcherToolOutput:
        output = None
        if input.data_type.value == DataType.FUNDAMENTAL_DATA.value:
            fundamental_data = self._get_fundamental_data(input)
            output = DataFetcherToolOutput(results=[fundamental_data])
        return output


async def main() -> None:
    tool = DataFetcherTool()
    stock_symbol = "IBM"
    data_type = DataType("FD")
    input = DataFetcherToolInput(stock_symbol=stock_symbol, data_type=data_type)
    data = await tool.run(input)
    logging.info(f"///////////////////////////////{data}")


if __name__ == "__main__":
    asyncio.run(main())
