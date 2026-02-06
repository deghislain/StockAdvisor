"""Provides buy/sell/hold recommendations based on analysis.
    The RecommendationAgent searches the internet and uses the insights from the AnalysisEngine and the sentiment score from
    the MarketSentiment module to generate a buy, sell, or hold recommendation.
    It considers the risk assessment to ensure that the recommendation aligns with the user's risk tolerance.
"""

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools.think import ThinkTool
from tools.stock_adv_web_search_tool import WebSearchTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import Tool
#from stock_adv_utils import SMALL_MODEL, LARGE_MODEL
from config.config import ModelConfig as mc
from utils.logging_helper import log_performance
from config.stock_adv_market_sent_analysis_instructions import WEB_SEARCH_INSTRUCTIONS
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@log_performance
async def call_recommendation_agent(user_query: str):
    """
        Asynchronously generates a buy/sell/hold recommendation based on user query.

        Args:
            user_query (str): The user's input query for stock analysis.

        Returns:
            str: A helpful and clear response containing the recommendation.
        """

    web_search_agent = RequirementAgent(
        name="WebSearchAgent",
        llm=ChatModel.from_name(mc.small_model),
        tools=[
            ThinkTool(),  # to reason
            WebSearchTool()
        ],
        instructions=WEB_SEARCH_INSTRUCTIONS,
        requirements=[
            ConditionalRequirement(ThinkTool, force_at_step=1),
            ConditionalRequirement(WebSearchTool, min_invocations=1),
        ])

    main_agent = RequirementAgent(
        name="RecommendationAgent",
        llm=ChatModel.from_name(mc.small_model),
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
    recom_agent_resp = ""
    try:
        response = await main_agent.run(user_query, expected_output="Helpful and clear response.")
        
        # Safely extract the response text
        if response and hasattr(response, 'state') and hasattr(response.state, 'answer'):
            recom_agent_resp = response.state.answer.text
            logging.info(f"call_recommendation_agent completed successfully")
        else:
            logging.warning("call_recommendation_agent returned unexpected response structure")
            recom_agent_resp = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            
    except FrameworkError as err:
        error_msg = f"Framework error occurred: {err.explain()}"
        logging.error(error_msg, exc_info=True)
        recom_agent_resp = "I encountered a technical issue while processing your request. Please try again."
        
    except AttributeError as err:
        logging.error(f"Response structure error: {err}", exc_info=True)
        recom_agent_resp = "I received an unexpected response format. Please try again."
        
    except Exception as err:
        logging.error(f"Unexpected error in call_recommendation_agent: {err}", exc_info=True)
        recom_agent_resp = "An unexpected error occurred. Please try again or contact support if the issue persists."
        
    return recom_agent_resp
