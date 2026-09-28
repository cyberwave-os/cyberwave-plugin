# Cyberwave driver development

Build a driver with the current `cyberwave.driver.BaseDriver` framework. Declare the interface once and let the SDK own cloud connection, lifecycle, command wiring, telemetry, edge health, and declared transports. Do not hand-roll MQTT loops for standard Cyberwave commands/topics.

## Establish the deliverable

Reuse supplied context and ask only for missing facts that affect the implementation:

- driver/project name and hardware model/protocol,
- existing catalog `REGISTRY_ID` or `unknown`,
- Python or C++ (Python is the maintained scaffold path),
- commands, publishers/listeners, sensors, units, and expected rates,
- child twins and device-access needs,
- local test hardware availability,
- author/license and target edge platform.

Search existing Cyberwave drivers and catalog assets first. Extend an existing driver when its hardware protocol and interface are compatible.

## Open-source reference drivers

Use these maintained public repositories as subsystem examples before designing a new integration:

| Repository | Reuse it for |
| --- | --- |
| [`cyberwave-edge-camera-driver`](https://github.com/cyberwave-os/cyberwave-edge-camera-driver) | USB/V4L2, IP/RTSP, and RealSense capture; WebRTC streaming; device passthrough; edge-injected configuration; frame/depth channels and Zenoh-aware video pipelines. |
| [`cyberwave-edge-camera-depth-estimation-driver`](https://github.com/cyberwave-os/cyberwave-edge-camera-depth-estimation-driver) | Combining a camera driver with local ML inference, configurable model backends, depth-map encoding, checkpoint handling, and CPU/CUDA deployment choices. |
| [`cyberwave-edge-so101`](https://github.com/cyberwave-os/cyberwave-edge-so101) | A complete robotic-arm example: serial servos, discovery and calibration, leader/follower teleoperation, remote operation, child cameras, device-health reporting, reconnect safety, and hardware-specific CLI utilities. |
| [`ugv-beast-driver`](https://github.com/cyberwave-os/ugv-beast-driver) | ROS 2-to-Cyberwave bridging, mapping-driven robot integration, bounded velocity/deadman/e-stop behavior, multi-robot namespacing, odometry/IMU telemetry, navigation, and video in one edge deployment. |
| [`deepak61296/cyberwave-edge-mavlink-driver`](https://github.com/deepak61296/cyberwave-edge-mavlink-driver) | Community, non-official drone example for MAVLink/ArduPilot/PX4, SITL-first testing, flight-mode/acknowledgement handling, command queues, velocity streaming, source-type filtering, and dead-man braking. Review its license and safety status before reuse. |

Choose the closest example by hardware and transport, then copy only the relevant adapter, configuration, packaging, and test patterns. Treat these repositories as reference implementations, not as the current framework contract: re-check their default branch and dependencies before reuse. If an example does not use the current `BaseDriver` API, start from this skill's scaffold and port the proven hardware/protocol logic into `hardware.py` and lifecycle hooks. The current SDK, embedded template, asset capabilities, and transport rules override older MQTT topics, environment variables, or lifecycle patterns found in an example.

For additional platform-contract examples rather than driver scaffolds:

- Piper users can consult the public [AgileX Piper quickstart](https://docs.cyberwave.com/tutorials/agilex-piper-quickstart) and [Piper workflow tutorial](https://docs.cyberwave.com/tutorials/agilex-piper-workflows). The Piper driver itself is not currently published as a standalone open-source repository, so do not present unpublished source as a customer-accessible template.
- Drone integrations can compare the public SDK's [DJI Mini example](https://github.com/cyberwave-os/cyberwave-python/blob/main/examples/drone_dji_mini.py), [hovering example](https://github.com/cyberwave-os/cyberwave-python/blob/main/examples/drone_hovering.py), and [flight capability implementation](https://github.com/cyberwave-os/cyberwave-python/blob/main/cyberwave/twin/capabilities/flight.py) to preserve the current command contract. These are client/control examples, not edge-driver templates.

## Scaffold

Resolve `scripts/scaffold_driver.py` relative to the parent Cyberwave skill directory, then run it from the directory that should contain the new project:

```bash
python /absolute/path/to/cyberwave/scripts/scaffold_driver.py \
  --name "<driver-name>" \
  --description "<hardware description>" \
  --author "<author>" \
  --registry-id "<manufacturer/model>" \
  --output-dir .
```

Add `--child-twins` only when the driver manages attached child twins. The scaffold refuses to overwrite an existing project directory.

The generated Python template must already use `BaseDriver`; do not keep or introduce a legacy polling shell and plan to fix it later.

## Canonical Python structure

```text
<driver-name>/
├── <package>/
│   ├── __init__.py
│   ├── __main__.py        asyncio.run(Driver.create_and_run_async())
│   ├── driver.py          interface, lifecycle, command/state callbacks
│   └── hardware.py        native serial/TCP/USB/vendor SDK adapter
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── .env.example
```

Keep hardware/protocol code behind `hardware.py`. Keep Cyberwave identity, lifecycle, and interface declarations in `driver.py`.

## BaseDriver contract

Use the public exports from `cyberwave.driver`:

- `BaseDriver`
- `TopicSpec`
- `CallbackGroup`
- `ProtocolArgs`
- `CommandArgs` / `CommandArg`
- `PublisherArgs`
- `DriverOperationMode`

Set `REGISTRY_ID` on the subclass when the catalog asset exists. Implement the required `@classmethod create()` factory to parse driver-specific environment/CLI configuration and return the configured instance. Then implement the async lifecycle hooks:

1. `on_configure` — parse config/build non-live objects.
2. `on_connect_to_device` — open the physical connection and fail loudly if unavailable.
3. `on_register_callbacks` — register device-native callbacks only.
4. `on_activate` — start streams/controllers.
5. `on_shutdown` — idempotent cleanup.

Use `on_tick` only for genuinely periodic device work. Use `driver_info_extra` or declared publishers for telemetry. Do not override `run_async`; the module entrypoint should await `create_and_run_async()`.

`BaseDriver` already provides:

- authenticated Cyberwave client and twin binding,
- lifecycle state transitions and reconnect shell,
- interface manifest generation/registration,
- standard management commands (`stop`, teleoperation modes, controller changes),
- MQTT subscription/dispatch from `define_interface`,
- scheduled publishers and rate governance,
- driver telemetry and edge-health heartbeat,
- optional declared Zenoh activation.

## Declare the interface

Define each custom command once on the MQTT-only `twin/command` topic:

```python
command_topic = TopicSpec(
    namespace="twin",
    leaf="command",
    payload_schema_ref="TwinCommandPayload",
    description="Device commands",
)
iface.add_listener(
    command_topic,
    CallbackGroup(callback=self._on_device_action),
    protocol=ProtocolArgs(source_types=["tele", "edge"]),
    command=CommandArgs(
        name="device_action",
        description="Perform one bounded device action",
    ),
)
```

Bind exact `CommandArgs.name` values. Do not route commands with keyword heuristics. Validate payload shape and hardware bounds before actuation.

Declare repeat behavior with a boolean `continuous`: explicit `false` keeps a light, gripper or other one-shot command from repeating even if an older input preset says otherwise. Omission retains legacy preset behavior. Declare accepted `source_types` on each driver input topic. These describe that driver, not every execution target: inspect the active simulation/runtime contract separately, rather than inferring simulation availability from the hardware source list. The driver keyboard guide and dispatcher exclude undeclared commands, mismatched actuations and invalid typed arguments while retaining the saved mapping for review. Reuse one input template with capability-scoped mappings rather than creating a controller per device feature; saved action mappings still require supported runtime activation.

Every message covered by the shared v1 transport envelope carries `source_type`
as a top-level field. Use only the centralized vocabulary: `edge`,
`edge_leader`, `edge_follower`, `tele`, `edit`, `sim`, or `sim_tele`. Domain
payload fields remain alongside it; do not introduce a nested envelope.

When helping configure an input, inspect the declared command parameters as well as its name. A gripper command may require an action choice; a trajectory requires joint names and ordered points. Preserve saved parameters when changing a key or movement amount. Use the existing mapping editor for declared parameter fields rather than making a parallel form. A saved key binding is configuration evidence only: validate hardware bounds, trajectory semantics and device readiness in the driver before execution. A Cartesian pose still requires real IK/planning and collision support.

For a command that needs parameters, use `CommandArg` with keyword-only `type`, `required`, `enum`, bounds or `min_items` in a supporting SDK release. For example, `CommandArg("action", type="string", required=True, enum=("grip", "release"))` declares a required gripper choice. Keep `CommandArg(name, default, unit)` for existing untyped integrations until explicitly migrated. Export through the existing registry and submit through `twin.driver.set_schema`; avoid the deprecated local compiler. The server validates the declaration. Do not guess required values when generating keyboard mappings: leave the command available for setup and explain which parameters are missing. Complete setup and driver readiness are separate. To change an existing typed command contract, refresh the twin, inspect the current schema, retain `twin.driver.get_revision()`, and pass that token as `expected_revision` to `set_schema`. A 409 means the reviewed target changed or the request omitted its revision; review again instead of retrying with an automatically refreshed token. An old untyped refresh must not erase adopted constraints. The revision covers the loaded twin, not immutable driver history.

For publishers, declare a typed `TopicSpec` and `PublisherArgs(rate_hz=...)`. Use units and source types in `ProtocolArgs`. Do not duplicate the built-in driver telemetry publisher.

Commands accepting alternative payloads can declare `CommandArgs(required_any_of=("pwm", "io4"), args=(...))` in a supporting release. Declare each referenced name as a typed `CommandArg`. The registry exports the same `required_any_of` list as YAML; the server compiler validates it. Do not add defaults merely to satisfy the group, since a driver's parameter precedence can change an existing command's meaning.

## MQTT and Zenoh

- MQTT is the default remote/cross-LAN path and remains enabled for normal topics.
- `twin/command` is MQTT-only; never enable Zenoh for it.
- For an edge-local data channel, set `enable_zenoh=True` and a stable `zenoh_channel` on its `TopicSpec`.
- Dual transport is inferred from `enable_mqtt=True` plus `enable_zenoh=True`.
- Use `CYBERWAVE_PUBLISH_MODE=mqtt_only` only as an operator override to disable Zenoh publishing.

Follow the public SDK's [fake IMU driver example](https://github.com/cyberwave-os/cyberwave-python/blob/main/examples/fake_imu_driver.py). Declare MQTT and Zenoh transport settings together with the unified `TopicSpec` fields.

## Runtime configuration and identity

Treat `CYBERWAVE_TWIN_JSON_FILE` plus sibling edge/environment/fingerprint files as the source of truth for twin, sensor, and binding identity. Parse once into a small immutable config object.

For camera and USB-audio hardware identity, use top-level
`metadata.serial_number` (exported as `CYBERWAVE_METADATA_SERIAL_NUMBER`), not a
sensor parameter or a device index. Keep serials as strings to preserve leading
zeroes. A serial pin must fail rather than substitute another physical unit.
Linux UVC resolution relies on `/dev/v4l/by-id` and USB audio resolution on
`/dev/snd/by-id`; declare the required device node and bind-mount the relevant
host tree when Edge Core is not launching the container for you.

Sensor lookup order:

1. `capabilities.sensors`
2. `asset.capabilities.sensors`
3. `universal_schema.sensors`
4. `asset.universal_schema.sensors`
5. `metadata._production_capabilities.sensors`

Use sensor `id` (fallback `name`) and `parent_link`. Do not invent `link`, `frame_id`, or `mount` fields. Keep framework-specific frames in the framework and bridge them explicitly.

Never hardcode secrets, twin UUIDs, camera paths, or sensor identity in the image. Do not log raw API keys or full sensitive configuration.

## Local development

When `REGISTRY_ID` exists:

```bash
python -m pip install cyberwave cyberwave-cli
cyberwave login
cyberwave twin create <registry-id> \
  --name "<driver-name>-dev" \
  --pair \
  --target-dir ./<driver-name>
```

Inspect `cyberwave twin create --help` in the installed CLI before relying on flags. Use a non-production environment and development twin. The generated `.env` is secret-bearing and must remain ignored.

Build and run:

```bash
cd <driver-name>
docker compose up --build
```

## Acceptance checks

Before registration or live deployment, verify:

1. scaffold unit tests and placeholder replacement,
2. package import, concrete `BaseDriver` subclass construction through `create()`,
3. manifest generation (`get_manifest`) and command/topic catalog,
4. configuration parsing with redacted logs,
5. hardware-connect failure and recovery behavior,
6. exact command dispatch and safety bounds,
7. publisher payloads, units, rates, MQTT, and declared Zenoh paths,
8. graceful shutdown and idempotent cleanup,
9. Docker build plus least-required device privileges,
10. development twin telemetry/health and asset capabilities matching the real interface.

Do not publish a driver or dispatch physical actions unless the user explicitly requested that external mutation and the registry/edge/twin are resolved.

## Completion evidence

Report generated path, registry ID, declared commands/topics/transports, build/test results, development twin/edge binding, and remaining steps before registry or live deployment.
