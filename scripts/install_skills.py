#!/usr/bin/env python3
"""Install the single Cyberwave skill from a cyberwave-skills checkout."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = PACKAGE_ROOT / "skills" / "cyberwave"


def destination(client: str, project: bool) -> Path:
    if project:
        return Path.cwd() / f".{client}" / "skills" / "cyberwave"
    if client == "codex":
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        return codex_home / "skills" / "cyberwave"
    return Path.home() / ".claude" / "skills" / "cyberwave"


def preserve_existing(path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.backup-{stamp}")
    counter = 1
    while backup.exists() or backup.is_symlink():
        backup = path.with_name(f"{path.name}.backup-{stamp}-{counter}")
        counter += 1
    path.rename(backup)
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("claude", "codex"), required=True)
    parser.add_argument(
        "--project",
        action="store_true",
        help="Install under the current project's .claude/.codex directory",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating a symlink to this checkout",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Move an existing installation to a timestamped backup before installing",
    )
    args = parser.parse_args()

    target = destination(args.client, args.project)
    if target.exists() or target.is_symlink():
        if not args.replace:
            raise SystemExit(
                f"Refusing to replace existing installation: {target}\n"
                "Re-run with --replace to preserve it as a timestamped backup."
            )
        backup = preserve_existing(target)
        print(f"Preserved existing installation at {backup}")

    target.parent.mkdir(parents=True, exist_ok=True)
    if args.copy:
        shutil.copytree(SKILL_SOURCE, target)
        method = "copied"
    else:
        target.symlink_to(SKILL_SOURCE, target_is_directory=True)
        method = "linked"

    print(f"Cyberwave skill {method}: {target} -> {SKILL_SOURCE}")


if __name__ == "__main__":
    main()
