#!/usr/bin/env python3
"""Run one generated RVV profiling experiment.

This is the Phase 6 runner interface.  It is intentionally stdlib-only so it
can run before the gem5 patch stack and Python dependencies are settled.
"""

from __future__ import annotations

import argparse
import json
import shutil
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
    return data, raw_text


def get_instruction_id(metadata: dict[str, Any]) -> str | None:
    instruction = metadata.get("instruction")
    if isinstance(instruction, dict):
        value = instruction.get("id")
        if value:
            return str(value)
    value = metadata.get("instruction_id")
    return str(value) if value else None


def get_lmul(metadata: dict[str, Any]) -> str:
    instruction = metadata.get("instruction")
    if isinstance(instruction, dict) and instruction.get("lmul"):
        return str(instruction["lmul"])
    return str(metadata.get("lmul") or "m1")


def default_markers(template_id: str) -> list[str]:
    if template_id == "T00_BASELINE_MARKER":
        return ["t0", "t1"]
    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return ["before", "after", "program_end"]
    return ["start", "end"]


def marker_labels(metadata: dict[str, Any]) -> list[str]:
    raw_markers = metadata.get("markers") or metadata.get("marker_labels")
    labels: list[str] = []
    if isinstance(raw_markers, list):
        for item in raw_markers:
            if isinstance(item, dict) and item.get("marker"):
                labels.append(str(item["marker"]))
            elif item is not None:
                labels.append(str(item))
    elif isinstance(raw_markers, str):
        labels = [part.strip() for part in raw_markers.split(",") if part.strip()]
    if labels:
        return labels
    return default_markers(str(metadata.get("template_id") or "UNKNOWN"))


def result_group(metadata: dict[str, Any]) -> str:
    explicit = metadata.get("result_group")
    if explicit:
        return str(explicit)
    template_id = str(metadata.get("template_id") or "")
    if template_id in COMMON_TEMPLATES:
        return "common"
    instruction_id = get_instruction_id(metadata)
    return instruction_id or "common"


def experiment_id(metadata: dict[str, Any]) -> str:
    value = metadata.get("experiment_id") or metadata.get("id")
    if not value:
        raise ExperimentError("experiment metadata missing experiment_id")
    return str(value)


def _instruction_timing(
    metadata: dict[str, Any], timing_model: dict[str, Any]
) -> tuple[int, int, dict[str, Any]]:
    instruction_id = get_instruction_id(metadata)
    lmul = get_lmul(metadata)
    factor = LMUL_FACTORS.get(lmul)
    if factor is None:
        raise ExperimentError(f"unsupported LMUL {lmul!r}; expected one of {sorted(LMUL_FACTORS)}")
    params = {}
    if instruction_id:
        raw = timing_model.get("instructions", {}).get(instruction_id, {})
        if isinstance(raw, dict):
            params = raw
    latency = int(params.get("latency_base", 1)) + int(params.get("latency_lmul_k", 0)) * factor
    release = int(params.get("release_base", 1)) + int(params.get("release_lmul_k", 0)) * factor
    return latency, release, params


def synthetic_delta_cycles(metadata: dict[str, Any], timing_model: dict[str, Any]) -> int:
    template_id = str(metadata.get("template_id") or "")
    latency, release, _ = _instruction_timing(metadata, timing_model)
    if template_id == "T00_BASELINE_MARKER":
        return 0
    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return max(1, latency)
    if template_id == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        return int(metadata.get("stream_length") or 6) * max(1, release)
    if template_id == "T11_SELF_RAW_CHAIN":
        return int(metadata.get("chain_length") or 6) * max(1, latency)
    if template_id == "T12_CONSUMER_RAW_GAP":
        return max(1, latency) + int(metadata.get("filler_count") or 0)
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        return int(metadata.get("pair_count") or 4) * max(1, release)
    if template_id == "T21_PAIR_WITH_SCALAR":
        return int(metadata.get("pair_count") or 4) * max(1, release)
    if template_id == "T30_LMUL_SCALING":
        return int(metadata.get("sample_count") or 6) * max(1, latency)
    return max(1, latency)


def build_synthetic_trace(
    metadata: dict[str, Any], timing_model: dict[str, Any], timing_model_path: Path
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

    latency, release, params = _instruction_timing(metadata, timing_model)
    return {
        "schema_version": 1,
        "experiment_id": exp_id,
        "template_id": metadata.get("template_id"),
        "mode": "dry_run",
        "marker_baseline_cycles": 0,
        "synthetic": {
            "timing_model": str(timing_model_path),
            "instruction_id": get_instruction_id(metadata),
            "lmul": get_lmul(metadata),
            "pipe": params.get("pipe"),
            "latency_cycles": latency,
            "release_cycles": release,
            "measured_delta_cycles": delta,
        },
        "entries": entries,
    }


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
    metadata_text: str | None,
    source_dir: Path | None,
    trace: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if metadata_text is None:
        metadata_text = dump_simple_yaml(metadata) + "\n"
    (output_dir / "experiment.yaml").write_text(metadata_text, encoding="utf-8")

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
    source_dir: Path | None = None,
    metadata_text: str | None = None,
) -> Path:
    exp_id = experiment_id(metadata)
    timing_model = load_timing_model(timing_model_path)
    group = result_group(metadata)
    output_dir = results_root / group / "experiments" / exp_id
    if not dry_run:
        raise ExperimentError(
            "gem5 execution is not wired yet; rerun with --dry-run until the simulator "
            "marker and timing patches are available"
        )
    trace = build_synthetic_trace(metadata, timing_model, timing_model_path)
    write_result_files(metadata, output_dir, metadata_text, source_dir, trace)
    return output_dir


def run_experiment_dir(
    source_dir: Path, *, dry_run: bool, results_root: Path, timing_model_path: Path
) -> Path:
    metadata, metadata_text = load_experiment_metadata(source_dir)
    return run_experiment_from_metadata(
        metadata,
        dry_run=dry_run,
        results_root=results_root,
        timing_model_path=timing_model_path,
        source_dir=source_dir,
        metadata_text=metadata_text,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "experiment",
        help="Experiment id under experiments/generated/ or a directory containing experiment.yaml",
    )
    parser.add_argument("--dry-run", action="store_true", help="write a deterministic synthetic trace")
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
        )
    except ExperimentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
