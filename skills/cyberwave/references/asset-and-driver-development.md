# Asset and driver development

Read this when onboarding a new catalog asset, uploading URDF/visual files, defining capabilities, or implementing a hardware driver.

## Distinguish the deliverables

- **Asset:** catalog/digital representation, files, metadata, universal schema, capabilities, visualization, and documentation.
- **Twin:** environment instance of an asset.
- **Driver:** edge service that bridges a real device's native interface to the Cyberwave twin/topic model.

A new asset does not always need a new driver, and a new driver may target an existing asset. Ask only enough to determine which deliverables are required.

## Reuse first

1. Search catalog/primitives for the exact or compatible hardware.
2. Inspect capabilities and setup documentation.
3. Check existing Cyberwave edge drivers and the detailed [driver-development reference](driver-development.md).
4. Extend an existing asset/driver when the protocol and command surface are genuinely compatible.

Do not fork a driver merely for a different display name or environment placement.

## Control setup

Keep hardware capability separate from the operator’s preferred input. In the catalog **Capabilities → Control preferences** editor, supported manual input and policy can be optional or required, with an independent preferred entry. Workbench and catalog share the form; the save target remains the asset, while twin assignments retain their existing scope. A preference never grants motion permission or proves adapter compatibility. Preserve existing control declarations during unrelated capability edits; do not downgrade unknown versions or retry a stale save without rereading the current configuration. Use the existing input/policy editors and verify the actual robot connection before execution.

## Asset onboarding

In the dashboard, use **Add asset** to choose an existing file (URDF/Xacro ZIP,
GLB/glTF, splat or scan) or generate from an image/prompt. Both paths follow
**Source → Details → Access**; review the workspace and private-by-default
visibility before submitting. The catalog defaults to one responsive row of matching personal assets above
public assets (empty personal sections are hidden), with an All assets/Yours/Public scope beside sorting. Vendor,
sensor and capability filters support multiple selections. Card identifiers
omit the `/catalog/` segment for readability; retain the full canonical slug
when resolving URLs or API targets.

Collect:

- manufacturer/model/version and stable name,
- asset type and physical dimensions/frame convention,
- URDF/package or GLB/visual source,
- joints, limits, sensors, movements/poses, and commands,
- visibility/workspace ownership and license/provenance,
- existing driver compatibility and setup guide.

For URDF through MCP:

1. Validate the ZIP locally: main URDF path, referenced meshes/textures, case-sensitive paths, units, joints/limits, and no unsafe paths.
2. Preview/resolve workspace and visibility.
3. Call `cw_create_urdf_asset_from_zip` with the exact package and main file when needed.
4. Immediately call `cw_set_asset_capabilities(execute=false)` with capabilities grounded in the asset/driver, inspect the preview, then execute.
5. Fetch/search the asset, instantiate a test twin with `cw_add_twin_to_environment`, and render/inspect it in a safe environment.

Capabilities live under `/extensions/cyberwave/capabilities`. Do not infer capabilities from appearance alone. Verify field names and semantics from the current Digital Twins documentation or schema before writing them.

For defaulted MJCF sources, verify the compiled round trip as well as schema validation: floating-base DOFs, inherited joint limits/dynamics, actuator semantics, visual/collision counts, inertia frames and solver settings. Missing names can be valid format shorthand, not missing robot knowledge. Preserve source-defined values through the shared importer rather than asking an agent to guess replacements. A source checkpoint is not compatible merely because the converted robot has matching joint names; use the frozen task/model contract and evaluation gates.

For geometry-derived inertia, the local shared importer supports
`MJCFParser().parse(source, resolve_inertia=True)` with MuJoCo installed. This
uses the compiled source mass, center of mass and inertia tensor; it does not
certify hardware measurements. Preserve declared textures through schema JSON,
the cloud asset resolver and the exported package, and check inherited mesh
scale and ellipsoid collision geometry. A model that compiles with fallback
mass or missing geometry is not a validated training import. Keep source/version
provenance and perform a bounded dynamics round-trip check before registration.

Separate simulated mechanics from accessible controls. A drone or quadruped may expose only velocity/navigation commands while its simulator has internal motors. Inspect the selected runtime's driver command catalog and the policy's output contract; do not infer physical actuator access from URDF/MJCF structure. A command-level policy needs the matched onboard/selected controller in training and evaluation, not direct motor access. Site motors are not joints: preserve their declared frames and signed gear vectors in the common schema, and require a compatible runtime adapter before execution.

## Simulation preparation

For asset creation and joint review, keep Cyberwave's right-handed **Z-up** frame:
XY is the ground plane; +Z is height. URDF joint origins are parent-link-relative;
signed joint axes are joint-frame-relative after the origin rotation. Positive
rotation follows the right-hand rule. Geometry origins are link-relative. Do not
add a Three.js Y-up conversion or infer axes from the viewing angle.

Read `cw_get_schema` and `cw_get_joint_states` before proposing joint motion.
Use exact names, types, limits and current state. `cw_set_joint` defaults to
degrees: pass `degrees=false` for radians or prismatic metres. `cw_motion_pose`
always takes radians/metres. Both accept absolute targets, not normalized policy
values. Keep control previews distinct from observed movement.

For `cw_request_asset_generation`, select a builder that implements the required
parts and motion; prose cannot change its joints. `hinged_box` is hollow with a
top lid (width X, depth Y, height Z; rear +Y hinge about -X); `hinged_enclosure` is
a solid cabinet body with a side door. Do not substitute one for the other or
rotate the whole asset to fake the requested articulation. Review closed,
intermediate and open poses using the generated schema and preview. Static
images and schema validity alone cannot establish clearance, reachability or
measured physical properties. Report unsupported structure explicitly.

For a twin or procedural object missing simulation data, resolve its exact environment and target ID. When the user authorizes preparation, use `cw_prepare_simulation_asset` with `target_kind`, `target_id`, and the required checks (`physics`, optionally `manipulation`/`camera`). This queues reviewable work; it does not apply changes, start training, execute a policy or publish an asset.

Use the same tool with `operation="inspect"` to read blockers before preparation. `operation="prepare"` is the backward-compatible default and immediately queues authorized work. Poll `operation="status", generation_uuid="..."` for progress, errors, proposed changes and validation. Preview `operation="apply", generation_uuid="..."`; after review repeat with `execute=true`. Material/inertia or agent-proposed gripper estimates also need explicit `accept_estimates=true`; applying requires stopped simulation/controllers/training. `simulator="mujoco"` is the only supported engine. Successful apply enables it only on the validated twin instance, never the shared catalog asset, and returns fresh readiness. Missing canonical geometry or other unsupported requirements remain actionable blockers, not automatic conversions.

The object's **Simulation readiness** UI remains an alternative for field-level review. Never invent joint/link identifiers, actuator limits/gains, or measured properties. A passing object smoke test is not proof of complete-environment compatibility, successful grasping, camera streaming or hardware safety. Blank/fallback images and unavailable renderers remain unresolved.

Keep preparation separate from changing shared assets or hardware capabilities. Existing calibration stays authoritative. Do not use this tool to bypass confirmation or apply an arbitrary metadata patch.

## Driver development handoff

For a driver deliverable, continue with [driver development](driver-development.md). The deterministic scaffold and template are resources of this same `cyberwave` skill; there is no separate driver skill to install or maintain.

## Completion evidence

For assets, report asset UUID/slug, files, capability status, test twin, and render/schema validation. For drivers, report repository/path, manifest summary, build/tests, development twin/edge binding, and what remains before live deployment.

## Reusable asset kits

Use a kit for an existing robot plus docked accessories instead of duplicating
catalog models. Catalog results mark kits with `is_kit`; their catalog asset UUID
and slug identify the kit. The UI supports **Catalog → Create kit**.

For authoring through the Python SDK, use `client.assets.create_kit(name,
components, workspace_uuid=..., visibility="private")`. Each component has a
unique `key`, an `asset_uuid`, optional `parent_key` and `attach_to_link`,
`position` in metres `[x,y,z]`, and quaternion `rotation` `[w,x,y,z]`.
Provide exactly one root and order parents before children; nested kits are
unsupported. Resolve real asset UUIDs and link names first.

Use `get_kit(kit_uuid)` to inspect components and `update_kit(...)` to replace the
definition; omitted description and visibility values remain unchanged. Use
`instantiate_kit(kit_uuid, environment_uuid)` to create all twins
atomically, returning the component twins. The existing twin-create API also
expands a kit UUID and returns the root twin. Check every component's access and
verify the resulting assembly; kit visibility does not grant component access.
Creating/deploying a kit does not dispatch hardware commands or purchase it.

## Imported robot simulation runtimes

A catalog may declare `metadata.simulation_runtime = {"kind": "go2_ros2"}`
(or `spot_ros2`, `mir250_ros2`). The existing `seed_asset_driver_config`
command copies the manifest's `simulation_runtime` into catalog metadata.
New twins inherit this with their other asset defaults; a twin's explicit
choice wins. `{"kind": "none"}` disables automatic ROS2 startup. Missing
metadata retains the legacy registry fallback; an invalid declaration blocks
startup with an error. Do not rename imported robots to a canonical registry
ID or infer a runtime from their display name or image filename.

This is operator/catalog configuration, not a live driver's topic advertisement.
It does not prove navigation readiness or choose an image: declared topology
still uses the existing `drivers` profiles. Review imported catalog defaults
and twin overrides before starting simulation; do not overwrite running setups.
