# Workflow authoring

Read this for workflow discovery, templates, natural-language creation/editing, node schemas, triggering, monitoring, and cancellation.

## Resolve scope and runtime

Resolve the environment first and list existing workflows with `cw_list_workflows`. Default new workflows to `mode="simulation"` unless the user explicitly requests preview or live/edge execution.

For live/edge workflows, confirm the target environment/twin and that edge requirements are satisfied before creation or triggering. The compatibility alias `edge` may map to `live`, but prefer the current tool schema's canonical value.

## Choose an authoring path

### Reuse a template

1. Search with `cw_search_workflow_templates`.
2. Inspect the selected workflow/template.
3. Preview `cw_clone_workflow_template(execute=false)` into the target environment.
4. Execute when the clone matches the request.
5. Apply simple field edits with `cw_update_workflow_fields`.

### Create from natural language

1. Write a concise prompt with trigger, data source, processing/condition, effects, runtime, target twin/environment, and success behavior.
2. If specific nodes matter, use `cw_list_node_schemas` with short ranked keywords, then `cw_get_node_schema` for exact typed parameters.
3. Pass valid `(node_type, node_subtype)` pairs as advisory `node_hints`; do not invent fields.
4. Preview with `cw_create_workflow_from_prompt(execute=false)`.
5. Inspect proposed environment setup, dropped hints, warnings, and graph.
6. Use `setup_mode="auto"` only when the user explicitly authorized proposed setup such as adding waypoints or a top-ranked catalog twin.
7. Execute to materialize a real workflow UUID, then fetch it with `cw_get_workflow`.

Preview drafts do not have a real UUID. Do not pass placeholders to field-edit tools.

If creation returns a real `workflow.uuid` with `needs_setup`, keep that workflow.
Complete missing node fields with a targeted `cw_edit_workflow_from_prompt` edit,
using the returned node identifiers and preserving the existing graph. Do not
repeat creation to resolve setup. Only retry creation after authorized environment
setup when no workflow UUID was saved. If node editing is unavailable, explain the
remaining setup instead of creating a replacement.

### Edit an existing workflow

- Use `cw_update_workflow_fields` for name, description, activation, visibility, or metadata.
- Use `cw_edit_workflow_from_prompt` for graph structure or node parameter changes.
- Resolve a real UUID first.
- Preview continuity-sensitive, structural, active, or large edits and obtain explicit approval before `execute=true`.
- Re-fetch the workflow and compare the resulting graph/fields with the requested change.

## Trigger and monitor

1. Confirm the workflow UUID, runtime, target environment/twin, and inputs. Inspect
   the Environment's `control_plane_access`: `direct_control` forbids workflow
   execution through MCP/A2A, while `workflows` and
   `direct_control_and_workflows` allow it.
2. Preview with `cw_trigger_workflow(execute=false)`.
3. Trigger only when execution was requested.
4. Capture the returned run UUID.
5. Monitor with `cw_get_workflow_run` or bounded `cw_list_workflow_runs` checks until a terminal state or the user's requested observation window ends.
6. On failure, report the failing node/error and relevant inputs without secrets.

Simulation runtime failures, including startup failures, appear in the environment's Simulate view. Check that view and the recorded run error when diagnosing a simulated workflow.

Do not repeatedly trigger a workflow because status is slow or unknown. Verify the existing run first.

Workflow authors can disable same-workflow concurrency (the default) and name
same-environment workflows that block a new run. A trigger rejected with the
`workflow_concurrency` conflict is an intentional safety gate: report the
blocking workflow/run when the response exposes it and wait or cancel it; do not
retry around the policy. A generic incompatible-workflow conflict may refer to a
workflow the caller cannot read; do not infer or disclose its identity. Remove
incoming and outgoing incompatible-workflow references before moving a workflow
to a different environment.

Concurrency admission applies to cloud-dispatched triggers, not telemetry from
independently started edge runs. Already-started edge runs remain recorded even
when they overlap; do not interpret a visible run as proof that the concurrency
gate approved it.

The central **Process** view (below the scene in Live and Simulation) and
`cw_get_workflow_run` use the same
recorded activation progress. Report the run status and named active steps, not
an invented percentage or physical-success claim. The bounded history preserves
parallel and repeated activations; `truncated=true` means some activity is omitted.
Names reflect the current workflow definition, not a frozen historical plan.
Opening Process only reads status; it never starts, resumes, or cancels a run.
It works in Monitor mode and is hidden in Edit and Replay, leaving the right
panel available for the agent.

## Cancel

Resolve the exact active run, preview `cw_cancel_workflow_run(execute=false)`, explain the effect, then execute when authorized. Verify the terminal status afterward.

## Authoring quality

- Prefer deterministic typed nodes and explicit data flow over prose hidden in metadata.
- Define observable success and failure paths.
- Add alerts/emails only when the user requested those external effects.
- Avoid duplicate effects on retries; use appropriate event-gate/idempotency semantics when supported by the node catalog.
- Keep simulation and live workflows visibly distinguishable.

## Model input and output compatibility

For an Online Controller Lifecycle node, select the target twin and optionally a
named skill from its Control / Skills setup. Set `action_key` to the saved skill
ID (for example `skill-pick-and-place`); the backend reviews that twin's saved
implementation through the same action binding used by the Control Agent. Do not
copy a controller UUID into the node or create a workflow per robot. Without an
`action_key`, its explicit controller assignment takes precedence, then the backend resolves a
single accessible asset runtime default for the workflow's execution target.
If defaults are missing or ambiguous, complete control setup instead of copying
a controller or workflow per robot. Adding a twin does not start its controller.
An inherited policy still needs its normal runtime and scene requirements; a
simulation-only policy does not gain physical support through inheritance.

Start from catalog **Run pick and place skill** when appropriate. It reuses the
Manual trigger and Online Controller Lifecycle node; configure its target twin
and saved `action_key`, then validate the resulting run. For perception, reuse
**Analyze camera frame** or **Analyze and annotate camera frame**, configuring
their model and sensor inputs. These templates are building blocks; their presence
does not establish a working locate/manipulate/verify pipeline or live support.

Model responses may include `inference_issue`: an unavailable checkpoint or
execution adapter blocks use even if task declarations are present. Keep that
reason visible; do not remove it or call an untyped endpoint as a workaround.
Recorded playground input/result pairs explain an earlier run and do not prove
that a deployment exists now. Task planning, image grounding, visual navigation,
road driving and locomotion retain separate contracts. The node's explicit
**Configure with AI** UI reuses workflow planning and reviewed application; it
does not activate the workflow. Task examples may fill an empty prompt, but must
not overwrite a user's existing value or upstream mapping automatically.

When a model exposes a versioned port contract, preserve its units, coordinate frame, axis/joint order and image/frame/time identities when mapping it. A catalog tag or matching array shape is not proof of compatibility. Do not substitute relative depth for metric depth, image points for navigation goals, or Cartesian values for joint targets without a configured converter. Inspect missing required model inputs before binding. If a model edit reports a stale-contract conflict, reload and review it; do not remove the version or annotations to force the edit through.

Task declarations describe expected output, not verified measurements or robot readiness. Preserve every required input, including alternatives, and inspect the selected task's image requirement. An image trajectory is not a navigation route. Metric depth needs runtime confirmation as well as a metric checkpoint; missing or contradictory evidence must not be treated as metres or millimetres. Do not claim that an advertised task has a deployed endpoint or that a model has been tested merely because its declaration is present.

Keep a saved model choice when the catalog refreshes. If it is unavailable or no
longer matches the requested task, explain the missing mapping and ask for an
explicit replacement; do not silently switch to a default. Matching a declared
task only identifies a candidate. Check that the actual workflow node selects
that task and wires its observations and parsed outputs before claiming it can run.

For an explicitly selected native task, retain the task when swapping models and
review its required observations. Updated cloud workflows validate synchronous
task output before downstream steps; typed edge depth also checks its actual
metric flag. Edge HTTP tasks forward the same reviewed contract and pin the
model revision from compilation. They require a compatible SDK and backend;
republish after reviewing model changes. Typed asynchronous execution remains
unsupported. A missing typed endpoint, stale revision or invalid response must
stop the task, without retrying an untyped run or deleting the contract. Existing
untyped calls retain their previous behavior. Saving a task does not certify a
camera calibration, world-coordinate conversion or a deployed worker.

Task discovery is available through
`GET /api/v1/workflows/{uuid}/nodes/{node_uuid}/model-tasks` (optional `model_uuid`
checks a replacement; `include_catalog=true` discovers tasks and candidate model UUIDs
even before a model is selected). The catalog uses workflow execution support and
workspace/public read access. Use its task choices and exact model revision; keep the
revision of the node you actually reviewed. For an explicit task change, send
`expected_updated_at` and `expected_model_updated_at` with the normal node update.
A 409 requires a fresh read and review, never a blind retry with a newer timestamp.
Omitting the task retains it. Explicit `task_contract: null` with the reviewed node
revision removes it only when the user intends to return to the model default.
Do not remove a task to get around unsupported execution or missing observations.
The inspector uses these same contracts and existing input mapping fields.
Choose task, then a compatible model, then wire observations. A blank/standard
Call Model node inherits the canonical task label; preserve explicit user names.
For a model swap, retain the existing task's output requirements rather than
replacing them with weaker requirements from the new model. Relative depth is not
metric geometry, a point cloud is not an occupancy grid, and neither implies SLAM.

Send Depth remains a visualization step. Its encoding choice does not turn
relative estimates into measured distances. Generated publishers retain actual
metric evidence; relative/unknown frames are excluded from backend metric depth
recording and fusion while the direct viewer output remains available. Do not
remove that evidence to bypass the check. A metric checkpoint still requires
calibration, source frame/time and a transform before it can support mapping.

A map image is a rendering of an artifact, not evidence of calibrated mapping or
SLAM. Projected occupancy keeps unobserved cells unknown. Existing NumPy grids can
be viewed through the map image endpoint while their downloads retain the original
format (`data_format` when returned). Do not rewrite a legacy grid merely to view
it or treat its pixels as proof of free space. Stream start records a request;
confirm a received snapshot before reporting a map is available.

Use the robot's declared mapping service when present. Its named sensors are
inputs; the robot owns the native map session. Missing or unsupported setup must
be corrected rather than bypassed with a legacy sensor route. Legacy mapping
remains usable when no service is declared, but sensor availability alone does not
prove that a mapping runtime is deployed. A depth-model task is not itself a SLAM
provider.

## Completion evidence

Return the workflow name/UUID, environment, mode, authoring path, important node chain, preview/execute state, and run UUID/status when triggered.

Buffered edge-node timestamps can describe when a node ran; missing, skewed or
inconsistent clocks fall back to receipt time. They do not establish control
readiness. A verified navigation capture without a node-execution reference can
be attached only to an unambiguous non-repeating node. Do not infer its firing
from timestamp proximity or relabel another run's capture.


### Control service links

A declared perception task can reference a typed Call Model node using version 5
of the existing asset/twin Control action configuration (`workflow_node_uuid`).
Configure Task → Model and observations on the workflow node first. Control links
that node; it does not copy the model or observations or start a run. Asset defaults
reference workflow templates; a twin must use a workflow in its own environment.
Re-read the Control action review before saving. Do not downgrade v5 settings or
clear a task to bypass compatibility, missing inputs or access checks. Relative
depth is not metric geometry, and sensor data alone is not a configured map/SLAM
pipeline. Existing workflow activation and execution validation remain required.

Compatible public catalog templates can be selected alongside environment
workflows. Browsing a template does not save or run it. Use template in this
environment creates a private, inactive copy; inherited templates use the same path.
The copy keeps task wiring and
gets linked atomically; declared source-twin selections are cleared for explicit
configuration in the existing editor. Check other workflow nodes' missing setup
as well as the model inputs. A failed or stale request must not be retried by
creating an unrelated second workflow.

In Workbench Control, a saved workflow task can be enabled or paused through the
existing workflow lifecycle. Enable applies to the whole linked workflow and
rechecks its readiness; it does not activate catalog templates. Keep model inference
placement separate from sensor capture/workflow placement. Offer cloud only for a
real supported deployment; preserve an explicit existing edge choice. A saved task
or Enabled label alone is not evidence of live sensor data or successful inference.

Reuse the existing embodiment/environment context for authored objects, current
sensor state and perception evidence. Refer to saved map artifacts rather than
copying point arrays into agent prompts or controller settings. Authored geometry,
observed geometry and model estimates retain their source, frame and time; one
does not silently overwrite another. Read artifacts through authorized APIs.
An inferred depth map is not odometry, SLAM, free space or a validated navigation
map. Report inference, delivery, persistence and geometry accuracy separately.
