# Cyberwave Agent Skills

The canonical cross-agent skill package for building and operating Physical AI systems with Cyberwave. It exposes one discoverable `cyberwave` skill. Focused procedures live behind that entrypoint as references and deterministic scripts:

These are **customer-facing skills for end-user agents**: they help Cyberwave users create environments and workflows, control and monitor robots, configure edge deployments, onboard assets, and develop drivers. They are not instructions for Cyberwave's internal engineering agents and do not define how agents should develop, review, release, or maintain the Cyberwave monorepo itself. Internal repository guidance remains in the monorepo's `AGENTS.md` files and engineering documentation.

```text
skills/cyberwave/
├── SKILL.md                    one MCP-aware orchestrator
├── references/                 domain and execution-plane procedures
├── scripts/scaffold_driver.py  deterministic driver generator
└── assets/driver-template/     current BaseDriver project template
```

This directory is the maintained source of truth. `skills/cyberwave/` is mirrored to the primary public repository, `cyberwave-os/cyberwave-skill`; `cyberwave-os/cyberwave-plugin` is a generated Claude plugin compatibility distribution. The plural and standalone driver repositories are not sync targets. Do not maintain public mirrors independently.

## Agent routing

Always start with `cyberwave`. Its execution-plane reference says which tasks belong to MCP and which require CLI, SDK, dashboard, or host-level work. CLI/edge and driver development are resources of the same skill, not separate discovery entries.

The portable behavior lives in `skills/cyberwave/SKILL.md` and follows the open Agent Skills layout. `.claude-plugin/` and `.mcp.json` package the same skill as a Claude plugin. `agents/openai.yaml` adds Codex/OpenAI discovery metadata without changing operational behavior.

## Install from a checkout

Install the skill for Claude Code:

```bash
python3 scripts/install_skills.py --client claude
```

Install the skill for Codex:

```bash
python3 scripts/install_skills.py --client codex
```

Use `--project` for project-local installation or `--copy` when symlinks are unsuitable. Run `python3 scripts/install_skills.py --help` for exact paths and options.

For ChatGPT or API runtimes that accept uploaded skill bundles, upload `skills/cyberwave` and promote a tested immutable version. Configure the hosted Cyberwave MCP endpoint and credentials in the runtime, never in the bundle.

## Validate

From the monorepo root:

```bash
python3 cyberwave-clis/cyberwave-skills/scripts/validate_skills.py \
  --mcp-source cyberwave-clis/cyberwave-mcp-server/cyberwave_mcp_server \
  --cli-source cyberwave-clis/cyberwave-python-cli/cyberwave_cli \
  --sdk-source cyberwave-sdks/cyberwave-python
```

The validator checks the skill, local links, secrets, driver scaffold, documented CLI commands, MCP tool drift, generated-driver compatibility with the current Python SDK, and plugin metadata. Use Python 3.11+ for the SDK import check.

The public singular mirror runs the portable subset on every pull request and push to `main`; the monorepo workflow additionally validates the package against the live MCP, CLI, and SDK sources.

## License

Apache-2.0.
