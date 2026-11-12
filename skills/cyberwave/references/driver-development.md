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

- Piper planned motion is the SDK's `PlannedMotionMixin`. The SDK ships only the in-process pinocchio backend; the Piper registers its own MoveIt backend (in its driver package, `motion/moveit/`) through `_motion_backend_factories`, and `moveit.enabled` (`CW_PIPER_MOVEIT_ENABLED`) sets `kinematics_backend` to `moveit` or `pinocchio`. Another driver adds MoveIt the same way (see the SDK docs page "Integrating MoveIt"). Piper MoveIt runs as the `moveit` service of the driver image's declared graph (the shared ros2-moveit image), not inside the driver, and the graph enables it. With `moveit.enabled` false (a plant without that graph), `ee_pose` and the collision-aware commands are planned in-process by the pinocchio backend: same commands and refusal codes, but `planner: "ompl"` is refused and `allow_touch` objects are left out of the collision model. With it true and `move_group` unreachable, they are refused `backend_unavailable` (detail starting `moveit:`); `state/motion` reports `kinematics_backend` and `backend_available`. Piper MoveIt `scene_set` contact permissions preserve the live allowed-collision matrix, including SRDF allowances for adjacent links and fixed wrist geometry. `allow_touch` changes only the named object/gripper pairs; revoking contact retains unrelated permissions. This requires the namespaced `get_planning_scene` service. If that read fails, the scene update is refused without acknowledgement or application; do not retry by clearing the matrix or disabling self-collision checks. Use one scene-policy writer per twin because the read/apply service pair is not an atomic transaction.
- Piper users can consult the public [AgileX Piper quickstart](https://docs.cyberwave.com/tutorials/agilex-piper-quickstart) and [Piper workflow tutorial](https://docs.cyberwave.com/tutorials/agilex-piper-workflows). The Piper driver itself is not currently published as a standalone open-source repository, so do not present unpublished source as a customer-accessible template.
- Piper's catalog exposes `twin.commands.add_obstacles(geometries=[...], frame_id="base_link")` for its in-process collision checks (the SDK's `WorldObstaclesMixin`). Each geometry uses the `scene_set` primitive shape (`id`, `primitive`, dimensions in metres, named position and quaternion). This **replaces** the whole Pinocchio world list, including the startup floor; include a finite floor box if needed. The active scene is stored in `twin.metadata["world_obstacles"]` with `frame_id="base_link"` (a legacy `pinocchio_obstacles` entry is still read); call `twin.refresh()` before reading it, since commands are asynchronous. On startup, the saved list (including `[]`) is validated and restored before activation; only a missing key uses the configured floor. Invalid saved geometry fails configuration rather than silently dropping collision objects. The startup slab appears as `id="floor"` when active. Remove one item with `twin.commands.remove_obstacle(id="...")`; unknown IDs leave the scene unchanged. No obstacle state topic is published. MoveIt remains separate: use `scene_set` for its motions. An invalid list or metadata write failure leaves the previous Pinocchio solver active, and updates during tracked motion are refused. Never describe a clear Pinocchio result as clearance from unlisted objects or attached payloads.
- Piper motion targets use latest-command-wins: a validated local Cartesian target (`ee_move`, `ee_rotate_*`, or local `ee_pose`) replaces the active `arm_controller/follow_joint_trajectory` goal. Arm joint teleop has higher priority, merges the latest value per joint, cancels displaced plans, and never replays them when teleop ends. A joint7-only gripper update keeps an active arm goal; it uses a separate ROS queue and is sent with the last accepted arm setpoint (or the first setpoint when a goal has just started). MoveIt retains only the latest replacement while awaiting cancellation acknowledgement, including a switch to local IK. Scene/payload edits still require idle motion. Replacements still require IK, collision, start-state and speed checks; they are not guaranteed to blend without a stop. Trajectories execute through the declared graph's `arm-controller` trajectory bridge, whose settle timeout ends a goal that never reaches its final tolerance. A submission acknowledgement is not execution completion. Home is an explicit command; driver teardown does not move the arm after ROS or CAN may have stopped.
- Piper keeps manual arm input (`joint_commands`, joint1…joint7), planned-trajectory input (`trajectory_joint_commands`, joint1…joint6, published by the `arm-controller` bridge) and gripper input (`gripper_commands`, joint7, also the `gripper-controller` bridge's output) on separate ROS subscriptions of its embedded arbiter, the single CAN writer. This prevents continuous trajectory output from overwriting a pending manual target before priority arbitration. Six-joint messages on the manual topic are refused; never point a bridge at `joint_commands` on hardware. MQTT command names and payloads are unchanged.
- Piper MQTT outages cancel motion and clear pending targets while preserving controller attachment and operation mode. A fresh measured posture is sent as a hold; reconnect permits fresh commands without reattaching or homing and does not replay cancelled motion. Piper `stop` likewise stops motion without entering `NO_OP`; explicit controller removal still enters `NO_OP`. The SDK's `mqtt.disconnect_count` lets Piper observe an outage that reconnects between ticks. Bundle the updated SDK (`CW_SDK_SOURCE=local` for checkout builds) for that brief-outage detection. Network-loss detection still depends on MQTT/socket keepalive; these changes do not shorten it.
- All three Piper command inputs keep only the latest pending target. Arbiter drop logs identify the source, target (arm radians, joint7 finger metres), ROS stamp, age and freshness limit, at most once per second per source. The embedded arbiter has its own `piper_motion_arbiter` logger; `vendor_log_level` applies to the fully namespaced vendor logger. Vendor command targets are available at DEBUG with a one-second throttle. These logs establish ROS admission, not physical completion; verify measured joint feedback.
- Piper arm speed defaults to `0.7 rad/s`. Set `CW_ROS2_MAX_JOINT_VELOCITY_RAD_S` inside the driver container to change an existing image without rebuilding; recreate the container to apply environment changes. A host export is insufficient because edge-core forwards only `CYBERWAVE_*`. This override drives both planning and managed ROS launch; remove conflicting `CW_MANAGED_LAUNCH_MAX_JOINT_VELOCITY_RAD_S` overrides. Config-file and `CW_PIPER_MAX_JOINT_VELOCITY_RAD_S` values are also forwarded to managed launch. Verify the motion-limits record and launch argument agree. S-V1.8-8 quantizes `0.7` to `0.69 rad/s` effective and `0.621 rad/s` for planning.
- Piper publishes TF on the absolute `/tf` (robot_state_publisher on the Piper description rooted at `dummy_link`), as the Kinova does, because the ros2-moveit service reads it. Two arms on one ROS domain therefore share one TF tree; give them distinct domains or frame prefixes before co-locating them.
- Piper's Python CAN feedback worker uses normal scheduling by default. `CW_PIPER_CAN_RX_FIFO=1` explicitly opts into FIFO 40 for a controlled trial; on a Pi 5, FIFO promotion preceded missing vendor joint feedback despite live CAN frames, and demotion restored ROS feedback. Verify fresh measured joint states before commanding motion; a successful command submission alone does not establish execution.
- Piper refuses manual and planned actuation while `/arm_status.ctrl_mode=2` (teaching). Entering teaching cancels active plans and clears pending targets. `teach_status=2` means teaching recording ended, but the controller can remain in `ctrl_mode=2` after the button LED turns off. At that point the driver requests CAN command mode once through the CAN owner's namespaced `request_can_mode_srv`, without sending a joint target. It waits for `/arm_status.ctrl_mode` to change before re-enabling through `enable_srv`, discards targets received during recovery, and primes from fresh joint feedback. If the mode request is ignored, planned motion remains blocked; AgileX documents a reset after teaching and warns it can remove motor support and let the arm fall, so the driver never resets automatically. Cartesian commands report `control_mode_unavailable` until `/arm_status` confirms CAN command mode; retry a one-shot pose after recovery. A failed enable service response is an error, not a successful re-arm.
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
- Answer MQTT v5 command requests. A `twin/command` message that carries a Response
  Topic (`{prefix}cyberwave/twin/{twin_uuid}/command/{client_id}/response`) and
  Correlation Data gets exactly one `twin.command_response.v1` reply on that topic,
  echoing the Correlation Data: `accepted`, `rejected` (refused before reaching the
  device), `denied` (the device refused, with its reason) or `timeout`. Messages
  without a Response Topic get no reply. Resolve the topic prefix like the SDK
  (`CYBERWAVE_MQTT_TOPIC_PREFIX`, else `CYBERWAVE_ENVIRONMENT` unless production):
  edge-core injects only `CYBERWAVE_ENVIRONMENT`. The SDK warns when the prefix
  does not match a hosted `*.mqtt.cyberwave.com` broker. See the cyberwave-contracts README and the
  PX4 gateway (`runtime-services/drivers/native/px4/px4_driver/gateway_service.py`).

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
11. for an arm driver, the SDK's capability-driven stress test on the development twin: `cyberwave-stress-test --uuid <twin-uuid> --list` prints which sections the twin's catalog, joints and `state/motion` select and why the rest are skipped, and moves nothing; `cyberwave-stress-test --uuid <twin-uuid> --yes` runs them on the robot and writes `report.json`. Every section passes on measured feedback, matched by `motion_id`. Every catalog command must be tested: an untested command (no section exercises it, or its sections are skipped for this twin) stops the run unless named in `--allow-untested`, and a driver-specific command needs its own `@section`. A skipped section is a gap to explain, not a pass. See https://docs.cyberwave.com/feature-reference/edge/drivers/stress-testing-your-driver.

Do not publish a driver or dispatch physical actions unless the user explicitly requested that external mutation and the registry/edge/twin are resolved.

## Completion evidence

Report generated path, registry ID, declared commands/topics/transports, build/test results, development twin/edge binding, and remaining steps before registry or live deployment.
