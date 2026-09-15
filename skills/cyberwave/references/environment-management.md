# Environment management

Read this for environment creation, scene building, catalog twins, primitives, areas, waypoints, transforms, property edits, layout validation, and object deletion.

## Establish context

1. Use `cw_get_environment_context` if an environment is already selected.
2. Otherwise resolve workspace/project/environment through the registration/context workflow.
3. Create a missing environment with `cw_create_environment(execute=false)` first, show the resolved workspace/project and proposed name, then execute when the user's request authorizes creation.
4. Refresh `cw_get_environment_context` and retain the created environment UUID.

Do not create a second environment merely because its name differs slightly. List and resolve first.

### Conversation continuity is not control authority

The environment's Edit and Monitor views share visible assistant history in the
current page session, including the workflow editor. Context labels identify
where a request originated; a delayed reply still belongs to that context.
Changing view does not move a running job, approve an old proposal, or authorize
physical control. Monitor remains read-only, including retained training cards.
Switching from an editing turn to Monitor requests a cooperative assistant stop;
an action already executing may finish. Robot/controller and training-job stops
are separate explicit operations. Recheck target and runtime before continuing
an action after a handover. Do not claim independent browser tabs or page reloads
restore this in-memory conversation.

## Plan the scene

Translate the request into a short object inventory with stable semantic names/IDs, types, approximate sizes, and explicit positions. In Cyberwave's Z-up frame, positions are `[x, y, z]`; Euler rotations are `[roll, pitch, yaw]` in radians unless the tool schema says otherwise.

Use the right kind:

- catalog twin: robot, sensor, or reusable catalog asset
- procedural primitive: tangible floor, wall, platform, obstacle, box, stairs, enclosure, or support surface
- area: intangible safety/no-go, patrol, inspection, staging, target/search, or coverage zone
- waypoint: named navigation location on the navigable floor

Do not model physical walls/floors as areas. Do not put ground-robot route waypoints at table/rack height.

## Discover assets and primitives

The dashboard and environment editor share an `@` context picker. **In this
environment** selects existing instances/geometry; **Catalog** selects an asset
definition, searchable by name or full slug. Selections carry exact UUIDs and
catalog slugs, not implicit scene mutations. Creation and editing both accept
`context_refs` on the existing agent message/creation APIs; the backend resolves
catalog UUIDs and enforces object ACLs and token workspace scope. Client labels
are not authority. A catalog asset reference must be instantiated and resolved
to a real twin before robot-specific training or control.

If a prompt combines scene setup with behavior, inspect/reuse a compatible policy
after setup or prepare a simulation-only skill-teaching proposal. Explain missing
task source/adapters; never treat scene completion as skill completion. Training
approval, controller binding, motion, and catalog publication remain separate.
Continue with [Policy training and evidence](policy-training.md) for that part
of the request; the same flow applies during creation and editing.

1. For common curated catalog objects, call `cw_list_primitives` first.
2. Use `cw_search_catalog` for broader or multi-object lookup; batch queries when the schema supports it.
3. Treat results as candidates, not scene edits. Select the exact returned catalog/procedural identifier.
4. Prefer a catalog result with matching capabilities and a maintained setup guide. Do not substitute a vaguely similar robot without telling the user.

## Create and edit

Prefer `cw_edit_environment` for normal multi-object or intent-level scene edits. Copy current `scene_edit_operation_hint` values from catalog search results, give every non-ground object and waypoint an explicit position, and create support surfaces before operations that snap to them.

Use atomic tools when the task is narrow or the intent-level tool is unavailable:

- `cw_add_twin_to_environment`
- `cw_create_procedural_primitive`
- `cw_create_area`
- `cw_create_waypoint`
- `cw_transform_environment_object`
- `cw_update_environment_entity_properties`
- `cw_resize_area`
- `cw_set_area_image`

For catalog twins, use the `registry_id` returned by current MCP catalog search because that MCP contract explicitly accepts it. Give the twin an explicit position during creation when possible.

Use `snap`/`snap_target` against exact existing IDs for floors, tables, racks, or walls. Use overlap avoidance/clearance options where available instead of estimating repeated nudges.

### Procedural walls and stairs

Read the current returned template schema and examples; use parameters rather than scaling a compiled bounding box. Dimensions are meters in local XY, with Z up. A parameter-only edit retains the existing ground anchor; an explicit transform is still a move.

- `cyberwave/staircase` (`stairs` alias) is a solid, static flight ascending local +X. Parameters are `step_count` (1–63), `step_height`, `step_depth`, `width`, and optional `landing_depth` (0 omits it). It is not the existing `cyberwave/ladder`. The same bounded box list drives visuals and MuJoCo collision; adding stairs does not mean a locomotion policy can climb them.
- `cyberwave/wall_loop` keeps its rectangular wall-centerline `width`/`depth` convention. Outer dimensions add one `thickness`; clear interior dimensions subtract it. Corners meet flush. `open_side` and `door_side` accept `none`, `front` (−Y), `back` (+Y), `left` (−X), or `right` (+X), before the primitive's rotation.
- A loop doorway is a real opening in visual and collision geometry. Configure `door_width`, `door_height`, and signed `door_offset` (local +X on front/back, +Y on left/right). Keep it below wall height and strictly between corners; it cannot be on the omitted side. The standalone legacy `door_opening` placeholder does **not** subtract a hole from another wall.
- `cyberwave/wall_path` accepts ordered local `[x, y]` `points`, `height`, `thickness`, and `closed`. Use 2–64 points (at least 3 for a loop); segments must exceed thickness and must not reverse onto themselves. `width` is a legacy thickness alias, not path length. Right-angle joins are flush; angled joins are box overlaps, not precision CAD miters. The inspector provides a metric footprint preview, point list, and **Apply footprint** action.

Use schema-provided presets as starting points, then validate the actual scene. Do not infer arbitrary window cutouts, curved walls, structural engineering certification, or robot traversal capability from these primitives.

### Groups and arrangement

Use the existing `cw_edit_environment` operation list for hierarchy and layout; do not create replacement twins or rewrite the environment's full settings. Inspect the current tool schema before using these operations:

- `group`: provide a stable `id`, a `name`, and at least two exact `targets` (`{kind, id}`). Targets may include existing groups; use `parent_id` only for an existing parent.
- `ungroup`: target the exact group to remove its container while retaining its objects.
- `translate`: provide `targets` and a relative `delta: [x, y, z]`. A group moves its descendants together, preserving their relative positions.
- `layout`: provide `targets` and a supported `command`, such as `align-top`, `distribute-horizontal`, `distribute-vertical`, `distribute-depth`, `stack-horizontal`, or `stack-vertical`.

Horizontal means X, vertical means world height Z, and depth means Y—not screen-relative directions. Distribution needs at least three targets. Stacking starts from the first target. Never target both a group and one of its descendants in the same operation. Do not move locked or parent-relative objects through a group.

Spatial feedback sizes use world X/Y/Z as well: a horizontal floor has a small Z extent. Do not swap depth and height when interpreting the returned bounds.

Read the current environment revision and supply `expected_revision` when required by the tool. On a conflict, refresh and replan; do not blindly replay a stale hierarchy. Preview before execution when supported, then re-read transforms and render a side/isometric view to verify placement, especially for hollow or irregular objects whose bounding boxes include empty space. Scene editing is not live robot control.

## Validate spatially

When missing physical/sensor/gripper data blocks simulation, use the [simulation preparation guidance](asset-and-driver-development.md#simulation-preparation). `cw_prepare_simulation_asset` works for both catalog twins and procedural objects. Queue only user-authorized preparation and show the object’s **Simulation readiness** panel; do not imply that preparation has changed a running simulation or verified real-world behavior.

After material edits:

1. Refresh `cw_get_environment_context` or `cw_list_environment_entities`.
2. Run `cw_analyze_environment_layout` for fast overlap/stacking checks.
3. Run `cw_render_environment_preview` for visual validation. Use a valid single view name from the tool schema; do not invent composite view names.
4. Correct unintended intersections, floating objects, blocked routes, or hidden important assets.

One top/isometric view can miss vertical problems. Use front/side or perspective when height and stacking matter.

## Deletion

Use `cw_delete_environment_object` only after listing/resolving the exact area, waypoint, twin, or procedural primitive. State the environment and target ID/name, obtain explicit deletion authorization, then use the host confirmation flow. Refresh context afterward.

Never use `all` or a broad name match unless the user explicitly requested that exact scope and the tool's preview shows the complete target set.

## Completion evidence

Report:

- environment name and UUID/slug,
- created/changed object names and stable identifiers,
- important transforms,
- analysis/render result,
- and any unresolved visual or capability warning.
