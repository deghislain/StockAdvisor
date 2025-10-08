"""Creates detailed reports based on the fetched data.
    The ReportGenerator compiles all the information, including data analysis, market sentiment, risk assessment,
     and the recommendation, into a comprehensive report.
    This report is formatted for easy reading and includes visual aids like charts and graphs.
"""
import asyncio, logging

from stock_adv_utils import DataType
from stock_adv_data_fetcher import DataFetcherAgent
from stock_adv_analysis_engine import FinAnalystAgent

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportGeneratorAgent:
    async def _fetch_fundamental_data(self, stock_symbol: str):
        logging.info(f"******************************_fetch_fundamental_data START with input: {stock_symbol}")
        data_fetcher_agent = DataFetcherAgent()
        fundamental_data = await data_fetcher_agent.fetch_data(stock_symbol, DataType.FUNDAMENTAL_DATA)
        logging.info(f"******************************_fetch_fundamental_data END with output: {fundamental_data}")
        return fundamental_data

    async def _perform_fundamental_analysis(self, stock_data):
        logging.info(f"******************************_perform_fundamental_analysis START with input: {stock_data}")
        fin_analyst_agent = FinAnalystAgent()
        fund_analysis = await fin_analyst_agent.analyse(stock_data)
        logging.info(f"******************************_perform_fundamental_analysis END with output: {fund_analysis}")
        return fund_analysis

    async def generate_report(self, stock_symbol: str):
        logging.info(f"******************************generate_report START with input: {stock_symbol}")
        fundamental_analysis = None
        fundamental_data = await self._fetch_fundamental_data(stock_symbol)
        if fundamental_data:
            fundamental_analysis = await self._perform_fundamental_analysis(fundamental_data)

        return fundamental_analysis


async def main():
    report_agent = ReportGeneratorAgent()
    generated_report = await report_agent.generate_report("IBM")


if __name__ == "__main__":
    asyncio.run(main())
