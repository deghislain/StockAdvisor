import asyncio
import logging
from datetime import datetime

from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError
import traceback
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def main():
    await create_interface()


if __name__ == "__main__":

    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No loop – start a fresh one
            start = datetime.now()
            logging.info(f"--- Start Time = {start:%H:%M:%S} ---")
            asyncio.run(main())
            end = datetime.now()
            logging.info(f"--- End Time = {end:%H:%M:%S} ---")
            duration = end - start
            logging.info(f"--- Process duration = {duration} ---")
        else:
            # Already inside a loop – just await the coroutine
            asyncio.create_task(main())

    except FrameworkError as fe:
        logging.error(fe)
        traceback.print_exc()
        sys.exit(fe.explain())
    except Exception as exc:  # catch‑all for unexpected errors
        logging.error("Unexpected error: %s", exc)
        traceback.print_exc()
        sys.exit(1)
