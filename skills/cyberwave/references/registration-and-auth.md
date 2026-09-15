# Registration and authentication

Read this when the user lacks Cyberwave access, credentials, MCP connectivity, or enough resource context for the requested operation.

## Establish the minimum missing layer

Work downward only as far as the task needs:

1. Cyberwave account
2. API key or authenticated CLI session
3. workspace
4. project
5. environment
6. twin

Do not ask for all six when the user already supplied a resource UUID/slug or the MCP session has current context.

## New account

Direct the user to [cyberwave.com/signup](https://cyberwave.com/signup) to register. Keep the user in control of email verification, organization/workspace choice, terms, billing, and any identity-provider flow. The hosted MCP requires an existing API token; it does not register an account or accept terms. Do not ask the user to paste a password or API key into chat.

After registration, the user needs a workspace and workspace-scoped API token. They can create/copy a token from [Profile → API Keys](https://cyberwave.com/profile), or use the interactive CLI login below to create and store one. If no workspace exists after login, ask them to create or join one in the dashboard, then resume with the workspace UUID/name.

## Existing account

For a local terminal, prefer the interactive CLI flow. It authenticates locally, lets the user select a workspace when needed, creates a workspace-scoped API token, and stores the result in the Cyberwave credentials file:

```bash
cyberwave login
```

The user must enter credentials in the terminal prompt, not in the agent conversation. If the user already has an API key, use the client's secret mechanism or `cyberwave login --token`/the interactive configuration flow without reproducing the value. `CYBERWAVE_API_KEY` is the primary environment variable. `CYBERWAVE_TOKEN` is a supported MCP fallback. The CLI may store credentials in `~/.cyberwave/credentials.json`; never display or commit that file.

Useful read-only checks:

```bash
cyberwave configure --show
```

Do not put a real key in a command example, repository file, issue, log, or response. If a key is exposed, advise revocation and replacement.

## Hosted Cyberwave MCP

Endpoint: `https://mcp.cyberwave.com/mcp` using Streamable HTTP and a Bearer API key. Configure it through the current client's supported MCP UI/config and secret interpolation. Keep the key outside committed configuration.

The conceptual configuration is:

```json
{
  "mcpServers": {
    "cyberwave": {
      "type": "http",
      "url": "https://mcp.cyberwave.com/mcp",
      "headers": {
        "Authorization": "Bearer <secret supplied by the client>"
      }
    }
  }
}
```

Do not claim that `${ENV_VAR}` interpolation works unless the user's MCP client documents it. If the client cannot store headers securely, use the local stdio server or guide the user through manual dashboard setup.

## Context discovery with MCP

When present, use this read-only chain and stop as soon as the target is unambiguous:

1. `cw_list_workspaces`
2. `cw_list_projects` scoped to the chosen workspace
3. `cw_list_environments` scoped to the chosen project
4. `cw_get_environment_context` for the chosen/current environment
5. `cw_resolve_twin` or `cw_list_twins` when a twin is needed

Use a supplied UUID or full slug directly. Auto-select only when exactly one visible candidate exists. If several candidates match, present their names and stable identifiers and ask the user to choose.

`CYBERWAVE_WORKSPACE_ID` and `CYBERWAVE_ENVIRONMENT_ID` can provide local defaults, but explicit request/session scope wins.

## Authentication errors

- `AUTH_ERROR` or 401: do not retry the same credential. Ask the user to authenticate or replace/re-authorize the key.
- 403: authentication succeeded but access is insufficient. Report the exact resource and requested capability; do not route around ACLs.
- No workspace: direct the user to create/join one, then retry discovery.
- MCP unavailable: follow [MCP and fallbacks](mcp-and-fallbacks.md).

## Resume contract

After any human-only step, resume when the user provides or the tools reveal:

- authenticated access,
- the selected workspace,
- the selected project/environment when required,
- and the target twin for robot-specific work.

Never require the raw API key in the conversation to resume.
