---
name: cyberwave-driver
description: Scaffold a new Cyberwave-compatible driver. Use when the user wants to write, create, or build a driver for a hardware device on the Cyberwave platform.
argument-hint: [driver-name]
---

# Cyberwave Driver Scaffold

You are helping the user create a new **Cyberwave-compatible driver** — a Dockerized service that bridges a hardware device's native API and the Cyberwave platform via the digital twin model.

Python drivers use **`cyberwave.driver.DriverBase`**: one driver class declares the MQTT manifest and callbacks (`define_interface`), implements lifecycle hooks for hardware, and starts with a ~5-line `__main__.py`. Do **not** hand-roll MQTT subscribe loops or a separate polling `run()` unless the user explicitly needs a non-SDK bridge.

Official reference: [Writing compatible drivers](https://docs.cyberwave.com/feature-reference/edge/drivers/writing-compatible-drivers) (programmatic manifest + callbacks section).

## Step 1 — Gather requirements

Ask the user the following questions **in a single message** before doing anything:

1. **Driver name** — project folder and Python package name (e.g. `my-lidar-driver`)
2. **Hardware description** — one sentence about the device (e.g. "a SICK LiDAR over Ethernet using the SOPAS protocol")
3. **Asset registry ID** — catalog id for `registry_ids` and dev twin creation (e.g. `unitree/go2`, `acme-corp/my-arm-v1`). Use `unknown` if not created yet and skip local dev steps later.
4. **Author / organisation** — LICENSE and README
5. **SDK language** — Python or C++? (default: Python)
6. **Child twins?** — cameras or other child twins attached to this driver? yes/no
7. **Interface sketch** (optional) — commands (e.g. `stop`, `move_forward`), topics (joint bus, telemetry, camera), teleop vs autonomous

Wait for answers before Step 2.

---

## Step 2 — Run the scaffold script

Run `scaffold.py` (same directory as this SKILL.md) to generate Dockerfile, docker-compose, pyproject/requirements, LICENSE, README, and starter Python files.

**Find `scaffold.py`:**

```bash
find ~ -name "scaffold.py" -path "*/cyberwave-driver-skill/*" 2>/dev/null | head -1
```

**Run it:**

```bash
python /path/to/scaffold.py \
  --name "<driver-name>" \
  --description "<hardware description>" \
  --author "<author>" \
  --output-dir "." \
  [--child-twins]
```

Show the script output to the user.

**Language choice.** C++ drivers: scaffold is Python-first. Offer a `CMakeLists.txt` skeleton with the C++ SDK (`DriverBase` in `cyberwave-sdks/cyberwave-cpp`) if they chose C++.

---

## Step 2b — Align generated code with `DriverBase` (required for Python)

The scaffold may still emit a legacy `hardware.py` + polling `driver.py`. **Restructure immediately** to the SDK pattern below (edit files in place; do not leave a hand-rolled MQTT loop).

### Target layout

| File | Role |
|------|------|
| `<package>/driver.py` | **Main work:** `DriverBase` subclass — `define_interface`, lifecycle hooks, command handlers |
| `<package>/hardware.py` | Optional hardware client (`connect`, `read_state`, …) — imported only from `driver.py` |
| `<package>/__main__.py` | Entrypoint: `MyDriver.from_env().run()` |
| `cw-driver.yml` | Optional on disk; manifest can be exported via `get_driver_manifest()` / `register_interface_on_twin()` |

### Minimal driver skeleton

```python
# <package>/driver.py
from dataclasses import dataclass
from cyberwave.driver import (
    DriverBase,
    CallbackGroup,
    CommandArgs,
    TopicSpec,
    PublisherArgs,
)


@dataclass
class MyDriverParams:
    serial_port: str = "/dev/ttyUSB0"

    @classmethod
    def from_env(cls) -> "MyDriverParams":
        import os
        return cls(serial_port=os.getenv("MY_SERIAL_PORT", "/dev/ttyUSB0"))


class MyDriver(DriverBase):
    registry_ids = ["<registry-id>"]
    driver_family = "python"

    def __init__(self, params: MyDriverParams | None = None) -> None:
        super().__init__(params or MyDriverParams.from_env())
        self._hw = None

    def define_interface(self, iface) -> None:
        cmd = TopicSpec(
            namespace="twin",
            leaf="command",
            payload_schema_ref="TwinCommandPayload",
            description="Device commands",
        )
        iface.add_listener(
            cmd,
            CallbackGroup(callback=self._on_stop),
            command=CommandArgs(name="stop"),
        )
        # Add joint listeners, publishers, etc. — see docs

    async def on_configure(self) -> None:
        from .hardware import HardwareClient
        self._hw = HardwareClient(config=self._edge_configs())

    async def on_connect_to_device(self) -> None:
        assert self._hw is not None
        self._hw.connect()  # raise if unreachable → process exits non-zero

    async def on_register_callbacks(self) -> None:
        pass  # device-local only; MQTT wiring is automatic

    async def on_activate(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        if self._hw:
            self._hw.close()

    def _on_stop(self, envelope: dict) -> None:
        ...

    @property
    def asset_key(self) -> str:
        return "<asset-key-from-catalog>"

    @property
    def twin_uuid(self) -> str:
        import os
        return os.environ["CYBERWAVE_TWIN_UUID"]

    def _edge_configs(self) -> dict:
        import json, os
        path = os.environ.get("CYBERWAVE_TWIN_JSON_FILE", "")
        if path:
            return json.loads(open(path).read()).get("metadata", {}).get("edge_configs", {})
        return {}
```

```python
# <package>/__main__.py
from .driver import MyDriver

if __name__ == "__main__":
    MyDriver.from_env().run()
```

### What `DriverBase` handles (do not reimplement)

| Concern | SDK behavior |
|---------|----------------|
| Cloud MQTT + twin | `Cyberwave(source_type="edge")`, `self.client`, `self.twin` |
| Lifecycle | `CONFIGURING` → `CONNECTING` → `INACTIVE` → `ACTIVE` → `DEACTIVATING` |
| Manifest on twin | `register_interface_on_twin()` after connect (when `registry_ids` set) |
| MQTT subscribe / command dispatch | `_wire_interface_from_registry()` from `define_interface` |
| Periodic publish | `add_publisher` callbacks run from tick loop |
| Teleop modes | `DriverOperationMode` (`NO_OP`, `TELEOP_LOCAL`, `TELEOP_REMOTE`); built-in `controller-changed`, `teleoperate`, `remoteoperate`, `stop` |
| Telemetry | `self.twin.telemetry.set_connected`, `driver_info`, lifecycle snapshots |

**Do not** call `subscribe_command_topic()` or raw `mqtt.subscribe` for catalog commands — use `iface.add_listener(..., command=CommandArgs(...))`.

**Do not** add keyword/phrase heuristics to route commands; bind explicit `CommandArgs.name` values only.

---

## Step 3 — Orient the user in the generated code

After scaffold + DriverBase alignment, tour these files:

1. **`<package>/driver.py`** — `define_interface` (manifest + callbacks), lifecycle hooks, command handlers. Primary edit surface.
2. **`<package>/hardware.py`** (optional) — device SDK / serial / TCP; called from `on_configure` / `on_connect_to_device` only.
3. **`<package>/__main__.py`** — should be only `MyDriver.from_env().run()`.
4. **`Dockerfile`** — system packages for the hardware SDK (`apt-get`, etc.).
5. **`cw-driver.yml`** (optional) — can be generated for review: `python -c "from <pkg>.driver import MyDriver; import yaml; print(yaml.dump(MyDriver().get_driver_manifest()))"` or persisted at runtime via `register_interface_on_twin()`.

Point them to declare every command and topic they implement in `define_interface` so teleop, agents, and `twin.commands` stay aligned.

---

## Step 4 — Set up local development environment

Skip if registry ID is `unknown`.

### 4a — Install the Cyberwave CLI

```bash
pip install cyberwave
```

### 4b — Authenticate

```bash
cyberwave login
```

### 4c — Create a dev twin and write `.env`

```bash
cyberwave twin create <registry-id> \
  --name "<driver-name>-dev" \
  --pair \
  --target-dir ./<driver-name>
```

Writes `CYBERWAVE_TWIN_UUID`, `CYBERWAVE_API_KEY`, and related vars into the project `.env`.

```bash
cat ./<driver-name>/.env
```

Set `CYBERWAVE_ASSET_KEY` in `.env` if the driver resolves the twin via `asset_key` + `twin_id` (match catalog asset key).

### 4d — Twin JSON stub

```bash
echo '{"metadata": {"edge_configs": {}}}' > /tmp/cyberwave-twin.json
```

`docker-compose.yml` should set `CYBERWAVE_TWIN_JSON_FILE` to that path for local dev.

### 4e — Build and run

```bash
cd <driver-name>
docker compose up --build
```

Healthy logs typically include:

- `[SUCCESS] MQTT connection established via Cyberwave SDK`
- `[STATE] … → configuring` / `→ active` lifecycle transitions
- `Wired interface registry` (after `on_register_callbacks`)
- `register_interface_on_twin` success when `registry_ids` is set
- No `sys.exit(1)` from twin fetch or MQTT timeout

Hardware not implemented yet: expect failure in `on_connect_to_device` until `hardware.py` connects — that is correct (non-zero exit for Edge Core).

### 4f — Iterate

> The driver runs against a real twin. In the dashboard, check telemetry (`driver_info`, `connected`) and commands from your manifest. Loop: edit `driver.py` / `hardware.py` → `docker compose up --build` → logs + dashboard.

Optional: push manifest without YAML file:

```python
from cyberwave import Cyberwave
from my_package.driver import MyDriver

cw = Cyberwave(source_type="edge")
cw.mqtt.connect()
twin = cw.twin(twin_id="...")
twin.driver.set_schema(MyDriver(MyDriverParams()))
```

---

## Step 5 — Offer to implement hardware + interface

Ask: *"Do you want help implementing `hardware.py` and `define_interface` for your device?"*

If yes, collect:

- Hardware SDK / protocol (`pyserial`, `pymodbus`, vendor SDK, …)
- Connection parameters — prefer `metadata.edge_configs` from `CYBERWAVE_TWIN_JSON_FILE`, not hardcoded image config
- Commands and topics to declare (match real behavior)

When implementing:

- Add SDK deps to `requirements.txt` / `pyproject.toml`
- Raise from `on_connect_to_device` if the device is unreachable (non-zero exit)
- Register every command handler with `CommandArgs(name="...")` on `twin/command`
- Use `PublisherArgs(rate_hz=...)` for joint/state streams
- Extend `driver_info_extra()` for custom telemetry fields if needed
- For teleop arms/UGVs, rely on built-in management commands; gate actuation listeners with `operation_modes` (defaults: teleop-only for non-command topics)

---

## Notes for Claude

- **Non-zero exit on unrecoverable failure.** Let `DriverBase` exit on MQTT/twin errors; raise from `on_connect_to_device` when hardware is required but missing.
- **`CYBERWAVE_TWIN_JSON_FILE` + `metadata.edge_configs`.** Per-device settings; no hardcoded IPs/ports in the image.
- **Hardware stays in `hardware.py`; platform I/O stays in `driver.py`.** Never import the hardware SDK from `__main__.py`.
- **One manifest source.** `define_interface` drives both runtime wiring and `get_driver_manifest()` — keep them in sync; avoid orphan `cw-driver.yml` that disagrees with code.
- **No intent heuristics.** Do not keyword-match user phrases to pick commands; use explicit `CommandArgs` and schemas.
- **`scaffold.py` refuses existing directories** — safe to re-run with a different `--name` only.
- **After scaffold, always apply Step 2b** until templates are updated to emit `DriverBase` natively.
