import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cyberwave.driver import BaseDriver, CallbackGroup, CommandArgs, ProtocolArgs, TopicSpec

from .hardware import HardwareClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DriverParams:
    """Immutable edge/runtime configuration parsed once at startup."""

    twin_json_file: Path
    child_uuids: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "DriverParams":
        twin_json_file = Path(
            os.environ.get("CYBERWAVE_TWIN_JSON_FILE", "/app/.cyberwave/twin.json")
        )
__CHILD_TWINS_SECTION__
        return cls(twin_json_file=twin_json_file, child_uuids=child_uuids)

    def load_twin_data(self) -> dict[str, Any]:
        return json.loads(self.twin_json_file.read_text(encoding="utf-8"))


class __CLASS_NAME__(BaseDriver):
    """__DESCRIPTION__"""

    Params = DriverParams
    # Leave empty only while the catalog asset is being created; set the stable
    # manufacturer/model registry ID before manifest registration or deployment.
    REGISTRY_ID = "__REGISTRY_ID__"
    TICK_RATE_HZ = 10.0

    def __init__(
        self,
        params: DriverParams | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(params or DriverParams.from_env(), **kwargs)
        self._hardware: HardwareClient | None = None
        self._latest_state: dict[str, Any] = {}

    @classmethod
    def create(cls) -> "__CLASS_NAME__":
        """Build the driver from edge-injected environment configuration."""
        return cls(DriverParams.from_env())

    def define_interface(self, iface) -> None:
        command_topic = TopicSpec(
            namespace="twin",
            leaf="command",
            payload_schema_ref="TwinCommandPayload",
            description="__DRIVER_NAME__ commands",
        )
        iface.add_listener(
            command_topic,
            CallbackGroup(callback=self._on_device_action),
            protocol=ProtocolArgs(source_types=["tele", "live", "edge"]),
            command=CommandArgs(
                name="device_action",
                description="Perform one bounded device action",
            ),
        )

    async def on_configure(self) -> None:
        twin_data = self.params.load_twin_data()
        edge_config = twin_data.get("metadata", {}).get("edge_configs", {})
        self._hardware = HardwareClient(config=edge_config)
        logger.info(
            "Configured %s (child_twins=%d)",
            type(self).__name__,
            len(self.params.child_uuids),
        )
__CHILD_TWINS_LOG__

    async def on_connect_to_device(self) -> None:
        assert self._hardware is not None
        self._hardware.connect()

    async def on_register_callbacks(self) -> None:
        # Register callbacks from the native device SDK here. Cyberwave MQTT
        # listeners are wired automatically from define_interface().
        return None

    async def on_activate(self) -> None:
        logger.info("Driver active for twin %s", self.twin_uuid)

    async def on_tick(self) -> None:
        if self._hardware is None:
            return
        self._latest_state = self._hardware.read_state()
        self._touch_edge_health()

    async def on_shutdown(self) -> None:
        if self._hardware is not None:
            self._hardware.disconnect()

    def driver_info_extra(self) -> dict[str, Any]:
        return {
            "hardware_connected": self._hardware is not None,
            "state_fields": sorted(self._latest_state),
        }

    def _on_device_action(self, envelope: dict[str, Any]) -> None:
        if self._hardware is None:
            raise RuntimeError("hardware is not connected")
        self._hardware.perform_action(envelope)
