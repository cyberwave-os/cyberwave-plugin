# Cyberwave Skill

A [Claude Code](https://claude.ai/claude-code) skill that guides you through building a Physical AI application on [Cyberwave](https://cyberwave.com) — controlling robots, reading sensors, managing digital twins, and streaming video.

## What it does

When invoked, the skill asks which interface you want to use:

- **Python SDK** (recommended) — full walkthrough: installation, authentication, twin connection, joint control, camera capture, video streaming, workflows, and alerts
- **C++ SDK** — coming soon; redirects you to Python SDK or raw APIs in the meantime
- **APIs directly** — guides you through the REST API (HTTPS, Bearer token) and MQTT API (real-time joint control, telemetry, WebRTC signalling) so you can build in any language

## Installation

```bash
# Global (available in all projects)
git clone https://github.com/cyberwave-os/cyberwave-skill ~/.claude/skills/cyberwave

# Or project-local
git clone https://github.com/cyberwave-os/cyberwave-skill .claude/skills/cyberwave
```

## Usage

In any Claude Code session, run:

```
/cyberwave
```

Describe what you want to build and Claude will guide you through the right interface, set up your environment, and help you implement the application loop.

## Requirements

- [Claude Code](https://claude.ai/claude-code)
- A Cyberwave account — [sign up](https://cyberwave.com)
- Python 3.10+ and FFMPEG (for the Python SDK path)

## License

Apache 2.0
