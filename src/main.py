import nest_asyncio
import asyncio
import logging
from datetime import datetime

from stock_adv_technical_analysis import perform_tech_analysis
from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError
import traceback
import sys
import streamlit as st

nest_asyncio.apply()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


#TODO I have to redesign from scratch
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


async def main():
    ticker = get_user_input()

    tab1, tab2 = st.tabs(["Fundamental analysis", "Technical analysis"])
    with tab1:
        st.header("Fundamental Analysis")
        #if 'generated_report' not in st.session_state:
        await create_interface(ticker)
    with tab2:
        st.header("Technical analysis")
        await perform_tech_analysis(ticker)


if __name__ == "__main__":

    try:
        with st.spinner(":green[In progress...]"):
            try:
                start = datetime.now()
                logging.info(f"--- Start Time = {start:%H:%M:%S} ---")
                asyncio.create_task(main())
            except RuntimeError:
                # No loop – start a fresh one
                asyncio.run(main())

            end = datetime.now()
            logging.info(f"--- End Time = {end:%H:%M:%S} ---")
            duration = end - start
            logging.info(f"--- Process duration = {duration} ---")

    except FrameworkError as fe:
        logging.error(fe)
        traceback.print_exc()
        sys.exit(fe.explain())

    except Exception as exc:  # catch‑all for unexpected errors
        logging.error("Unexpected error: %s", exc)
        traceback.print_exc()
        sys.exit(1)
