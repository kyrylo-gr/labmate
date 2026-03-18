#!/usr/bin/env python3
"""Check or fix the package version against the main branch version."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CONFIG_PATH = Path("labmate/__config__.py")
VERSION_RE = re.compile(r'(__version__\s*=\s*")([0-9]+(?:\.[0-9]+){2})(")')


def parse_version(version: str) -> tuple[int, int, int]:
    try:
        parts = tuple(int(part) for part in version.split("."))
    except ValueError as exc:
        raise SystemExit(f"Invalid semantic version '{version}': {exc}") from exc
    if len(parts) != 3:
        raise SystemExit(f"Invalid semantic version '{version}': expected MAJOR.MINOR.PATCH")
    return parts


def read_current_version(config_path: Path) -> tuple[str, tuple[int, int, int], str]:
    text = config_path.read_text()
    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit(f"Unable to find __version__ in {config_path}")
    version_str = match.group(2)
    return text, parse_version(version_str), version_str


def bump_patch(version: tuple[int, int, int]) -> tuple[int, int, int]:
    major, minor, patch = version
    return (major, minor, patch + 1)


def format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def run_check(main_version: tuple[int, int, int], current_version: tuple[int, int, int]) -> int:
    if current_version <= main_version:
        print(
            "Error: current version must be greater than main version "
            f"({format_version(current_version)} <= {format_version(main_version)})"
        )
        return 1
    print(
        "Version check passed: current version is greater than main version "
        f"({format_version(current_version)} > {format_version(main_version)})"
    )
    return 0


def run_fix(
    config_path: Path,
    text: str,
    current_version: tuple[int, int, int],
    current_str: str,
    main_version: tuple[int, int, int],
) -> int:
    if current_version > main_version:
        print(
            "No version update needed: current version already exceeds main version "
            f"({current_str} > {format_version(main_version)})"
        )
        return 0

    new_version = bump_patch(main_version)
    new_version_str = format_version(new_version)
    updated_text = VERSION_RE.sub(rf"\g<1>{new_version_str}\g<3>", text, count=1)
    config_path.write_text(updated_text)
    print(f"Updated version from {current_str} to {new_version_str}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "main_version",
        help="Version currently on main, for example 0.10.7",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Fail if the current version is not greater than main",
    )
    mode.add_argument(
        "--fix",
        action="store_true",
        help="Bump the current version if it is not greater than main",
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help="Path to the config file that contains __version__",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    main_version = parse_version(args.main_version)
    text, current_version, current_str = read_current_version(config_path)

    if args.check:
        return run_check(main_version, current_version)
    return run_fix(config_path, text, current_version, current_str, main_version)


if __name__ == "__main__":
    sys.exit(main())
