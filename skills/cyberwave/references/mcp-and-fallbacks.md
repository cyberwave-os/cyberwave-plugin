# MCP, CLI, SDK, and dashboard routing

Read this for every Cyberwave task before choosing an execution plane. MCP is the preferred cloud control plane, but it cannot install packages, change a host service, access local devices, or author a complete driver repository.

## Capability ownership matrix

| Outcome | Preferred plane | Why / fallback |
| --- | --- | --- |
| Resolve workspace/project/environment/twin context | MCP | Typed, authenticated, and session-aware; SDK/dashboard if MCP is unavailable. |
| Create/edit/render an environment | MCP | Intent-level previews and structured mutations; SDK only for application code or a missing operation. |
| Create/edit/run/inspect workflows | MCP | Typed schemas, preview, and run state; CLI for explicit shell workflows, SDK for application integration. |
| Plan/dispatch robot control | MCP | Central capability and simulation/live route resolution. Static instructions cannot verify live control. |
| Inspect telemetry, joints, frames, runs, schemas | MCP | Use the least expensive bounded observation; SDK when embedding monitoring in an application. |
| Register/authenticate a human account or accept terms | Dashboard/user step | MCP/CLI may connect an existing key, but the user owns identity, legal, organization, and billing decisions. |
| Install the `cyberwave` CLI | Host shell | MCP cannot mutate the local Python/OS package environment. Verify the public package and current OS instructions. |
| Pair/install/uninstall Edge Core | CLI on the target host | Requires local packages, privileges, devices, Docker, and systemd/launchd. Use [edge configuration](edge-configuration.md). |
| Start/stop edge services, containers, workers, or media bridges | CLI on the target host | Host-local operational state is outside hosted MCP. Inspect status and exact targets first. |
| Create cloud assets/capabilities from supported inputs | MCP | Use typed asset tools when exposed; dashboard/SDK for unsupported upload flows. |
| Write or modify a driver repository | Local files + SDK | Use [driver development](driver-development.md) and `scripts/scaffold_driver.py`; MCP may create the test asset/twin but does not write the hardware implementation. |
| Build/test a driver image | Host shell/Docker | Requires repository and device/runtime access. MCP can verify resulting cloud telemetry later. |
| Low-level MQTT/Zenoh integration | SDK/driver code | Only when required; use declared interfaces, not ad hoc topics. |
| Search exact current behavior | `cw_search_docs`, installed package source, official docs | Tool/source verification precedes examples when interfaces can drift. |

One task can cross planes. For example: MCP creates a development environment and twin; the local scaffold creates a driver; the CLI pairs an edge host; MCP then verifies telemetry. Preserve resource identifiers across those handoffs.

## Capability discovery

Treat the client's callable tool list and tool schemas as authoritative for the current session. Tool families currently include:

- context and resolution: `cw_list_workspaces`, `cw_list_projects`, `cw_list_environments`, `cw_get_environment_context`, `cw_list_environment_entities`, `cw_resolve_twin`
- catalog and scenes: `cw_list_primitives`, `cw_search_catalog`, `cw_edit_environment`, atomic environment tools, render/layout checks
- workflows: template search/clone, prompt create/edit, node schemas, run lifecycle
- control: `cw_list_control_surfaces`, `cw_plan_control_action`, `cw_resolve_control_route`, `cw_dispatch_control_action`
- observation: twin/schema/joints, captures, frames, environment previews
- documentation: `cw_search_docs`

Inspect parameters before calling. If a named tool is absent, choose an available equivalent or fallback; do not pretend the call happened.

Deprecated interfaces must not be newly recommended:

- `cw_list_assets` -> use `cw_search_catalog`
- `cw_create_twin` -> use `cw_add_twin_to_environment`
- `cw_plan_scene` -> use `cw_edit_environment` for normal scene creation/editing

## MCP result discipline

Read both human content and structured result fields. At minimum inspect:

- `status`
- `code`
- `retry_safe`
- `details`
- action metadata such as mutation/destructive/preview support
- returned resource UUIDs and mode

Retry only when `retry_safe` is true and something relevant changed. Never turn an ambiguous-target response into a guessed target. Preserve request IDs when reporting a platform failure.

## Selection order

1. Cyberwave MCP for typed contextual platform operations.
2. Python SDK for application code or operations not exposed through MCP.
3. Cyberwave CLI for authentication plus host-local installation, pairing/bootstrap, service/container/media operations, diagnostics, and explicit CLI workflows.
4. Dashboard for registration, identity, permissions, billing, visual/manual steps, or unsupported mutations.
5. Verified REST/MQTT/Zenoh only for a lower-level integration requirement.

The presence of MCP does not mean every task should be performed through MCP. If the user asks for production application code, use MCP to inspect/setup context and write code against the verified SDK surface.

## Verify changing interfaces

For exact SDK methods, CLI commands, API schemas, MQTT topics, or workflow node fields:

1. Call `cw_search_docs` with a focused query when present.
2. In a Cyberwave checkout, inspect current source and `docs-mintlify`.
3. Otherwise use [docs.cyberwave.com](https://docs.cyberwave.com).

Do not use an old example as proof of a current interface. In particular, prefer unified slugs over deprecated `registry_id`/`catalog_seed_id` where the current API supports slugs; MCP catalog instantiation may still explicitly require a returned `registry_id`.

## SDK baseline

Use Python 3.11+ unless current package metadata says otherwise:

```bash
python -m pip install cyberwave
export CYBERWAVE_API_KEY="<secret>"
```

Inspect the installed SDK or official docs before emitting methods. Use the SDK's simulation/live routing rather than manually changing source markers. Keep application setup code separate from edge driver code.

## CLI baseline

Verify commands with `cyberwave --help` and subgroup `--help` in the installed version. Known stable entrypoints include:

```bash
cyberwave login
cyberwave configure --show
cyberwave pair --help
cyberwave edge --help
cyberwave twin --help
cyberwave workflow --help
```

Do not automate interactive login with a password argument. Let the user type secrets into the CLI prompt or use a secure token path.

## Transport boundary

- MQTT is the remote broker path for SDK, UI, and cross-LAN teleoperation. `twin/command` is MQTT-only.
- Zenoh is the edge-colocated `DataBus` path on the same host as workers. It is opt-in per publisher/listener through declared driver topic metadata.
- Dual transport is declared by the driver interface; do not invent a process-wide backend switch. `CYBERWAVE_PUBLISH_MODE=mqtt_only` disables Zenoh publishing where supported.

Verify current topic specifications before publishing raw messages. Prefer the SDK's unified driver `TopicSpec` abstraction, declaring `enable_mqtt` / `enable_zenoh` / `zenoh_channel` on the same spec.

## MCP absent

Offer the smallest viable fallback:

- setup task: dashboard or verified CLI/SDK
- coding task: SDK plus official docs
- edge bootstrap: CLI
- live state/control task: ask the user to enable Cyberwave MCP or provide an authenticated runtime; static guidance alone cannot verify a live outcome

Be explicit about what remains unexecuted and what observation will prove completion.
