import pandas as pd
from pandas import DataFrame, Series
import yfinance as yf
from pydantic import BaseModel, Field, ConfigDict
import streamlit as st
from typing import Optional
from beeai_framework.emitter import Emitter
from beeai_framework.tools import Tool, ToolRunOptions
from beeai_framework.context import RunContext
from beeai_framework.tools.search import SearchToolOutput, SearchToolResult
from stock_adv_utils import DataType
import asyncio
import logging

from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool, YahooFinanceNewsInput

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
    additional_info: Optional[Series] = None
    financial_news: Optional[str] = None
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

    @st.cache_data
    def get_fundamental_data(input: DataFetcherToolInput) -> DataFetcherToolResult:
        logging.info(f"_get_fundamental_data START with input {input}")

        result = None
        try:
            stock_data = yf.Ticker(input.stock_symbol)

            income_statement = getattr(stock_data, "income_stmt", None)
            balance_sheet = getattr(stock_data, "balance_sheet", None)
            cash_flow = getattr(stock_data, "cash_flow", None)
            info = yf.Ticker(input.stock_symbol).info
            additional_info = pd.Series(info)

            yf_news_tool = YahooFinanceNewsTool()

            financial_news = yf_news_tool.run(tool_input=input.stock_symbol)

            logging.info(
                f"**********************************************financial_news= {financial_news} *************")

            logging.info(
                f"**********************************************additional_info= {additional_info} *************")

            result = DataFetcherToolResult(
                title=f"Financial statements for {input.stock_symbol}",
                description="""Income statement, balance sheet, cash‑flow data and company's attributes 
                    such as ratios e.g P/E fetched via yfinance.""",
                url=f"https://finance.yahoo.com/quote/{input.stock_symbol}",
                income_statement=income_statement,
                balance_sheet=balance_sheet,
                cash_flow=cash_flow,
                additional_info=additional_info,
                financial_news=financial_news
            )
            logging.info(f"***********************************get_fundamental_data END with output {result}")
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
            fundamental_data = DataFetcherTool.get_fundamental_data(input)
            output = DataFetcherToolOutput(results=[fundamental_data])
        return output


async def main() -> None:
    tool = DataFetcherTool()
    stock_symbol = "IBM"
    data_type = DataType("FFD")
    input = DataFetcherToolInput(stock_symbol=stock_symbol, data_type=data_type)
    data = await tool.run(input)
    logging.info(f"///////////////////////////////{data}")


if __name__ == "__main__":
    asyncio.run(main())
