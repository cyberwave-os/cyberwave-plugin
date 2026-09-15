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
