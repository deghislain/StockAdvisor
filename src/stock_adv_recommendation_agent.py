"""Provides buy/sell/hold recommendations based on analysis.
    The RecommendationAgent searches the internet and uses the insights from the AnalysisEngine and the sentiment score from
    the MarketSentiment module to generate a buy, sell, or hold recommendation.
    It considers the risk assessment to ensure that the recommendation aligns with the user's risk tolerance.
"""

from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools.think import ThinkTool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import Tool
from stock_adv_utils import SMALL_MODEL
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def call_recommendation_agent(user_query: str):
    recom_agent_resp = ""
    web_search_agent = RequirementAgent(
        llm=ChatModel.from_name(SMALL_MODEL),
        tools=[
            ThinkTool(),  # to reason
            DuckDuckGoSearchTool(),  # search web
            WikipediaTool()
        ],
        instructions="""
                           You are a search agent equipped with tools that allow you to search the internet effectively. 
                           Your primary task is to conduct a search based on the user query provided.

              Omission Criteria:
                  Exclude examples, anecdotes, and minor details that do not contribute to the core message.
                  Avoid adding any personal commentary or opinions in your final response.

              Clarity and Coherence:
                  Ensure that your final response is coherent and easy to understand, maintaining
                   the original context of the information.

              Your goal is to provide concise and informative responses that effectively 
              convey the essential content without unnecessary elaboration.

                          """,
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=1),
            ConditionalRequirement(WikipediaTool, only_after=[DuckDuckGoSearchTool], min_invocations=1),
        ])

    main_agent = RequirementAgent(
        name="MainAgent",
        llm=ChatModel.from_name(SMALL_MODEL),
        tools=[
            ThinkTool(),
            HandoffTool(
                web_search_agent,
                name="websearchagent",
                description="Consult the Web Search Agent for latest and up to date information.",
            ),
        ],
        requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
        # Log all tool calls to the console for easier debugging
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    try:
        response = await main_agent.run(user_query, expected_output="Helpful and clear response.")
        recom_agent_resp = response.state.answer.text
        logging.info(f"*****************************call_recommendation_agent END with output: {recom_agent_resp}")
    except FrameworkError as err:
        logging.error(f"Error: {err.explain()}")
    return recom_agent_resp
