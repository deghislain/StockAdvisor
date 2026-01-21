"""Manages the app's user interface and user interactions.
Triggers the DataFetcher module to gather real-time data for the specified stock symbol"""
import asyncio

import streamlit as st
import logging
from typing import Dict, Any

from stock_adv_agent import get_recommendation_agent_response
from stock_adv_report_generator import ReportGeneratorAgent
from stock_adv_technical_analysis import perform_tech_analysis

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


async def generate_report(user_stock: str):
    """Generate and display the report."""
    report_generator = ReportGeneratorAgent(user_stock)
    generated_report = None
    if 'generated_report' not in st.session_state:
        generated_report = await report_generator.generate_report()

    return generated_report


def get_user_questions():
    user_input_messages = st.chat_input("Any question?")
    if user_input_messages:
        return user_input_messages
    return None


def get_user_input() -> str:
    """
    Prompt the user for a stock ticker symbol and store it in ``st.session_state``.

    Returns
    -------
    str
        The ticker symbol entered by the user (empty string if none).
    """
    STOCK_KEY = "stock"

    # Retrieve the current value from session state, if any
    current_stock: str = st.session_state.get(STOCK_KEY, "")

    # Streamlit widget – the value argument pre‑populates the field
    user_stock: str = st.text_input(
        label=":blue[Enter a stock symbol:]",
        value=current_stock,
        placeholder="e.g. IBM",
    ).strip().upper()

    # Update session state only when the user provides a non‑empty value
    if user_stock:
        st.session_state[STOCK_KEY] = user_stock
    elif STOCK_KEY in st.session_state:
        # Preserve the previous value if the input is cleared
        user_stock = st.session_state[STOCK_KEY]

    logging.info("get_user_input END with output %s", user_stock)
    return user_stock


async def perform_fundamental_analysis(user_stock: str):
    if st.button("Generate Report"):
        if user_stock:
            logging.info(
                f"---------------------------------------------Generating report for: {user_stock}**********************")
            generated_report = None
            current_input = None
            if 'stock' in st.session_state:
                current_input = st.session_state.stock
            # A new report is generated when user has changed stock symbol or when there is not an existing one
            if (current_input and current_input is not user_stock) or ('generated_report' not in st.session_state):
                generated_report = await generate_report(user_stock)
            else:
                generated_report = st.session_state.generated_report

            if generated_report:
                st.text_area(":blue[Here is the generated report:]", value=generated_report, height=500)
                st.success("Done")

            user_question = get_user_questions()
            if user_question:
                agent_response = await get_recommendation_agent_response(user_question)
                if agent_response:
                    update_chat_history(user_question, agent_response)
            display_chat_history()
        else:
            st.write("Enter a stock symbol please")


async def create_interface():
    """Create the user interface and handle interactions."""
    logging.info("**************------------------****************create_interface START")
    user_stock = get_user_input()

    tab1, tab2 = st.tabs(["Fundamental analysis", "Technical analysis"])
    with tab1:
        st.header("Fundamental Analysis")
        # if 'generated_report' not in st.session_state:
        await perform_fundamental_analysis(user_stock)
    with tab2:
        st.header("Technical analysis")
        await perform_tech_analysis(user_stock)

    logging.info("**************------------------****************create_interface END")
