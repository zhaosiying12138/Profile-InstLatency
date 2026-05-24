#!/usr/bin/env python3
"""Run one generated RVV profiling experiment.

This is the Phase 6 runner interface.  It is intentionally stdlib-only so it
can run before the gem5 patch stack and Python dependencies are settled.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


INSTRUCTION_SET: dict[str, dict[str, str]] = {
    "vadd_vv": {"asm": "vadd.vv", "sched_write": "WriteVIALUV"},
    "vsll_vv": {"asm": "vsll.vv", "sched_write": "WriteVShiftV"},
    "vmul_vv": {"asm": "vmul.vv", "sched_write": "WriteVIMulV"},
    "vdivu_vv": {"asm": "vdivu.vv", "sched_write": "WriteVIDivV"},
    "vmseq_vv": {"asm": "vmseq.vv", "sched_write": "WriteVICmpV"},
    "vcpop_m": {"asm": "vcpop.m", "sched_write": "WriteVMPopV"},
    "viota_m": {"asm": "viota.m", "sched_write": "WriteVIotaV"},
    "vslideup_vx": {"asm": "vslideup.vx", "sched_write": "WriteVSlideUpX"},
    "vrgather_vv": {"asm": "vrgather.vv", "sched_write": "WriteVRGatherVV"},
    "vredsum_vs": {"asm": "vredsum.vs", "sched_write": "WriteVIRedV_From"},
}

LMUL_FACTORS = {"m1": 1, "m2": 2, "m4": 4}
COMMON_TEMPLATES = {
    "T00_BASELINE_MARKER",
    "T01_DECODE_EXEC_KILLCHECK",
    "T40_COMMON_VLSU_LOAD_HIT",
}
DEFAULT_PATHS_CONFIG = Path("config/paths.yaml")
DEFAULT_CPU_CLOCK = "1GHz"
GEM5_TICKS_PER_CYCLE_1GHZ = 1000
MARKER_RE = re.compile(r"^\s*TIMESTAMP_MARK\s+([A-Za-z0-9_.$-]+)\s*(?:#.*)?$")
EXEC_PC_RE = re.compile(r"^\s*(?P<tick>\d+):.*?\b0x(?P<pc>[0-9a-fA-F]+)\b")


class ExperimentError(RuntimeError):
    """Raised when experiment metadata cannot be consumed."""


def _strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char == "#":
            return line[:index]
    return line


def _split_top_level(value: str, separator: str = ",") -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            current.append(char)
            quote = char
            continue
        if char in "[{(":
            depth += 1
            current.append(char)
            continue
        if char in "]})":
            depth -= 1
            current.append(char)
            continue
        if char == separator and depth == 0:
            pieces.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        pieces.append(tail)
    return pieces


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item) for item in _split_top_level(inner)]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for item in _split_top_level(inner):
            if ":" not in item:
                raise ExperimentError(f"cannot parse YAML flow mapping item: {item}")
            key, raw = item.split(":", 1)
            result[key.strip().strip("'\"")] = _parse_scalar(raw)
        return result
    try:
        return int(value, 10)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _sequence_item_text(text: str) -> str | None:
    if text == "-":
        return ""
    if text.startswith("- "):
        return text[2:].strip()
    return None


def _parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    if lines[index][0] < indent:
        return {}, index
    if lines[index][0] == indent and lines[index][1] in {"{}", "[]"}:
        return _parse_scalar(lines[index][1]), index + 1
    if _sequence_item_text(lines[index][1]) is not None:
        items: list[Any] = []
        while index < len(lines):
            line_indent, text = lines[index]
            item_text = _sequence_item_text(text)
            if line_indent != indent or item_text is None:
                break
            index += 1
            if not item_text:
                if index < len(lines) and lines[index][0] > indent:
                    item, index = _parse_yaml_block(lines, index, lines[index][0])
                else:
                    item = None
                items.append(item)
                continue
            if ":" in item_text and not item_text.startswith(("{", "[")):
                key, raw = item_text.split(":", 1)
                item_map: dict[str, Any] = {}
                item_map[key.strip()] = _parse_scalar(raw) if raw.strip() else None
                if index < len(lines) and lines[index][0] > indent:
                    child, index = _parse_yaml_block(lines, index, lines[index][0])
                    if isinstance(child, dict):
                        item_map.update(child)
                    else:
                        item_map[key.strip()] = child
                items.append(item_map)
            else:
                items.append(_parse_scalar(item_text))
        return items, index

    mapping: dict[str, Any] = {}
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent != indent or _sequence_item_text(text) is not None:
            break
        if ":" not in text:
            raise ExperimentError(f"cannot parse YAML line: {text}")
        key, raw = text.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        index += 1
        if raw:
            mapping[key] = _parse_scalar(raw)
            continue
        if index < len(lines) and lines[index][0] > indent:
            mapping[key], index = _parse_yaml_block(lines, index, lines[index][0])
        else:
            mapping[key] = None
    return mapping, index


def parse_simple_yaml(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped_comment = _strip_yaml_comment(raw).rstrip()
        if not stripped_comment.strip():
            continue
        indent = len(stripped_comment) - len(stripped_comment.lstrip(" "))
        if "\t" in stripped_comment[:indent]:
            raise ExperimentError("tabs are not supported in YAML indentation")
        lines.append((indent, stripped_comment.strip()))
    if not lines:
        return {}
    parsed, index = _parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ExperimentError(f"unparsed YAML content near: {lines[index][1]}")
    return parsed


def load_structured_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return parse_simple_yaml(text)


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list) and all(not isinstance(item, (dict, list)) for item in value):
        return "[" + ", ".join(_format_scalar(item) for item in value) + "]"
    text = str(value)
    if text == "" or any(char in text for char in ":#[]{}," ) or text.strip() != text:
        return json.dumps(text)
    lowered = text.lower()
    if lowered in {"null", "true", "false", "~"}:
        return json.dumps(text)
    return text


def dump_simple_yaml(data: Any, indent: int = 0) -> str:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        if not data:
            return f"{prefix}{{}}"
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(dump_simple_yaml(value, indent + 2))
            elif isinstance(value, list) and any(isinstance(item, (dict, list)) for item in value):
                lines.append(f"{prefix}{key}:")
                lines.append(dump_simple_yaml(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{prefix}[]"
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.append(dump_simple_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.append(dump_simple_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_format_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{_format_scalar(data)}"


def load_timing_model(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"instructions": {}}
    data = load_structured_file(path)
    if not isinstance(data, dict):
        raise ExperimentError(f"timing model must be a mapping: {path}")
    instructions = data.get("instructions")
    if not isinstance(instructions, dict):
        raise ExperimentError(f"timing model missing instructions mapping: {path}")
    return data


def load_paths_config(path: Path = DEFAULT_PATHS_CONFIG) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = load_structured_file(path)
    if not isinstance(data, dict):
        raise ExperimentError(f"paths config must be a mapping: {path}")
    return data


def is_bare_executable_name(value: str) -> bool:
    has_separator = os.sep in value or (os.altsep is not None and os.altsep in value)
    return not has_separator and not value.startswith(".")


def resolve_config_path(config: dict[str, Any], key: str, *, search_path: bool = False) -> Path:
    value = config.get(key)
    if not value:
        raise ExperimentError(f"missing `{key}` in {DEFAULT_PATHS_CONFIG}")
    expanded = os.path.expandvars(os.path.expanduser(str(value)))
    if search_path and is_bare_executable_name(expanded):
        discovered = shutil.which(expanded)
        if discovered:
            return Path(discovered)
    path = Path(expanded)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def require_executable(config: dict[str, Any], key: str) -> Path:
    path = resolve_config_path(config, key, search_path=True)
    if not path.exists() or not os.access(path, os.X_OK):
        raise ExperimentError(f"`{key}` is not an executable path: {path}")
    return path


def marker_symbol(label: str, index: int | None = None) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", label)
    if not safe or safe[0].isdigit():
        safe = f"m_{safe}"
    suffix = "" if index is None else f"_{index}"
    return f"__prof_marker_{safe}{suffix}"


def metadata_marker_specs(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    raw_markers = metadata.get("marker_metadata")
    if raw_markers is None:
        experiment = metadata.get("experiment")
        if isinstance(experiment, dict):
            experiment_markers = experiment.get("markers")
            if isinstance(experiment_markers, list) and any(
                isinstance(item, dict) and item.get("symbol") for item in experiment_markers
            ):
                raw_markers = experiment_markers
    if raw_markers is None:
        raw_markers = metadata.get("markers")
    if raw_markers is None:
        experiment = metadata.get("experiment")
        if isinstance(experiment, dict):
            raw_markers = experiment.get("markers")
    specs: list[dict[str, Any]] = []
    if isinstance(raw_markers, list):
        for index, item in enumerate(raw_markers):
            if isinstance(item, dict):
                label = item.get("label") or item.get("marker") or item.get("name")
                if label is None:
                    continue
                specs.append(
                    {
                        "label": str(label),
                        "symbol": str(item.get("symbol") or marker_symbol(str(label), index)),
                        "zero_cost": bool(item.get("zero_cost", True)),
                        "occupies_issue_slot": bool(item.get("occupies_issue_slot", False)),
                    }
                )
            elif item is not None:
                label = str(item)
                specs.append(
                    {
                        "label": label,
                        "symbol": marker_symbol(label, index),
                        "zero_cost": True,
                        "occupies_issue_slot": False,
                    }
                )
    if specs:
        return specs
    return [
        {
            "label": label,
            "symbol": marker_symbol(label, index),
            "zero_cost": True,
            "occupies_issue_slot": False,
        }
        for index, label in enumerate(marker_labels(metadata))
    ]


def lower_timestamp_markers(source_text: str, metadata: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Replace TIMESTAMP_MARK pseudo lines with assembler-visible labels.

    The label itself emits no instruction.  gem5 marker extraction maps the
    label address to the first executed instruction at that PC, so adjacent
    markers naturally share a cycle and validate the zero-cost baseline.
    """

    marker_specs: list[dict[str, Any]] = []
    lowered_lines: list[str] = []
    seen: dict[str, int] = {}
    for raw_line in source_text.splitlines():
        match = MARKER_RE.match(raw_line)
        if not match:
            lowered_lines.append(raw_line)
            continue
        label = match.group(1)
        ordinal = seen.get(label, 0)
        seen[label] = ordinal + 1
        symbol = marker_symbol(label, None if ordinal == 0 else ordinal)
        marker_specs.append(
            {
                "label": label,
                "symbol": symbol,
                "zero_cost": True,
                "occupies_issue_slot": False,
            }
        )
        lowered_lines.extend(
            [
                f"    .globl {symbol}",
                f"{symbol}:",
                f"    # zero-cost TIMESTAMP_MARK {label}",
            ]
        )
    if not marker_specs:
        marker_specs = metadata_marker_specs(metadata)
    return "\n".join(lowered_lines).rstrip() + "\n", marker_specs


def run_command(argv: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExperimentError(f"command timed out after {timeout}s: {' '.join(argv)}") from exc


def checked_command(argv: list[str], *, cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = run_command(argv, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()
        raise ExperimentError(f"command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
    return result


def assemble_and_link(
    *,
    source_dir: Path,
    metadata: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    config = load_paths_config()
    assembler = require_executable(config, "assembler")
    linker = require_executable(config, "linker")
    source_path = source_dir / "test.s"
    if not source_path.exists():
        raise ExperimentError(f"missing source assembly: {source_path}")

    build_dir = output_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    lowered_text, marker_specs = lower_timestamp_markers(source_path.read_text(encoding="utf-8"), metadata)
    lowered_path = build_dir / "test.lowered.s"
    object_path = build_dir / "test.o"
    elf_path = build_dir / "test.elf"
    lowered_path.write_text(lowered_text, encoding="utf-8")

    assemble = checked_command(
        [
            str(assembler),
            "-triple=riscv64",
            "-mattr=+v,+zvl128b",
            "-filetype=obj",
            str(lowered_path),
            "-o",
            str(object_path),
        ],
        timeout=60,
    )
    link = checked_command(
        [
            str(linker),
            "-m",
            "elf64lriscv",
            "--no-relax",
            "-Ttext=0x80000000",
            "-o",
            str(elf_path),
            str(object_path),
        ],
        timeout=60,
    )
    build = {
        "lowered_assembly": str(lowered_path),
        "object": str(object_path),
        "elf": str(elf_path),
        "assembler": str(assembler),
        "linker": str(linker),
        "assemble_returncode": assemble.returncode,
        "link_returncode": link.returncode,
    }
    return elf_path, marker_specs, build


def marker_addresses(elf_path: Path, marker_specs: list[dict[str, Any]]) -> dict[str, int]:
    config = load_paths_config()
    nm = resolve_config_path(config, "llvm_nm") if config.get("llvm_nm") else None
    if nm is None:
        assembler = resolve_config_path(config, "assembler")
        nm = assembler.with_name("llvm-nm")
    if not nm.exists():
        raise ExperimentError(f"cannot find llvm-nm next to assembler: {nm}")
    result = checked_command([str(nm), "-n", str(elf_path)], timeout=60)
    wanted = {str(item["symbol"]): str(item["label"]) for item in marker_specs}
    addresses: dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        address_text, _kind, symbol = parts[0], parts[1], parts[2]
        if symbol not in wanted:
            continue
        addresses[wanted[symbol]] = int(address_text, 16)
    missing = [item["label"] for item in marker_specs if str(item["label"]) not in addresses]
    if missing:
        raise ExperimentError(f"linked ELF is missing marker symbols: {', '.join(missing)}")
    return addresses


def parse_exec_cycles(exec_log: Path, addresses: dict[str, int]) -> tuple[list[dict[str, Any]], list[str]]:
    address_to_labels: dict[int, list[str]] = {}
    for label, address in addresses.items():
        address_to_labels.setdefault(address, []).append(label)
    first_cycle_by_pc: dict[int, tuple[int, int]] = {}
    warnings: list[str] = []
    for raw in exec_log.read_text(encoding="utf-8", errors="replace").splitlines():
        match = EXEC_PC_RE.match(raw)
        if not match:
            continue
        tick = int(match.group("tick"))
        pc = int(match.group("pc"), 16)
        first_cycle_by_pc.setdefault(pc, (tick // GEM5_TICKS_PER_CYCLE_1GHZ, tick))
    entries: list[dict[str, Any]] = []
    for label, address in addresses.items():
        cycle_tick = first_cycle_by_pc.get(address)
        if cycle_tick is None:
            warnings.append(f"marker {label} at 0x{address:x} was not observed in Exec trace")
            continue
        cycle, tick = cycle_tick
        entries.append(
            {
                "marker": label,
                "cycle": cycle,
                "tick": tick,
                "pc": f"0x{address:x}",
            }
        )
    return entries, warnings


def run_gem5_minor_trace(
    *,
    metadata: dict[str, Any],
    output_dir: Path,
    source_dir: Path,
    repeat_index: int | None = None,
) -> dict[str, Any]:
    config = load_paths_config()
    gem5 = require_executable(config, "gem5_build")
    gem5_checkout = resolve_config_path(config, "gem5_checkout")
    se_config = gem5_checkout / "configs" / "deprecated" / "example" / "se.py"
    if not se_config.exists():
        raise ExperimentError(f"missing gem5 se.py config: {se_config}")

    elf_path, marker_specs, build = assemble_and_link(
        source_dir=source_dir,
        metadata=metadata,
        output_dir=output_dir,
    )
    addresses = marker_addresses(elf_path, marker_specs)
    gem5_out = output_dir / "gem5"
    gem5_out.mkdir(parents=True, exist_ok=True)
    debug_file = "exec.log"
    argv = [
        str(gem5),
        "--outdir",
        str(gem5_out),
        "--debug-flags=Exec",
        "--debug-file",
        debug_file,
        str(se_config),
        "--cpu-type=RiscvMinorCPU",
        "--caches",
        "--cpu-clock",
        DEFAULT_CPU_CLOCK,
        "--sys-clock",
        DEFAULT_CPU_CLOCK,
        "--mem-size",
        "512MiB",
        "--cmd",
        str(elf_path),
    ]
    result = checked_command(argv, timeout=180)
    exec_log = gem5_out / debug_file
    if not exec_log.exists():
        raise ExperimentError(f"gem5 did not write Exec log: {exec_log}")
    entries, warnings = parse_exec_cycles(exec_log, addresses)
    expected_labels = [str(item["label"]) for item in marker_specs]
    observed_labels = {str(item["marker"]) for item in entries}
    missing = [label for label in expected_labels if label not in observed_labels]
    if missing:
        raise ExperimentError(f"gem5 trace missing marker observations: {', '.join(missing)}")

    trace = {
        "schema_version": 1,
        "experiment_id": experiment_id(metadata),
        "template_id": metadata_template_id(metadata),
        "result_group": result_group(metadata),
        "instruction_id": get_instruction_id(metadata),
        "lmul": get_lmul(metadata),
        "mode": "real_platform_profile",
        "backend": "gem5_minor",
        "dry_run_trace": False,
        "marker_baseline_cycles": 0,
        "timestamp_model": {
            "kind": "zero_cost_label_marker",
            "occupies_issue_slot": False,
            "cycles": 0,
        },
        "build": build,
        "gem5": {
            "command": argv,
            "returncode": result.returncode,
            "stdout": result.stdout.splitlines()[-20:],
            "stderr": result.stderr.splitlines()[-40:],
            "outdir": str(gem5_out),
            "exec_log": str(exec_log),
            "cpu_type": "RiscvMinorCPU",
            "clock": DEFAULT_CPU_CLOCK,
            "ticks_per_cycle": GEM5_TICKS_PER_CYCLE_1GHZ,
        },
        "markers": marker_specs,
        "marker_addresses": {label: f"0x{addr:x}" for label, addr in addresses.items()},
        "warnings": warnings,
        "entries": entries,
    }
    if repeat_index is not None:
        trace["repeat_index"] = repeat_index
    return trace


def resolve_experiment_dir(experiment: str, generated_root: Path) -> Path:
    candidate = Path(experiment)
    if (candidate / "experiment.yaml").exists():
        return candidate
    generated = generated_root / experiment
    if (generated / "experiment.yaml").exists():
        return generated
    raise ExperimentError(
        f"cannot find experiment metadata for {experiment!r}; expected "
        f"{candidate / 'experiment.yaml'} or {generated / 'experiment.yaml'}"
    )


def load_experiment_metadata(source_dir: Path) -> tuple[dict[str, Any], str]:
    metadata_path = source_dir / "experiment.yaml"
    raw_text = metadata_path.read_text(encoding="utf-8")
    data = load_structured_file(metadata_path)
    if not isinstance(data, dict):
        raise ExperimentError(f"experiment metadata must be a mapping: {metadata_path}")
    return normalize_experiment_metadata(data), raw_text


def metadata_template_id(metadata: dict[str, Any]) -> str:
    value = metadata.get("template_id")
    if value:
        return str(value)
    experiment = metadata.get("experiment")
    if isinstance(experiment, dict) and experiment.get("template_id"):
        return str(experiment["template_id"])
    raise ExperimentError("experiment metadata missing template_id")


def metadata_experiment_id(metadata: dict[str, Any]) -> str:
    value = metadata.get("experiment_id") or metadata.get("id")
    if value:
        return str(value)
    experiment = metadata.get("experiment")
    if isinstance(experiment, dict) and experiment.get("id"):
        return str(experiment["id"])
    raise ExperimentError("experiment metadata missing experiment_id")


def _raw_marker_labels(metadata: dict[str, Any]) -> list[str]:
    raw_markers = metadata.get("markers") or metadata.get("marker_labels")
    if raw_markers is None:
        experiment = metadata.get("experiment")
        if isinstance(experiment, dict):
            raw_markers = experiment.get("markers")
    labels: list[str] = []
    if isinstance(raw_markers, list):
        for item in raw_markers:
            if isinstance(item, dict):
                value = item.get("label") or item.get("marker") or item.get("name")
                if value is not None:
                    labels.append(str(value))
            elif item is not None:
                labels.append(str(item))
    elif isinstance(raw_markers, str):
        labels = [part.strip() for part in raw_markers.split(",") if part.strip()]
    return labels


def normalize_experiment_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    template = metadata_template_id(metadata)
    exp_id = metadata_experiment_id(metadata)
    instruction = metadata.get("instruction")
    instruction_id = metadata.get("instruction_id")
    if not instruction_id and isinstance(instruction, dict):
        instruction_id = instruction.get("id")
    parameters = metadata.get("parameters")
    lmul = metadata.get("lmul")
    if lmul is None and isinstance(parameters, dict):
        lmul = parameters.get("lmul")
    sew = metadata.get("sew")
    if sew is None and isinstance(parameters, dict):
        sew = parameters.get("sew")
    markers = _raw_marker_labels(metadata) or default_markers(template)
    group = metadata.get("result_group")
    if not group:
        group = "common" if template in COMMON_TEMPLATES else instruction_id or "common"

    normalized: dict[str, Any] = {
        "schema_version": metadata.get("schema_version", 1),
        "experiment_id": exp_id,
        "template_id": template,
        "result_group": str(group),
        "instruction_id": str(instruction_id) if instruction_id else None,
        "lmul": str(lmul) if lmul else None,
        "sew": sew,
        "markers": markers,
    }
    for key, value in metadata.items():
        if key not in normalized:
            normalized[key] = value
    return normalized


def get_instruction_id(metadata: dict[str, Any]) -> str | None:
    value = metadata.get("instruction_id")
    if value:
        return str(value)
    instruction = metadata.get("instruction")
    if isinstance(instruction, dict):
        value = instruction.get("id")
        if value:
            return str(value)
    return None


def get_lmul(metadata: dict[str, Any]) -> str:
    value = metadata.get("lmul")
    if value:
        return str(value)
    parameters = metadata.get("parameters")
    if isinstance(parameters, dict) and parameters.get("lmul"):
        return str(parameters["lmul"])
    instruction = metadata.get("instruction")
    if isinstance(instruction, dict) and instruction.get("lmul"):
        return str(instruction["lmul"])
    return "m1"


def default_markers(template_id: str) -> list[str]:
    if template_id == "T00_BASELINE_MARKER":
        return ["t0", "t1"]
    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return ["before", "after", "program_end"]
    return ["start", "end"]


def marker_labels(metadata: dict[str, Any]) -> list[str]:
    labels = _raw_marker_labels(metadata)
    if labels:
        return labels
    return default_markers(metadata_template_id(metadata))


def result_group(metadata: dict[str, Any]) -> str:
    explicit = metadata.get("result_group")
    if explicit:
        return str(explicit)
    template_id = metadata_template_id(metadata)
    if template_id in COMMON_TEMPLATES:
        return "common"
    instruction_id = get_instruction_id(metadata)
    return instruction_id or "common"


def experiment_id(metadata: dict[str, Any]) -> str:
    return metadata_experiment_id(metadata)


def body_value(metadata: dict[str, Any], key: str, default: Any = None) -> Any:
    body = metadata.get("body")
    if isinstance(body, dict) and key in body:
        return body[key]
    return metadata.get(key, default)


def _instruction_timing(
    metadata: dict[str, Any], timing_model: dict[str, Any]
) -> tuple[int, int, dict[str, Any], bool]:
    instruction_id = get_instruction_id(metadata)
    return _instruction_timing_by_id(instruction_id, get_lmul(metadata), timing_model)


def _instruction_timing_by_id(
    instruction_id: str | None, lmul: str, timing_model: dict[str, Any]
) -> tuple[int, int, dict[str, Any], bool]:
    factor = LMUL_FACTORS.get(lmul)
    if factor is None:
        raise ExperimentError(f"unsupported LMUL {lmul!r}; expected one of {sorted(LMUL_FACTORS)}")
    params = {}
    found = False
    if instruction_id:
        raw = timing_model.get("instructions", {}).get(instruction_id, {})
        if isinstance(raw, dict):
            params = raw
            found = bool(raw)
    latency = int(params.get("latency_base", 1)) + int(params.get("latency_lmul_k", 0)) * factor
    release = int(params.get("release_base", 1)) + int(params.get("release_lmul_k", 0)) * factor
    return latency, release, params, found


def pair_instruction_id(metadata: dict[str, Any]) -> str | None:
    pair = metadata.get("pair_instruction")
    if isinstance(pair, dict) and pair.get("id"):
        return str(pair["id"])
    body = metadata.get("body")
    if isinstance(body, dict):
        instances = body.get("instances")
        if isinstance(instances, list):
            for item in instances:
                if isinstance(item, dict) and item.get("side") == "B" and item.get("instruction"):
                    return str(item["instruction"])
    return None


def pair_delta_cycles(metadata: dict[str, Any], timing_model: dict[str, Any]) -> int:
    lmul = get_lmul(metadata)
    instr_a = get_instruction_id(metadata)
    instr_b = pair_instruction_id(metadata)
    _lat_a, rel_a, params_a, _found_a = _instruction_timing_by_id(instr_a, lmul, timing_model)
    _lat_b, rel_b, params_b, _found_b = _instruction_timing_by_id(instr_b, lmul, timing_model)
    pipe_a = str(params_a.get("pipe") or "any")
    pipe_b = str(params_b.get("pipe") or "any")
    iterations = int(body_value(metadata, "iterations", body_value(metadata, "pair_count", 4)))
    if pipe_a == pipe_b and pipe_a in {"pipe0", "pipe1"}:
        pair_release = rel_a + rel_b
    else:
        pair_release = max(rel_a, rel_b)
    return iterations * max(1, pair_release)


def synthetic_delta_cycles(metadata: dict[str, Any], timing_model: dict[str, Any]) -> int:
    template_id = metadata_template_id(metadata)
    latency, release, _, _ = _instruction_timing(metadata, timing_model)
    if template_id == "T00_BASELINE_MARKER":
        return 0
    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return max(1, latency)
    if template_id == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        return int(body_value(metadata, "iterations", body_value(metadata, "stream_length", 6))) * max(1, release)
    if template_id == "T11_SELF_RAW_CHAIN":
        return int(body_value(metadata, "iterations", body_value(metadata, "chain_length", 6))) * max(1, latency)
    if template_id == "T12_CONSUMER_RAW_GAP":
        return max(1, latency) + int(body_value(metadata, "filler_count", 0) or 0)
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        return pair_delta_cycles(metadata, timing_model)
    if template_id == "T21_PAIR_WITH_SCALAR":
        return int(body_value(metadata, "iterations", body_value(metadata, "pair_count", 4))) * max(1, release)
    if template_id == "T30_LMUL_SCALING":
        scaling = metadata.get("scaling")
        shape = scaling.get("shape") if isinstance(scaling, dict) else None
        if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
            return int(body_value(metadata, "iterations", body_value(metadata, "sample_count", 6))) * max(1, release)
        if shape == "T12_CONSUMER_RAW_GAP":
            return max(1, latency) + int(body_value(metadata, "filler_count", 0) or 0)
        return int(body_value(metadata, "iterations", body_value(metadata, "sample_count", 6))) * max(1, latency)
    if template_id == "T40_COMMON_VLSU_LOAD_HIT":
        return max(1, latency + release)
    return max(1, latency)


def build_synthetic_trace(
    metadata: dict[str, Any],
    timing_model: dict[str, Any],
    timing_model_path: Path,
    *,
    mode: str,
    dry_run: bool,
    repeat_index: int | None = None,
) -> dict[str, Any]:
    labels = marker_labels(metadata)
    delta = synthetic_delta_cycles(metadata, timing_model)
    base_cycle = int(metadata.get("synthetic_base_cycle") or 1000)
    if len(labels) <= 1:
        cycles = [base_cycle]
    elif len(labels) == 2:
        cycles = [base_cycle, base_cycle + delta]
    else:
        cycles = [base_cycle]
        for index in range(1, len(labels) - 1):
            cycles.append(base_cycle + delta)
        cycles.append(base_cycle + delta)

    exp_id = experiment_id(metadata)
    entries = []
    for index, (label, cycle) in enumerate(zip(labels, cycles)):
        entries.append(
            {
                "marker": label,
                "cycle": cycle,
                "pc": f"0x{0x80000000 + index * 4:08x}",
                "experiment_id": exp_id,
            }
        )

    latency, release, params, found = _instruction_timing(metadata, timing_model)
    backend = "synthetic_cmodel"
    observation: dict[str, Any] = {
        "source": "synthetic_cmodel_raw_marker_cycles",
        "primary_delta_cycles": delta,
        "template_id": metadata_template_id(metadata),
        "instruction_id": get_instruction_id(metadata),
        "lmul": get_lmul(metadata),
        "iterations": body_value(metadata, "iterations", body_value(metadata, "stream_length", None)),
        "filler_count": body_value(metadata, "filler_count", None),
        "pair_instruction_id": pair_instruction_id(metadata),
    }
    trace = {
        "schema_version": 1,
        "experiment_id": exp_id,
        "template_id": metadata_template_id(metadata),
        "result_group": result_group(metadata),
        "instruction_id": get_instruction_id(metadata),
        "lmul": get_lmul(metadata),
        "mode": "dry_run" if dry_run else mode,
        "backend": backend,
        "dry_run_trace": bool(dry_run),
        "marker_baseline_cycles": 0,
        "timestamp_model": {
            "kind": "zero_cost_marker",
            "occupies_issue_slot": False,
            "cycles": 0,
        },
        "inference_source": "raw_marker_cycles",
        "observation": observation,
        "synthetic": {
            "backend": backend,
            "role": "ground_truth_for_post_inference_mismatch_only",
            "timing_model": str(timing_model_path),
            "timing_model_mode": timing_model.get("mode"),
            "instruction_id": get_instruction_id(metadata),
            "lmul": get_lmul(metadata),
            "timing_model_entry_found": found,
            "pipe": params.get("pipe"),
            "latency_cycles": latency,
            "release_cycles": release,
            "configured": {
                "pipe": params.get("pipe"),
                "latency_base": params.get("latency_base"),
                "latency_lmul_k": params.get("latency_lmul_k"),
                "release_base": params.get("release_base"),
                "release_lmul_k": params.get("release_lmul_k"),
            },
            "measured_delta_cycles": delta,
        },
        "entries": entries,
    }
    if repeat_index is not None:
        trace["repeat_index"] = repeat_index
    return trace


def placeholder_assembly(metadata: dict[str, Any]) -> str:
    instruction_id = get_instruction_id(metadata) or "unknown"
    asm = INSTRUCTION_SET.get(instruction_id, {}).get("asm", instruction_id)
    template_id = str(metadata.get("template_id") or "UNKNOWN")
    lmul = get_lmul(metadata)
    comments = [
        "# Synthetic placeholder produced by scripts/run_experiment.py --dry-run.",
        f"# experiment_id: {experiment_id(metadata)}",
        f"# template_id: {template_id}",
        f"# instruction: {instruction_id}",
        f"# asm: {asm}",
        f"# lmul: {lmul}",
        "# Real assembly should be supplied by Phase 5 under experiments/generated/<id>/test.s.",
    ]
    return "\n".join(comments) + "\n"


def write_result_files(
    metadata: dict[str, Any],
    output_dir: Path,
    source_dir: Path | None,
    trace: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "experiment.yaml").write_text(dump_simple_yaml(metadata) + "\n", encoding="utf-8")

    source_test = source_dir / "test.s" if source_dir else None
    if source_test and source_test.exists():
        shutil.copyfile(source_test, output_dir / "test.s")
    else:
        (output_dir / "test.s").write_text(placeholder_assembly(metadata), encoding="utf-8")

    (output_dir / "trace.json").write_text(
        json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run_experiment_from_metadata(
    metadata: dict[str, Any],
    *,
    dry_run: bool,
    results_root: Path,
    timing_model_path: Path,
    mode: str = "synthetic_calibration",
    backend: str = "auto",
    source_dir: Path | None = None,
    repeat_index: int | None = None,
) -> Path:
    metadata = normalize_experiment_metadata(metadata)
    exp_id = experiment_id(metadata)
    timing_model = load_timing_model(timing_model_path)
    group = result_group(metadata)
    output_dir = results_root / group / "experiments" / exp_id
    if backend == "auto":
        backend = "gem5_minor" if mode == "real_platform_profile" and not dry_run else "synthetic_cmodel"
    if dry_run:
        trace = build_synthetic_trace(
            metadata,
            timing_model,
            timing_model_path,
            mode=mode,
            dry_run=dry_run,
            repeat_index=repeat_index,
        )
        write_result_files(metadata, output_dir, source_dir, trace)
        return output_dir
    if backend == "gem5_minor":
        if source_dir is None:
            raise ExperimentError("gem5_minor backend requires a source experiment directory")
        trace = run_gem5_minor_trace(
            metadata=metadata,
            output_dir=output_dir,
            source_dir=source_dir,
            repeat_index=repeat_index,
        )
        write_result_files(metadata, output_dir, source_dir, trace)
        return output_dir
    if backend != "synthetic_cmodel":
        raise ExperimentError(f"unsupported backend {backend!r}")
    if mode == "real_platform_profile":
        raise ExperimentError("real_platform_profile requires --backend gem5_minor")
    if mode != "synthetic_calibration":
        raise ExperimentError(f"unsupported mode {mode!r}")
    trace = build_synthetic_trace(
        metadata,
        timing_model,
        timing_model_path,
        mode=mode,
        dry_run=dry_run,
        repeat_index=repeat_index,
    )
    write_result_files(metadata, output_dir, source_dir, trace)
    return output_dir


def run_experiment_dir(
    source_dir: Path,
    *,
    dry_run: bool,
    results_root: Path,
    timing_model_path: Path,
    mode: str = "synthetic_calibration",
    backend: str = "auto",
    repeat_index: int | None = None,
) -> Path:
    metadata, metadata_text = load_experiment_metadata(source_dir)
    return run_experiment_from_metadata(
        metadata,
        dry_run=dry_run,
        results_root=results_root,
        timing_model_path=timing_model_path,
        mode=mode,
        backend=backend,
        source_dir=source_dir,
        repeat_index=repeat_index,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "experiment",
        help="Experiment id under experiments/generated/ or a directory containing experiment.yaml",
    )
    parser.add_argument("--dry-run", action="store_true", help="write a deterministic synthetic trace")
    parser.add_argument(
        "--mode",
        choices=("synthetic_calibration", "real_platform_profile"),
        default="synthetic_calibration",
        help="execution mode; synthetic_calibration uses the stdlib synthetic cmodel",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "synthetic_cmodel", "gem5_minor"),
        default="auto",
        help="execution backend; auto selects synthetic for calibration and gem5 for real-platform mode",
    )
    parser.add_argument(
        "--generated-root",
        type=Path,
        default=Path("experiments/generated"),
        help="root containing generated experiment directories",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results"),
        help="root where normalized experiment results are written",
    )
    parser.add_argument(
        "--timing-model",
        type=Path,
        default=Path("config/rvv_timing_model.yaml"),
        help="RVV timing model used for dry-run synthetic traces",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        source_dir = resolve_experiment_dir(args.experiment, args.generated_root)
        output_dir = run_experiment_dir(
            source_dir,
            dry_run=args.dry_run,
            results_root=args.results_root,
            timing_model_path=args.timing_model,
            mode=args.mode,
            backend=args.backend,
        )
    except ExperimentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
