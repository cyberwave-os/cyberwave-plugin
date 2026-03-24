import logging
from typing import Any

logger = logging.getLogger(__name__)


class HardwareClient:
    """
    Abstraction over the __DESCRIPTION__ native SDK/API.

    TODO: Replace the stub implementation below with your real hardware SDK.
    Reference docs / library: <add link here>
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def connect(self) -> None:
        # TODO: open connection to hardware (serial, TCP, USB, SDK init, etc.)
        logger.info("HardwareClient.connect() — replace with real implementation")

    def read_state(self) -> dict[str, Any]:
        # TODO: poll hardware and return a dict of state fields to merge into the twin.
        # Example: return {"battery_pct": 87, "status": "idle"}
        return {}

    def disconnect(self) -> None:
        # TODO: close connection gracefully
        pass
