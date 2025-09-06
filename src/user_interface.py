"""Manages the app's user interface and user interactions.
Triggers the DataFetcher module to gather real-time data for the specified stock symbol"""

import streamlit as st
from prompts import RECOMMENDATION_BOT_PROMPT
from typing import List, Dict, Any


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


def get_the_messages(input: str) -> List[Dict[str, str]]:
    """
    Manages messages in a Streamlit application.

    Args:
        input (str): The user input message.

    Returns:
        List[Dict[str, str]]: A list of message dictionaries.
    """
    msg = ""
    if 'messages' not in st.session_state:
        msg = [
            create_message("system", RECOMMENDATION_BOT_PROMPT),
            create_message("user", input),
        ]
    else:
        st.session_state.messages.append(create_message("system", RECOMMENDATION_BOT_PROMPT))
        st.session_state.messages.append(create_message("user", input))

    st.session_state.messages = msg

    return msg


def get_chat_history(session_state: Dict[str, any] = st.session_state) -> List[str]:
    """
    Retrieves chat history from Streamlit session state.

    Args:
        session_state (Dict): The current Streamlit session state. Default is st.session_state.

    Returns:
        List[str]: A list of chat messages, or an empty list if no chat history exists.
    """
    if 'chat_history' not in session_state:
        return []

    chat_history = session_state['chat_history']
    return chat_history


def display_chat_history(session_state: Dict[str, any] = st.session_state) -> None:
    """
    Displays chat history alternately between user and assistant messages in a Streamlit app.

    Args:
        session_state (Dict): The current Streamlit session state. Default is st.session_state.

    Returns:
        None
    """
    chat_history = get_chat_history(session_state)

    if not chat_history:
        return  # Return early if there's no chat history to avoid unnecessary iteration

    user_messages, assistant_messages = [], []

    for message in chat_history:
        if not user_messages or len(user_messages) >= len(chat_history):
            user_messages.append(message)
            if len(user_messages) == len(assistant_messages):
                # Display assistant message after alternating through both lists
                st.write(f"Assistant: {assistant_messages.pop(0)}")
        else:
            assistant_messages.append(message)
            if len(assistant_messages) == len(user_messages):
                # Display user message after alternating through both lists
                st.write(f"User: {user_messages.pop(0)}")


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
    if 'topic' not in st.session_state:
        topic = st.text_input(":blue[Enter a stock symbol:]", placeholder="eg IBM")
        st.session_state.topic = topic
    else:
        topic = st.text_input(":blue[Enter a stock symbol:]", value=st.session_state.topic, placeholder="eg IBM")
    return topic


def generate_report():
    """Generate and display the report."""
    generated_report = "My first report"
    if generated_report:
        st.text_area(":blue[Here is the generated report:]", value=generated_report, height=500)
        user_input_messages = st.chat_input("Any question?")
        if user_input_messages:
            return user_input_messages
    return None


def call_recommendation_agent(user_question: str):
    return "response"


def create_interface():
    """Create the user interface and handle interactions."""
    topic = get_user_input()

    if st.button("Generate Report"):
        if topic:
            user_question = generate_report()
            if user_question:
                print("User-------------------question", user_question)
                agent_response = call_recommendation_agent(user_question)
                if agent_response:
                    update_chat_history(user_question, agent_response)

                display_chat_history()
        else:
            st.write("Enter a stock symbol please")
