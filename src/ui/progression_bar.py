import streamlit as st

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ProgressionBar:
    def __init__(self, ):
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()

    def update_progression_bar(self, progression: int, task_completed: str):
        logging.info(f"....................////////***************** update_progression_bar STRT with progression={progression} and task_completed ={task_completed}")
        if task_completed == "fund_analysis":
            status = "Completed Fundamental Analysis..."
        elif task_completed == "market_sent_analysis":
            status = "Completed Market sentiment Analysis..."
        elif task_completed == "risk_assessment":
            status = "Completed Risk Analysis..."
        else:
            progression += 25
            status = "Generating final report..."

        self.status_text.text(status)
        self.progress_bar.progress(progression)
