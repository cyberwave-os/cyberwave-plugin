# Edge configuration

Read this for pairing an edge host, selecting an environment/twins, installing or updating Edge Core, configuring drivers/workers, transport setup, and edge diagnostics.

These operations are normally CLI/host work, not hosted MCP work. MCP may create or resolve the environment and twins before the handoff and verify cloud-visible state afterward. Read the [verified CLI command map](cli-command-map.md) before emitting exact commands.

## Separate the layers

1. **Control-plane registration:** Cyberwave edge record, fingerprint, workspace/environment/twin bindings.
2. **Host bootstrap:** packages, Docker, system service, configuration directory, credentials.
3. **Driver/worker deployment:** images, manifests, per-twin configuration, device access.
4. **Data plane:** MQTT remote path and optional Zenoh edge-local path.
5. **Health:** service, containers, drivers, telemetry, camera/stream readiness.

Diagnose and change one layer at a time.

## Preflight

- Confirm the command runs on the intended edge host and operating system.
- Inspect the installed CLI with `cyberwave --version`, `cyberwave pair --help`, and `cyberwave edge --help`.
- Confirm authenticated workspace/environment access without exposing the key.
- Check Docker/systemd/device permissions only to the extent the chosen driver requires.
- Preserve existing edge configuration unless the user requested re-pairing or replacement.

## Pair/bootstrap

The current CLI uses `cyberwave pair` as the first-time device flow and aliases it to `cyberwave edge install`. Prefer the interactive command because it performs workspace, environment, twin, package, and boot-service selection together:

```bash
sudo cyberwave pair
```

Inspect `cyberwave pair --help` before using flags such as environment selection, non-interactive confirmation, release channel, or camera/microphone reconfiguration. Do not include a token directly on the command line unless the user accepts shell-history/process-list exposure and no safer input mechanism exists.

Do not re-run pairing repeatedly after a partial failure. Inspect the service/config/edge registration first and resume the failed layer.

## Configuration source

Treat the generated edge configuration directory and mounted twin/environment JSON as the runtime source of truth. Avoid hardcoding twin UUIDs, sensor IDs, device paths, or credentials inside images.

Driver configuration should derive:

- twin and asset identity from the mounted twin JSON,
- environment binding from environment configuration,
- edge identity from the device fingerprint,
- device selection from injected environment/config mappings,
- secrets from environment/secret storage.

## MQTT and Zenoh

- MQTT is the remote broker path for SDK, UI, and cross-LAN teleoperation; `twin/command` is MQTT-only.
- Zenoh is for edge-colocated `DataBus` traffic on the same host as workers.
- A driver opts into Zenoh per publisher/listener in its declared interface. Dual transport is not inferred from a global backend switch.
- Use `CYBERWAVE_PUBLISH_MODE=mqtt_only` only when the operator explicitly needs to disable Zenoh publishing.

When editing a driver, follow the current unified `TopicSpec(enable_mqtt=True, enable_zenoh=True, zenoh_channel=...)` declarations from current SDK examples rather than hand-writing duplicate loops. `twin/command` remains MQTT-only.

## Drivers and containers

Inspect current CLI support before operating containers. The CLI may expose `cyberwave edge driver list|start|stop`; starting a stopped container is not the same as deploying a new driver image. New deployment should remain under Edge Core's image selection/configuration.

Account for systemd or another supervisor: stopping only a Docker container may cause it to restart. Change the owning service through the platform-supported flow when necessary.

## Diagnose in order

1. Edge Core/system service state and recent logs.
2. Configuration/fingerprint/environment binding.
3. Docker availability and driver/worker container state.
4. Driver lifecycle and hardware connection.
5. MQTT connection and remote telemetry.
6. Zenoh/local worker data only for declared dual-transport channels.
7. Camera/stream or application-specific readiness.

Some legacy CLI `edge health`/`remote-status` commands are deprecated because Edge Core handles those checks. Prefer current service/container/telemetry diagnostics; use deprecated commands only when the installed CLI documents them as the relevant compatibility path.

## Destructive/re-pair operations

Uninstall, registration deletion, configuration wipe, fingerprint replacement, or re-pairing can release twins and stop/remove managed containers. Resolve the exact host/fingerprint/environment and require explicit authorization before those operations. State what can be recovered and what must be paired again.

## Completion evidence

Report edge fingerprint/record identifier when safe, environment/twin bindings, installed channel/version, service state, driver/worker container state, transport readiness, and unresolved hardware or permission errors. Do not report credentials.
