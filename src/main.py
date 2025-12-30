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
        label="Enter a stock symbol:",
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
