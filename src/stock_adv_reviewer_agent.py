from langchain_ollama import ChatOllama
from stock_adv_utils import FIN_MODEL
from stock_adv_prompts import get_fundamental_analysis_review_prompt, get_fundamental_analysis_improve_prompt

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class QualityCheckAgent:
    def __init__(self):
        self.quality_check_agent = ChatOllama(model=FIN_MODEL, temperature=0)

    async def _review_fund_analysis(self, data, analysis):
        logging.info(
            f"******************************review_improve_fundamental_analysis START with input: {data}****{analysis}")
        prompt = get_fundamental_analysis_review_prompt(data, analysis)
        feedback = await self.quality_check_agent.ainvoke(prompt)
        logging.info(
            f"******************************review_improve_fundamental_analysis End with output: {feedback.content}")

        return feedback.content

    async def _improve_fund_analysis(self, data, analysis, feedback):
        logging.info(
            f"******************************_improve_fund_analysis START with input: {data}****{analysis}")
        prompt = get_fundamental_analysis_improve_prompt(data, analysis, feedback)
        improved_fund_analysis = await self.quality_check_agent.ainvoke(prompt)
        logging.info(
            f"******************************_improve_fund_analysis End with output: {improved_fund_analysis.content}")

        return improved_fund_analysis.content

    async def review_and_improve_fundamental_analysis(self, stock_data, fund_analysis) -> str:
        logging.info(
            f"******************************review_and_improve_fundamental_analysis START with input: {stock_data}****{fund_analysis}")
        feedback = await self._review_fund_analysis(stock_data, fund_analysis)

        if feedback:
            improved_fund_analysis = await self._improve_fund_analysis(stock_data, fund_analysis, feedback)
            if improved_fund_analysis:
                return improved_fund_analysis
