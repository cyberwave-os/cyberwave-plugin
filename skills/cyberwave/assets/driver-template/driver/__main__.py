import asyncio
import logging

from .driver import __CLASS_NAME__


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(__CLASS_NAME__.create_and_run_async())


if __name__ == "__main__":
    main()
