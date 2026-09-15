# Verified CLI command map

This map summarizes the maintained command groups in the Cyberwave CLI. Treat it as routing guidance, then inspect the installed command's `--help` because installed versions can lag current documentation.

## Identity and configuration

| Intent | Command |
| --- | --- |
| Authenticate interactively | `cyberwave login` |
| Remove saved login | `cyberwave logout` |
| Inspect or set non-interactive configuration | `cyberwave configure` |
| Show the credential/config directory | `cyberwave config-dir` |
| Inspect paired edge identity | `cyberwave edge whoami` |

Avoid passwords and tokens on command lines when an interactive or secret-injected path is available.

## Resource-oriented command groups

- `cyberwave environment` — list/inspect supported environment state.
- `cyberwave twin` — create, list, show, pair, and delete twins.
- `cyberwave workflow` — list, inspect, author/run supported workflows and templates.
- `cyberwave model`, `compute`, and `worker` — model, cloud-node, and workflow-worker operations.
- `cyberwave camera`, `scan`, and `so101` — device discovery and supported hardware helpers.
- `cyberwave manifest` — inspect/generate supported manifests.
- `cyberwave plugin` and `completion` — CLI extensions and shell completion.

Prefer MCP for environment/workflow/cloud mutations when the equivalent typed tool is present. Use the CLI when the user explicitly wants shell automation or the operation is host-local.

## Edge group

| Intent | Current command |
| --- | --- |
| First-time setup/pairing | `cyberwave pair` or `cyberwave edge install` |
| Remove local edge service/config | `cyberwave edge uninstall` |
| Service lifecycle | `cyberwave edge start`, `stop`, `restart`, `status` |
| Refresh local config | `cyberwave edge pull` |
| Recent/followed service logs | `cyberwave edge logs` |
| Enumerate local cameras | `cyberwave edge cameras` |
| Reconfigure media bridges | `cyberwave edge install --reconfigure-camera`, `--reconfigure-microphone`, or `--reconfigure-speaker` |
| Install worker runtime extras | `cyberwave edge install-deps` |
| Refresh workflow bindings | `cyberwave edge sync-workflows` |
| Inspect loaded models | `cyberwave edge list-models --twin-uuid <uuid>` |
| List/start/stop driver containers | `cyberwave edge driver list|start|stop` |
| Benchmark edge execution | `cyberwave edge bench` |

`edge health` and `edge remote-status` can exist as compatibility commands in some CLI versions. Prefer `edge status`, bounded `edge logs`, and current dashboard/MCP telemetry for new guidance unless installed `--help` and current docs require the compatibility commands.

## Pairing facts

- `--environment` accepts an environment UUID or full slug and never creates the environment.
- Explicit `--token` overrides stored credentials for pairing. Do not expose it in logs or examples with a real value.
- `--channel` accepts `stable`, `dev`, or `staging`; production guidance defaults to `stable`.
- On unattended setup, `--yes` can also bypass twin selection. Use it only after proving the environment has the intended unambiguous edge-compatible target.
- Linux service installation/uninstallation requires appropriate root privileges; macOS uses LaunchAgents and local media bridges.

## Diagnostics order

1. `cyberwave --version`
2. `cyberwave edge whoami`
3. `cyberwave edge status`
4. `cyberwave edge driver list --all`
5. `cyberwave edge logs --lines 100`
6. Device-specific checks (`edge cameras`, worker status/logs, Docker state)
7. Network/MQTT/Zenoh checks only when the earlier evidence points to transport failure

Do not delete/re-pair as an initial diagnostic step.
