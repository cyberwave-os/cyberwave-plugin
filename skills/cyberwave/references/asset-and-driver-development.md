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

## Asset onboarding

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

For a twin or procedural object missing simulation data, resolve its exact environment and target ID. When the user authorizes preparation, use `cw_prepare_simulation_asset` with `target_kind`, `target_id`, and the required checks (`physics`, optionally `manipulation`/`camera`). This queues reviewable work; it does not apply changes, start training, execute a policy or publish an asset.

Direct the user to the object's **Simulation readiness** section for progress and field-level review. Material/inertia or agent-proposed gripper estimates need explicit acceptance; applying requires stopped simulation/controllers/training. Never invent joint/link identifiers, actuator limits/gains, or measured properties. A passing model smoke test is not evidence of successful grasping, camera streaming or hardware safety. Blank/fallback images and unavailable renderers remain unresolved.

Keep preparation separate from changing shared assets or hardware capabilities. Existing calibration stays authoritative. Do not use this tool to bypass confirmation or apply an arbitrary metadata patch.

## Driver development handoff

For a driver deliverable, continue with [driver development](driver-development.md). The deterministic scaffold and template are resources of this same `cyberwave` skill; there is no separate driver skill to install or maintain.

## Completion evidence

For assets, report asset UUID/slug, files, capability status, test twin, and render/schema validation. For drivers, report repository/path, manifest summary, build/tests, development twin/edge binding, and what remains before live deployment.
