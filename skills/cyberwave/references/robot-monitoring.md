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
6. Use `cw_list_workflow_runs`/`cw_get_workflow_run` for automation execution state.
7. For edge/stream health, inspect current Edge Core/service/container telemetry before deprecated CLI health commands.

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

## Bounded monitoring

For a finite watch:

1. State the interval and end condition.
2. Prefer event/run status or telemetry updates over rapid polling.
3. Apply a maximum duration/sample count.
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
8. workflow/run-specific errors.

Do not classify a robot as healthy from one fresh camera frame alone, or offline from one missing frame alone.

## Alerts and external effects

Reading alerts is monitoring. Creating, acknowledging, resolving, or silencing alerts is a mutation; identify the exact alert and follow the user's requested scope. Sending email/chat notifications or triggering remediation is an additional external effect and requires explicit request or an already-authorized workflow.

## Completion evidence

Report target, source/mode, signal(s), observation window/frame count, timestamps/freshness, current state, notable anomalies, and confidence/unknowns. Link or display media through the client when available instead of dumping encoded bytes.
