from agents.stock_adv_recommendation_agent import call_recommendation_agent
from utils.logging_helper import log_performance
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


@log_performance
async def get_recommendation_agent_response(user_question: str, timeout: int = 180):
    """
    Get a response from the recommendation agent with proper error handling.
    
    Args:
        user_question: The user's question
        timeout: Timeout in seconds (default: 180)
        
    Returns:
        str: Agent response or error message
    """
    logging.info(f"call_recommendation_agent START with input: {user_question}")
    
    try:
        # Add timeout to prevent hanging
        recom_agent_resp = await asyncio.wait_for(
            call_recommendation_agent(user_question),
            timeout=timeout
        )
        
        if recom_agent_resp:
            logging.info("call_recommendation_agent completed successfully")
            return recom_agent_resp
        else:
            error_msg = "Sorry, I was unable to find an appropriate answer to your query. Try reformulating it."
            logging.warning(f"call_recommendation_agent returned empty response")
            return error_msg
            
    except asyncio.TimeoutError:
        error_msg = f"Request timed out after {timeout} seconds. Please try again with a simpler question."
        logging.error(f"call_recommendation_agent timed out: {error_msg}")
        return error_msg
        
    except Exception as e:
        error_msg = f"An error occurred while processing your request: {str(e)}"
        logging.error(f"call_recommendation_agent failed with error: {e}", exc_info=True)
        return error_msg
