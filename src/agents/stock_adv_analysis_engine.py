"""Analyzes stock performance and trends. The fetched data is then passed to the AnalysisEngine, which performs
    technical and fundamental analysis.
    It evaluates key metrics such as price trends, volume, earnings reports, and other relevant indicators.
"""
import logging
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool

from config.config import ModelConfig as mc
from tools.stock_adv_data_fetcher_tool import DataFetcherTool
from config.stock_adv_analysis_instructions import (FUNDAMENTAL_ANALYSIS_INSTRUCTIONS,
                                                    FUNDAMENTAL_ANALYSIS_REVIEW_INSTRUCTION,
                                                    FUNDAMENTAL_ANALYSIS_IMPROVE_INSTRUCTION)

from config.stock_adv_prompts import get_stock_analysis_prompt
from utils.logging_helper import log_performance

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class FinAnalystAgent:
    def __init__(self, ticker: str):
        """
            Initializes the Financial Analyst Agent.

               Args:
                   ticker: Stock symbol (e.g., 'IBM')
        """
        self.ticker_symbol = ticker.upper()

    async def _perform_fundamental_analysis(self, ) -> str:
        data_fetcher_agent = RequirementAgent(
            name="DataFetchAgent",
            llm=ChatModel.from_name(mc.small_model, timeout=6000),
            tools=[
                ThinkTool(),  # to reason
                DataFetcherTool()
            ],
            instructions="Retrieve financial stock data given a stock symbol",
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(DataFetcherTool, min_invocations=1, max_invocations=1, consecutive_allowed=False,
                                       only_success_invocations=True),
            ],
        )

        financial_analyst_agent = RequirementAgent(
            name="FinancialAnalystAgent",
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=FUNDAMENTAL_ANALYSIS_INSTRUCTIONS,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        quality_check_agent = RequirementAgent(
            name="QualityCheckAgent",
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=FUNDAMENTAL_ANALYSIS_REVIEW_INSTRUCTION,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        fundamental_analysis_enhancer_agent = RequirementAgent(
            name="FundamentalAnalysisEnhancerAgent",
            llm=ChatModel.from_name(mc.fin_model, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=FUNDAMENTAL_ANALYSIS_IMPROVE_INSTRUCTION,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(mc.small_model, timeout=12000, temperature=0),
            tools=[
                ThinkTool(),
                HandoffTool(
                    data_fetcher_agent,
                    name="DataFetcherAgent",
                    description="Consult the Data Fetcher Agent for retrieving financial stock data.",
                ),
                HandoffTool(
                    financial_analyst_agent,
                    name="FinancialAnalysis",
                    description="""Consult the Financial Analyst Agent for fundamental analysis using data fetched
                         by the Data Fetcher Agent.""",
                ),
                HandoffTool(
                    quality_check_agent,
                    name="QualityChecking",
                    description="""Consult the Quality Check Agent to review the fundamental analysis written by 
                        the Financial Analyst Agent using data retrieved by the Data Fetcher Agent.""",
                ),
                HandoffTool(
                    fundamental_analysis_enhancer_agent,
                    name="FundamentalAnalysisEnhancement",
                    description="""Consult the Fundamental Analysis Enhancer Agent to improve 
                    the fundamental analysis written by the Financial Analyst Agent using 
                    the feedback provided by the Quality Check  Agent.""",
                ),

            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )

        prompt = get_stock_analysis_prompt(self.ticker_symbol)
        logging.info(f"Starting fundamental analysis for: {self.ticker_symbol}")
        agent_response = None

        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")

            # Safely extract the response
            if response and hasattr(response, 'last_message') and hasattr(response.last_message, 'text'):
                fund_analys_report = response.last_message.text

                if fund_analys_report:
                    agent_response = fund_analys_report
                    logging.info(f"Fundamental analysis completed successfully for {self.ticker_symbol}")
                else:
                    logging.warning(f"Empty fundamental analysis report for {self.ticker_symbol}")
                    agent_response = f"Unable to generate fundamental analysis for {self.ticker_symbol}. Please try again."
            else:
                logging.error("Unexpected response structure from fundamental analysis agent")
                agent_response = f"Technical error occurred during fundamental analysis for {self.ticker_symbol}."

        except FrameworkError as err:
            error_msg = f"Framework error in fundamental analysis: {err.explain()}"
            logging.error(error_msg, exc_info=True)
            agent_response = f"Analysis framework error for {self.ticker_symbol}. Please try again later."

        except AttributeError as err:
            logging.error(f"Response structure error in fundamental analysis: {err}", exc_info=True)
            agent_response = f"Data structure error during analysis of {self.ticker_symbol}."

        except Exception as err:
            logging.error(f"Unexpected error in fundamental analysis for {self.ticker_symbol}: {err}", exc_info=True)
            agent_response = f"Unexpected error occurred during fundamental analysis of {self.ticker_symbol}."

        return agent_response

    @log_performance
    async def analyze(self, ) -> str:
        fundamental_analysis = await self._perform_fundamental_analysis()
        return fundamental_analysis
