import streamlit as st


def update_progression_bar(progression: int, task_completed: str):
    #progress_bar = st.progress(progression)
    status_text = st.empty()
    status = ""
    if task_completed == "fund_analysis":
        status = "Completed Fundamental Analysis..."
    elif task_completed == "market_sent_analysis":
        status = "Completed Market sentiment Analysis..."
    elif task_completed == "risk_assessment":
        status = "Completed Risk Analysis..."
    else:
        status_text.text("Generating final report...")

    status_text.text(status)
    st.progress(progression)
