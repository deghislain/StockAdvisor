"""Manages the app's user interface and user interactions.
Triggers the DataFetcher module to gather real-time data for the specified stock symbol"""

import streamlit as st
from prompts import RECOMMENDATION_BOT_PROMPT


def get_the_messages(input):
    msg = []
    if 'messages' not in st.session_state:
        msg = [
            {"role": "system", "content": RECOMMENDATION_BOT_PROMPT},
            {"role": "user", "content": input},
        ]
    else:
        msg = st.session_state['messages']
        msg.append({"role": "system", "content": RECOMMENDATION_BOT_PROMPT})
        msg.append({"role": "user", "content": input})

    st.session_state['messages'] = msg

    return msg


def display_chat_history():
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


def update_chat_history(input, result):
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    chat_history = st.session_state['chat_history']
    chat_history.extend([input, result])


def create_interface():
    topic = st.text_input(":blue[Enter a stock symbol:]", placeholder="eg IBM")
    btn_submit = st.button("Generate Report")
    if btn_submit and topic:
        gen_report = "My first report"
        if gen_report:
            st.text_area(":blue[Here is the generated report:]", value=gen_report, height=500)
            input = st.chat_input("Any question about the report?")
            if input:
                messages = get_the_messages(input)
