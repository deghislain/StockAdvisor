"""Analyzes stock performance and trends. The fetched data is then passed to the AnalysisEngine, which performs
    technical and fundamental analysis.
    It evaluates key metrics such as price trends, volume, earnings reports, and other relevant indicators.
"""
import logging

from pandas import DataFrame

from langchain_ollama import ChatOllama

from stock_adv_prompts import get_fundamental_analysis_prompt
from stock_adv_utils import FIN_MODEL

fin_analyst_agent = ChatOllama(model=FIN_MODEL, temperature=0)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class FinAnalystAgent:
    async def _perform_fundamental_analysis(self, stock_data: DataFrame) -> str:
        logging.info(f"******************************_perform_fundamental_analysis START with input: {stock_data}")
        prompt = get_fundamental_analysis_prompt(stock_data)
        logging.info(f"******************************_perform_fundamental_analysis Prompt: {prompt}")
        fund_analysis = await fin_analyst_agent.ainvoke(prompt)
        logging.info(f"******************************_perform_fundamental_analysis START with input: {fund_analysis}")
        return fund_analysis.content

    async def analyse(self, stock_info) -> str:
        fundamental_analysis = await self._perform_fundamental_analysis(stock_info)
        return fundamental_analysis
