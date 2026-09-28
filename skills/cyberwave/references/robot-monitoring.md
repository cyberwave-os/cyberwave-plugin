# Robot monitoring

Read this for robot state, joint/schema inspection, camera frames or streams, environment captures, workflow runs, alerts, edge/container health, and bounded monitoring.

## Define the observation

Clarify only missing essentials:

- target twin/environment,
- signal: state, joints, schema, frame, stream, run, alert, edge/driver health,
- time window or frame/sample count,
- freshness requirement,
- and whether the user wants a snapshot, diagnosis, or ongoing monitor.

Use the least expensive signal that answers the question.

## Read hierarchy

1. Resolve the environment/twin exactly.
2. Use `cw_get_twin` for current twin summary/status.
3. Use `cw_get_joint_states` for joints and `cw_get_schema` for a specific universal-schema path.
4. Check `cw_list_environment_captures` before taking a new camera frame when recent workflow-produced evidence may suffice.
5. Use `cw_capture_frame` for one current image or `cw_capture_frames` for a bounded burst (current MCP maximum is 10; inspect the schema).
6. Use `cw_get_twin_metrics` for operational state (power, navigation, load, errors). It reads the current snapshot by default; pass `latest=false` only when a trend is needed.
7. Use `cw_get_twin_logs` for what the driver itself reported, or `cw_get_environment_driver_logs` when the question spans twins. `level` is an exact match, not a minimum severity.
8. Use `cw_get_twin_telemetry` for the structured event stream. It applies a default window when none is given and reports the window it used.
9. Use `cw_list_alerts` for what has already been raised; start from `status=['active']` when triaging.
10. Use `cw_list_workflow_runs`/`cw_get_workflow_run` for automation execution state, then `cw_get_workflow_run_nodes` with the same run UUID for the per-node detail that says which node failed and why.
11. For edge/stream health, inspect current Edge Core/service/container telemetry before deprecated CLI health commands.

Distinguish a missing/stale observation from a valid zero/empty reading.

## Frames and video

- Capture one frame first unless temporal change requires a burst.
- Set an explicit small count and interval for bursts.
- Identify the sensor when multiple cameras exist; never silently choose the first for a safety decision.
- Report capture timestamp/freshness and mock/simulation status.
- Simulation-viewer **video fps** counts received/decoded video frames, which may repeat a previous render. Do not interpret it as fresh sensor FPS or evidence of real-time policy observations; verify capture generations/timestamps and simulator cadence separately.
- Do not embed large Base64 payloads in narrative output; use the client's image/attachment support.
- Do not save, upload, or retain frames beyond the requested task without explicit scope.

MCP exposes bounded latest-frame capture, not an indefinite viewer. For a user-facing WebRTC stream, use the dashboard or verified SDK/edge streaming flow. If implementing streaming code, verify the current SDK camera extras, FFMPEG requirement, signaling, cleanup, and sensor identity from official docs/source.

For asynchronous `VirtualCameraStreamer` providers, return a cached
`CapturedVideoFrame` with the image's acquisition clocks and an increasing
acquisition ID. Do not refresh its timestamp on each send: repeating an image
is not a new observation. `None` produces a placeholder without a capture
timestamp. Source timing alone does not prove stored-video/Replay alignment;
verify that separately before reporting synchronized evidence.

For numeric depth, use an explicit MQTT source and inspect its declared units and
metric evidence. SDK `raw=False` honors its scale/window and rejects explicit
relative or unconfirmed normalized frames; use `raw=True` for display/storage
values. REST grayscale retains a legacy range approximation and is not calibrated
metric evidence. Name the sensor when several share a twin topic. Identified
frames are isolated; untagged legacy feeds cannot distinguish cameras.

For a saved world-frame cloud, preserve the selected frame's `frame_metadata`,
including `camera_pose` and calibrated `intrinsics` with their `width`/`height`.
The simulator attaches the optical camera pose from the captured scene snapshot;
updated camera → model → Send Depth workers carry it with the capture timestamp.
`mqtt.publish_pointcloud(camera_pose=..., timestamp=...)` keeps XYZ optical.
After establishing metric scale, use SDK `cyberwave.utils.depth.pointcloud_to_world`
on an N×3/N×6 array and that same pose (metres, quaternion `[w,x,y,z]`, explicit
world/environment frame). Missing capture pose is a configuration gap, not a
reason to use the robot's latest position. Runtime intrinsics are resized to the
model output; cropped/rectified images require corrected calibration. This does
not establish depth accuracy, multi-camera fusion or automatic map persistence.

## Bounded monitoring

For a finite watch:

1. State the interval and end condition.
2. Prefer event/run status or telemetry updates over rapid polling.
3. Apply a maximum duration/sample count. The observability reads are already bounded well below their REST limits; page with `offset` rather than raising `limit`, and narrow the window when a read reports `has_more`.
4. Back off on unchanged state or rate limits.
5. Stop on terminal state, user cancellation, authentication failure, or repeated non-retry-safe errors.

For recurring monitoring, use the host client's supported automation/monitor mechanism rather than an unbounded loop inside a skill invocation.

## Diagnosis order

When data is missing:

1. authentication and ACL,
2. correct workspace/environment/twin/sensor,
3. freshness/timestamp and simulation vs live source,
4. edge/service/container state,
5. driver hardware connection and manifest/capabilities,
6. MQTT remote path,
7. declared Zenoh local path for edge-local workers,
8. workflow/run-specific errors — read the failing node, not just the run status.

Do not classify a robot as healthy from one fresh camera frame alone, or offline from one missing frame alone.

For an empty simulated range scan, inspect the sensor's parent link and local
mount pose through `cw_get_schema`, then check self-hit and valid-return counts.
A sensor inside imported collision or visual geometry cannot establish free
space. For a 3D scan, check declared horizontal/vertical samples and FOV as well;
a legacy single-plane cloud is not volumetric coverage. Use the existing schema
patch flow for an authorized correction, scoped to the twin when it is a virtual
test mount. Preserve physical calibration and shared defaults. Verify fresh
returns after restart; keep pointcloud, saved map, SLAM and obstacle avoidance
acceptance separate.

## Alerts and external effects

Reading alerts through `cw_list_alerts`/`cw_get_alert` is monitoring. Creating, acknowledging, resolving, or silencing alerts is a mutation; identify the exact alert and follow the user's requested scope. `cw_update_alert_status` previews by default and needs `execute=true` to apply — clearing an alert removes a signal a human operator may be relying on, and does not fix the underlying condition. Sending email/chat notifications or triggering remediation is an additional external effect and requires explicit request or an already-authorized workflow.

## Completion evidence

Report target, source/mode, signal(s), observation window/frame count, timestamps/freshness, current state, notable anomalies, and confidence/unknowns. Link or display media through the client when available instead of dumping encoded bytes.


## Thermal display evidence

The dashboard's thermal camera effect colorizes RGB brightness in live and
simulation views. The palette is not temperature data: raw camera captures
remain RGB, and a colour is never a reading. Do not infer temperatures from
the displayed palette.

Measured temperatures are separate `type: "thermal"` twin telemetry. Read
them with `cw_get_twin_telemetry` and select events whose `metadata.type` is
`thermal` (they are stored under the generic twin-telemetry event type, like
`motor_status`). The payload is `metadata.data.min_c` / `max_c` / `avg_c` plus
`spots[]` and `boxes[]`, in °C, with the sensor id in `sensor`. They come from a
thermal camera driver such as `flir/ax8` (`source_type: "edge"`, calibrated
readings) or from a MuJoCo simulation (`source_type: "sim"`). Simulated values
come from a heuristic heat model: ambient scenery, a cold sky, and robots
warming with motor load. A twin can also have a fixed "heat signature"
(`metadata.thermal.temperature_c`, set under Twin properties), which the simulator
shows exactly. A hot object in simulation may therefore be one someone
configured. Simulated values illustrate the pipeline, and are not evidence of
a real thermal anomaly. State the source type whenever you report a
temperature. If no thermal telemetry exists for the twin, say so rather than
reading the palette.
