"""Responsible for gathering stock data from various sources.The DataFetcher collects data from various sources,
including stock exchanges, financial news websites, and historical databases"""
from pandas import DataFrame
import yfinance as yf
from pydantic import BaseModel, Field, ConfigDict

from typing import Any, Optional
from beeai_framework.emitter import Emitter
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions
from beeai_framework.context import RunContext
from beeai_framework.tools.search import SearchToolOutput, SearchToolResult
import asyncio
from enum import Enum
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DataType(str, Enum):
    """The type of data being fetched: Fundamental(FD), Technical(TD), Non Financial(NFD)"""
    FD = "FD"
    NFD = "NFD"
    TD = "TD"


class DataFetcherToolInput(BaseModel):
    stock_symbol: str = Field(description="Stock symbol of the data to retrieve.")
    data_type: DataType = Field(description="The type of data being fetched. eg fundamental data")


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
    description = """This tool retrieves data from specialized websites based on a given stock symbol,
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
            description="Income statement, balance sheet and cash‑flow data fetched via yfinance.",
            url=f"https://finance.yahoo.com/quote/{input.stock_symbol}",
            income_statement=income_statement,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            additional_info=additional_info
        )
        return result

    #def _get_technical_data(self, stock_symbol: str, start_date: str, end_date : str)-> DataFetcherToolResult:

    async def _run(
            self,
            input: DataFetcherToolInput,
            options: ToolRunOptions | None,
            context: RunContext,
    ) -> DataFetcherToolOutput:
        output = None
        if input.data_type.value == DataType.FD.value:
            fundamental_data = self._get_fundamental_data(input)
            if fundamental_data:
                output = DataFetcherToolOutput(results=[fundamental_data])

        return output


async def main() -> None:
    tool = DataFetcherTool()
    stock_symbol = "IBM"
    input = DataFetcherToolInput(stock_symbol=stock_symbol, data_type=DataType.FD)
    data = await tool.run(input)
    logging.info(f"///////////////////////////////{data}")


if __name__ == "__main__":
    asyncio.run(main())
