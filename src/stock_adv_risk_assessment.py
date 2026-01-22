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
from beeai_framework.tools.think import ThinkTool

#from stock_adv_utils import FIN_MODEL
from config import ModelConfig as mc
from stock_adv_risk_assesment_tool import StockRiskAnalysisTool
from stock_adv_risk_instructions import (RISK_ASSESSMENT_INSTRUCTIONS,
                                         RISK_ASSESSMENT_REVIEW_INSTRUCTIONS,
                                         RISK_ASSESSMENT_IMPROVE_INSTRUCTIONS)
from stock_adv_prompts import get_stock_risk_assessment_prompt

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
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[ThinkTool(), StockRiskAnalysisTool()],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1),
                          ConditionalRequirement(StockRiskAnalysisTool, min_invocations=1, max_invocations=1,
                                                 consecutive_allowed=False,
                                                 only_success_invocations=True),
                          ],
            role="risk analyzer",
            instructions=RISK_ASSESSMENT_INSTRUCTIONS
        )
        quality_check_agent = RequirementAgent(
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[ThinkTool()],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="quality checker",
            instructions=RISK_ASSESSMENT_REVIEW_INSTRUCTIONS
        )
        risk_assessment_enhancer_agent = RequirementAgent(
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[ThinkTool()],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="risk assessment enhancer",
            instructions=RISK_ASSESSMENT_IMPROVE_INSTRUCTIONS
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(mc.fin_model, timeout=12000, temperature=0),
            tools=[
                ThinkTool(),
                HandoffTool(
                    risk_assessment_agent,
                    name="RiskAssessment",
                    description="Consult the Risk Assessment Agent for risk analysis given a stock symbol.",
                ),
                HandoffTool(
                    quality_check_agent,
                    name="QualityChecking",
                    description="""Consult the Quality Check Agent to review the risk analysis produce by 
                                            the Risk Assessment Agent.""",
                ),
                HandoffTool(
                    risk_assessment_enhancer_agent,
                    name="RiskAssessmentEnhance",
                    description="""Consult the Risk Assessment Enhancer Agent to improve 
                                        the risk assessment produce by the Financial Analyst Agent using 
                                        the feedback provided by the Quality Check  Agent.""",
                ),

            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )

        prompt = get_stock_risk_assessment_prompt(self.ticker_symbol)
        logging.info(f"Starting risk assessment for: {self.ticker_symbol}")
        agent_response = None
        
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            
            # Safely extract the response
            if response and hasattr(response, 'last_message') and hasattr(response.last_message, 'text'):
                risk_analysis_report = response.last_message.text
                
                if risk_analysis_report:
                    agent_response = risk_analysis_report
                    logging.info(f"Risk assessment completed successfully for {self.ticker_symbol}")
                else:
                    logging.warning(f"Empty risk assessment report for {self.ticker_symbol}")
                    agent_response = f"Unable to generate risk assessment for {self.ticker_symbol}. Please try again."
            else:
                logging.error("Unexpected response structure from risk assessment agent")
                agent_response = f"Technical error occurred during risk assessment for {self.ticker_symbol}."
                
        except FrameworkError as err:
            error_msg = f"Framework error in risk assessment: {err.explain()}"
            logging.error(error_msg, exc_info=True)
            agent_response = f"Analysis framework error for {self.ticker_symbol}. Please try again later."
            
        except AttributeError as err:
            logging.error(f"Response structure error in risk assessment: {err}", exc_info=True)
            agent_response = f"Data structure error during risk assessment of {self.ticker_symbol}."
            
        except Exception as err:
            logging.error(f"Unexpected error in risk assessment for {self.ticker_symbol}: {err}", exc_info=True)
            agent_response = f"Unexpected error occurred during risk assessment of {self.ticker_symbol}."

        return agent_response

    async def analyze(self):
        report = await self._perform_risk_analysis()
        if report:
            logging.info(f"******************************----****generate_report result: {report}")
            return report


async def main():
    risk_analyzer = StockRiskAnalyzer("AUID")
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
