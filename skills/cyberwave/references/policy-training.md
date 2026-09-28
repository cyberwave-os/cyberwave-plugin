# Policy training and evidence

Read this when a user asks to teach, train, retrain, evaluate, bind or review a learned skill. For motion planning and dispatch, also read [Robot control](robot-control.md).

## Choose the control interface first

Separate the task family (grasp, push, walk, fly) from the interface the selected runtime exposes:

| Boundary | Example | Verify |
| --- | --- | --- |
| User/controller input → policy | Goal position or requested walking speed | The policy's declared inference-command schema and trained range |
| Policy → robot/controller output | Joint positions/efforts or bounded body velocities | Frozen action interface, target runtime/driver contract, units and limits |
| Controller → physical plant | Onboard flight controller driving hidden rotor motors | Matched lower-controller identity/configuration, state freshness and stop behavior |

A robot can expose body commands without exposing actuators. A URDF/MJCF describes mechanics, not physical driver permissions. A velocity task input does not imply velocity policy output. Reject an incompatible policy or explain the missing adapter; do not silently translate between interfaces. Simulation preparation cannot grant hardware capabilities.

The shared adapter's body-velocity output port is simulation-only. The normal
RL controller can select an explicitly frozen aerial output, but first requires
the same action interface and exact twin binding plus a command-free, running
plant audit. That worker report must match the lower-controller source hash,
MuJoCo version, timestep and rotor-motor actuation; metadata or wrench fallback
alone cannot satisfy it. Use a fresh simulation for this initial flight slice.
Unknown output adapters, physical execution and Zenoh command output still fail
closed. A confirmed local drone job now has both held-out evaluation Replay and
an automatically reported normal simulation deployment in the dashboard. This
validates its position-goal task, not heading-stable hover or hardware readiness.

The existing retained `simulation-audit` read route also serves this pre-command
startup report and current workload status. Empty command activity is expected
there; it proves neither controller execution nor task success. Do not fabricate
activity to make a startup report resemble a completed deployment.

The native task adapter can train explicit flight-command tasks using the
simulator's matched lower controller and the existing custom action/observation
terms. Validate actual manager/plant parity before training, including frames,
feedback cadence and reset state. A changed lower-controller fingerprint needs a
fresh task version and evaluation; do not reuse an old successful video as proof.
Adapter smoke tests are not confirmed platform jobs or accepted deployments.

Compare the compiled task model with the normal simulator scene before training,
including integrator and fluid settings. Attaching an MJCF entity does not carry
its global options into the training scene. Author needed density/viscosity in
the existing `CyberwaveMujocoCfg` (finite non-negative values; omission preserves
compiled settings), alongside timestep/integrator. Passing action-manager parity
alone does not detect differing training and deployment physics.

For an explicitly requested physics/policy validation, the simulation-start API
accepts `runtime.robot_stack="physics_only"` alongside CPU/device options. This
runs the same MuJoCo plant and policy path without ROS/Nav2; the selected scope
is retained in the workload and simulation listing. Omit it (or use `auto`) for
the asset's normal robot stack. Missing driver images must fail that normal
stack, never silently select physics-only mode. Do not rename a catalog robot or
strip its driver identity to get a test to launch, and do not report a
physics-only pass as ROS/navigation-stack or hardware acceptance.

Before retraining for a waypoint failure, compare actual command limits,
expiry/Stop behavior and endpoint headings across planning and dispatch. A
path rebuilt around obstacles must preserve authored arrival orientations only
on their corresponding endpoints, not copy them onto detours. Test the same
held-out criteria after a runtime fix; unchanged actor weights mean an
integration improvement, not newly learned behavior.

Command-level flight requires complete measured root pose/twist frames from the
simulation source. Missing joints are not filled with invented positions, and
partial root frames cannot refresh old velocity. Deployment acceptance reuses
the frozen goal-hold/failure criteria on this measured root through the full
horizon. The plant retains its all-external-forces flag while separately checking
exact aerodynamic drag written by the built-in rotor controller; unexpected
forces, fallback thrust, controller handover or stale feedback fail acceptance.
Do not treat ordinary modeled drag as either a physics bypass or permission to
ignore arbitrary applied forces.

The backend selects required report checks from the frozen policy output, not
the report's claims. Aerial outputs require both no unaccounted external forces
and a matching lower controller; other outputs keep the original no-external-
forces check. Failed checks remain failures. A position-hold task without a
heading/angular-rate criterion can pass while rotating: inspect all relevant
metrics and Replay, and use a newly confirmed task version for stronger criteria.

For models with no scalar joints, measured root twist supplies base velocity;
do not invent joint-velocity channels to satisfy an articulated-robot check.
Mixed free/scalar models still need both feeds. Simulation sensor validation uses
the target twin snapshot, so inspect instance overrides before changing the
shared catalog asset. An imported model without declared sensor cadence needs
explicit simulation settings, not an inferred hardware sampling rate.

## Teaching and new policy versions

For a new or revised platform-managed task, keep MCP discovery compact: use
`cw_inspect_rl_tasks(operation="list", environment_uuid=...)`, then
`operation="get"` for the selected task's source manifest, scene entities,
orchestration hints and training options. Use `cw_author_rl_task` for all
authoring mutations. Its operation selects create/update, one exact source-file
upsert, whole scene-entity replacement, strict Python scene-spec validation or
apply, or generated scene-config regeneration. Every mutation previews by default. Read
an existing source with `cw_inspect_rl_tasks(operation="get_source", ...)`
before replacing it, and inspect the task again after an applied mutation.
Creating or editing a task never starts training.

Create/update previews validate JSON specifications on the backend. A populated
command spec must contain `commands` (a list); action specs use `actions` (a list)
and observation specs use `groups` (a mapping). Unknown envelope fields and wrong
collection types are errors, not empty configurations. Use `{}` to intentionally
clear a spec. Spec validation does not execute source files or weights.

Nested action terms, observation groups/terms and command terms also reject
unknown fields; correct a misspelling rather than relying on normalization to
discard it. Type-specific fields must belong to that term type. Custom `kwargs`
remain the supported extension point.

For a third-party checkpoint, use `cw_deploy_rl_policy(operation="inspect")`
first. A local `.pt`, `.pth`, or `.zip` uses a two-step signed upload:
`prepare_upload` returns an HTTP PUT URL and explicit upload handle, and
`complete_upload` finalizes that handle after the caller transfers the bytes.
Then `register_checkpoint` records either that attachment or an HTTPS
`weights_url`; `publish_controller` creates the controller policy; and
`assign_controller` binds it to a twin. Mutations preview by default, controller
replacement requires `replace_existing=true`, and assignment does not start the
controller. `start_controller` defaults to `mode="simulation"`; physical execution
requires explicitly setting `mode="live"` as well as the live confirmation and
step bound. Start the simulation with `auto_run_controllers=true` only after the
user asks to run the assigned policy.

Registration stores weights; it does not install an executable adapter. Inspect
again after registration: `cw_deploy_rl_policy(operation="inspect", rl_task_uuid=...,
checkpoint_uuid=...)` reports compatibility and blockers. Publication/assignment
reject undeclared or unsupported formats. Only for genuine legacy skrl agent
checkpoints, register `metadata={"checkpoint_format": "skrl"}`. Never relabel a
TorchScript actor as skrl. Manifest-based policies retain their independent
evaluation gate. `declared_compatible` is static preflight, never proof of execution:
`execution_verified` remains false. The task's source/configuration must implement
the observation ordering/history, normalization, action mapping/scaling and timing
used during training. An arbitrary TorchScript actor still needs a supported
adapter/loader implementation and a simulation smoke test; neither dimensions nor
successful upload/publication establish that compatibility.

Compatibility is checked again on controller start, including policies assigned
before these checks were introduced. A blocked preview must be corrected before
execution; `execute=true` does not override compatibility.
If inspection/preview reports `INVALID_CONTROLLER_PROVENANCE`, repair the named
`rl_task_uuid`/`checkpoint_uuid` metadata references or publish a controller from
the correct registered checkpoint. This is not a missing upload: re-uploading
weights alone does not repair the controller's provenance.

For hosted-run evidence, use `cw_deploy_rl_policy(operation="inspect",
rl_task_uuid=..., twin_uuid=...)`: this returns retained deployment reports and
controller-session history, including terminal failures. Select `workload_uuid`
from a session to retrieve its latest 200 log lines; logs require environment
write access. Task/checkpoint/workload filters restrict retained reports, whose
original evidence-source labels and hardware-approval flags are preserved.
Capture available simulated camera frames separately with `cw_capture_frame`
or `cw_capture_frames`, using `mock=false`.

For an episode reset, stop the current run with `cw_stop_simulation`, then use
`cw_start_simulation`. Each start creates a fresh simulation workload/worker and
new MuJoCo model/data from the current scene configuration. Stop also stops the
environment's controllers. Wait for the new run to be running, then start the
assigned controller, or explicitly request `auto_run_controllers` at start.
There is no separate in-place reset API; stop/start is the supported functional
reset. Keep the scene configuration and initial conditions consistent across
trials; a fresh process does not itself guarantee identical randomized seeds.

Before training, read the [supported checkpoint contract](https://docs.cyberwave.com/feature-reference/uploading-policies#supported-checkpoint-contract)
and [task/adapter contract](https://docs.cyberwave.com/feature-reference/rl-tasks).
Arbitrary PyTorch/TorchScript actors are not currently supported through the
upload-to-controller path; do not mislabel them as skrl checkpoints.
Missing reports are not zero-success episodes, and worker/operator reports are
not independent evaluation. Do not infer a >60% success rate from workload
completion, log text, camera availability, or policy registration.

For a shared physical lab, use `cw_manage_remote_lab(operation="status")`, then
preview and apply `request_access`. Do not start while queued: the session must
be `active` for the target twin's exact environment. After assignment, preview
`cw_deploy_rl_policy(operation="start_controller", mode="live", ...)`, show the
resolved twin/controller/session and bounded `max_steps`, and apply only with
the user's current explicit physical intent plus `confirm_live=true`. MQTT is
the default transport; request Zenoh only when the lab driver declares the full
live data-plane capability. Use `stop_controller` for the exact policy/twin, or
`cw_manage_remote_lab(operation="end_session", execute=true)` to stop active
environment controllers before releasing the reservation. Session expiry also
force-stops controllers and restores the bindings captured when the reservation
became active. Status polling also recovers expired sessions synchronously if
their timer was lost, without enqueueing duplicate cleanup tasks. The reservation
remains occupied until cleanup succeeds. A deployed workload is
not evidence that the learned task worked.

When a requested capability needs training, `cw_request_skill_teaching` prepares a simulation-only proposal; it does not start a job. Reusing an existing compatible policy is the default. When the user explicitly requests retraining or a new version, set `reuse_existing_policy=false` if the callable schema supports it. The dashboard's existing teaching card offers **Train a new version** and opens the same review/confirmation flow. Do not confirm policy reuse while describing it as training.

Omit optional training settings to use their declared defaults; do not send `null` or invent adapter-specific fields to express compute constraints. Local compute limits belong to the proposal's `training.compute`, not arbitrary optimizer options. Verify the task adapter's supported parameters before overriding them. MCP `status=ok` only means the tool call succeeded: inspect `teaching_status` and the refreshed request's requirements. The same card in chat and the task view reads current server state; repeated status reads should not become separate confirmation cards.

Async task adapters now declare `training_options.json` next to `training.py`. Discover its versioned strategies, JSON Schema constraints and defaults through `GET /api/v1/rl-tasks/{uuid}/training-options` or `proposal.training.options`. The proposal exposes `resolved_strategy_config`, which is frozen into the confirmed job. Nested object overrides replace the whole object; supply all its required fields. Missing descriptors or invalid settings produce `needs_input`, not a runnable proposal. Correct the task source or prepare a fresh request; never silently edit an approved request. Historical checkpoints and recordings remain readable, but an old unconfirmed proposal must be prepared again under this contract. Training images must be rebuilt to include the same validator before enabling the updated worker path.

For explicitly selected demonstration/teacher files, author optional
`training_inputs.json` beside the adapter: `schema_version: 1` and `files`, each
with a canonical relative `path`, readable `attachment_uuid`, lowercase `sha256`
and exact `size_bytes`. Use the existing Attachment create/upload APIs with an
explicit workspace or environment anchor; never put binary weights in source
rows or give a worker download credentials/URLs. `.npz` and `.onnx.data` uploads
are opaque payloads, not deserialized by the API. Private sources must be in the
task workspace. Preparation freezes exact copies at
`<task_id>/training_inputs/<path>` and lists them in the shared confirmation
card; those copies follow the task's sharing permissions. Limits are 16 files,
64 MiB per file and 128 MiB total, within the existing bundle/expanded limits.
Access and fingerprints are rechecked at confirmation, dispatch and worker
requests. The ordinary source export is not the confirmed data bundle; use the
proposal's frozen attachment for reproducibility. A missing/replaced file needs
a fresh proposal. Only task training imports its teacher; normal held-out
evaluation and deployment must use the newly learned actor alone.

The shared chat/task card offers **Cancel training** with confirmation for its
active attempt. Cancellation prevents new result registration; verify worker
shutdown separately. **Prepare a new attempt** on a failed/cancelled request
reuses its settings but requires a fresh proposal and confirmation. Preserve
earlier attempts, policies and recordings; retrying does not establish success.
The same button is available for **Needs input** once the missing task inputs
are corrected. It prepares a fresh proposal; it does not fix inputs or confirm
training automatically.
Changed-input confirmation conflicts and expired requests offer **Prepare a
fresh proposal** in the same card. Inspect the refusal, prepare from the current
task, and review the new card; do not retry an old approval hash or bypass its
fingerprint checks. Preparation still does not confirm or start training.

Keep the previous checkpoint and binding unchanged until the new version passes evaluation and the user explicitly selects **Use on this robot**. A completed workload proves execution ended, not that a robot task succeeded; inspect fresh measured motion and physical acceptance evidence.

For failed or underperforming attempts, use `cw_plan_policy_improvement` when
available, with the exact teaching request UUID. The Policy Improvement Agent
inspects that attempt and recent task history, returning cited observations,
hypotheses and one proposed next step. It applies nothing. A
`prepare_training` result includes validated `teaching_request` arguments for
`cw_request_skill_teaching`; use them only within an authorized retry request,
then leave the existing confirmation card to the user. Setup suggestions go to
the existing simulation preparation flow; task-source/reward/observation changes
need a reviewed task revision. Do not silently lower evaluation criteria or
repeat training without a new testable change. Different contracts or missing
metrics cannot substantiate an improvement claim. The current agent does not
automatically wake after a job, run a campaign, bind, publish or actuate hardware.
When training starts from frozen actor weights, the improvement evidence may
include the unchanged initial actor's same-protocol baseline separately from the
neutral baseline. Compare both before attributing success to new learning.
Missing or invalid initialization evidence is unknown, not zero performance.

Supporting perception (such as cube tracking or depth estimation) is a workflow
and task-input change, not permission to fabricate sensor readings. Reuse a
verified model/workflow and declare whether its output is pixel position,
calibrated world position, measured depth or predicted depth. Review frame,
units/scale, latency, confidence and missing-data behavior; training and deployed
observations must match. Simulated privileged state can help training, but cannot
silently replace unavailable deployment perception. The improvement agent may
propose this setup; arbitrary perception-to-policy wiring is not automatic.

The completed teaching card offers **Use on this robot** directly for an evaluated checkpoint, even before a controller exists. That explicit action validates the lineage, creates a private controller if needed, and binds it atomically; replacement still requires confirmation and an inactive controller. It does not start motion. **Publish to catalog** is a separate permission-checked action and does not require binding first. Reading the card never creates a controller or publishes an artifact.

Evaluation workers may return bounded measured-joint episodes with optional measured procedural-object poses. New free-base bindings require measured world-root poses in every returned frame; they can have zero scalar joints. The backend resolves logical names through the approved task snapshot, checks current environment access and object identity, and ingests them into the existing Recording/Parquet path. Find their **Replay** links in the task's policy evaluation evidence. Ingestion is idempotent and honors recording opt-out. Replay never executes the actor or publishes control commands. Only recordings explicitly containing object/root poses animate those transforms; older joint-only episodes leave them at their authored position. None implies camera evidence or independent success certification. Do not present joint-only playback as proof of locomotion or that an object was grasped or carried.

For an external MuJoCo deployment, supplement sampled controller telemetry with the runner's per-physics-step audit (contacts, simultaneous force-bearing contacts, non-finite state, warnings, applied external forces and coverage). This endpoint uses the runner's deployment-configured control API protection; keep that service private/protected. An audit is not a task result or hardware approval. Require matching runtime, plant/session/workload identity, complete coverage and a task-specific acceptance check. Preserve failed runs, including version mismatches.

The normal simulator worker now retains a bounded audit after controller commands have been quiet for at least one second. When no matching MCP tool is available, read retained evidence through `GET /api/v1/cloud-node-workloads/{uuid}/simulation-audit`, using the exact simulation workload UUID. This survives worker shutdown and rechecks current environment/controller access and recording opt-out. Generic workload responses omit the raw audit. Retention is best-effort: an active command stream, stop request, abrupt exit or upload failure can leave it missing or without a final snapshot. Inspect its actual command activity, coverage and `finished` flag; do not infer shutdown coverage from a terminal workload. The audit remains worker-reported physics, not automatic task acceptance, a learned policy evaluation, or hardware approval. Never upload an invented audit or give controller/task code the simulator service credential.

Completed simulation trials can have operator-reported deployment evidence in **RL task → Policies → Policy evidence → Deployment reports**. When no matching MCP tool is available, the verified REST reporting surface is `POST /api/v1/rl-tasks/{uuid}/deployment-reports` (`checkpoint_uuid`, `report`), with GET on the same route. Reuse the validator's actual report, including failures; do not invent measurements or checks. Registration checks current access and the frozen dispatch, and is idempotent for the same report. These records are separate from held-out evaluation and do not grant deployment or hardware approval, bind a policy, or publish a model. Reported checks and digests are not independent backend certification.

Newly confirmed task versions can include an optional `deployment_acceptance.py`
with an `assess` function. The simulation controller runs this task-authored check
from its hash-verified bundle after bounded control, using measured vector
observations/actions and a matching retained plant audit. It reports through the
same deployment-reports route before exiting; the UI labels this source
**Automatically reported by the controller**. It does not add an evaluator to
historical checkpoints. Adding/changing the check requires a fresh confirmed
training version. Capture is limited to 4,096 steps and 4 MiB, with vector
observations only; missing/incomplete capture, audit or upload is not a pass.
Recording opt-out and current permissions apply. Neither the report nor its
digest independently certifies the task-authored checks or enables hardware.

The shared recorder additionally checks the measured plant timestep against
`rl_policy.embodiment.physics_contract.physics_dt` in the frozen artifact.
Missing/invalid metadata, a changed timestep or a mismatch fails this check;
an authored failure stays failed. This adds no task evaluator to old artifacts
and never changes the frozen task source or relaxes its success criteria.

The same **Policy evidence** card has **Deployment recordings**. For supported simulation runs, the normal RL controller samples fresh measured joint/object feeds and, for newly frozen free-base bindings, the declared root-pose feed. It uploads a bounded recording before exiting, using the confirmed training bundle's frozen bindings. The existing environment Replay viewer opens it after the session ends. Capture honors the robot's cloud-recording setting at dispatch and ingestion; missing/stale feeds, abrupt worker termination or upload failure can leave no recording. Freshness is per measured joint/body, not inferred from another moving body or a cached startup pose. A failed run can have a recording, and a recorded run is not necessarily successful. This path does not capture cameras; a world-root recording cannot currently replay a twin that has since been docked. `GET /api/v1/rl-tasks/{uuid}/deployment-replays` lists accessible recordings; POST is reserved for the matching running controller-workload credential, not an operator upload route. Do not manufacture a deployment recording by submitting an actor rollout or commanded targets.

**Replay deployment** also opens available camera recordings when their robot,
frozen simulator-run identity and time window match the motion recording. The
list endpoint returns these as `media_recording_uuids`; it does not capture
cameras itself or infer missing run identity from timestamps. Camera finalization
can lag behind the controller; the visible evidence card refreshes its listing.
Links are bounded, and unavailable/additional media can be selected in the
existing recording calendar. Associated recordings do not imply frame-accurate
synchronization, useful sensor images or a successful policy. Historical camera
rows without queryable run provenance may require the existing recording mirror
to be refreshed from their retained metadata; do not invent or relabel provenance.

For wrist-camera checks, use the declared sensor ID and simulation source. A cached image alone is not liveness: inspect advancing producer generations. Policy-depth PNGs are normalized 16-bit values using the declared min/max depth, distinct from MQTT's metric-millimetre encoding. Validate optical frames and actual scene visibility; a dark depth preview can reflect the configured range. Report API frame capture separately from working live video in the UI, which also requires the media relay. Never use mock frames as evidence or request a physical-camera pull for a simulation check.

When reviewing deployment evidence, inspect **Final task outcome maintained**
as well as intermediate stages and physical checks. Passing every intermediate
stage does not imply sustained success. A missing final outcome is **Not
reported**, never a pass inferred from other badges.

## Export for local custom-reward training

`cw_export_mujoco_scene(environment_uuid, wait_seconds=0, poll_interval=2)`
exports the environment as a MuJoCo ZIP with its required assets. Use an actual
UUID from `cw_list_environments` or scene creation. The API key must have read
access to that environment. Export may generate a cached package; it does not
start a training job, bind a policy, or move hardware.

Call with `wait_seconds=30` to poll for up to 30 seconds between backend calls
(an in-flight HTTP request can take longer). The normal tool envelope contains
`data.status`, `data.ready`, `data.url`, `data.environment_uuid`,
`data.entrypoint` (`mujoco_scene.xml`), `data.format` (`zip`) and
`data.retry_after_seconds`:

- `pending`, `ready=false`: call the same tool again after `retry_after_seconds`.
  This is a resumable generation state, not successful export or a failed job.
- `completed`, `ready=true`: download `url` promptly and extract the **entire**
  ZIP, preserving relative asset paths. Retain a local copy for reproducibility.
- Envelope `status=error`, `code=scene_export_failed`: read `details`, correct
  the scene/assets, and retry after correction. Other errors retain the existing
  authentication/permission or transport error contract. Missing URLs and unknown
  generation states are errors, never ready packages.

`wait_seconds` is finite and between 0 and 30; `poll_interval` is finite and
between 1 and 10 seconds. A default call reads once. Polling uses the same
permission-checked route each time. No user confirmation is required for export;
platform training still requires the existing Cyberwave confirmation flow.

### Piper pick-and-place recipe

1. Reuse `cw_search_catalog`, `cw_edit_environment` and
   `cw_get_environment_context` to prepare and inspect the Piper/table/cube scene.
   Fix the table and arm base; use dynamic 0.02 m cubes resting on the surface.
   Give the target area an explicit position on that same surface. Preserve the
   verified camera configuration; an exported camera is not a live RealSense feed.
2. Call `cw_export_mujoco_scene` with that environment UUID, repeat pending calls,
   and download/extract the completed ZIP. Do not substitute the XML-only export,
   which does not bundle meshes. The existing SDK's
   `cw.environments.export_mujoco_scene(environment_uuid, "scene.zip")` is a
   synchronous fallback for clients with the Python SDK.
3. Load the extracted package in a local Python environment with MuJoCo:

   ```python
   from pathlib import Path
   import mujoco

   scene = Path("scene/mujoco_scene.xml").resolve()
   model = mujoco.MjModel.from_xml_path(str(scene))
   data = mujoco.MjData(model)
   mujoco.mj_forward(model, data)
   print(model.nu, model.nq, model.nv)
   ```

4. Author the local RL environment and reward against the **exported** body,
   joint and actuator names. Inspect actuator types, control ranges and timestep
   before choosing bounded actions. Step with `mujoco.mj_step(model, data)` and
   compute the custom reward from measured simulation state. Keep reset state,
   observations and target/cube bindings explicit; do not assume a generic arm
   policy or zero controls will hold the Piper safely in simulation.
5. Train and iterate locally using your chosen trainer. Freeze separate held-out
   resets/seeds and measure sustained cube placement in the target region on the
   same surface. Retain reward source, ZIP hash, dependency versions, checkpoint,
   episode outcomes and success-rate denominator. The demo criterion is **>60%**,
   not >=60%; export/load success alone does not meet it. Privileged simulation
   state must not be described as camera-based deployment perception.

This path permits arbitrary local reward code; it does not submit that code to
`cw_request_skill_teaching`. Local checkpoints are not automatically platform
policies or hardware-approved controllers. Platform training and subsequent
binding continue through their existing review and authorization flows.

## LeRobot VLA fine-tuning sources

Use the existing MLTraining/LeRobot path for VLA fine-tuning. A selected checkpoint
wins over a generic base repository; missing weights or dataset downloads are
errors, never a reason to choose another source. Preserve Hub `policy_revision`
and the saved camera/joint/normalization contract. Hub-based adapter exports keep
the resolved base commit for deployment on another worker. An arbitrary local
base must also be available when reloading its adapter; request the original base
or a complete policy rather than substituting one. Verify the exported checkpoint
can reload and infer before task evaluation. A few optimizer steps with finite
simulated actions establish pipeline operation, not learned task success.


The shared training path supports SmolVLA and experimental LeRobot π0/π0.5
contracts. Preserve `policy_type` and `policy_runtime` through training and
export; an older OpenArm π0.5 checkpoint is a separate runtime. Do not select
SmolVLA as a fallback for an unknown model. π models retain their own optimizer
and processor defaults and require their upstream dependencies. Passing config
or mocked loader tests does not establish successful pretrained-weight training.

Use **Camera setup** on a model to review its saved setup in an environment or,
with model write access, save an environment setup as a recommendation. Camera
recipes preserve slugs, physical optics, Z-up placement and mounting ancestors;
local bindings belong to the environment. Review missing resources or changed
asset definitions explicitly. Model read access is enough to apply a recipe to
a scene the user can edit. Do not rewrite an external model, copy stream
credentials into it, or replace training provenance with current scene settings.
Restart simulation after changes before collecting data. Mixed/unknown recording
setups require review; the exported recipe is not measured calibration.


## Import external robot policy weights

Use **AI models → Import robot policy** for complete LeRobot SmolVLA, π0 or π0.5
checkpoint archives. The flow creates an owned private catalog model (or a
workspace model when selected), with its source attachment, portable slug,
family, state/action dimensions and camera roles. A plain tensor file is not a
complete executable policy. Importing proves neither compatible action semantics
nor task success. Review the model's joint order, units and camera setup before
running it; an OpenArm/SO101 dimensional mismatch needs a matching checkpoint or
an explicit supported adapter, not truncation or padding.

API fallback: upload through the existing Attachment API, then POST
`/api/v1/mlmodels/import-policy` with `name`, `workspace_uuid`, `attachment_uuid`
and optional `visibility` (`private` or `workspace`). For replacing an existing
model's weights, POST `/api/v1/mlmodels/{uuid}/weights` with the readable
`attachment_uuid` and exact `expected_updated_at`. Null detaches the weights.
Do not write storage paths or arbitrary `weights_url` into metadata. Keep server
timestamp precision; a version conflict requires reloading and reviewing again.

Archives should place policy `config.json` and optional
`cyberwave_camera_setup.json` before large tensor files. The API only inspects
bounded JSON metadata; tensor loading remains a worker operation. Older exports
may require repackaging. A separate recipe can be imported in **Camera setup**
or POST `/api/v1/model-camera-setups/{uuid}/import` with `setup` and
`expected_fingerprint`. Supplied setup is labeled imported, not recorded training
evidence. Apply it to an owned environment only after review; restart an existing
simulation so its scene reflects the saved setup. Missing, changed or detached
weights must not fall back to another checkpoint.

LeRobot training, inference and previews share the checkpoint downloader. It
checks the catalog endpoint before using cached weights; a removed model or lost
read access must still fail when local files exist. The weights response includes
`sha256` when known. Workers verify this digest before extraction and use it for
cache identity; rotated download links alone do not change the weights. Older
endpoints and direct URLs without a digest are downloaded again. Interrupted or
invalid archives never become reusable checkpoints. Cyberwave credentials are
sent only to configured API hosts, never to signed object downloads.

Fine-tuning an imported LeRobot adapter continues from its saved tensors and
preserves the base repository/revision. This starts a new fine-tuning run; it is
not a resume of the earlier optimizer state. Validate the newly exported model
with fresh camera images and measured simulation feedback before task evaluation.

New training requests retain the selected model source before conversion starts.
A changed or inaccessible source stops the queued run and asks for a new reviewed
request; renaming alone is allowed. Completed runs retain their source name and
contract even after the original model is removed. Each new run produces its own
output model and controller versions; retrying deployment reuses that run's versions. Historical
runs without a saved source cannot prove their original request-time selection.
Do not edit the saved training source to force a queued run to use another model.
