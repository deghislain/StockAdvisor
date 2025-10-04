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
from stock_adv_utils import DataType
from stock_adv_prompts import DATA_FETCHING_PROMPT
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class DataFetcherAgent:
    """Responsible for gathering stock data from various sources."""
    async def _retrieve_data(self, prompt: str):
        """
              Use a lightweight LLM to fetch the requested data.
              Returns the raw response text.
              """
        # Build the agent that will perform the actual fetching
        data_fetcher_agent = RequirementAgent(
            name="DataFetchAgent",
            llm=ChatModel.from_name(SMALL_MODEL),
            tools=[
                ThinkTool(),  # to reason
                DataFetcherTool()
            ],
            instructions=DATA_FETCHING_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(DataFetcherTool, min_invocations=1),
            ]
        )
        # The main agent orchestrates the hand‑off to the data fetcher
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
            user_query = prompt
            response = await main_agent.run(user_query, expected_output="Helpful and clear response.")
            agent_response = response.state.answer.text
            logging.info(f"*****************************fetch_data END with output: {agent_response}")
        except FrameworkError as err:
            logging.error(f"Error: {err.explain()}")
        return agent_response

    async def fetch_data(self, stock_symbol: str, data_type: DataType):
        """
               Public entry point that composes the user query and invokes internal logic.
               """
        user_query = f"Fetch the data for this stock: {stock_symbol}. Use {data_type} as data type"
        return await self._retrieve_data(user_query)


async def main():
    data_fetcher_agent = DataFetcherAgent()
    await data_fetcher_agent.fetch_data("IBM", DataType.FUNDAMENTAL_DATA)


if __name__ == "__main__":
    asyncio.run(main())
