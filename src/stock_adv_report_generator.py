"""Creates detailed reports based on the fetched data.
    The ReportGenerator compiles all the information, including data analysis, market sentiment, risk assessment,
     and the recommendation, into a comprehensive report.
    This report is formatted for easy reading and includes visual aids like charts and graphs.
"""
import asyncio, logging

from stock_adv_analysis_engine import FinAnalystAgent
from stock_adv_market_sentiment import StockMarketSentimentAnalyzer

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportGeneratorAgent:
    def __init__(self, stock_symbol: str):
        self.fin_analyst_agent = FinAnalystAgent(stock_symbol)
        self.market_sentiment_analyzer = StockMarketSentimentAnalyzer(stock_symbol)
        self.fund_analysis = None
        self.market_sentiment_analysis = None
        self.stock_symbol = stock_symbol
        self.generated_report = None

    async def _perform_fundamental_analysis(self, ):
        logging.info(
            f"******************************_perform_fundamental_analysis START with input: {self.stock_symbol}")
        if self.stock_symbol:
            self.fund_analysis = await self.fin_analyst_agent.analyze()
        logging.info(
            f"******************************_perform_fundamental_analysis END with output: {self.fund_analysis}")
        return self.fund_analysis

    async def _perform_market_sentiment_analysis(self, ):
        logging.info(
            f"******************************_perform_market_sentiment_analysis START with input: {self.stock_symbol}")
        if self.stock_symbol:
            self.fund_analysis = await self.market_sentiment_analyzer.analyze()
        logging.info(
            f"******************************_perform_market_sentiment_analysis END with output: {self.fund_analysis}")
        return self.fund_analysis

    async def generate_report(self, ):
        logging.info(f"******************************generate_report START with input: {self.stock_symbol}")

        if self.stock_symbol:
            self.fund_analysis = await self._perform_fundamental_analysis()
        if self.stock_symbol:
            self.market_sentiment_analysis = await self._perform_market_sentiment_analysis()

        if self.fund_analysis and self.market_sentiment_analysis:
            self.fund_analysis = "{}\n\n\n".format(self.fund_analysis)
            self.generated_report = f"{self.fund_analysis} {self.market_sentiment_analysis}"

        if self.generated_report:
            return self.generated_report


async def main():
    report_agent = ReportGeneratorAgent("IBM")
    generated_report = await report_agent.generate_report()
    if generated_report:
        logging.info(f"******************************----****generate_report result: {generated_report}")


if __name__ == "__main__":
    asyncio.run(main())
