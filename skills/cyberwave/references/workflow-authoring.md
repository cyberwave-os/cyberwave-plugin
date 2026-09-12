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

1. Confirm the workflow UUID, runtime, target environment/twin, and inputs.
2. Preview with `cw_trigger_workflow(execute=false)`.
3. Trigger only when execution was requested.
4. Capture the returned run UUID.
5. Monitor with `cw_get_workflow_run` or bounded `cw_list_workflow_runs` checks until a terminal state or the user's requested observation window ends.
6. On failure, report the failing node/error and relevant inputs without secrets.

Do not repeatedly trigger a workflow because status is slow or unknown. Verify the existing run first.

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

## Completion evidence

Return the workflow name/UUID, environment, mode, authoring path, important node chain, preview/execute state, and run UUID/status when triggered.
