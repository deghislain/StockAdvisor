"""Analyzes stock performance and trends. The fetched data is then passed to the AnalysisEngine, which performs
    technical and fundamental analysis.
    It evaluates key metrics such as price trends, volume, earnings reports, and other relevant indicators.
"""
import logging
from langchain_ollama import ChatOllama
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.errors import FrameworkError
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from stock_adv_utils import SMALL_MODEL, FIN_MODEL
from beeai_framework.tools.think import ThinkTool
from stock_adv_data_fetcher_tool import DataFetcherTool
from stock_adv_prompts import (get_fundamental_analysis_prompt,
                               get_fundamental_analysis_review_prompt,
                               get_fundamental_analysis_improve_prompt)

fin_analyst_agent = ChatOllama(model=FIN_MODEL, temperature=0, timeout=2400)

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
            llm=ChatModel.from_name(SMALL_MODEL, timeout=3000),
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
            llm=ChatModel.from_name(FIN_MODEL, timeout=6000),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=get_fundamental_analysis_prompt(),
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        quality_check_agent = RequirementAgent(
            name="QualityCheckAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=3000),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=get_fundamental_analysis_review_prompt(),
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        fundamental_analysis_enhancer_agent = RequirementAgent(
            name="FundamentalAnalysisEnhancerAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=3000),
            tools=[
                ThinkTool(),  # to reason
            ],
            # instructions=""" Provide a fundamental analysis given stock's data""",
            instructions=get_fundamental_analysis_improve_prompt(),
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(SMALL_MODEL, timeout=6000),
            tools=[
                ThinkTool(),
                HandoffTool(
                    data_fetcher_agent,
                    name="DataFetcherAgent",
                    description="Consult the Data Fetcher Agent for retrieving financial stock data.",
                ),
                HandoffTool(
                    financial_analyst_agent,
                    name="FinancialAnalystAgent",
                    description="""Consult the Financial Analyst Agent for fundamental analysis using data fetched
                         by the Data Fetcher Agent.""",
                ),
                HandoffTool(
                    quality_check_agent,
                    name="QualityCheckAgent",
                    description="""Consult the Quality Check Agent to review the fundamental analysis written by 
                        the Financial Analyst Agent using data retrieved by the Data Fetcher Agent.""",
                ),
                HandoffTool(
                    fundamental_analysis_enhancer_agent,
                    name="FundamentalAnalysisEnhancerAgent",
                    description="""Consult the Fundamental Analysis Enhancer Agent to improve 
                    the fundamental analysis written by the Financial Analyst Agent using 
                    the feedback provided by the Quality Check  Agent.""",
                ),

            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )

        prompt = (
            f"""
                        You are a Senior Financial Analyst specializing in fundamental Analysis for stock market. 
                        Your task: produce an exceptional fundamental analysis report for {self.ticker_symbol} stock
                         by iterating between research, analysis, and a focused quality review. Follow these steps exactly:

                        Research — fetch fundamental stock data and info.
                        Initial Analysis — produce a concise, structured fundamental analysis report 
                        Quality Review — perform a quality-review of the initial fundamental analysis report.
                        Revision — apply the review's fixes and produce the final, improved fundamental analysis report.

                        Constraints and rules:
                        Use concise, data-driven language and quantify claims where possible. Flag uncertainties.
                        Do not fabricate numbers; if data is unavailable, state which inputs were missing and why.
                        Cite sources for all factual claims.
                        Output: Return the revised final report to the user.
                        Use "price as of" timestamps for any market data.

                     """)
        logging.info(f"*-*-/-* User Prompt**-***-: {prompt}")
        agent_response = None
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            agent_response = response.state.answer.text
            logging.info(
                f"...................................................Fundamental analysis {agent_response}")
        except FrameworkError as err:
            logging.error(f"Error: {err.explain()}")
        return agent_response

    async def analyze(self, ) -> str:
        fundamental_analysis = await self._perform_fundamental_analysis()
        return fundamental_analysis
