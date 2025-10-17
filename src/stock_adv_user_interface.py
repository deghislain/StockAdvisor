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


def get_user_input():
    """Get user input for stock symbol."""
    user_stock = ""
    if 'stock' not in st.session_state:
        user_stock = st.text_input(":blue[Enter a stock symbol:]", placeholder="eg IBM")
        if user_stock:
            st.session_state["stock"] = user_stock

    else:
        user_stock = st.session_state.stock
        st.text_input(":blue[Enter a stock symbol:]", value=user_stock, placeholder="eg IBM")

    return user_stock


async def generate_report(user_stock: str):
    """Generate and display the report."""
    report_generator = ReportGeneratorAgent()
    #generated_report = await asyncio.create_task(report_generator.generate_report(user_stock))
    generated_report = await report_generator.generate_report(user_stock)
    #if generated_report:
    #    st.text_area(":blue[Here is the generated report:]", value=generated_report, height=500)
    return generated_report


def get_user_questions():
    user_input_messages = st.chat_input("Any question?")
    if user_input_messages:
        return user_input_messages
    return None


async def create_interface():
    """Create the user interface and handle interactions."""
    user_stock = get_user_input()
    if st.button("Generate Report") or user_stock:
        if user_stock:
            #Using create_task to avoid 'Event loop is closed' error
            generated_report = await asyncio.create_task(generate_report(user_stock))
            if generated_report:
                st.text_area(":blue[Here is the generated report:]", value=generated_report, height=500)
            user_question = get_user_questions()
            if user_question:
                agent_response = await get_recommendation_agent_response(user_question)
                if agent_response:
                    update_chat_history(user_question, agent_response)
            display_chat_history()
        else:
            st.write("Enter a stock symbol please")
