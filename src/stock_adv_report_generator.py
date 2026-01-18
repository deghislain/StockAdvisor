"""Creates detailed reports based on the fetched data.
    The ReportGenerator compiles all the information, including data analysis, market sentiment, risk assessment,
     and the recommendation, into a comprehensive report.
    This report is formatted for easy reading and includes visual aids like charts and graphs.
"""

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.errors import FrameworkError

import asyncio, logging
from typing import Any

from stock_adv_analysis_engine import FinAnalystAgent
from stock_adv_market_sentiment import StockMarketSentimentAnalyzer
from stock_adv_risk_assessment import StockRiskAnalyzer
from stock_adv_utils import FIN_MODEL, SMALL_MODEL
from stock_adv_report_instructions import REPORT_WRITER_INSTRUCTIONS
from stock_adv_prompts import get_final_report_prompt

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportGeneratorAgent:
    def __init__(self, stock_symbol: str):
        self.fin_analyst_agent = FinAnalystAgent(stock_symbol)
        self.market_sentiment_analyzer = StockMarketSentimentAnalyzer(stock_symbol)
        self.risk_assessment_agent = StockRiskAnalyzer(stock_symbol)

        self.fund_analysis = None
        self.market_sentiment_analysis = None
        self.stock_symbol = stock_symbol
        self.generated_report = None
        self.report_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    async def _perform_fundamental_analysis(self, ):
        logging.info(
            f"******************************_perform_fundamental_analysis START with input: {self.stock_symbol}")
        if self.stock_symbol:
            self.fund_analysis = await self.fin_analyst_agent.analyze()
            if self.fund_analysis:
                await self.report_queue.put(("fund_analysis", self.fund_analysis))
        logging.info(
            f"******************************_perform_fundamental_analysis END with output: {self.fund_analysis}")
        # return self.fund_analysis

    async def _perform_market_sentiment_analysis(self, ):
        logging.info(
            f"******************************_perform_market_sentiment_analysis START with input: {self.stock_symbol}")
        if self.stock_symbol:
            self.market_sentiment_analysis = await self.market_sentiment_analyzer.analyze()
            if self.market_sentiment_analysis:
                await self.report_queue.put(("market_sent_analysis", self.market_sentiment_analysis))
        logging.info(
            f"******************************_perform_market_sentiment_analysis END with output: {self.fund_analysis}")

    async def _perform_risk_assessment(self, ):
        logging.info(f"******************************_perform_risk_assessment START with input: {self.stock_symbol}")
        if self.stock_symbol:
            self.risk_assessment = await self.risk_assessment_agent.analyze()
            if self.risk_assessment:
                await self.report_queue.put(("risk_assessment", self.risk_assessment))
        logging.info(
            f"******************************_perform_risk_assessment END with output: {self.risk_assessment}")

    async def _write_final_report(self, initial_report: str) -> str:
        logging.info(f"******************************_write_final_report STARTS with input: {initial_report} *******///")
        report_writer = RequirementAgent(
            llm=ChatModel.from_name(SMALL_MODEL, timeout=6000),
            tools=[ThinkTool(), ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="Report Writer",
            instructions=REPORT_WRITER_INSTRUCTIONS,
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(SMALL_MODEL, timeout=12000),
            tools=[
                ThinkTool(),
                HandoffTool(
                    report_writer,
                    name="ReportWriting",
                    description="Consult the Report Writer Agent for report writing.",
                ),



            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )
        prompt = get_final_report_prompt(initial_report)
        agent_response = None
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            final_report = response.last_message.text
            if final_report:
                agent_response = final_report

        except FrameworkError as err:
            print("Error:", err.explain())
        logging.info(f"******************************_write_final_report ENDS with output: {agent_response}")
        return agent_response

    async def generate_report(self, ):
        logging.info(f"******************************generate_report START with input: {self.stock_symbol}")
        tasks = [
            asyncio.create_task(self._perform_fundamental_analysis()),
            asyncio.create_task(self._perform_market_sentiment_analysis()),
            asyncio.create_task(self._perform_risk_assessment())
        ]

        # Wait for the two results (order depends on which thread finishes first)
        results: dict[str, Any] = {}
        for _ in range(3):
            logging.info(f"-----------------*********------------LOOP")
            kind, payload = await self.report_queue.get()  # blocks until a result is available
            logging.info(f"-----------------*********------------Task Completed {kind} with output {payload}")
            results[kind] = payload
        await asyncio.gather(*tasks)
        separator = "\n\n\n"
        initial_report = separator.join([results["fund_analysis"], results["market_sent_analysis"],
                                         results["risk_assessment"]])
        if initial_report:
            self.generated_report = await self._write_final_report(initial_report)
            logging.info(f"******************************generate_report ENDS with output: {self.generated_report}")
            self.report_queue.task_done()
            return self.generated_report


'''
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
'''


async def main():
    report_agent = ReportGeneratorAgent("IBM")
    generated_report = await report_agent.generate_report()
    if generated_report:
        logging.info(f"******************************----****generate_report result: {generated_report}")


if __name__ == "__main__":
    asyncio.run(main())
