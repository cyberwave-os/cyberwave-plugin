#!/usr/bin/env python3
"""
scaffold.py — Cyberwave driver project generator

Copies the files from the templates/ directory into a new project folder,
substituting __PLACEHOLDER__ tokens with values derived from your answers.

Usage (interactive):
    python scaffold.py

Usage (non-interactive / CI):
    python scaffold.py \
        --name my-lidar-driver \
        --description "A SICK LiDAR over Ethernet using the SOPAS protocol" \
        --author "Acme Robotics" \
        --child-twins
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Name helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def to_class_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("-"))


def to_package_name(slug: str) -> str:
    return slug.replace("-", "_")


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def prompt(question: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return answer or default


def prompt_bool(question: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        answer = input(f"{question} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    if not answer:
        return default
    return answer.startswith("y")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

# Sections injected into templates when child twins are enabled / disabled.
_CHILD_TWINS_SECTION_ON = """\
    child_uuids = [
        u.strip()
        for u in os.environ.get("CYBERWAVE_CHILD_TWIN_UUIDS", "").split(",")
        if u.strip()
    ]"""

_CHILD_TWINS_SECTION_OFF = "    child_uuids: list[str] = []"

_CHILD_TWINS_LOG_ON = """\

        if self.child_uuids:
            logger.info("Child twin UUIDs: %s", self.child_uuids)
            # TODO: coordinate child twins (e.g. cameras) using self.child_uuids"""

_CHILD_TWINS_LOG_OFF = ""


def build_vars(slug: str, description: str, author: str, year: int, has_child_twins: bool) -> dict:
    return {
        "__DRIVER_NAME__": slug,
        "__CLASS_NAME__": to_class_name(slug),
        "__PACKAGE_NAME__": to_package_name(slug),
        "__DESCRIPTION__": description,
        "__AUTHOR__": author or slug,
        "__YEAR__": str(year),
        "__CHILD_TWINS_SECTION__": _CHILD_TWINS_SECTION_ON if has_child_twins else _CHILD_TWINS_SECTION_OFF,
        "__CHILD_TWINS_LOG__": _CHILD_TWINS_LOG_ON if has_child_twins else _CHILD_TWINS_LOG_OFF,
    }


def render(text: str, vars: dict) -> str:
    for key, value in vars.items():
        text = text.replace(key, value)
    return text


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------

def scaffold(inputs: dict, output_dir: str) -> Path:
    slug = slugify(inputs["name"])
    package = to_package_name(slug)
    root = Path(output_dir) / slug
    templates_dir = Path(__file__).parent / "templates"

    if root.exists():
        print(f"\nError: '{root}' already exists. Remove it or choose a different name.")
        sys.exit(1)

    if not templates_dir.exists():
        print(f"\nError: templates directory not found at {templates_dir}")
        sys.exit(1)

    vars = build_vars(
        slug=slug,
        description=inputs["description"],
        author=inputs["author"],
        year=inputs["year"],
        has_child_twins=inputs["has_child_twins"],
    )

    print(f"\n  Scaffolding '{slug}' into {root.resolve()}\n")

    for src in sorted(templates_dir.rglob("*")):
        if src.is_dir():
            continue

        # Determine output path: rename the `driver/` package folder to the actual package name
        rel = src.relative_to(templates_dir)
        parts = list(rel.parts)
        if parts[0] == "driver":
            parts[0] = package
        out = root / Path(*parts)

        out.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")
        out.write_text(render(content, vars), encoding="utf-8")
        print(f"  created  {out.relative_to(root.parent)}")

    return root


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a Cyberwave-compatible driver project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--name", help="Driver project name (e.g. my-lidar-driver)")
    parser.add_argument("--description", help="One-sentence hardware description")
    parser.add_argument("--author", help="Author name or organisation", default="")
    parser.add_argument("--output-dir", default=".", help="Where to create the project folder (default: current directory)")
    parser.add_argument("--child-twins", action="store_true", default=None, help="Driver manages child twins")
    parser.add_argument("--year", type=int, default=None, help="Copyright year (default: current year)")
    return parser.parse_args()


def collect_inputs(args: argparse.Namespace) -> dict:
    interactive = not all([args.name, args.description, args.author])

    if interactive:
        print("\n  Cyberwave Driver Scaffold")
        print("  " + "─" * 40)

    name = args.name or prompt("Driver name (e.g. my-lidar-driver)")
    if not name:
        print("Error: driver name is required.")
        sys.exit(1)

    description = args.description or prompt(
        "Hardware description (one sentence)",
        default="A hardware device connected to Cyberwave",
    )
    author = args.author or prompt("Author / organisation", default="")
    has_child_twins = (
        args.child_twins
        if args.child_twins is not None
        else prompt_bool("Does this driver manage child twins (e.g. cameras)?", default=False)
    )
    year = args.year or datetime.date.today().year

    return dict(name=name, description=description, author=author, has_child_twins=has_child_twins, year=year)


def print_next_steps(root: Path) -> None:
    pkg = root.name.replace("-", "_")
    print(f"""
  Done! Next steps:

    1. Implement the hardware layer:
         {root}/{pkg}/hardware.py  ← fill in connect() and read_state()

    2. Set up local dev:
         pip install cyberwave
         cyberwave login
         cyberwave twin create <registry-id> --name "{root.name}-dev" --pair --target-dir {root}
         echo '{{"metadata": {{}}}}' > /tmp/cyberwave-twin.json
         cd {root} && docker compose up --build

  Reference drivers:
    • https://github.com/cyberwave-os/cyberwave-edge-camera-driver
    • https://github.com/cyberwave-os/cyberwave-edge-so101

  Docs:
    • https://docs.cyberwave.com/edge/drivers/writing-compatible-drivers
""")


def main() -> None:
    args = parse_args()
    inputs = collect_inputs(args)
    root = scaffold(inputs, args.output_dir)
    print_next_steps(root)


if __name__ == "__main__":
    main()
