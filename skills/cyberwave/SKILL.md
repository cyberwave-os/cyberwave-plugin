---
name: cyberwave
description: Build and operate Physical AI systems on Cyberwave. Use for account onboarding, environment creation or editing, workflow authoring, teaching or evaluating robot policies, robot control in simulation or live mode, edge setup, asset or driver onboarding, telemetry, camera monitoring, or Cyberwave SDK/CLI/MCP integration.
license: Apache-2.0
metadata:
  author: "cyberwave-os"
  version: "2.0.0"
  compatibility: "Cyberwave MCP, SDK, CLI, dashboard, or network access may be needed for platform operations."
---

# Cyberwave orchestrator

Help the user reach a verified Cyberwave outcome. Use Cyberwave MCP tools when they are available; use the SDK or CLI when the user is building code or MCP does not cover the operation. Do not turn a focused request into a mandatory setup interview.

## Start here

1. Extract the requested outcome, target resources, desired runtime (`simulation` or `live`), and whether the user asked for execution or only guidance/code.
2. Read [MCP, CLI, SDK, and dashboard routing](references/mcp-and-fallbacks.md), then inspect the Cyberwave MCP tools actually available in the client. Never assume that every documented `cw_*` tool is callable or that host-local work belongs in MCP.
3. Establish only the missing context the task requires: account/authentication, workspace, project, environment, then twin. Reuse session context and supplied UUIDs/slugs instead of asking again.
4. Read the narrow workflow reference from the routing table below. Revisit the execution-plane reference when tools are missing, ambiguous, or return structured errors.
5. Resolve exact targets before mutation. Prefer preview, plan, dry-run, or `execute=false` modes when the available tool supports them.
6. Execute within the user's request and the safety rules below.
7. Verify by re-reading state or using the workflow-specific check. Report resource names and identifiers, runtime mode, material changes, and verification result. Never print secrets.

## Route the request

| Intent | Read |
| --- | --- |
| Sign up, sign in, API keys, connect MCP, resolve workspace/project/environment | [Registration and authentication](references/registration-and-auth.md) |
| Create or edit a scene/environment, catalog twin, primitive, area, waypoint, or transform | [Environment management](references/environment-management.md) |
| Create, clone, edit, trigger, cancel, or inspect a workflow | [Workflow authoring](references/workflow-authoring.md) |
| Move, navigate, stop, pose, or set joints in simulation or on a physical robot | [Robot control](references/robot-control.md) |
| Teach, train, retrain, evaluate, bind or review a learned skill, policy or Replay | [Policy training and evidence](references/policy-training.md) |
| Install/use the CLI, pair an edge host, manage services/containers, configure media, diagnose host health | [Edge configuration](references/edge-configuration.md) and [verified CLI map](references/cli-command-map.md) |
| Add a catalog asset, upload URDF, or define capabilities | [Asset and driver development](references/asset-and-driver-development.md) |
| Create or update a hardware driver, manifest, transport, container, or dev twin | [Driver development](references/driver-development.md) |
| Inspect schema, joints, telemetry, frames, streams, captures, runs, alerts, or edge state | [Robot monitoring](references/robot-monitoring.md) |
| Decide what needs MCP versus CLI/SDK/dashboard, implement code, inspect docs, or recover from missing tools | [MCP, CLI, SDK, and dashboard routing](references/mcp-and-fallbacks.md) |

Read at most the references needed for the current request. Do not preload the whole package.

## Execution policy

- Prefer intent-level MCP tools over composing raw REST, MQTT, or Zenoh calls.
- Inspect tool schemas at call time. A reference names current tools but is not proof that the current client exposes them.
- Inspect `status`, `code`, `retry_safe`, `details`, and structured result metadata. Retry only when the error says retrying is safe and the inputs or external condition have changed.
- Use official Cyberwave docs when an interface is uncertain or likely changed. Prefer `cw_search_docs` when present, then current repository docs or [docs.cyberwave.com](https://docs.cyberwave.com).
- Do not invent SDK methods, CLI commands, REST endpoints, MQTT topics, node parameters, or capability fields. Verify them first.
- Keep credentials in the client's secret store, environment, or Cyberwave CLI credentials file. Never add credentials to source control, skill files, shell examples with real values, or responses.

## Safety invariants

- Simulation is the default for robot control and workflow authoring when the user does not specify a runtime.
- Live actuation requires explicit live/physical intent in the current request, one resolved target twin, compatible control capabilities, and a bounded action. Planning alone does not authorize dispatch.
- Dispatch exactly one planned control action at a time. Verify its result before another action.
- If physical state, target identity, driver health, or route readiness is uncertain, do not move the robot. Prefer a stop action or ask for the missing fact.
- Resolve destructive targets exactly and obtain explicit authorization before deletion. Do not treat a broad build/configure request as authorization to delete.
- Do not accept legal terms, choose an organization, expose credentials, or make account/billing decisions for the user.
- Do not silently record or retain camera/video data. Bound monitoring duration, frame count, and polling.
- Client permissions, Cyberwave ACLs, and host confirmation flows remain authoritative. This skill does not grant permissions.

## Completion contract

Finish with evidence appropriate to the task:

- Environment: refreshed context plus rendered or quantitative layout feedback.
- Workflow: saved workflow UUID, inspected graph/fields, and run state if triggered.
- Robot control: target, mode, planned action, dispatch result, and observed/returned state.
- Learned skill: proposal/attempt and checkpoint identifiers, evaluation versus baseline, binding state, and measured deployment/Replay evidence. Training completion is not task success.
- Edge: installed/configured service state, resolved environment/twins, and driver/container health.
- Asset/driver: asset identifier, capabilities status, validation/build/test results, and registration status.
- Monitoring: signal source, observation window or frame count, freshness, and any uncertainty.

If an external human step blocks completion, give the shortest exact handoff, state what identifier or confirmation is needed afterward, and resume from there.
