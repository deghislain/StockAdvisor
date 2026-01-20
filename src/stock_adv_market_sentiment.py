"""Gathers and analyzes market sentiment from news and social media.The MarketSentiment module analyzes recent
news articles, social media posts, and analyst opinions related to the stock.
It generates a sentiment score indicating whether the market sentiment is positive, negative, or neutral."""
import asyncio

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools.think import ThinkTool
from stock_adv_web_search_tool import WebSearchTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.errors import FrameworkError
from beeai_framework.tools import Tool
from stock_adv_utils import SMALL_MODEL, FIN_MODEL

from stock_adv_market_sent_analysis_instructions import (WEB_SEARCH_INSTRUCTIONS,
                                                         MARKET_SENT_ANALYSIS_INSTRUCTIONS,
                                                         MARKET_SENT_ANALYSIS_REVIEW_INSTRUCTIONS,
                                                         MARKET_SENT_ANALYSIS_IMPROVE_INSTRUCTIONS)

from stock_adv_prompts import get_stock_market_sent_analysis_prompt
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class StockMarketSentimentAnalyzer:
    def __init__(self, ticker: str):
        """
            Initializes the Market Sentiment Analyzer.

               Args:
                   ticker: Stock symbol (e.g., 'IBM')
        """
        self.ticker_symbol = ticker.upper()

    async def _perform_market_sentiment_analysis(self) -> str:
        web_search_agent = RequirementAgent(
            name="WebSearchAgent",
            llm=ChatModel.from_name(SMALL_MODEL),
            tools=[
                ThinkTool(),  # to reason
                WebSearchTool()
            ],
            instructions=WEB_SEARCH_INSTRUCTIONS,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(WebSearchTool, min_invocations=1),
            ])
        financial_analyst_agent = RequirementAgent(
            name="FinancialAnalystAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            instructions=MARKET_SENT_ANALYSIS_INSTRUCTIONS,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )
        quality_check_agent = RequirementAgent(
            name="QualityCheckAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            instructions=MARKET_SENT_ANALYSIS_REVIEW_INSTRUCTIONS,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )
        market_sentiment_analysis_enhancer_agent = RequirementAgent(
            name="MarketSentimentAnalysisEnhancerAgent",
            llm=ChatModel.from_name(FIN_MODEL, timeout=6000, temperature=0),
            tools=[
                ThinkTool(),  # to reason
            ],
            instructions=MARKET_SENT_ANALYSIS_IMPROVE_INSTRUCTIONS,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
        )
        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(SMALL_MODEL, timeout=12000, temperature=0),
            tools=[
                ThinkTool(),
                HandoffTool(
                    web_search_agent,
                    name="WebSearchAgent",
                    description="""Consult the Web Search Agent for recent news articles, social media posts, 
                    and opinions for the provided stock.""",
                ),
                HandoffTool(
                    financial_analyst_agent,
                    name="FinancialAnalysis",
                    description="""Consult the Financial Analyst Agent for market sentiment analysis using news and info
                     fetched by the Web Search Agent.""",
                ),
                HandoffTool(
                    quality_check_agent,
                    name="QualityChecking",
                    description="""Consult the Quality Check Agent to review the market sentiment analysis written by 
                             the Financial Analyst Agent using data retrieved by the Web Search Agent.""",
                ),
                HandoffTool(
                    market_sentiment_analysis_enhancer_agent,
                    name="MarketSentimentAnalysisEnhancement",
                    description="""Consult the Market Sentiment Analysis Enhancer Agent to improve 
                            the market sentiment analysis written by the Financial Analyst Agent using 
                            the feedback provided by the Quality Check Agent.""",
                ),
            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )
        prompt = get_stock_market_sent_analysis_prompt(self.ticker_symbol)
        logging.info(f"Starting market sentiment analysis for: {self.ticker_symbol}")
        agent_response = None
        
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            
            # Safely extract the response
            if response and hasattr(response, 'last_message') and hasattr(response.last_message, 'text'):
                risk_market_sent_report = response.last_message.text
                
                if risk_market_sent_report:
                    agent_response = risk_market_sent_report
                    logging.info(f"Market sentiment analysis completed successfully for {self.ticker_symbol}")
                else:
                    logging.warning(f"Empty market sentiment report for {self.ticker_symbol}")
                    agent_response = f"Unable to generate market sentiment analysis for {self.ticker_symbol}. Please try again."
            else:
                logging.error("Unexpected response structure from market sentiment agent")
                agent_response = f"Technical error occurred during market sentiment analysis for {self.ticker_symbol}."
                
        except FrameworkError as err:
            error_msg = f"Framework error in market sentiment analysis: {err.explain()}"
            logging.error(error_msg, exc_info=True)
            agent_response = f"Analysis framework error for {self.ticker_symbol}. Please try again later."
            
        except AttributeError as err:
            logging.error(f"Response structure error in market sentiment analysis: {err}", exc_info=True)
            agent_response = f"Data structure error during market sentiment analysis of {self.ticker_symbol}."
            
        except Exception as err:
            logging.error(f"Unexpected error in market sentiment analysis for {self.ticker_symbol}: {err}", exc_info=True)
            agent_response = f"Unexpected error occurred during market sentiment analysis of {self.ticker_symbol}."
            
        return agent_response

    async def analyze(self):
        return await self._perform_market_sentiment_analysis()


async def main():
    ticker = "RGTI"
    ms_analyzer = StockMarketSentimentAnalyzer(ticker)
    market_sentiment_report = await ms_analyzer.analyze()
    if market_sentiment_report:
        print(market_sentiment_report)


if __name__ == "__main__":
    asyncio.run(main())
