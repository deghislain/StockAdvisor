"""
    Evaluates the risk associated with specific stocks or portfolios.
    The RiskAssessment module evaluates the risk associated with the stock based on volatility, market conditions,
    and historical performance.
    It provides a risk score that helps users understand the potential risks of investing in the stock.
"""

import asyncio
from datetime import datetime

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
#from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.think import ThinkTool
#from beeai_framework.tools.weather import OpenMeteoTool

from stock_adv_utils import FIN_MODEL
from stock_adv_risk_assesment_tool import StockRiskAnalysisTool
from stock_adv_risk_prompts import risk_assessment_prompt

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class StockRiskAnalyzer:
    def __init__(self, ticker: str):
        """
            Initializes the Risk Analyst Agent.

               Args:
                   ticker: Stock symbol (e.g., 'IBM')
        """
        self.ticker_symbol = ticker.upper()

    async def _perform_risk_analysis(self, ) -> str:
        risk_assessment_agent = RequirementAgent(
            llm=ChatModel.from_name(FIN_MODEL, timeout=3000),
            tools=[ThinkTool(), StockRiskAnalysisTool()],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1),
                          ConditionalRequirement(StockRiskAnalysisTool, min_invocations=1, max_invocations=1,
                                                 consecutive_allowed=False,
                                                 only_success_invocations=True),
                          ],
            role="risk analyzer",
            instructions=risk_assessment_prompt
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=3000),
            tools=[
                ThinkTool(),
                HandoffTool(
                    risk_assessment_agent,
                    name="RiskAssessmentAgent",
                    description="Consult the Risk Assessment Agent for risk analysis given a stock symbol.",
                ),

            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )

        prompt = (
            f"""
                              You are a Senior Financial Analyst specializing in Risk Analysis for stock market. 
                              Your task: produce an exceptional risk analysis report for {self.ticker_symbol} stock.
                             

                           """)
        logging.info(f"******************************************User: {prompt}")
        agent_response = None
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            if response:
                agent_response = response.last_message.text

        except FrameworkError as err:
            print("Error:", err.explain())

        return agent_response

    async def analyze(self):
        report = await self._perform_risk_analysis()
        if report:
            logging.info(f"******************************----****generate_report result: {report}")
            return report


async def main():
    risk_analyzer = StockRiskAnalyzer("QUBT")
    risk_report = await risk_analyzer.analyze()
    if risk_report:
        logging.info(f"******************************----****risk_report result: {risk_report}")


if __name__ == "__main__":
    start = datetime.now()
    logging.info(f"--- Start Time = {start:%H:%M:%S} ---")
    asyncio.run(main())
    end = datetime.now()
    logging.info(f"--- End Time = {end:%H:%M:%S} ---")
    duration = end - start
    logging.info(f"--- Process duration = {duration} ---")
