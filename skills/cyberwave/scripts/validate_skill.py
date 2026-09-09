#!/usr/bin/env python3
"""Validate the portable Cyberwave skill and optional checkout parity.

The script is intentionally standard-library only so it can run in any skill
checkout or distribution pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
REQUIRED_ROUTES = {
    "registration-and-auth",
    "mcp-and-fallbacks",
    "environment-management",
    "workflow-authoring",
    "robot-control",
    "policy-training",
    "edge-configuration",
    "cli-command-map",
    "asset-and-driver-development",
    "driver-development",
    "robot-monitoring",
}
TOOL_PATTERN = re.compile(r"\bcw_[a-z0-9_]+\b")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SECRET_PATTERNS = {
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Cyberwave API key": re.compile(r"\bcw_[A-Za-z0-9]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def text_files(root: Path) -> Iterable[Path]:
    allowed = {".md", ".json", ".yaml", ".yml", ".py", ".txt"}
    for path in iter_files(root):
        if path.suffix.lower() in allowed or path.name in {"SKILL.md", "README.md"}:
            yield path


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, "\n".join(lines[end + 1 :])


def validate_frontmatter(errors: list[str]) -> None:
    skill_path = SKILL_DIR / "SKILL.md"
    if not skill_path.exists():
        errors.append("Missing SKILL.md")
        return
    try:
        fields, body = parse_frontmatter(skill_path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    if fields.get("name") != "cyberwave":
        errors.append("SKILL.md name must be 'cyberwave'")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields.get("name", "")):
        errors.append("Skill name must contain lowercase letters, digits, and single hyphens only")
    description = fields.get("description", "")
    if not description or len(description) > 1024:
        errors.append("Skill description must be present and at most 1024 characters")
    if len(skill_path.read_text(encoding="utf-8").splitlines()) >= 500:
        errors.append("SKILL.md must remain below 500 lines")
    if "## Route the request" not in body:
        errors.append("SKILL.md is missing the orchestrator routing table")


def validate_links(errors: list[str]) -> None:
    for path in text_files(SKILL_DIR):
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(SKILL_DIR.resolve())
            except ValueError:
                errors.append(f"{path.relative_to(SKILL_DIR)} links outside the skill: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"Broken link in {path.relative_to(SKILL_DIR)}: {raw_target}")


def validate_routes(errors: list[str]) -> None:
    missing = [route for route in REQUIRED_ROUTES if not (SKILL_DIR / "references" / f"{route}.md").exists()]
    if missing:
        errors.append(f"Missing routed references: {', '.join(sorted(missing))}")

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for route in REQUIRED_ROUTES:
        if f"references/{route}.md" not in skill_text:
            errors.append(f"SKILL.md does not route to references/{route}.md")


def load_tool_manifest(errors: list[str]) -> tuple[set[str], set[str]]:
    path = SKILL_DIR / "references" / "mcp-tools.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid MCP tool manifest: {exc}")
        return set(), set()
    current = set(data.get("current", []))
    deprecated = set(data.get("deprecated", {}).keys())
    if not current:
        errors.append("MCP tool manifest has no current tools")
    if current & deprecated:
        errors.append("MCP tool manifest marks the same tool current and deprecated")
    return current, deprecated


def documented_tools() -> set[str]:
    tools: set[str] = set()
    for path in [SKILL_DIR / "SKILL.md", *(SKILL_DIR / "references").glob("*.md")]:
        tools.update(TOOL_PATTERN.findall(path.read_text(encoding="utf-8")))
    return tools


def discover_mcp_tools(source: Path) -> set[str]:
    candidates = [source / "server.py", source / "tool_metadata.py"]
    if source.is_file():
        candidates = [source]
    available: set[str] = set()
    for path in candidates:
        if path.exists():
            available.update(TOOL_PATTERN.findall(path.read_text(encoding="utf-8")))
    return available


def validate_tools(errors: list[str], mcp_source: Path | None) -> None:
    current, deprecated = load_tool_manifest(errors)
    used = documented_tools()
    unknown = used - current - deprecated
    if unknown:
        errors.append(f"Documented MCP tools missing from manifest: {', '.join(sorted(unknown))}")
    if mcp_source is None:
        return
    if not mcp_source.exists():
        errors.append(f"MCP source does not exist: {mcp_source}")
        return
    available = discover_mcp_tools(mcp_source)
    missing = current - available
    if missing:
        errors.append(f"Current MCP tools not found in server registration: {', '.join(sorted(missing))}")


def validate_openai_metadata(errors: list[str]) -> None:
    path = SKILL_DIR / "agents" / "openai.yaml"
    if not path.exists():
        errors.append("Missing agents/openai.yaml")
        return
    text = path.read_text(encoding="utf-8")
    for key in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{key}:\s*\"[^\"]+\"\s*$", text, re.MULTILINE):
            errors.append(f"agents/openai.yaml must include a quoted {key}")
    if "$cyberwave" not in text:
        errors.append("agents/openai.yaml default_prompt must mention $cyberwave")


def validate_evals(errors: list[str]) -> None:
    path = SKILL_DIR / "evals" / "scenarios.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid eval scenarios: {exc}")
        return
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 10:
        errors.append("Eval suite must contain at least 10 realistic scenarios")
        return
    ids: set[str] = set()
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            errors.append(f"Eval scenario {index} is not an object")
            continue
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"Eval scenario {index} has no id")
        elif scenario_id in ids:
            errors.append(f"Duplicate eval scenario id: {scenario_id}")
        else:
            ids.add(scenario_id)
        for key in ("prompt", "expected_routes", "required_decisions", "forbidden_actions"):
            if not scenario.get(key):
                errors.append(f"Eval scenario {scenario_id or index} has empty {key}")
        routes = set(scenario.get("expected_routes", []))
        unknown_routes = routes - REQUIRED_ROUTES
        if unknown_routes:
            errors.append(
                f"Eval scenario {scenario_id or index} uses unknown routes: "
                f"{', '.join(sorted(unknown_routes))}"
            )


def validate_secrets(errors: list[str]) -> None:
    for path in text_files(SKILL_DIR):
        text = path.read_text(encoding="utf-8")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"Possible {label} in {path.relative_to(SKILL_DIR)}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_map(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): digest(path) for path in iter_files(root)}


def validate_parity(errors: list[str], other: Path | None) -> None:
    if other is None:
        return
    if not other.exists():
        errors.append(f"Comparison directory does not exist: {other}")
        return
    local_files = file_map(SKILL_DIR)
    other_files = file_map(other)
    missing = set(local_files) - set(other_files)
    extra = set(other_files) - set(local_files)
    changed = {path for path in set(local_files) & set(other_files) if local_files[path] != other_files[path]}
    if missing:
        errors.append(f"Comparison directory is missing: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Comparison directory has extra files: {', '.join(sorted(extra))}")
    if changed:
        errors.append(f"Comparison directory differs: {', '.join(sorted(changed))}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mcp-source",
        type=Path,
        help="Path to an MCP registration source file or directory.",
    )
    parser.add_argument("--compare", type=Path, help="Require byte-level parity with another skill directory.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit a JSON result.")
    args = parser.parse_args()

    errors: list[str] = []
    validate_frontmatter(errors)
    validate_links(errors)
    validate_routes(errors)
    validate_tools(errors, args.mcp_source)
    validate_openai_metadata(errors)
    validate_evals(errors)
    validate_secrets(errors)
    validate_parity(errors, args.compare)

    result = {
        "status": "error" if errors else "ok",
        "skill_dir": str(SKILL_DIR),
        "checks": 8,
        "errors": errors,
    }
    if args.json_output:
        print(json.dumps(result, indent=2))
    elif errors:
        print("Cyberwave skill validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"Cyberwave skill validation passed ({result['checks']} checks).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
