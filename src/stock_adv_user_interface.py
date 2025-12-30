"""Manages the app's user interface and user interactions.
Triggers the DataFetcher module to gather real-time data for the specified stock symbol"""
import asyncio

import streamlit as st

from typing import Dict, Any

from stock_adv_agent import get_recommendation_agent_response
from stock_adv_report_generator import ReportGeneratorAgent
import logging

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
    report_generator = ReportGeneratorAgent()
    #generated_report = await report_generator.generate_report(user_stock)
    if 'generated_report' not in st.session_state:
        try:
            generated_report = await asyncio.create_task(report_generator.generate_report(user_stock))
        except RuntimeError:
            # No loop – start a fresh one
            generated_report = await asyncio.run(report_generator.generate_report(user_stock))
        if generated_report:
            st.session_state["generated_report"] = generated_report
    else:
        generated_report = st.session_state.generated_report

    return generated_report


def get_user_questions():
    user_input_messages = st.chat_input("Any question?")
    if user_input_messages:
        return user_input_messages
    return None


async def create_interface(user_stock):
    """Create the user interface and handle interactions."""
    if st.button("Generate Report") or user_stock:
        if user_stock:
            logging.info(
                f"---------------------------------------------Generating report for: {user_stock}**********************")
            generated_report = None
            current_input = None
            if 'stock' in st.session_state:
                current_input = st.session_state.stock
            # A new report is generated when user has changed stock symbol or when there is not an existing one
            if (current_input and current_input is not user_stock) or ('generated_report' not in st.session_state):
                logging.info(f"*****current_input = {current_input} and user_stock ={user_stock}/// {current_input and current_input is not user_stock}")
                logging.info(
                    f"*****('generated_report' not in st.session_state) = {('generated_report' not in st.session_state)}")
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
