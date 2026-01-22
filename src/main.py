import logging
from datetime import datetime
import traceback
import streamlit as st

from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    try:
        start = datetime.now()
        logging.info(f"--- Start Time = {start:%H:%M:%S} ---")
        create_interface()
        end = datetime.now()
        logging.info(f"--- End Time = {end:%H:%M:%S} ---")
        duration = end - start
        logging.info(f"--- Process duration = {duration} ---")

    except FrameworkError as fe:
        logging.error(fe)
        traceback.print_exc()
        st.error(f"Framework Error: {fe.explain()}")
    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        traceback.print_exc()
        st.error(f"Unexpected error: {exc}")