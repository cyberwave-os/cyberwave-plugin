# Robot control

Read this for navigation, motion poses, joint commands, stop commands, observation actions, controller-policy routing, and simulation/live handoff.

## External SmolVLA policy setup

Use the model playground's **Assist joint setup** for a reviewed proposal and
interactive pose preview. It reads the model's declared dimensions, robot
schema and supplied checkpoint context; unknown units or ordering remain
visible assumptions. This is not a physics evaluation or task-success claim.

The REST proposal endpoint is
`POST /api/v1/agents/mlmodels/{uuid}/joint-binding/plan`, with `asset_uuid`,
`prompt` and the model's exact `expected_updated_at`. It is read-only and uses
existing agent credits. Review the proposal before saving a separate binding;
never update the publisher model to save a consumer mapping.
Bindings are separate immutable workspace-owned records, not model metadata.
Create with `POST /api/v1/policy-joint-bindings`: `workspace_uuid`, `model_uuid`,
`asset_uuid`, `name`, reviewed `joint_order`, `joint_value_transforms`, the returned
`model_source` and `robot_source`, `evidence`, and `unresolved`. Read access to
catalog resources is sufficient; the destination workspace requires editor access.
List with `GET /api/v1/policy-joint-bindings?asset_uuid=...` (optional `model_uuid`,
`limit`, `offset`). Each save returns a new UUID; `supersedes_uuid` retains lineage.

Use `previous_binding_uuid` on the assistant proposal endpoint to adapt a retained
contract to the selected model, even if the old model was deleted. Review changed
fields and unresolved assumptions; never silently switch models or claim deleted
weights are available. Bindings do not grant access to their references.

Pass `policy_joint_binding_uuid` in controller execution/controller metadata, or
under `robot_context` for playground runs. Source or robot schema changes require
review; do not retry stale mappings unchanged. Workload parameters freeze the
selected mapping. The ghost preview compares an independent robot pose with the
converted policy values; it neither commands a robot nor proves calibration.

The conversion is `policy_value = twin_SI_value * scale + offset`; output uses
its inverse. These are dataset units, not learned mean/std normalization.

Keep camera UUIDs in the existing per-twin controller camera bindings.
Default execution to simulation and inspect actual telemetry separately from
sent targets. Dimension compatibility does not establish learned task success.

## Classify a control request

Determine:

- target environment and twin,
- requested action and bounds,
- mode: `simulation` or `live`,
- whether the user requested a plan or execution,
- and what observation will prove success.

If mode is omitted, use `simulation`. Do not infer live mode from words like "robot", "edge", "camera", or a physical asset name.

## Resolve target and affordances

1. Use `cw_resolve_twin` or `cw_list_twins` until exactly one twin is selected.
2. Use `cw_list_control_surfaces` with the same `mode` as planning to inspect available movement, pose, joint, observation, controller-policy, and stop affordances. The SDK equivalent is `agents.control.list_surfaces(environment_uuid, mode="simulation")`. Explicit Live driver restrictions do not describe simulation actuators; an omitted mode is evaluated as live, the strictest view.
3. Inspect the surface’s per-mode `runtimes` readiness (`available`, `runtime`, and `reason`). Backend admission includes twin health and registered edge availability; do not reconstruct it from client metadata flags. Local connection loss can further disable Live controls. Inspect twin/schema/joint state or edge/driver health when it affects safe execution.
4. If the target or affordance is ambiguous, ask the user to choose; do not guess.

## Saved pose and movement execution

Use the existing `saved-poses-movements` route with `motion_type`, `name`, and
`scope`; do not introduce a robot-specific motion executor. The same route is
available through the UI's pin selector. A stored name is only a library entry:
prepare the selected motion for the requested runtime and inspect readiness.
SDK/direct action previews apply the same joint and runtime capability validation as execution and return normalized targets without queueing commands. Every step must use declared independent joints within their limits. Unsupported
or duplicate aliases reject the entire sequence before dispatch; explicit driver
`command_input=false` blocks Live joint motion without blocking simulation.
Legacy catalogs with unknown command support retain their existing compatibility
behavior; unknown is not proof of physical support.

Simulation saved motions use the shared timed joint command transport. A
`completion_scope=command_trajectory_only` result does not establish measured
motion success: inspect actual joint telemetry. Editor snap/preview tools do not
establish that a controller or hardware command path works. No new MCP or SDK
method is needed, and Live confirmation and ACL still apply.

## Prompt movement input

Use the existing `prompt-motion` route with `inputs.prompt` for a declared
prompt-to-movement capability. The UI exposes the same input in Controllers and
Pin, with an explicit Plan movement button, shared plan feedback and separate
Run/Live confirmation. Typing does not invoke a model. Monitoring and stopped
simulation cannot generate or execute through this input.

Generated inline plans require controllable actuated joints, not an existing
saved motion library. They reuse saved-motion validation before returning Ready
and are checked again at dispatch. Do not bypass unsupported joints or a Live
driver restriction by changing an action to an inline plan. Capability discovery
is not runtime readiness or evidence that the robot moved.

## Operator targets and service identity

The UI remembers each environment's last Control/Monitor role in local browser
storage. This personal preference is not authorization evidence for an agent,
a running session or a restored input connection. Monitor remains read-only;
inspect current mode, permissions and runtime readiness through the existing
control services before acting. A pinned saved-input guide does not activate it.
Edit configuration remains available for supported capabilities restricted only
by the Live driver. Saving inputs does not permit Live execution: input
preparation rechecks the requested runtime. Losing the Live connection invalidates
prepared UI confirmation; reconnecting requires a fresh check and confirmation,
without automatically replaying the retained target.
Input preparation also belongs to its requested owner and operating context:
the UI discards a late handoff after changing twin, environment, mode or Control
access, closing the selector, or restoring the previous setup. A successful
preparation response alone does not mean the browser selected or activated it.

For docked robots, resolve each independently controllable twin and its actual
parent link. Send base navigation to the base twin and joint commands to the
arm or gripper that owns those joints. Verify the children follow the measured
parent frame and inspect each twin's joint telemetry; a moving assembly does
not prove independent joint actuation. A changed mount may invalidate the saved
robot revision: review the mapping through the normal setup path. Never bypass
that check because the displayed keys appear unchanged.

A docked vacuum tool may have only fixed geometry: its IO can still belong to
the arm driver. The UR7 reference setup uses Robotiq EPick. Resolve the deployed
route before binding commands: generic `gripper` publishes `action=grip|release|reset`
to a ROS consumer, while EPick `/grip_cmd` and UR SetIO are separate interfaces.
The legacy `ee_fixed_joint` IO proxy is not a seventh arm joint. Keep it out of IK
and arm trajectories; retain the installation's threshold and pin settings.
Only `tele` reaches physical tool IO, including aggregated joint maps. A successful
publish does not confirm suction, and a configured TCP does not certify a payload.
For UR's declared `gripper` command, use `data.action=grip/release/reset` (SDK:
`twin.commands.gripper(action=...)`), not a standalone `grip` command. The current
MuJoCo handler requires an explicit actuator command binding (below). Docking
the EPick and reaching its TCP are not evidence of a simulated grasp; keep
suction/contact validation separate from arm motion. Do not invent a moving joint
for a vacuum tool.

The SDK's `mqtt.publish()` boolean reports local client acceptance only. Explicit
failure raises `CyberwaveMQTTError` through the shared twin command path and
fails newly generated control/pose/virtual-controller workflow nodes. Inspect the
node error before continuing an inspection or grasp sequence. Old generated
workers require regeneration; legacy injected MQTT clients returning `None`
cannot confirm delivery. Never interpret `sent=true` as motion or grasp completion.

For simulation lifecycle, use `cw_start_simulation`, then poll
`cw_get_simulation_status` for the returned `simulation_id`. The result's
`status=ok` means the tool call succeeded; `simulation_status` carries the
actual lifecycle state, such as `loading` or `running`. A running physics
simulation does not establish navigation, perception or controller readiness.
For managed runs, wait for `simulation_ready` before dispatching navigation;
an explicitly unready runtime rejects the command instead of buffering it.
The reported remaining time includes physics time consumed while runtime services
start; readiness does not restart the duration budget.
An accepted publish or a `local_preview_only` result is not evidence of motion.
Verify measured arrival and any requested final heading on the selected run.
Check the intended control surface before dispatch. Stop the selected run with
`cw_stop_simulation`; do not start another run to check whether loading finished.

For perception validation, separately verify sensor delivery, mapping-provider
output, a saved map and its coverage/alignment in the environment. A pointcloud
or completed waypoint alone establishes none of the later steps. Use a declared
sensor and the configured provider; do not copy a different robot's camera mount
or silently reuse its scan-density filters. Stop mapping and await the final
artifact before stopping simulation. An interrupted map retains received
snapshots; periodic uploads cannot reopen that interrupted session, while a late
final snapshot may still complete it. UI Map details exposes the same stored
status and source; navigation/avoidance needs separate measured acceptance.
Saved point clouds have an authenticated bounded display projection at
`GET /api/v1/maps/{uuid}/point-cloud.ply`; original data stays unchanged. The
inspector and Overview share this geometry. Scene overlays require explicit
environment-frame coordinates in meters; display does not establish calibration
or free space. Fixed single-body box/sphere props can derive simulation
eligibility from their schema without a robot driver. Other simulation blockers
use the existing preparation/review flow; accepting a successful MuJoCo probe
updates only that twin's MuJoCo compatibility, not the shared asset or live
hardware readiness.
Saved maps are layers in the collapsible left scene list in Edit, Simulate and
Live; selecting a row opens its preview and details in the right inspector.
The list shows the latest map in each source/type/robot series; use Map history
for earlier versions. Selected, visible and pinned versions remain accessible.
Legacy unaddressed map updates reuse one destination per twin/type/runtime;
use an explicit saved map or mapping session for an independent acquisition.
A stale or foreign map reference is an error, not a request to create a new map.
Visibility and management remain on the left row. The right Mapping section
is for acquisition. A map pinned to Overview is a presentation reference to the
same artifact, separate from scene visibility and the navigation anchor. Do not
infer localization readiness from a visible map or pin; a robot marker needs
compatible frames and current measured pose. Monitor is read-only for map
mutation and acquisition. Select a robot with a declared mapping service
and use Control with edit access; wait for simulation readiness before requesting
a map there. Do not repeat a request while it is pending. Temporary mapping-session
updates do not require re-saving control setup;
changed robot declarations, localization or policy references still need review.

Workbench point and joint panels use the same declared control routes as agent commands. A user-typed or scene-selected world point is direct input: do not invent a perception task or model evidence record for it. Perception-derived targets still require the existing evidence, metric scale, calibration and frame validation. Joint geometry alone never grants command support; use the declared named joints, units and limits.

An IK target uses the inherited or explicitly overridden service/tool frame. Keep the configured provider and closure constraints; never infer a default from the robot's name. A pin or scene marker is presentation/staged input, not a request to execute. Resolve and validate the target before dispatch, preserve plan identity and explicit Live confirmation. Hidden or monitor panels cannot send commands. Panel visibility and pinning do not replace backend authorization.

The existing read-only kinematics preview accepts `operation="workspace"` with
its current model revision. A sampled guide, when supported by the configured
solver, is only a placement aid: orientation, collisions and holes in the envelope
are not certified. Keep closed-chain solvers and do not invent missing bounds.
A `valid_ik_joint_limits` failure is a model-configuration problem: inspect the
named joint and correct the source declaration through the normal review path.
Moving the target or retrying without orientation cannot repair that problem.

## Configuration review and reusable inputs

Use the server's `control_capabilities` projection and control routes. Structural joints and a topic direction do not establish joint command support. Explicit driver `command_input=false` blocks new direct-joint setup; absent metadata is legacy uncertainty, not proof of readiness. Preview, simulation and live acceptance require their own runtime evidence.

For a reviewed policy run, retain the returned `plan_id`. If the policy or its linked model changes before dispatch, request a new plan and review it again. Do not retry the stale plan or omit its ID to bypass the check. Older cached policy plans may also require a fresh review after a backend upgrade. This change check does not establish model/robot compatibility or freeze an execution's artifacts.

For direct joint targets, use the independent joints listed by the control surface and their declared units and limits. Mechanically coupled mimic joints and explicitly passive joints are not separate targets, including when an older joint-ordering list mentions them. They can still appear in model state or visualization. Do not infer passivity from missing legacy actuator records or from a solver temporarily holding a joint fixed. Missing limits are unknown, not zero. Review again after changing any target; a ready plan is not evidence of motion.

Send Pose validates the same independent targets on save and when resolving cloud
or generated edge commands, including values received from upstream models. A
known empty joint interface is not an unknown legacy interface: do not bypass it
with raw joint names. Choose a supported service or correct the source declaration.
After adopting schema changes, regenerate and redeploy an edge workflow before
relying on its updated contract; a catalog edit does not rewrite a running worker.

Send Pose requires a target plus either a saved pose or enabled joint values.
Use its Connected joint values section (or the same workflow input mappings via
API/MCP) to bind a producer; no separate controller assignment is created.
A selected target is retained when legacy upstream data also carries a twin UUID.
Use an explicit target input mapping for intentional dynamic cloud routing;
compiled edge workflows stay bound to their compile target.
An unrelated trigger does not satisfy this command requirement. Selecting a
saved pose remains supported, including existing named-pose value mappings.

For a linear workflow, Send Pose can consume `positions`, `velocities` and
`efforts` from its connected upstream node without duplicating a saved pose.
Prefer explicit input references for new configurations; existing implicit
connections remain supported. Branch activation must use its explicit caller
mapping rather than combining sibling outputs. Cloud and generated edge workers
use the same numeric filter: invalid, boolean and non-finite values are skipped
with a warning, valid zero values are retained, and an empty resolved command
fails without publishing. These checks do not validate model units, joint limits,
collision clearance or learned-policy compatibility.

Managed immediate simulation joint commands use actuator `target_positions`, not measured `positions` (which retain the legacy direct-state/preview meaning). A publish failure returns an error; a queued command does not prove movement. Completion for this route requires measured positions for every requested joint within the server's absolute tolerance (currently 0.001 in each command unit). Updated workers report progress during simulation; compatible backends can confirm arrival before the run ends. Older workers may report only at termination, so do not retry a pending command merely because completion has not arrived. Timed trajectories and older action records retain their separate completion semantics. Progress does not add immediate-target cancellation or authorize simultaneous input ownership.

If a reachable simulation target sags under a docked load, inspect measured
joint error, ground contacts and the authored actuator configuration first.
For supported position servos, the existing universal-schema actuator extension
`gravity_compensation: true` enables model-bias feedforward in updated MuJoCo
workers. Review and save it through the existing schema configuration, then
restart the simulation. It is opt-in, preserves native gains/force/control limits,
and supports one stateless, unit-gear position actuator per joint. Do not enable
it for other actuator types or compensate the whole robot with external forces.
This does not configure physical driver compensation, identify payloads or prove
collision-free motion. Keep arrival tolerance and requested targets unchanged;
verify fresh measured state after dispatch, including Stop with another twin active.

Navigation goals use the existing Cyberwave navigation service, not locomotion WASD mappings. End-effector poses use the declared IK adapter: Frax for configured serial-chain models, or Placo with its configured active/passive joints and closure constraints. A missing solver or an unsupported provider remains a setup issue. Do not infer MoveIt availability or rename Cartesian outputs into joints.

For suction tools without moving joints, do not invent a joint target. Updated
Robot Format supports an explicit MuJoCo body adhesion actuator in the existing
universal schema (`type: "adhesion"`, empty `joint`, `control_range`, and
`extensions.mjcf_adhesion` with `body` and a force `gain`). This preserves a
simulation primitive. To route a declared command, add
`extensions.command_binding` on that actuator with `command: "gripper"`,
`argument: "action"`, `source: "parent"` and
`values: {"grip": 1, "release": 0, "reset": 0}`. `source: "self"` is the default;
`parent` resolves the actual directly docked twin, not a copied catalog UUID.
The simulator validates actuator ownership, enum choices and native bounds;
ambiguous parent routes fail setup. Use the existing revision-checked twin schema
patch, and keep uncalibrated gains local to validation. The backend, Robot Format
and simulator must all contain this support; restart stale workers after upgrade.
Commands use the existing source/session gates. The actuator holds its last
accepted target when a producer stops, so stopping a workflow does not drop a
payload; releasing requires a subsequent authorized command. Contact/seal feedback
and a completed managed grasp workflow still need separate validation. A queued command or `can_grip` alone proves neither
attachment nor release. Do not publish unsupported grip commands as a successful
simulation step or turn on uncalibrated physical suction.

If Nav2 rejects a destination, inspect the returned navigation status and map
coverage before changing the locomotion policy. A recent costmap can explain
unobserved space, a point outside the grid or insufficient obstacle clearance.
Suggest an observed destination or extending the map; do not silently enable
unknown-space traversal. A free destination cell does not prove a clear route.
When validating locally, verify the navigation processes have stopped as well
as the physics workload before starting another session.

A published navigation command is not runtime acceptance. Follow its action ID
until the runtime reports a result. If that result names a missing module or
another runtime dependency, repair/redeploy the matching navigation image and
run its dependency smoke check before retrying; editing input mappings or the
locomotion policy does not repair an incomplete image.

With deferred Nav2 startup enabled, both an observed occupancy grid and the
map-to-base transform must be available. SLAM's initial transform alone is not
readiness. Check sensor delivery and map generation if startup remains pending;
do not disable the gate to make an unobserved environment appear ready.

Tool-frame authoring uses the same `GET`/`PUT /api/v1/{assets|twins}/{uuid}/kinematics/tool-frame` contract. Read its revision, edit only a declared model link and `tool_pose` (metres in that link's frame, quaternion `[w,x,y,z]`), then PUT with `expected_revision`. Provider and robot-model internals cannot be replaced through this endpoint. Save does not execute motion or establish collision/runtime readiness. Newly added twins adopt the asset defaults; a twin edit stays in that environment. Managed IK settings must not be overwritten through a generic metadata PUT. Stale revisions, unavailable declarations and active runs require resolution rather than a forced overwrite. Full worker snapshot pinning remains a release requirement.

An IK preview with `status="not_configured"` can identify a missing solver
runtime. Repair the matching backend deployment before retrying; changing the
target or tool offset cannot install Placo/Frax. A busy or unavailable runtime
returns an error explaining availability; it does not establish that a target
is unreachable. Retry a busy runtime, or inspect deployment logs for repeated
failures before changing the robot's geometry. A successful pose calculation
does not establish a command interface: also check declared actuators and that
the solver's output joint names match the twin's supported targets.

A declared IK service or tool frame remains discoverable when joint control is
unavailable. Its route reports `needs_setup` and `controllable_joints`, with the
same reason returned by planning. Review the asset's actuators and the driver's
joint-command support; a listed route or selected Placo/Frax service does not
authorize a target. Do not infer actuators from visual joints or bypass the block.

Keep an unsaved tool offset and its reviewed revision together. Background refresh
must not silently replace either. After a conflict or refresh failure, explicitly
reload and review before retrying; do not substitute a newer revision onto the
old offset. A target change starts a new edit. Catalog and Workbench use this same
flow, and Monitor can inspect the frame without saving or placing its point.

Prefer reusing an existing input controller reference and a reviewed action-local mapping over creating another controller/slug. The action API supports saved joint mappings and, on v3-capable deployments, command mappings; these are not general activated template inheritance. Review migration preserves original presets and existing drafts; never report a saved draft as active migration. Calibration/device pairing remains instance-specific. Catalog Control and Workbench share the setup form; Capabilities declares support rather than hosting Control preferences.

When changing only a key or gamepad trigger, preserve the saved command arguments, including absent values and legacy aliases. Do not merge newly advertised defaults into an existing payload: they may change which operation the driver performs. Defaults initialize new bindings; parameter changes require their own review. A listed command without an argument contract is not evidence that it accepts an empty payload.

Several distinct keys or gamepad triggers may invoke the same declared command
with different parameters (for example Grip/Release or two light intensities).
Keep them as separate rows in the existing input mapping. Identify the row by
its trigger when editing; deduplicating by command/actuation loses configuration.
The UI's Add key / Add input follows this same format without creating a preset.

A command spec may declare `required_any_of`: supply at least one of those typed argument names, preserving its declared type and bounds. Zero is a value, not a missing setting. For UGV lighting, `pwm` sets both lights; existing channel or array parameters remain valid alternatives. Do not add `pwm` to a saved channel-specific payload. Setup validation and saving do not execute the driver.

Preset joint keys are reviewed against the target's joints before the editor offers reuse. An absent action mapping reuses those reviewed keys; an explicit empty mapping clears them; Reset removes only the override. Extra legacy settings, other command modes or foreign joints require review, not a lossy conversion. A preset update invalidates the save review. This authoring projection is not a frozen runtime snapshot or permission to execute.

For reusable command keyboards, the action response may include `input_layout` on an input option. This is an explicit suggestion, not an inherited or active mapping. Use it only after checking the intended keys; save it through the existing v3 action configuration with `expected_revision`. Driver declarations supply the commands, typed defaults and repeat behavior. Unsupported, ambiguous or incomplete commands remain unmapped; do not infer values or create another robot-specific controller. Preserve existing custom maps and deliberately cleared maps. A changed template requires a new review. Catalog saves affect asset defaults; twin saves remain local. This does not start an input or policy.

## Plan

Use `cw_plan_control_action` as the primary entry for move, navigate, stop, observe, pose/motion, or joint intents. State the action precisely and pass explicit environment/twin/mode.

Use `cw_resolve_control_route` only as a lower-level pre-validation step when a specific route needs structured inputs. If it reports `needs_setup`, fill missing fields only from accepted target shapes and listed candidates, then plan again.

Inspect the plan for:

- selected twin and mode,
- exactly described action(s),
- limits/units/targets,
- warnings and missing requirements,
- and whether dispatch is required.

Planning never authorizes motion.

Before dispatch, inspect the Environment's `control_plane_access` policy.
`workflows` forbids direct twin dispatch through MCP/A2A;
`direct_control` and `direct_control_and_workflows` permit it. A workflows-only
policy still allows an authorized workflow's nodes to command twins. Do not work
around a policy denial with a lower-level control tool.

## Environment assistant handoff

In the environment UI, keep using the same assistant conversation across Edit,
Monitor and Control. Mode labels identify where a request happened; retained
history does not authorize actions in a new mode. Monitor inspects only. Control
can inspect capabilities, propose a skill and call the control planner; **Review
in Simulation/Live** opens the existing execution controls without replanning.
Switching runtime requires a new matching plan, not reuse of a simulation plan
on hardware. Switching modes requests an assistant stop, not a robot/job stop.

Reuse the workflow assistant for setup proposals. In this Control sidebar,
workflow creation/editing and run requests are previews: switch to Edit to apply
changes, and open the workflow to verify its runtime target before running it.
An MCP client may expose additional execution tools; its explicit permissions
and the live execution gate below still apply.

## Simulation execution

When the user requested execution, pass exactly one returned action to `cw_dispatch_control_action` with `mode="simulation"`. Verify its result and observed state before another action.

Atomic tools such as `cw_set_joint`, `cw_motion_pose`, `cw_navigation_goto`, and `cw_navigation_stop` remain useful for supported direct/diagnostic flows. Inspect their schemas and preview/execute behavior. Prefer the plan/dispatch path for general agent control.

For a bounded learned-policy run, preserve the requested positive integer
`max_steps` and inference `device` (`cpu` or `gpu`) in the controller-policy
route inputs; a shorter saved step limit still applies. These are per-run
options, not changes to the saved policy. The control agent uses the same
controller lifecycle as the normal controller surface. Its action status reads
the actual session, and cancellation targets that session only. `cancelling`
means shutdown is still in progress; a terminal execution is not proof that the
robotic task succeeded. Inspect deployment acceptance and Replay separately.

When sending joint position targets, omit an effort channel you do not intend to
command. `effort: 0` is an explicit zero-torque request, not a placeholder; on a
motor it can override the position servo. Saved keyboard inputs follow the same
optional-channel contract as the SDK. Check measured motion after dispatch,
including after switching from an effort policy to manual position control:
command delivery alone does not prove that the previous channel was released.

External learned/code policies do not accept the separate velocity adapter's
`velocity_command`, flat velocity/gait/origin fields, or `duration_ms`. Planning
marks those unsupported and execution rejects them before dispatch instead of
silently ignoring them. Run saved defaults with `max_steps`, or use a policy's
declared, validated `inference_command` surface for a task-command change. Never
infer velocity support from the robot's form factor or the policy's name.

For a verified low-level SDK integration, `mqtt.update_joints_state(..., as_targets=True)` accepts `joint_positions={}` when a non-empty `velocities` or `efforts` map is supplied. Do not invent position targets to send torque or velocity, and do not label commands as measured state. Zero-valued targets still command that channel. This does not establish the robot/driver's support: inspect its declared actuator interface and limits first. The compiled policy adapter separates scalar position servos from stateless unit-gain/unit-gear joint motors on MQTT; motor outputs use efforts, never angles. Mixed position/effort models retain separate channels, and startup pose seeding never initializes motor torque. Velocity, geared/dynamic/multi-actuator, and flight thrust/moment interfaces still need their own validated conversion; do not relabel or drop their outputs. The controller's Zenoh joint-position channel rejects velocity/effort channels rather than silently dropping them. An evaluated artifact or accepted command layout alone does not prove plant compatibility or authorize physical deployment.

For code/random controllers with a staged model, the shared `sim.data` view now
mirrors explicitly bound free-body pose and twist as well as scalar joints,
before FK and before class-controller construction. Missing/invalid root data or
unmapped free/ball joints fail; do not replace them with the model's starting
pose. The staged loader uses the transport's entity-prefix mapping. This fixes
state reconstruction, not flight commands or hardware readiness; verify freshness,
latency and stop behavior separately. No-model/lite controllers still cannot
claim floating-base observations.

Control level is an output-interface constraint, not a robot category. A policy
may output body velocities to an onboard/selected controller without access to
its internal actuators. Do not confuse that output with the policy's external
task input (e.g. a requested walking speed). The shared remote adapter now has an
explicit, simulation-only body-velocity port using the existing MQTT command
contracts, workload/session ownership and expiry. The normal RL controller now
selects a frozen aerial output only after checking the matching action term,
target twin and observed plant lower-controller identity. This is not a claim
that every drone/quadruped policy supports velocity output. Inspect the frozen
task, selected runtime and driver command catalog; never infer physical actuator
access from a URDF or silently convert joint outputs into velocity commands.
The policy's trained actuator must also match the selected runner. A learned
actuator such as ANYmal's ActuatorNetLSTM cannot be replaced by PD gains. Retain
the selected policy as incomplete setup until its actuator adapter is supported;
do not enable its runtime target to bypass the reported incompatibility.
See the [policy training reference](policy-training.md) for startup evidence,
root-state freshness and acceptance gates. A local drone's position-goal task
has verified evaluation Replay and an automatically reported normal simulation
deployment; this does not establish heading-stable hover or physical readiness.

## Live execution gate

Before dispatching with `mode="live"`, all of these must be true:

1. The current user request explicitly says live, real, or physical execution—not merely planning or code generation.
2. One physical target twin is resolved by stable identifier.
3. The action is bounded: one pose, one joint delta/target, one navigation destination, or one stop.
4. Compatible control capabilities and a ready control route are present.
5. Edge/driver health and relevant telemetry are sufficiently current for the action.
6. The user has not asked to bypass limits or safety systems.
7. A stop/recovery path is available.

Then show the resolved target, mode, and bounded action and use the client's confirmation/approval flow. Pass exactly one planned action to `cw_dispatch_control_action` with `plan_id` from the planning response and the confirmation field required by the live tool schema. The Python SDK equivalent is `client.agents.control.dispatch(environment_uuid, action, mode="live", confirmed=True, plan_id=plan_id)`. Keep the action unchanged; request a new plan if it expires or has already been consumed.

If any condition is false, do not dispatch. Offer simulation, planning, a stop, or the specific missing setup step.

For an assigned learned controller on a shared remote lab, reserve the hardware
with `cw_manage_remote_lab` first and require an `active` session for the exact
environment. `cw_deploy_rl_policy(operation="start_controller")` is a continuous
controller lifecycle operation, not a single planned action: preview it, bound
it with `max_steps`, and apply with `mode="live"`, `confirm_live=true`, and the
exact twin and controller UUIDs. Stop it explicitly before unrelated work.
Ending or expiring the lab reservation force-stops environment controllers and
restores the controller assignments captured at activation; verify the stop/end
result rather than assuming ACL revocation stopped motion.

## Stop and uncertain state

A stop request has priority over new motion. Resolve the target as quickly as safely possible and use the planned/direct stop route supported by the tool set. Do not wait for nonessential monitoring.

In the MuJoCo joint-control path, clearing an active controller latches the measured joint pose for the simulator's hold controller. It does not request a return to the startup/home pose. This is simulation behavior, not a claim about a physical driver's stop mode; inspect live stop capabilities separately. Returning home is a separate bounded motion request.

If dispatch times out or returns an uncertain result:

- do not retry the motion automatically,
- inspect current state/telemetry,
- use a stop if it is safe and supported,
- report the uncertainty and request operator direction.

## Control setup and catalog defaults

Use `cw_get_control_setup` with an explicit `target_kind` (`asset` or `twin`)
and UUID. Its overview returns the same capability choices, saved mappings and
setup findings as the UI. Read again with the chosen `action_key` to get its
configuration, selectable inputs/policies and review revision. Use
`cw_save_control_setup` to save the edited configuration with that
`expected_revision`; preserve its version and unrelated fields. A stale save
requires a fresh read and review. Do not substitute raw metadata writes.

Standard `input_layout` suggestions can be reused across actions. They become
local mappings only when deliberately selected and saved; an explicitly empty
mapping stays empty. A saved velocity-input policy may supply the standard
keyboard/gamepad layout even without a hardware command catalog. Its returned
`input_setup.source` identifies the policy and simulation scope. This does not
enable hardware access or fix an incompatible output/actuator adapter.

When a finding has `resolution=runtime_adapter_required`, explain its short
summary and offer another compatible policy or implementation of the required
runtime adapter. This is not an automatic parameter repair: retain the technical
`message` for inspection and never replace a trained actuator with guessed gains.
These tools save configuration only; starting an input, runtime or motion still
uses its existing execution path and permissions.

On deployments with the Workbench Control setup assistant, start from the selected
twin's available actions. Input presets explain how an operator invokes an action;
the executable controller/policy and its robot connection are separate concerns.
An unavailable controller in a filtered catalog is not permission to replace the
twin's saved assignment. Check access and the existing reference first.

The read-only `POST /api/v1/agents/assets/{uuid}/control/setup/plan` accepts an
optional `prompt`. An empty prompt uses existing catalog recommendations; a
natural-language prompt uses the platform's existing model and credit routing.
Suggestions can fill an empty default route with an existing readable controller.
They do not prove hardware/model compatibility or supply an IK implementation.
The UI reviews each suggestion before applying it through the existing asset
control-profile route API with `expected_revision`. A 409 requires refreshed
evidence and a new review. Twin edit rights do not grant asset edit rights.

In **action setup**, the same form in Catalog
and Workbench can retain several saved input presets and a policy for one action.
These drafts do not replace current controls, start a robot or activate a policy.
Workbench offers an optional **Test** link for external scripted/RL policies that
support a step limit. Opening it automatically checks the saved policy revision;
changing the limit invalidates and repeats that check. **Start test** remains an explicit action. Saving never
starts it. This uses the policy's saved parameters and leaves manual inputs and
default assignments in place. It does not connect keyboard commands to a policy
or activate all saved bindings. Missing command/robot adapters remain blocking.
If the saved action, policy or model changes after review, review it again; retain
the returned plan ID when dispatching. Existing native velocity, navigation and
VLA runtime controls retain their own required inputs.

A preset remains shared: reviewing/editing it opens the existing controller
catalog, and concrete leader-arm pairing still needs a twin. Do not change a
working twin's primary input merely to complete draft pairing. Draft revisions
are reviewable; a stale save needs a fresh review, never an automatic retry.
Unknown versions require a compatible editor. There is no draft-activation MCP
tool; check deployment support and keep existing runtime configuration explicit.

If the action exposes `input_setup.kind=keyboard_joint`, **Map keys** reuses the
existing driver keyboard form inside the action. It binds selected keyboard
presets to declared independent joint positions. Apply changes the local form;
Save persists a version 2 action draft. It does not edit the shared preset or
activate controls. Policy changes retain the mappings. Do not use this shape for
locomotion command ports, gamepad axes, leader pairing or Cartesian output.
A v2 head rejects older v1 writes even with a fresh review token. Historical
restoration must explicitly acknowledge removing maps and preserve the v2
write-version floor; never silently retry as v1 or rewrite the original snapshot.
Robot-owned coupling is derived and checked centrally, not supplied by the LLM.

If `input_setup.kind=keyboard_commands`, use its scoped `mqtt_schema` and the same
keyboard form for the action's declared commands and parameters. Save as v3 with
`input_mappings[controller_uuid] = {kind: "keyboard_commands", bindings: [...]}`.
One input template UUID can be reused across Drive, Camera direction and Lighting;
local mappings belong to each action, not new controller records. Templates are
discovered through catalog ACL and may show a purpose-specific `input_label`.
Use the returned template compatibility review before selecting a reference. A fresh revision token does not bypass an unsupported template version or intent profile. Keep existing maps inspectable; remove an incompatible reference deliberately instead of creating a replacement clone. Gamepad/leader template eligibility alone does not prove runtime support.
Unknown/opaque legacy command fields need explicit review, not lossy conversion.
V3 saves check command contracts and key conflicts across explicit saved action
sections. They do not activate inputs or resolve legacy fallback keys, workflow
shortcuts, device ownership or release behavior. Old editors cannot downgrade v3
configuration. Preserve the returned write-version floor when restoring history.

When the deployment exposes a policy `connection` on action-draft options, use
that shared backend review rather than rebuilding compatibility rules in the
agent. `needs_runtime_validation` is not permission or proof of readiness.
ONNX output indices and a VLA processor's joint order are different declarations;
native navigation/motion services need no invented learned-joint adapter. Review
the selected action contract, exact model processors, units, observations and
runtime support. A model edit or access change invalidates the reviewed save
token. Older drafts missing model fingerprints remain readable but need a new
review; do not retry stale writes or rewrite legacy metadata automatically.

Prefer the shared dashboard review when no corresponding MCP tool is exposed;
do not invent a setup MCP command. Check deployment support before using the
endpoint. Older deployments still use manual profile configuration. A Cartesian
pose requires actual kinematics, frames, IK/planning and collision configuration;
renaming coordinates to joints is invalid. Never mark a runtime ready based only
on a saved recommendation.

**Add action with assistant** prepares an editable contextual draft. It neither
sends the request nor starts motion or training. Existing teaching proposals and
their confirmation/adoption steps remain the training path. Related workflows
show explicit twin references; dynamically chosen targets may not be listed.

For device setup, inspect the driver's declared operations and the connected
twin's setup/Alerts. Joint geometry does not imply a live joint command port,
and having actuators does not imply a `recalibrate` command. SO-101 follower/
leader calibration, DJI compass calibration and a policy's robot adapter are
different operations. Keep device-specific calibration on the device/twin;
reusable input mappings and adapter recipes do not certify that calibration.
Older SO-101 catalogs may omit the command declaration: retain the existing
guided setup path, without extending that exception to other robot families.

## Teaching or evaluating a skill

Read [Policy training and evidence](policy-training.md) for capability gaps, reuse versus retraining, confirmation, asynchronous attempts, controller binding, catalog publication and Replay/deployment acceptance. A request to move is not permission to train, bind, publish or actuate hardware.

## Continuous control

Do not translate a single request into an unbounded motion loop, autonomous live policy, or indefinite teleoperation session. Continuous live operation requires explicit scope, duration/termination conditions, operator controls, and a purpose-built controller/workflow.

## Completion evidence

Report target twin name/UUID, mode, planned action, whether dispatch occurred, dispatch/request ID, returned/observed state, and stop/recovery status when relevant.

For waypoint arrival, report the remaining distance when measured, including
whether it comes from localization or simulation ground truth. A runtime's
completed status does not imply zero error. Use the user's accepted tolerance;
do not keep tuning for extra precision after it is sufficient for the task.
The shared Nav2 bridge rejects dispatch or completion when its localized
`map -> base` transform is missing or stale. Restore the selected SLAM/localizer
and its sensor stream before retrying. A simulation ground-truth pose or a
visible map alone does not clear this error; do not loosen the freshness limit
to hide a stopped localizer.
If localization and ground truth disagree, check that only one runtime owns
`map -> odom`. Stop mapping can keep RTAB-Map running in localization mode;
a cleared capture session does not mean it has released the transform to AMCL.
The saved-map loader checks the configured `mapping_localizer_node` in the
robot's ROS namespace before taking ownership. Do not restart another localizer
or discard the map merely to clear a status warning.
Distinguish the robot's stopping pose from the object being inspected. Supply
an explicit body/camera heading when the inspection needs it; an automatically
inferred transit direction is not evidence of a valid inspection view. Capture
still depends on the required orientation and settling checks. Report a failure
to settle or align rather than repeatedly requesting the same correction.

### Legacy locomotion mapping compatibility

Runtime locomotion keys come from the selected input preset's `keyboard_bindings`.
The shared resolver supplies W/S/A/D only for empty or old joint-only presets;
explicit command maps are authoritative. A selected preset's declared control
mode overrides stale twin mode metadata. Asset animation-preview key bindings
are a separate scope; do not silently convert them into runtime commands.
The existing mapping dialog can show these movement keys without issuing robot
commands. Joint action draft mappings remain draft-only; do not imply activation.
Check the policy's trained command envelope: the runtime may clamp generic
speed requests. Preserve the runner's limits and report them; do not infer a
hardware-safe range from a label or a successful scene preview.
When evaluating an inspection policy, include restarting after an idle period
and stopping at a station. Continuous walking alone does not validate that cycle.

### Editing existing command keys

When a controller response has `command_key_revision`, Catalog and Workbench
can reuse **Edit keys** for its explicit keyboard commands. Save through
`PUT /api/v1/controller-policies/{uuid}/command-keys` with `expected_revision`
and the complete ordered `keys` list. The backend keeps every command's saved
arguments, runtime metadata and assignments. A 409 needs a refreshed mapping
and review; do not replace the whole metadata or reassign the twin to retry.
The preset is shared, not a per-action override. Missing revision support means
use the existing read-only/legacy path; do not infer a migration for leader,
joint, model or asset-override configurations. No new MCP tool is introduced.

### VLA preview mapping failures

Playground predictions are not executable robot targets merely because their width matches the robot DOF. Updated OpenVLA/SmolVLA preview workers retain native output columns. A backend `derived.reason_code` of `joint_mapping_required` means the output-to-joint mapping needs configuration; `invalid_action_chunk` means the output matrix is malformed or non-finite. Keep the raw prediction for diagnosis, but do not replay it, pad/truncate it, rename Cartesian features to joints, or retry identical input as a configuration repair. Exact-width legacy positional previews remain supported; this does not prove units, trained embodiment, frame, normalization or action semantics. Existing completed results and older workers have not been migrated. Use the model's trained processor contract and the robot's declared interface when proposing a repair, with the appropriate model/asset/twin ACL and revision checks.

New preview workloads retain a versioned output interpretation. An `output_semantics_invalid` finding requires correcting the model declaration or using a supported snapshot version, not replaying raw values or retrying the same result. Explicit pose/joint and absolute/delta declarations override legacy family defaults; fine-tuning alone does not imply joint output. Existing jobs without a snapshot keep their legacy lookup. A preview snapshot is not an immutable live execution manifest or an approved model/robot adapter.

### Operator presentation

`operator_ui.visible` is a presentation setting on an asset/twin action binding, not permission or runtime availability. A presentation-only update uses the existing `PUT /api/v1/{assets|twins}/{uuid}/control-profile/actions/{action_key}` with `expected_revision` and `operator_ui: {visible: false|true}`. Provide this or `configuration`, never both. It retains policy/model review fingerprints and input mappings. Older full configuration writes that omit the field preserve it. New twins copy the asset setting once; later catalog edits do not change the twin snapshot.

Hidden typed route panels remain discoverable in Control setup; saved pins retain their references. Agent/SDK/workflow route resolution and ACL checks are unchanged. Do not infer that a hidden panel makes an action unavailable, disables keyboard presets, revokes control access, or stops an execution.


### Twin-local keyboard mappings

`PUT /api/v1/twins/{uuid}/keyboard-bindings` edits the assigned keyboard's keys without creating a preset or changing the assignment. Supply `policy_uuid`, its reviewed `expected_policy_updated_at` (pass the API string unchanged, including microseconds), the reviewed `expected_bindings`, and replacement `keyboard_bindings`. Requires twin write and preset read access. A 409 means the assignment, preset or effective keys changed; reload and review rather than replaying an old edit. For joint maps, `[]` explicitly clears the map; unknown joints, duplicate keys, injected command fields and incorrect mimic couplings are rejected. A preset with `command_key_revision` also supports twin-local command re-keying: retain the complete ordered binding list and every field except `key`, including command values and release behavior. Missing, added or changed commands fail. Driver-declared command surfaces are supported without a legacy control mode. Mixed inputs retain their existing editor. Preserve control mode and driver capabilities. Saving keys does not dispatch motion or activate saved action drafts. Use the environment-owned twin's settings; do not rewrite a shared preset to customize one robot.


### Composed keyboard inputs

The control input review with `include_services=true` also lists the configured
services for each action, including built-in navigation, IK and mapping. Use the
returned provider and setup issues rather than inferring them from robot names.
A provider's `selected` field describes its configuration, not runtime readiness.
An unavailable custom policy/workflow remains a repairable selection; do not
silently replace it with a default service. Reading this overview creates no
service instance and grants no control access.

Overview keeps older mappings under **Previous input setup** when saved inputs
overlap. **Assigned input setup** stays expanded while the twin still uses its
previous assignment. Neither label means the device or robot is connected.
**Keyboard selected** describes an explicit browser selection; Monitor remains
read-only. Expanding a previous map does not migrate or activate it.

Where supported, `POST /api/v1/twins/{uuid}/control-profile/inputs/prepare` requires
`expected_revision` from the input composition review and `mode` (`live` or
`simulate`). Optional device selection and handoff fields are described below. It returns a browser input snapshot after writer/environment access,
version, mapping, conflict and selected policy-route checks. It does not assign a
controller, start a worker or dispatch a command; it is not a control grant or an
exclusive lease. Workbench's **Use saved mappings** selects it explicitly for one
twin in this browser, keeping executable policy assignment separate. The existing
keyboard runtime and transport handle operator keys. Mode changes pause it;
restoring previous setup is explicit. Older clients retain their saved presets.
Do not equate `configuration_ready` with physical readiness or successful execution.
When provided, `keyboard_selection_ready` and each input's `selection_ready`
describe eligibility for the selected device, while `configuration_ready` still
describes the whole setup. A changed gamepad may need review while the keyboard
remains usable. Use the backend result; do not infer eligibility by filtering
warning text. Shared robot findings, unknown references and keyboard key conflicts
remain blocking. Older services omit these fields and retain whole-setup gating.
The prepare endpoint still validates the reviewed revision and runtime route;
selection creates no new controller or asset/twin configuration document.
The driver-based browser input releases holds on focus loss; keyboard repeat does
not resume motion after pause or command reconnection. Release the held key and
press again. Device templates alone do not imply a compatible input runtime is installed. A saved leader
assignment permits keyboard/gamepad preparation only for a client implementing
leader handoff version 1. Send `leader_handoff_version: 1` only when composition
advertises `supports_leader_handoff`; otherwise retain the old-client path.
Never claim that version on behalf of a client that cannot release its leader.
Preparation sends no commands and retains the assignment. The Workbench pauses and releases its
leader serial port when selecting a different input or changing mode/access.
Restoring the leader requires an explicit Connect; late serial reads cannot resume
publication. These browser lifecycle checks are not a cross-client actuator lease.
Do not infer that all saved input types support action composition: leader
references still use the existing assigned-input mapping/calibration path.


### Asset leader defaults

Reuse a readable declared leader template instead of cloning a controller per
robot. Read `/api/v1/assets/{uuid}/control-profile`, then PATCH its
`/{option_id}/settings` route with the profile's `expected_revision`, the selected
policy's `expected_policy_updated_at`, and `leader_arm_bindings` or
`custom_leader_arm_bindings`. Preserve the returned reference (including slug
paths). Asset write access is required; shared preset write access is not.
This saves robot joint mappings on the asset. Selecting the input as the existing
manual default lets newly created twins inherit it; existing twin overrides stay
unchanged. Do not write mappings into shared policy metadata or certify physical
calibration from asset defaults. Overview and the joint action show the saved
pairs; Edit mapping opens the same scoped editor. Action-template eligibility
alone still does not activate multi-input leader composition.


### Twin-local leader settings

For an assigned `leader_arm` or `custom_leader_arm` input, GET
`/api/v1/twins/{uuid}/control-profile/input-settings` before editing. PUT the same
path with `expected_revision` and a `settings` patch containing only that input's
mapping/calibration fields. The response returns `twin` and `review` together;
use the returned revision for subsequent edits. Never fetch a new revision just
to overwrite someone else's change. On 409, reload and review. Requires twin write
and preset read access; a read-only reusable preset is valid. Joint names must
appear in `available_joints`; sensor measurements alone do not grant joint commands.
`[]` clears a mapping without returning to template keys. Do not use generic twin
metadata or shared controller metadata updates for these managed settings.
The existing editors and serial runtime use this path for calibration, zero poses
and complete setups too. Saving does not connect hardware or publish movement.
`review.settings_version=1` identifies an authoritative twin-local snapshot:
missing optional calibration fields remain absent and must not be repopulated
from an old browser cache. A null or omitted value preserves legacy handling.
Calibration belongs to the assigned input on this twin; switching input or twin
must release the old device and its volatile zero pose. Monitor remains read-only.


### Typed gamepad composition (v4-capable services)

Reuse the standard gamepad catalog reference; Drive, Camera and Lighting have
separate action-local maps. Use the action's scoped command schema and shared
argument validator. `gamepad_commands` bindings use `trigger` (button/index or
axis/index/direction) plus `command`, `actuation`, and `args`. Do not put keyboard
keys in gamepad maps or create robot-specific controller records. Axis inputs need
continuous commands; optional `axis_argument` is a declared numeric parameter with
reviewed zero/full-scale limits. Enable button/dead zone must agree across sections.

Save v4 with optimistic revision checks. Retain unknown/legacy settings and do not
downgrade v4 to earlier schemas. The input prepare endpoint can select an explicit
`input_uuid` and freeze a version-2 gamepad snapshot for one browser session. It does
not activate a robot, provision a worker, replace a policy or grant a device lease.
Omitting the reference retains the keyboard path. Device selection and a neutral,
fresh enable gesture remain necessary; no automatic resume after loss of focus or
connection. Physical acceptance, scoped resource release and multi-action leader
composition remain separate gates.


### Gamepad joint targets

When the action response advertises `supports_gamepad_joints`, reuse **Standard
gamepad** for declared joint-position control. Save a v6 action mapping with
`kind: gamepad_joint`, `joint_mode: position`, and button/axis triggers paired
with `jointName` and `direction`. Reuse the target's independent joints and
robot-owned mimic coupling. Never translate Cartesian coordinates into joint
names, add keyboard keys to this mapping, or downgrade an existing v6 action.

The same input can also have command maps on other actions. Shared settings and
trigger conflicts apply across all its sections. To prepare a joint-capable input,
send `gamepad_joint_version: 1` only when advertised; the returned v3 snapshot
uses `gamepad_inputs` for its composed joint/command rows. Older clients must
refuse that snapshot. Saving does not select a device or command motion. The
browser retains enable/dead-zone, focus/release, joint limits and feedback checks.

### Shared gamepad settings

Read `/api/v1/{assets|twins}/{uuid}/control-profile/inputs` and require
`supports_shared_input_settings` before PUT to that same endpoint. Supply its
`expected_revision`, the saved gamepad's `input_uuid` and complete
`settings: {enable_button, dead_zone}`. This updates every saved action map for
that input atomically; do not rewrite each action or the shared preset in turn.
Conflicts, unsupported maps and stale tokens require review. The save preserves
existing dependency warnings and does not update an input already in use.
When adding another action, reuse its option's `shared_gamepad_settings.settings`;
an `issue` requires shared-settings review rather than guessing defaults.
This endpoint is distinct from the assigned leader's `input-settings` endpoint.

### Input compatibility when robot setup changes

Simulation success does not establish Live readiness. Respect the control
surface's declared runtime restriction: `structural.joint_target_modes` allows
`["simulation", "live"]`, `["simulation"]`, `["live"]`, or `[]` (unsupported).
This declaration constrains direct joints, joint-based end-effector targets and
saved motions. Simulation-only controls remain visible but disabled in Live;
fully unsupported actions are hidden from operational controllers and pickers.
Their declaration remains in the asset Capabilities page. A twin cannot widen
its asset's allowed modes.

Absent/null modes preserve legacy `supports_joint_targets: false` as unsupported;
otherwise a rejecting driver indicates missing Live implementation, not hardware
incapability. Simulation remains allowed when its own prerequisites are met.
Required setup and disconnection disable affected controls with explanations.
Do not change capability declarations, remap, pin, or switch modes to bypass an
execution restriction.

Executable pose and motion requests, including direct twin actions and workflow
plans, use the same joint validation. Complete poses may include coupled fingers
only when their values match the same step's driver targets; dispatch normalizes
them to independent commands. Do not send a follower-only command or bypass a
missing actuation declaration. Correct the catalog/twin setup or the motion.

Use the capability's command availability and the input compatibility response
before selecting a standard keyboard or gamepad. `command_interface_missing`
means the action has no declared command interface; creating another controller
or remapping keys cannot repair it. Review the robot's supported driver commands.
Saved maps remain available for inspection and explicit removal. Preserve them and
the source preset on read; do not label every custom input deprecated or claim
that a visible saved key certifies a runnable command.

Starting a new VLA inference workload requires an authenticated caller, even when the model is public. A sign-in error is an access issue; do not retry it as an adapter or robot-configuration repair. Public vision-model playground behavior is unchanged.


Navigation runtime ownership: robot-specific navigation profiles and configuration
files are shipped by the driver bundle; shared Nav2/SLAM services execute them.
Do not reinstate a Go2-only navigation or inspection executor. Map generation is
a perception lifecycle, while AMCL uses a saved map for localization. A stopped
capture can leave RTAB-Map localizing; inspect the current owner before starting
another localizer. An unobserved goal is not evidence of an unreachable goal:
prefer an observed intermediate point and reassess, without treating unknown
space as free or declaring arrival from a stale/cached pose.


Calibrated navigation command floors are opt-in policy settings. A nonempty
`navigation_command_minimums` must declare a positive
`navigation_minimum_activation`; do not supply zero to force motion. The
simulator scales planar commands without changing their bearing, and requested
speed and trained command bounds remain authoritative. This does not certify a
policy's tracking accuracy or replace Nav2 obstacle avoidance.

Navigation messages stamped `nav_frame_coords` carry ROS map coordinates. Do not
interpret them as environment-world points. The simple simulator can retain a
backend-supplied relative-motion fallback in its declared frame; surveyed map
paths without that fallback are rejected with a navigation failure. Use the
configured navigation runtime and validate its frame/localization alignment;
do not remove the frame flag to bypass the check.

### Named robot skills

Skills are configured inside Asset Control and twin Workbench / Control, alongside existing capability tabs. Read the target's control profile and saved action draft before choosing an implementation. A declared skill has a versioned ID (`skill-…`), label and `input_contract`; a compatible policy advertises that descriptor in `metadata.skill` and the same `metadata.execution_contract`. Reuse existing action draft GET/PUT, revision checks and inheritance. A declaration alone is not runtime readiness.

Review a saved skill with the existing Control Agent `controller-policy` route and `saved_action: {action_key, revision}`. Preserve the returned plan ID when dispatching. Do not replace the robot's primary controller merely to run a named skill. Workflow lifecycle nodes can use `action_key` to select the same saved implementation. Keep unsupported robot/runtime adapters unavailable; the current robotics harness's real physics validation is Kinova/MuJoCo only.

Use `cw_get_control_setup` or `cw_list_control_surfaces` to discover configured
skills and their saved references, then pass that reference to
`cw_resolve_control_route` with `route_id="controller-policy"`, target, mode and
simulation backend. Only a ready plan can be dispatched. A skill label or catalog
entry alone does not establish robot/runtime readiness.

An optional keyboard `input_trigger` belongs to the saved action configuration,
not the controller implementation. It uses the same revision/admission checks and
run lifecycle. Do not create a separate controller just to add an input shortcut.
Browser shortcuts act only on the selected twin in Control mode. Selecting another
robot changes the shortcut target; holding a key does not repeat a skill.
