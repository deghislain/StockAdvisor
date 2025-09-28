"""Provides buy/sell/hold recommendations based on analysis.
    The RecommendationAgent searches the internet and uses the insights from the AnalysisEngine and the sentiment score from
    the MarketSentiment module to generate a buy, sell, or hold recommendation.
    It considers the risk assessment to ensure that the recommendation aligns with the user's risk tolerance.
"""

from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools.think import ThinkTool
from stock_adv_web_search_tool import WebSearchTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import Tool
from stock_adv_utils import SMALL_MODEL, LARGE_MODEL
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def call_recommendation_agent(user_query: str):
    """
        Asynchronously generates a buy/sell/hold recommendation based on user query.

        Args:
            user_query (str): The user's input query for stock analysis.

        Returns:
            str: A helpful and clear response containing the recommendation.
        """

    recom_agent_resp = ""
    web_search_agent = RequirementAgent(
        name="WebSearchAgent",
        llm=ChatModel.from_name(SMALL_MODEL),
        tools=[
            ThinkTool(),  # to reason
            WebSearchTool()
        ],
        instructions="""
                           You are a search agent tasked with performing an internet search using a search tool 
                           and returning a concise summary of the most pertinent information to the user.

                            Follow these steps to complete your task:
                            
                                Perform Initial Search:
                                    Execute a search based on the user’s query using a reliable search tool.
                                   
                                Filter and Summarize Information:
                                    Review the search results to filter out irrelevant or duplicate information.
                                    Summarize the relevant findings, ensuring the summary:
                                        Is concise and to the point.
                                        Covers all key points from the scraped content.
                                        Maintains clarity and coherence.
                                    For each scraped page, create a brief summary that captures the essential information.
                                    Combine these individual summaries into an overall summary that provides a comprehensive overview of the search results.
                            
                                Return Results to User:
                                    Format the summarized information into a readable format, such as:
                                        A list of bullet points.
                                        A short paragraph.
                                    Deliver the formatted summary back to the user promptly, ensuring it is easy to understand and actionable.

                          """,
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(WebSearchTool, min_invocations=1),
        ])

    main_agent = RequirementAgent(
        name="RecommendationAgent",
        llm=ChatModel.from_name(LARGE_MODEL),
        tools=[
            ThinkTool(),
            HandoffTool(
                web_search_agent,
                name="WebSearchAgent",
                description="Consult the Web Search Agent for latest and up to date information.",
            ),
        ],
        instructions=""" 
        You are a specialized recommendation agent focused on stock and financial analysis. Your primary objective
         is to provide accurate, insightful, and actionable responses to user inquiries about specific stocks. 
         To achieve this, follow these guidelines:
        
        ### Integration of Web Information
        Use the most recent information gathered from the internet by the web search agent to enhance your analysis. 
        Deliver the Response:
        Promptly deliver the formatted response back to the user.
        Be prepared to provide additional information or clarification if the user has follow-up questions.
""",
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
