import asyncio

from stock_adv_user_interface import create_interface
from beeai_framework.errors import FrameworkError
import traceback
import sys


async def main():
    await create_interface()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except FrameworkError as e:
        traceback.print_exc()
        sys.exit(e.explain())
