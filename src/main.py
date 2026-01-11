#import nest_asyncio
import asyncio
import logging
from datetime import datetime
import traceback
import sys
import streamlit as st

from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError


#nest_asyncio.apply()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    async def main():
        try:
            with st.spinner(":green[Generating Report In Progress.................. please wait.]"):

                start = datetime.now()
                logging.info(f"--- Start Time = {start:%H:%M:%S} ---")
                await create_interface()
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


    asyncio.run(main())

