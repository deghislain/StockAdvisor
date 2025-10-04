from pandas import DataFrame
import yfinance as yf
from pydantic import BaseModel, Field, ConfigDict

from typing import Optional
from beeai_framework.emitter import Emitter
from beeai_framework.tools import Tool, ToolRunOptions
from beeai_framework.context import RunContext
from beeai_framework.tools.search import SearchToolOutput, SearchToolResult
import asyncio
import logging
from enum import Enum

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DataType(Enum):
    FUNDAMENTAL_DATA = "FD"
    TECHNICAL_DATA = "NTD"
    NON_FINANCIAL_DATA = "NFD"


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
    description = """This tool fetch data from specialized websites based on a given stock symbol,
     providing users with up-to-date financial information and insights"""
    input_schema = DataFetcherToolInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "data_fetcher", "DataFetcher"],
            creator=self,
        )

    def _get_fundamental_data(self, input: DataFetcherToolInput) -> DataFetcherToolResult:
        logging.info(f"_get_fundamental_data START with input {input}")
        stock_symbol = yf.Ticker(input.stock_symbol)

        # yfinance may return `None` if a particular statement is unavailable
        income_statement = getattr(stock_symbol, "income_stmt", None)
        balance_sheet = getattr(stock_symbol, "balance_sheet", None)
        cash_flow = getattr(stock_symbol, "cash_flow", None)
        info = yf.Ticker(input.stock_symbol).info
        additional_info = DataFrame([info])

        result = DataFetcherToolResult(
            title=f"Financial statements for {input.stock_symbol}",
            description="""Income statement, balance sheet, cash‑flow data and company's attributes 
            such as ratios e.g P/E fetched via yfinance.""",
            url=f"https://finance.yahoo.com/quote/{input.stock_symbol}",
            income_statement=income_statement,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            additional_info=additional_info
        )
        #logging.info(f"_get_fundamental_data END with output {result}")
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
