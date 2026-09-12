# Cyberwave Agent Skill

A portable Agent Skill for building and operating Physical AI systems on [Cyberwave](https://cyberwave.com). One `cyberwave` entrypoint routes agents to focused guidance for:

- registration, authentication, and Cyberwave MCP connection
- environment creation and editing
- workflow authoring and run management
- safe robot control in simulation and live mode
- edge pairing, drivers, workers, and MQTT/Zenoh configuration
- asset onboarding and driver development
- robot telemetry, camera, workflow, and edge monitoring

The core follows the open [Agent Skills](https://agentskills.io) format. Cyberwave MCP is the preferred typed execution plane when available, but the skill degrades to the verified SDK, CLI, dashboard, or official documentation.

## Install

### Canonical public skill (Claude Code or Codex)

```bash
git clone https://github.com/cyberwave-os/cyberwave-skill ~/.claude/skills/cyberwave
# Codex: clone to ~/.codex/skills/cyberwave instead
```

Use `/cyberwave` in Claude Code, `$cyberwave` in Codex, or describe a matching Cyberwave task and allow automatic discovery.

### Project-local or other Agent Skills clients

Clone/copy the repository as a directory named `cyberwave` beneath the client's project or user Agent Skills search path. The required entrypoint is `SKILL.md`; provider-specific metadata is additive.

For ChatGPT or API runtimes that accept uploaded skill bundles, upload the same directory/ZIP and promote an immutable tested version. Keep MCP credentials in runtime configuration, not the bundle.

## Cyberwave MCP

Hosted endpoint: `https://mcp.cyberwave.com/mcp` (Streamable HTTP). It uses a user-scoped Cyberwave API key in the `Authorization: Bearer ...` header. Configure the key with the client's secret mechanism; never commit it.

The skill discovers the tools actually exposed by the current client. MCP is optional for guidance and code authoring, but live platform execution and verification require an authenticated execution plane.

## Architecture

`SKILL.md` is a compact orchestrator. It loads only the relevant module from `references/` for the current task. This keeps the discovery and activation context small while retaining detailed domain procedures.

## Validate

Run the portable validation before opening a pull request:

```bash
python3 scripts/validate_skill.py
```

To compare two skill checkouts before distribution:

```bash
python3 scripts/validate_skill.py --compare /path/to/cyberwave-skill
```

The evaluator scenarios in `evals/scenarios.json` define the expected routing and safety decisions for realistic user requests. Tests should assert those decisions and observable effects rather than exact prose.

## License

Apache-2.0.
