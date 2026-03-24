import logging
import os
import sys

from __PACKAGE_NAME__.driver import __CLASS_NAME__

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    required = ["CYBERWAVE_TWIN_UUID", "CYBERWAVE_API_KEY", "CYBERWAVE_TWIN_JSON_FILE"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error("Missing required environment variables: %s", missing)
        sys.exit(1)

    twin_uuid = os.environ["CYBERWAVE_TWIN_UUID"]
    api_key = os.environ["CYBERWAVE_API_KEY"]
    twin_json_file = os.environ["CYBERWAVE_TWIN_JSON_FILE"]
__CHILD_TWINS_SECTION__
    driver = __CLASS_NAME__(
        twin_uuid=twin_uuid,
        api_key=api_key,
        twin_json_file=twin_json_file,
        child_uuids=child_uuids,
    )

    try:
        driver.run()
    except Exception:
        logger.exception("Driver crashed — exiting with non-zero code so Edge Core can restart")
        sys.exit(1)


if __name__ == "__main__":
    main()
