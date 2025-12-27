"""Creates detailed reports based on the fetched data.
    The ReportGenerator compiles all the information, including data analysis, market sentiment, risk assessment,
     and the recommendation, into a comprehensive report.
    This report is formatted for easy reading and includes visual aids like charts and graphs.
"""
import asyncio, logging

from stock_adv_analysis_engine import FinAnalystAgent
from stock_adv_reviewer_agent import QualityCheckAgent

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportGeneratorAgent:
    def __init__(self):
        self.fin_analyst_agent = FinAnalystAgent()
        self.quality_check_agent = QualityCheckAgent()
        self.fund_analysis = None
        self.reviewed_fund_analysis = None

    async def _perform_fundamental_analysis(self, stock_symbol):
        logging.info(
            f"******************************_perform_fundamental_analysis START with input: {stock_symbol}")
        if stock_symbol:
            self.fund_analysis = await self.fin_analyst_agent.analyse(stock_symbol)
        logging.info(
            f"******************************_perform_fundamental_analysis END with output: {self.fund_analysis}")
        return self.fund_analysis

    async def _review_and_improve_fundamental_analysis(self):
        logging.info(f"******************************_review_and_improve_fundamental_analysis START "
                     f"with input: *************{self.fund_analysis}")
        self.reviewed_fund_analysis = await self.quality_check_agent.review_and_improve_fundamental_analysis(
            self.fund_analysis)
        logging.info(
            f"******************************_review_and_improve_fundamental_analysis END with output: {self.reviewed_fund_analysis}")
        return self.reviewed_fund_analysis

    async def generate_report(self, stock_symbol: str):
        logging.info(f"******************************generate_report START with input: {stock_symbol}")
        '''
        self.fundamental_data = await self._fetch_fundamental_data(stock_symbol)
        if self.fundamental_data:
            self.fund_analysis = await self._perform_fundamental_analysis()
        '''
        if stock_symbol:
            self.fund_analysis = await self._perform_fundamental_analysis(stock_symbol)

        return self.fund_analysis


async def main():
    report_agent = ReportGeneratorAgent()
    generated_report = await report_agent.generate_report("IBM")


if __name__ == "__main__":
    asyncio.run(main())
