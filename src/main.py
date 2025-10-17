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
        # Get the current time
        current_time = datetime.now()
        start_time = current_time.hour * 60 + current_time.minute
        asyncio.run(main())
        end_time = current_time.hour * 60 + current_time.minute
        duration = end_time - start_time
        logging.info(f"---------------------Process duration = {duration}-------------")


    except FrameworkError as e:
        logging.error(e)
        traceback.print_exc()
        sys.exit(e.explain())

