"""Responsible for gathering stock data from various sources.The DataFetcher collects data from various sources,
including stock exchanges, financial news websites, and historical databases"""
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools.think import ThinkTool
from stock_adv_data_fetcher_tool import DataFetcherTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import Tool
from stock_adv_utils import SMALL_MODEL, LARGE_MODEL
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def fetch_data(stock_symbol: str):
    data_fetcher_agent = RequirementAgent(
        name="DataFetchAgent",
        llm=ChatModel.from_name(SMALL_MODEL),
        tools=[
            ThinkTool(),  # to reason
            DataFetcherTool()
        ],
        instructions=""" 
        You are an AI agent tasked with retrieving financial data essential for stock investors from Yahoo Finance. Please follow these guidelines to ensure thorough and accurate data retrieval:
    Data Retrieval Procedure

    Fetch the Data
        Use the DataFetcherTool to obtain financial data based on the provided stock symbol.

    Data Retrieval Sequence

        Income Statement: Collect the following metrics:
            Net Income
            Earnings per Share (EPS)
            Total Revenues
            Total Expenses
            Gross Profit Margin
            Operating Income (EBIT)
            Operating Cash Flow

        Balance Sheet: Gather the following data points:
            Total Assets
            Current Liabilities
            Long-Term Debt
            Total Liabilities
            Shareholders’ Equity

        Cash Flow Statement: Retrieve these key ratios:
            Debt-to-Equity Ratio
            Current Ratio
            Return on Equity (ROE)

        Additional information: Provide any extra relevant information that aids in fundamental analysis.

    Finalize Your Response
        Ensure that all the listed metrics and data points are included in your final response.
        Verify the completeness of the information, ensuring no critical details are omitted.

By adhering to this structured approach, you will deliver valuable and comprehensive data for stock investors.

        """,
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(DataFetcherTool, min_invocations=1),
        ]
    )
    main_agent = RequirementAgent(
        name="MainAgent",
        llm=ChatModel.from_name(SMALL_MODEL),
        tools=[
            ThinkTool(),
            HandoffTool(
                data_fetcher_agent,
                name="DataFetchAgent",
                description="Consult the data fetcher Agent when ask to fetch data about a provided stock.",
            ),

        ],
        requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
        # Log all tool calls to the console for easier debugging
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )
    agent_response = ""
    try:
        user_query = f"Fetch the data for this stock: {stock_symbol}."
        response = await main_agent.run(user_query, expected_output="Helpful and clear response.")
        agent_response = response.state.answer.text
        logging.info(f"*****************************fetch_data END with output: {agent_response}")
    except FrameworkError as err:
        logging.error(f"Error: {err.explain()}")
    return agent_response


async def main():
    await fetch_data("IBM")


if __name__ == "__main__":
    asyncio.run(main())
