import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1.0


class __CLASS_NAME__:
    """
    __DESCRIPTION__

    Bridges the hardware API and the Cyberwave platform via the digital twin model.
    """

    def __init__(
        self,
        twin_uuid: str,
        api_key: str,
        twin_json_file: str,
        child_uuids: list[str],
    ) -> None:
        self.twin_uuid = twin_uuid
        self.api_key = api_key
        self.twin_json_file = Path(twin_json_file)
        self.child_uuids = child_uuids
        self._twin_data: dict[str, Any] = self._load_twin_json()

        # Read per-device runtime config from edge_configs
        metadata = self._twin_data.get("metadata", {})
        self.edge_configs: dict[str, Any] = metadata.get("edge_configs", {})
        logger.info("Edge configs: %s", self.edge_configs)
__CHILD_TWINS_LOG__
        self._hardware = self._connect_hardware()

    # ------------------------------------------------------------------
    # Twin JSON helpers
    # ------------------------------------------------------------------

    def _load_twin_json(self) -> dict[str, Any]:
        try:
            return json.loads(self.twin_json_file.read_text())
        except Exception:
            logger.exception("Failed to read twin JSON file at %s", self.twin_json_file)
            raise

    def _save_twin_json(self) -> None:
        self.twin_json_file.write_text(json.dumps(self._twin_data, indent=2))

    def _update_twin_state(self, updates: dict[str, Any]) -> None:
        """Merge updates into twin metadata and persist to disk for Edge Core to sync."""
        self._twin_data.setdefault("metadata", {}).update(updates)
        self._save_twin_json()

    # ------------------------------------------------------------------
    # Hardware
    # ------------------------------------------------------------------

    def _connect_hardware(self):
        """Instantiate and return the hardware client. Exits non-zero if unavailable."""
        from __PACKAGE_NAME__.hardware import HardwareClient
        try:
            client = HardwareClient(config=self.edge_configs)
            client.connect()
            logger.info("Hardware connected")
            return client
        except Exception:
            logger.exception("Cannot connect to hardware — exiting so Edge Core restarts the driver")
            raise

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("Driver running (twin=%s)", self.twin_uuid)
        while True:
            try:
                state = self._hardware.read_state()
                self._update_twin_state(state)
            except Exception:
                logger.exception("Error in main loop")
            time.sleep(POLL_INTERVAL_SECONDS)
