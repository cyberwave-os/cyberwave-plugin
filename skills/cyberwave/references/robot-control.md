# Robot control

Read this for navigation, motion poses, joint commands, stop commands, observation actions, controller-policy routing, and simulation/live handoff.

## Classify the request

Determine:

- target environment and twin,
- requested action and bounds,
- mode: `simulation` or `live`,
- whether the user requested a plan or execution,
- and what observation will prove success.

If mode is omitted, use `simulation`. Do not infer live mode from words like "robot", "edge", "camera", or a physical asset name.

## Resolve target and affordances

1. Use `cw_resolve_twin` or `cw_list_twins` until exactly one twin is selected.
2. Use `cw_list_control_surfaces` to inspect available movement, pose, joint, observation, controller-policy, and stop affordances.
3. Inspect twin/schema/joint state or edge/driver health when it affects safe execution.
4. If the target or affordance is ambiguous, ask the user to choose; do not guess.

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

Then show the resolved target, mode, and bounded action and use the client's confirmation/approval flow. Pass exactly one planned action to `cw_dispatch_control_action` with the confirmation field required by the live tool schema.

If any condition is false, do not dispatch. Offer simulation, planning, a stop, or the specific missing setup step.

## Stop and uncertain state

A stop request has priority over new motion. Resolve the target as quickly as safely possible and use the planned/direct stop route supported by the tool set. Do not wait for nonessential monitoring.

In the MuJoCo joint-control path, clearing an active controller latches the measured joint pose for the simulator's hold controller. It does not request a return to the startup/home pose. This is simulation behavior, not a claim about a physical driver's stop mode; inspect live stop capabilities separately. Returning home is a separate bounded motion request.

If dispatch times out or returns an uncertain result:

- do not retry the motion automatically,
- inspect current state/telemetry,
- use a stop if it is safe and supported,
- report the uncertainty and request operator direction.

## Teaching or evaluating a skill

Read [Policy training and evidence](policy-training.md) for capability gaps, reuse versus retraining, confirmation, asynchronous attempts, controller binding, catalog publication and Replay/deployment acceptance. A request to move is not permission to train, bind, publish or actuate hardware.

## Continuous control

Do not translate a single request into an unbounded motion loop, autonomous live policy, or indefinite teleoperation session. Continuous live operation requires explicit scope, duration/termination conditions, operator controls, and a purpose-built controller/workflow.

## Completion evidence

Report target twin name/UUID, mode, planned action, whether dispatch occurred, dispatch/request ID, returned/observed state, and stop/recovery status when relevant.
