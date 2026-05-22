#!/usr/bin/env python3
"""Phase 0 environment checker for the RVV latency profiling workspace."""

from __future__ import annotations

import json
import os
import argparse
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "paths.yaml"
VALID_MODES = {"synthetic_calibration", "real_platform_profile"}
VALID_COMMANDS = {"plan", "dry_run", "scaffold"}
MIN_PYTHON = (3, 9)
EXPECTED_KEYS = (
    "mode",
    "llvm_checkout",
    "gem5_checkout",
    "gem5_build",
    "assembler",
    "linker",
    "output_root",
)
PLAN_REQUIRED_KEYS = {
    "llvm_checkout",
    "gem5_checkout",
    "gem5_build",
    "assembler",
    "linker",
    "output_root",
}
DRY_RUN_REQUIRED_KEYS = {"mode", "output_root"}
DRY_RUN_OPTIONAL_KEYS = PLAN_REQUIRED_KEYS - DRY_RUN_REQUIRED_KEYS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check RVV profiling workspace paths and tools."
    )
    parser.add_argument(
        "--command",
        choices=sorted(VALID_COMMANDS),
        default="plan",
        help=(
            "Workflow command to validate. The default 'plan' path requires real "
            "gem5/toolchain paths; 'dry_run' and 'scaffold' relax those tools."
        ),
    )
    parser.add_argument(
        "--allow-dry-run-missing-tools",
        action="store_true",
        help=(
            "Allow gem5/toolchain paths to be absent for dry-run or scaffold-only "
            "work. This does not validate real platform profiling readiness."
        ),
    )
    return parser.parse_args(argv)


def required_keys_for(command: str, allow_dry_run_missing_tools: bool) -> set[str]:
    if command in {"dry_run", "scaffold"} or allow_dry_run_missing_tools:
        return set(DRY_RUN_REQUIRED_KEYS)
    return set(PLAN_REQUIRED_KEYS)


def strip_inline_comment(text: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None:
            return text[:index].rstrip()
    return text.rstrip()


def parse_scalar(value: str) -> str | None:
    value = strip_inline_comment(value).strip()
    if not value or value.lower() in {"null", "~"}:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_simple_yaml(path: Path) -> dict[str, str | None]:
    data: dict[str, str | None] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line[:1].isspace():
            raise ValueError(f"line {line_number}: nested YAML is not supported")
        if ":" not in raw_line:
            raise ValueError(f"line {line_number}: expected 'key: value'")
        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"line {line_number}: empty key")
        data[key] = parse_scalar(value)
    return data


def resolve_path(value: str | None) -> str | None:
    if value is None:
        return None
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return str(path.resolve(strict=False))


def path_status(
    name: str,
    value: str | None,
    *,
    expect: str,
    required: bool = False,
    executable: bool = False,
) -> dict[str, Any]:
    resolved = resolve_path(value)
    exists = False
    kind_ok = False
    executable_ok = not executable
    executable_value: bool | None = None
    if resolved is not None:
        candidate = Path(resolved)
        exists = candidate.exists()
        if expect == "dir":
            kind_ok = candidate.is_dir()
        elif expect == "file":
            kind_ok = candidate.is_file()
        elif expect == "any":
            kind_ok = exists
        else:
            raise ValueError(f"unknown expected path kind for {name}: {expect}")
        executable_ok = not executable or os.access(candidate, os.X_OK)
        if executable:
            executable_value = os.access(candidate, os.X_OK)

    if resolved is None:
        status = "missing_required" if required else "unspecified_optional"
    elif kind_ok and executable_ok:
        status = "present"
    elif required:
        status = "missing_required"
    else:
        status = "missing_optional"

    return {
        "configured": value,
        "resolved": resolved,
        "required": required,
        "expected": expect,
        "executable_required": executable,
        "executable": executable_value,
        "exists": exists,
        "status": status,
    }


def tool_status(name: str, value: str | None, *, required: bool = False) -> dict[str, Any]:
    if value is None:
        return {
            "configured": None,
            "resolved": None,
            "required": required,
            "exists": False,
            "executable": False,
            "status": "missing_required" if required else "unspecified_optional",
        }

    configured_path = resolve_path(value)
    discovered = configured_path
    if os.sep not in value and not value.startswith("."):
        discovered = shutil.which(value)

    exists = bool(discovered and Path(discovered).exists())
    executable = bool(discovered and os.access(discovered, os.X_OK))
    if executable:
        status = "present"
    elif required:
        status = "missing_required"
    else:
        status = "missing_optional"
    return {
        "configured": value,
        "resolved": discovered,
        "required": required,
        "exists": exists,
        "executable": executable,
        "status": status,
    }


def python_status() -> dict[str, Any]:
    current = sys.version_info
    ok = current >= MIN_PYTHON
    return {
        "executable": sys.executable,
        "version": f"{current.major}.{current.minor}.{current.micro}",
        "required": f">={MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
        "ok": ok,
        "status": "present" if ok else "missing_required",
    }


def status_error(
    name: str,
    status: dict[str, Any],
    *,
    command: str,
    allow_dry_run_missing_tools: bool,
    group: str,
) -> str:
    configured = status.get("configured")
    resolved = status.get("resolved")
    expected = status.get("expected", "executable tool")
    target = resolved or configured or "<unset>"
    dry_run_hint = ""
    if name in DRY_RUN_OPTIONAL_KEYS and command == "plan" and not allow_dry_run_missing_tools:
        dry_run_hint = (
            "; for scaffold-only checks rerun with --allow-dry-run-missing-tools "
            "or --command dry_run"
        )
    config_hint = f"set {name} in config/paths.yaml"
    if group == "tools":
        return f"{name}: required executable not found ({target}); {config_hint}{dry_run_hint}"
    if status.get("executable_required"):
        return f"{name}: required executable file not found ({target}); {config_hint}{dry_run_hint}"
    return f"{name}: required {expected} not found ({target}); {config_hint}{dry_run_hint}"


def build_report(
    *,
    command: str = "plan",
    allow_dry_run_missing_tools: bool = False,
) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    warnings: list[str] = []
    config: dict[str, str | None] = {}
    required_keys = required_keys_for(command, allow_dry_run_missing_tools)

    report: dict[str, Any] = {
        "schema_version": 1,
        "repo_root": str(REPO_ROOT),
        "command": command,
        "allow_dry_run_missing_tools": allow_dry_run_missing_tools,
        "config": {
            "path": str(CONFIG_PATH),
            "exists": CONFIG_PATH.exists(),
            "values": {},
        },
        "python": python_status(),
        "mode": None,
        "paths": {},
        "tools": {},
        "warnings": warnings,
        "errors": errors,
        "ok": False,
    }

    if not report["python"]["ok"]:
        errors.append(
            f"Python {report['python']['required']} is required; found {report['python']['version']}"
        )

    if not CONFIG_PATH.exists():
        errors.append(f"missing config file: {CONFIG_PATH}")
        return report, 1

    try:
        config = load_simple_yaml(CONFIG_PATH)
    except ValueError as exc:
        errors.append(f"invalid config file: {exc}")
        return report, 1

    report["config"]["values"] = config
    missing_keys = [key for key in EXPECTED_KEYS if key not in config]
    if missing_keys:
        warnings.append(f"config is missing expected keys: {', '.join(missing_keys)}")
    missing_required_keys = [key for key in sorted(required_keys) if key not in config]
    for key in missing_required_keys:
        errors.append(f"{key}: missing required config key; set {key} in config/paths.yaml")

    mode = config.get("mode")
    report["mode"] = mode
    if mode not in VALID_MODES:
        errors.append(
            "invalid mode: expected one of "
            + ", ".join(sorted(VALID_MODES))
            + f"; found {mode!r}"
        )

    report["paths"] = {
        "llvm_checkout": path_status(
            "llvm_checkout",
            config.get("llvm_checkout"),
            expect="dir",
            required="llvm_checkout" in required_keys,
        ),
        "gem5_checkout": path_status(
            "gem5_checkout",
            config.get("gem5_checkout"),
            expect="dir",
            required="gem5_checkout" in required_keys,
        ),
        "gem5_build": path_status(
            "gem5_build",
            config.get("gem5_build"),
            expect="file",
            required="gem5_build" in required_keys,
            executable=True,
        ),
        "output_root": path_status(
            "output_root",
            config.get("output_root"),
            expect="any",
            required="output_root" in required_keys,
        ),
    }
    report["tools"] = {
        "assembler": tool_status(
            "assembler",
            config.get("assembler"),
            required="assembler" in required_keys,
        ),
        "linker": tool_status(
            "linker",
            config.get("linker"),
            required="linker" in required_keys,
        ),
    }

    for group in ("paths", "tools"):
        for name, status in report[group].items():
            if status["status"] in {"missing_optional", "unspecified_optional"}:
                warnings.append(f"{name}: {status['status']}")
            elif status["status"] == "missing_required":
                errors.append(
                    status_error(
                        name,
                        status,
                        command=command,
                        allow_dry_run_missing_tools=allow_dry_run_missing_tools,
                        group=group,
                    )
                )

    exit_code = 1 if errors else 0
    report["ok"] = exit_code == 0
    return report, exit_code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report, exit_code = build_report(
        command=args.command,
        allow_dry_run_missing_tools=args.allow_dry_run_missing_tools,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
