"""Manages the app's user interface and user interactions.
Triggers the DataFetcher module to gather real-time data for the specified stock symbol"""
import asyncio

import streamlit as st
import logging
from typing import Dict, Any

from stock_adv_agent import get_recommendation_agent_response
from stock_adv_report_generator import ReportGeneratorAgent
from stock_adv_technical_analysis import perform_tech_analysis
from stock_adv_security import (
    validate_stock_symbol,
    sanitize_input,
    report_rate_limiter,
    chat_rate_limiter
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def create_message(role: str, content: str) -> Dict[str, str]:
    """
    Creates a message dictionary with the given role and content.

    Args:
        role (str): The role of the message (e.g., "system", "user").
        content (str): The content of the message.

    Returns:
        Dict[str, str]: A dictionary representing the message.
    """
    return {"role": role, "content": content}


def display_chat_history() -> None:
    """
    Displays chat history alternately between user and assistant messages in a Streamlit app.

    Returns:
        None
    """
    if 'chat_history' in st.session_state:
        chat_history = st.session_state['chat_history']
        count = 0
        for m in chat_history:
            if m != "":
                if count % 2 == 0:
                    output = st.chat_message("user")
                    output.write(m)
                else:
                    output = st.chat_message("assistant")
                    output.write(m)
            count += 1


def update_chat_history(input: Any, result: Any) -> None:
    """
    Updates the chat history in the session state with the given input and result.

    Parameters:
    - input (Any): The input data to be added to the chat history.
    - result (Any): The result data to be added to the chat history.

    Returns:
    - None
    """
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    chat_history = st.session_state['chat_history']
    chat_history.extend([input, result])


async def generate_report_async(user_stock: str):
    """Generate the report asynchronously."""
    # Check if report already exists in session state for this stock
    if 'generated_report' in st.session_state and st.session_state.get('report_stock') == user_stock:
        logging.info(f"Using cached report for {user_stock}")
        return st.session_state['generated_report']
    
    logging.info(f"Generating new report for {user_stock}")
    report_generator = ReportGeneratorAgent(user_stock)
    generated_report = await report_generator.generate_report()
    
    # Store in session state
    if generated_report:
        st.session_state['generated_report'] = generated_report
        st.session_state['report_stock'] = user_stock
        logging.info(f"Report cached in session state for {user_stock}")
    
    return generated_report


def get_user_input() -> str:
    """
    Prompt the user for a stock ticker symbol and store it in ``st.session_state``.
    Includes validation to ensure only valid stock symbols are accepted.

    Returns
    -------
    str
        The ticker symbol entered by the user (empty string if none).
    """
    STOCK_KEY = "stock"
    VALIDATION_KEY = "stock_validation_error"

    # Retrieve the current value from session state, if any
    current_stock: str = st.session_state.get(STOCK_KEY, "")

    # Streamlit widget – the value argument pre‑populates the field
    user_stock: str = st.text_input(
        label=":blue[Enter a stock symbol:]",
        value=current_stock,
        placeholder="e.g. IBM",
    ).strip().upper()

    # Validate and update session state only when the user provides a non‑empty value
    if user_stock:
        # Validate stock symbol
        is_valid, error_message = validate_stock_symbol(user_stock)
        
        if is_valid:
            st.session_state[STOCK_KEY] = user_stock
            # Clear any previous validation errors
            if VALIDATION_KEY in st.session_state:
                del st.session_state[VALIDATION_KEY]
        else:
            # Show validation error
            st.error(f"Invalid stock symbol: {error_message}")
            st.session_state[VALIDATION_KEY] = error_message
            logging.warning(f"Invalid stock symbol entered: {user_stock} - {error_message}")
            return ""
    elif STOCK_KEY in st.session_state:
        # Preserve the previous value if the input is cleared
        user_stock = st.session_state[STOCK_KEY]

    logging.info("get_user_input END with output %s", user_stock)
    return user_stock


def perform_fundamental_analysis(user_stock: str):
    """Perform fundamental analysis and display results."""
    if st.button("Generate Report"):
        if user_stock:
            # Get or create session ID for rate limiting
            if 'session_id' not in st.session_state:
                import uuid
                st.session_state['session_id'] = str(uuid.uuid4())
            
            session_id = st.session_state['session_id']
            
            # Check rate limit
            if not report_rate_limiter.is_allowed(session_id):
                remaining = report_rate_limiter.get_remaining_requests(session_id)
                st.error("⚠️ Rate limit exceeded. Please wait a few minutes before generating another report.")
                st.info(f"You can generate {remaining} more reports in the next 5 minutes.")
                logging.warning(f"Rate limit exceeded for session: {session_id}")
                return
            
            try:
                logging.info(f"Generating report for: {user_stock}")
                
                # Check if we need to regenerate
                current_stock = st.session_state.get('report_stock')
                if current_stock != user_stock or 'generated_report' not in st.session_state:
                    # Run async function synchronously
                    with st.spinner(":green[Generating comprehensive report... This may take a few minutes.]"):
                        generated_report = asyncio.run(generate_report_async(user_stock))
                else:
                    generated_report = st.session_state['generated_report']
                    logging.info(f"Using cached report for {user_stock}")

                if generated_report:
                    st.text_area(":blue[Here is the generated report:]", value=generated_report, height=500)
                    st.success("Report generated successfully!")
                else:
                    st.error("Failed to generate report. Please try again.")
                    
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                logging.error(f"Report generation failed: {e}", exc_info=True)
        else:
            st.error("Please enter a stock symbol")
    
    # Chat interface - outside button logic to prevent state loss
    if 'generated_report' in st.session_state and st.session_state.get('report_stock') == user_stock:
        st.divider()
        st.subheader("Ask Questions About the Report")
        
        user_question = st.chat_input("Any questions about the analysis?")
        
        if user_question:
            # Get session ID for rate limiting
            session_id = st.session_state.get('session_id', 'default')
            
            # Check rate limit for chat
            if not chat_rate_limiter.is_allowed(session_id):
                st.error("⚠️ Too many questions. Please wait a moment before asking again.")
                logging.warning(f"Chat rate limit exceeded for session: {session_id}")
                return
            
            # Sanitize user input
            sanitized_question = sanitize_input(user_question)
            
            if not sanitized_question:
                st.error("Invalid question. Please try again with a different question.")
                return
            
            try:
                with st.spinner("Getting answer..."):
                    agent_response = asyncio.run(get_recommendation_agent_response(sanitized_question))
                    if agent_response:
                        update_chat_history(user_question, agent_response)
                    else:
                        st.error("Failed to get response. Please try again.")
            except Exception as e:
                st.error(f"Error processing question: {str(e)}")
                logging.error(f"Question processing failed: {e}", exc_info=True)
        
        display_chat_history()


def create_interface():
    """Create the user interface and handle interactions."""
    logging.info("create_interface START")
    user_stock = get_user_input()

    tab1, tab2 = st.tabs(["Fundamental analysis", "Technical analysis"])
    with tab1:
        st.header("Fundamental Analysis")
        perform_fundamental_analysis(user_stock)
    with tab2:
        st.header("Technical analysis")
        try:
            asyncio.run(perform_tech_analysis(user_stock))
        except Exception as e:
            st.error(f"Error in technical analysis: {str(e)}")
            logging.error(f"Technical analysis failed: {e}", exc_info=True)

    logging.info("create_interface END")