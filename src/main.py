import nest_asyncio
import asyncio
import logging
from datetime import datetime

from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError
import traceback
import sys
import streamlit as st

nest_asyncio.apply()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def main():
    tab1, tab2 = st.tabs(["Fundamental analysis", "Technical analysis"])
    with tab1:
        await create_interface()
    with tab2:
        st.header("Inside Tab 2")
        st.write("This content is in the second tab.")


if __name__ == "__main__":

    try:
        with st.spinner("In progress..."):
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
