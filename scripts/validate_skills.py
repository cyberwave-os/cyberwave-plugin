#!/usr/bin/env python3
"""Validate the canonical single-skill Cyberwave distribution."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PACKAGE_ROOT / "skills" / "cyberwave"
REQUIRED_SKILL_DIRS = {"cyberwave"}
REQUIRED_REFERENCES = {
    "registration-and-auth.md",
    "mcp-and-fallbacks.md",
    "environment-management.md",
    "workflow-authoring.md",
    "robot-control.md",
    "policy-training.md",
    "edge-configuration.md",
    "cli-command-map.md",
    "asset-and-driver-development.md",
    "driver-development.md",
    "robot-monitoring.md",
}
REQUIRED_TOP_LEVEL_COMMANDS = {
    "camera",
    "compute",
    "configure",
    "edge",
    "environment",
    "login",
    "pair",
    "twin",
    "workflow",
    "worker",
}
REQUIRED_EDGE_COMMANDS = {
    "install",
    "uninstall",
    "start",
    "stop",
    "restart",
    "status",
    "cameras",
    "install-deps",
    "logs",
    "sync-workflows",
    "list-models",
    "whoami",
    "pull",
    "bench",
}


def add_error(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def validate_layout(errors: list[str]) -> None:
    skills_root = PACKAGE_ROOT / "skills"
    actual = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if actual != REQUIRED_SKILL_DIRS:
        add_error(
            errors,
            "The package must expose exactly one discoverable skill named cyberwave; "
            f"found: {', '.join(sorted(actual)) or '(none)' }",
        )
    missing = REQUIRED_REFERENCES - {
        path.name for path in (SKILL_DIR / "references").glob("*.md")
    }
    if missing:
        add_error(errors, f"Missing required references: {', '.join(sorted(missing))}")
    for required in (
        SKILL_DIR / "scripts" / "scaffold_driver.py",
        SKILL_DIR / "assets" / "driver-template" / "driver" / "driver.py",
        PACKAGE_ROOT / ".claude-plugin" / "plugin.json",
        PACKAGE_ROOT / ".mcp.json",
    ):
        if not required.exists():
            add_error(errors, f"Missing required package file: {required.relative_to(PACKAGE_ROOT)}")


def run_skill_validator(errors: list[str], mcp_source: Path | None) -> None:
    command = [sys.executable, str(SKILL_DIR / "scripts" / "validate_skill.py")]
    if mcp_source is not None:
        command.extend(["--mcp-source", str(mcp_source)])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        add_error(errors, result.stdout.strip() or result.stderr.strip())


def validate_plugin_metadata(errors: list[str]) -> None:
    try:
        plugin = json.loads((PACKAGE_ROOT / ".claude-plugin" / "plugin.json").read_text())
        mcp = json.loads((PACKAGE_ROOT / ".mcp.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        add_error(errors, f"Invalid plugin/MCP JSON: {exc}")
        return
    if plugin.get("name") != "cyberwave":
        add_error(errors, "Claude plugin name must be cyberwave")
    endpoint = mcp.get("mcpServers", {}).get("cyberwave", {}).get("url")
    if endpoint != "https://mcp.cyberwave.com/mcp":
        add_error(errors, "Hosted MCP endpoint is missing or unexpected")


def discover_cli_commands(cli_source: Path) -> tuple[set[str], set[str]]:
    main_text = (cli_source / "main.py").read_text(encoding="utf-8")
    top_level = set(re.findall(r'^\s*"([a-z0-9-]+)":\s*\(', main_text, re.MULTILINE))
    edge_commands: set[str] = set()
    for path in (cli_source / "commands" / "edge").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        edge_commands.update(
            re.findall(r'@(?:(?:edge|click)\.)?command\("([a-z0-9-]+)"\)', text)
        )
    return top_level, edge_commands


def validate_cli(errors: list[str], cli_source: Path | None) -> None:
    if cli_source is None:
        return
    if not (cli_source / "main.py").exists():
        add_error(errors, f"CLI source is invalid: {cli_source}")
        return
    top_level, edge_commands = discover_cli_commands(cli_source)
    missing_top = REQUIRED_TOP_LEVEL_COMMANDS - top_level
    missing_edge = REQUIRED_EDGE_COMMANDS - edge_commands
    if missing_top:
        add_error(errors, f"Required CLI groups not found: {', '.join(sorted(missing_top))}")
    if missing_edge:
        add_error(errors, f"Required edge commands not found: {', '.join(sorted(missing_edge))}")


def validate_scaffold(errors: list[str], sdk_source: Path | None) -> None:
    scaffold = SKILL_DIR / "scripts" / "scaffold_driver.py"
    with tempfile.TemporaryDirectory(prefix="cyberwave-skill-") as tmp:
        command = [
            sys.executable,
            str(scaffold),
            "--name",
            "validation-sensor-driver",
            "--description",
            "A validation-only sensor",
            "--author",
            "Cyberwave",
            "--registry-id",
            "cyberwave/validation-sensor",
            "--child-twins",
            "--output-dir",
            tmp,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            add_error(errors, f"Driver scaffold failed: {result.stderr or result.stdout}")
            return
        generated = Path(tmp) / "validation-sensor-driver"
        driver_text = (generated / "validation_sensor_driver" / "driver.py").read_text(
            encoding="utf-8"
        )
        main_text = (generated / "validation_sensor_driver" / "__main__.py").read_text(
            encoding="utf-8"
        )
        if "def create(cls)" not in driver_text:
            add_error(errors, "Generated BaseDriver is missing the required create() factory")
        if "create_and_run_async()" not in main_text:
            add_error(errors, "Generated entrypoint must call create_and_run_async()")
        placeholders: list[str] = []
        for path in generated.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if re.search(r"__[A-Z][A-Z0-9_]+__", text):
                    placeholders.append(str(path.relative_to(generated)))
                if path.suffix == ".py":
                    try:
                        py_compile.compile(
                            str(path),
                            cfile=str(path.with_suffix(path.suffix + ".pyc")),
                            doraise=True,
                        )
                    except py_compile.PyCompileError as exc:
                        add_error(errors, f"Generated Python is invalid: {exc}")
        if placeholders:
            add_error(errors, f"Unresolved scaffold placeholders: {', '.join(placeholders)}")

        if sdk_source is None:
            return
        if not (sdk_source / "cyberwave" / "driver" / "base.py").exists():
            add_error(errors, f"Python SDK source is invalid: {sdk_source}")
            return
        if sys.version_info < (3, 11):
            print("Warning: SDK import check requires Python 3.11+; static scaffold checks passed.")
            return

        twin_json = Path(tmp) / "twin.json"
        twin_json.write_text('{"metadata": {}}', encoding="utf-8")
        env = os.environ.copy()
        python_path = [str(sdk_source), str(generated)]
        if env.get("PYTHONPATH"):
            python_path.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(python_path)
        env["CYBERWAVE_TWIN_JSON_FILE"] = str(twin_json)
        contract_check = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from validation_sensor_driver.driver import ValidationSensorDriver; "
                    "driver = ValidationSensorDriver.create(); "
                    "manifest = driver.get_manifest(); "
                    "assert manifest['registry_id'] == 'cyberwave/validation-sensor'; "
                    "assert manifest['mqtt']['twin']['command']; "
                    "assert manifest['mqtt']['commands']['supported']"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if contract_check.returncode:
            add_error(
                errors,
                "Generated driver does not satisfy the current Python SDK contract: "
                f"{contract_check.stderr or contract_check.stdout}",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcp-source", type=Path)
    parser.add_argument("--cli-source", type=Path)
    parser.add_argument("--sdk-source", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    validate_layout(errors)
    run_skill_validator(errors, args.mcp_source)
    validate_plugin_metadata(errors)
    validate_cli(errors, args.cli_source)
    validate_scaffold(errors, args.sdk_source)

    if errors:
        print("Cyberwave skills validation failed:")
        for error in errors:
            for line in error.splitlines():
                print(f"- {line}")
        return 1
    print("Cyberwave skills validation passed (single skill, MCP/CLI/scaffold checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
