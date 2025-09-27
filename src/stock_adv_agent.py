from stock_adv_recommendation_agent import call_recommendation_agent

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def get_agent_response(user_question: str):
    logging.info(f"call_recommendation_bot ************************************* START with input {user_question}")
    recom_agent_resp = await call_recommendation_agent(user_question)

    if recom_agent_resp:
        return recom_agent_resp
    else:
        """Sorry I regret to tell you that I was not able to find an appropriate answer to your query.
         Try reformulating it"""
