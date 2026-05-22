#!/usr/bin/env python3
"""Generate deterministic RVV assembly experiment scaffolding.

The generated programs intentionally include ``TIMESTAMP_MARK <label>`` pseudo
lines. They are consumed by the future runner/simulator layer and are not
expected to assemble before that layer exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Iterable


SEW = 32
VL_VALUE = 64
GENERATOR_VERSION = 1

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("experiments/generated")
DEFAULT_TEMPLATE_PATH = Path("templates/rvv_program.s.tpl")

LMUL_FACTORS = {
    "m1": 1,
    "m2": 2,
    "m4": 4,
}


TEMPLATE_IDS = (
    "T00_BASELINE_MARKER",
    "T01_DECODE_EXEC_KILLCHECK",
    "T10_INDEPENDENT_STREAM_THROUGHPUT",
    "T11_SELF_RAW_CHAIN",
    "T12_CONSUMER_RAW_GAP",
    "T20_PAIRWISE_PIPE_CLASSIFICATION",
    "T21_PAIR_WITH_SCALAR",
    "T30_LMUL_SCALING",
)

T30_SHAPES = (
    "T10_INDEPENDENT_STREAM_THROUGHPUT",
    "T11_SELF_RAW_CHAIN",
    "T12_CONSUMER_RAW_GAP",
)

TEMPLATE_PURPOSES = {
    "T00_BASELINE_MARKER": "Confirm marker read baseline and zero-cost timestamp semantics.",
    "T01_DECODE_EXEC_KILLCHECK": "Prove the selected RVV instruction decodes and reaches program end.",
    "T10_INDEPENDENT_STREAM_THROUGHPUT": "Measure independent stream throughput for resource occupancy.",
    "T11_SELF_RAW_CHAIN": "Measure observable self RAW latency for chainable result paths.",
    "T12_CONSUMER_RAW_GAP": "Sweep independent fillers between producer and consumer.",
    "T20_PAIRWISE_PIPE_CLASSIFICATION": "Classify pairwise RVV pipe affinity.",
    "T21_PAIR_WITH_SCALAR": "Probe scalar pairing, single-issue, and multi-uop behavior.",
    "T30_LMUL_SCALING": "Reuse timing shapes across LMUL values for scaling fits.",
}


@dataclass(frozen=True)
class InstructionSpec:
    instr_id: str
    asm: str
    sched_write: str
    result_kind: str
    chainable: bool
    notes: str


INSTRUCTIONS = {
    "vadd_vv": InstructionSpec(
        "vadd_vv",
        "vadd.vv",
        "WriteVIALUV",
        "vector",
        True,
        "Simple vector integer ALU operation.",
    ),
    "vsll_vv": InstructionSpec(
        "vsll_vv",
        "vsll.vv",
        "WriteVShiftV",
        "vector",
        True,
        "Vector shift using a vector shift-count operand.",
    ),
    "vmul_vv": InstructionSpec(
        "vmul_vv",
        "vmul.vv",
        "WriteVIMulV",
        "vector",
        True,
        "Vector integer multiply.",
    ),
    "vdivu_vv": InstructionSpec(
        "vdivu_vv",
        "vdivu.vv",
        "WriteVIDivV",
        "vector",
        True,
        "Unsigned vector integer divide; inputs avoid zero divisors.",
    ),
    "vmseq_vv": InstructionSpec(
        "vmseq_vv",
        "vmseq.vv",
        "WriteVICmpV",
        "mask",
        False,
        "Vector compare producing a mask result.",
    ),
    "vcpop_m": InstructionSpec(
        "vcpop_m",
        "vcpop.m",
        "WriteVMPopV",
        "scalar",
        False,
        "Mask population count producing a scalar integer result.",
    ),
    "viota_m": InstructionSpec(
        "viota_m",
        "viota.m",
        "WriteVIotaV",
        "vector",
        False,
        "Mask-to-vector prefix index operation.",
    ),
    "vslideup_vx": InstructionSpec(
        "vslideup_vx",
        "vslideup.vx",
        "WriteVSlideUpX",
        "vector",
        True,
        "Vector slide-up with a scalar offset operand.",
    ),
    "vrgather_vv": InstructionSpec(
        "vrgather_vv",
        "vrgather.vv",
        "WriteVRGatherVV",
        "vector",
        True,
        "Vector gather using vector indices.",
    ),
    "vredsum_vs": InstructionSpec(
        "vredsum_vs",
        "vredsum.vs",
        "WriteVIRedV_From",
        "vector",
        True,
        "Vector reduction into a scalar element held in a vector register.",
    ),
}

INSTRUCTION_IDS = tuple(INSTRUCTIONS)


def repo_path(path: Path | str) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def dump_yaml(value: Any, indent: int = 0) -> str:
    spaces = " " * indent
    if isinstance(value, dict):
        if not value:
            return f"{spaces}{{}}"
        lines: list[str] = []
        for key, item in value.items():
            key_text = str(key)
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}{key_text}:")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{spaces}{key_text}: {yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return f"{spaces}[]"
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{spaces}-")
                lines.append(dump_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{spaces}-")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{spaces}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{spaces}{yaml_scalar(value)}"


def write_yaml(path: Path, value: Any) -> None:
    path.write_text(dump_yaml(value) + "\n", encoding="utf-8")


def sanitize_part(part: str) -> str:
    return part.replace("_", "-").replace(".", "-").lower()


def short_template(template_id: str) -> str:
    return template_id.split("_", 1)[0]


def require_instruction(instr_id: str) -> InstructionSpec:
    try:
        return INSTRUCTIONS[instr_id]
    except KeyError as exc:
        valid = ", ".join(INSTRUCTION_IDS)
        raise SystemExit(f"unknown instruction id {instr_id!r}; valid ids: {valid}") from exc


def validate_lmul(lmul: str) -> None:
    if lmul not in LMUL_FACTORS:
        raise SystemExit(f"unknown LMUL {lmul!r}; valid values: {', '.join(LMUL_FACTORS)}")


def aligned_groups(lmul: str) -> list[int]:
    factor = LMUL_FACTORS[lmul]
    return list(range(0, 32, factor))


def vector_reg(index: int) -> str:
    return f"v{index}"


def scalar_reg(index: int) -> str:
    return f"x{index}"


def base_vector_sources(lmul: str) -> tuple[str, str]:
    groups = aligned_groups(lmul)
    return vector_reg(groups[0]), vector_reg(groups[1])


def output_groups(lmul: str) -> list[int]:
    groups = aligned_groups(lmul)
    return groups[2:]


def output_vectors(lmul: str, count: int, *, allow_reuse: bool = False) -> tuple[list[str], bool]:
    groups = output_groups(lmul)
    if count <= len(groups):
        return [vector_reg(group) for group in groups[:count]], False
    if not allow_reuse:
        raise SystemExit(
            f"LMUL {lmul} has {len(groups)} independent output groups, "
            f"but {count} were requested"
        )
    regs = [vector_reg(groups[index % len(groups)]) for index in range(count)]
    return regs, True


def scalar_outputs(count: int, start: int = 10) -> list[str]:
    regs = []
    for index in range(count):
        reg = start + index
        if reg > 31:
            reg = 10 + (index % 22)
        regs.append(scalar_reg(reg))
    return regs


def emit_instruction(
    spec: InstructionSpec,
    *,
    dest: str,
    src_a: str,
    src_b: str,
    scalar: str,
) -> str:
    if spec.instr_id in {"vadd_vv", "vsll_vv", "vmul_vv", "vdivu_vv", "vmseq_vv", "vrgather_vv"}:
        return f"{spec.asm} {dest}, {src_a}, {src_b}"
    if spec.instr_id == "vcpop_m":
        return f"{spec.asm} {dest}, {src_a}"
    if spec.instr_id == "viota_m":
        return f"{spec.asm} {dest}, {src_a}"
    if spec.instr_id == "vslideup_vx":
        return f"{spec.asm} {dest}, {src_a}, {scalar}"
    if spec.instr_id == "vredsum_vs":
        return f"{spec.asm} {dest}, {src_a}, {src_b}"
    raise AssertionError(f"unhandled instruction {spec.instr_id}")


def emit_consumer(result_kind: str, result: str, dest: str, fallback_src: str) -> str:
    if result_kind == "scalar":
        return f"add {dest}, {result}, x0"
    if result_kind == "mask":
        return f"vcpop.m {dest}, {result}"
    return f"vadd.vv {dest}, {result}, {fallback_src}"


def indent_lines(lines: Iterable[str], prefix: str = "    ") -> str:
    return "\n".join(prefix + line if line else "" for line in lines)


def setup_block(lmul: str | None) -> str:
    lines = [
        "# Scalar setup used by vector length and scalar-pair probes.",
        f"li x5, {VL_VALUE}",
        "li x6, 1",
        "li x7, 2",
        "li x20, 20",
        "li x21, 21",
        "li x22, 22",
        "li x23, 23",
        "li x24, 24",
        "li x25, 25",
        "li x26, 26",
        "li x27, 27",
        "li x28, 28",
        "li x29, 29",
        "li x30, 30",
        "li x31, 31",
    ]
    if lmul is None:
        lines.extend(
            [
                "",
                "# No vsetvli is needed for the marker-only baseline.",
            ]
        )
        return indent_lines(lines)

    lines.extend(
        [
            "",
            f"# Fixed first-version vector shape: SEW=e{SEW}, LMUL={lmul}.",
            f"vsetvli x0, x5, e{SEW}, {lmul}, ta, ma",
            "",
            "# Initialize aligned vector groups. Values are simple and non-zero",
            "# where divisor/index operands might otherwise create simulator noise.",
        ]
    )
    for idx, group in enumerate(aligned_groups(lmul)):
        value = (idx % 7) + 1
        lines.append(f"vmv.v.i {vector_reg(group)}, {value}")
    lines.extend(
        [
            "",
            "# Establish a reusable all-true mask input for mask instructions.",
            "vmseq.vi v0, v0, 1",
        ]
    )
    return indent_lines(lines)


def metadata_instruction(spec: InstructionSpec) -> dict[str, Any]:
    return {
        "id": spec.instr_id,
        "asm": spec.asm,
        "llvm_sched_write": spec.sched_write,
        "result_kind": spec.result_kind,
        "chainable": spec.chainable,
        "notes": spec.notes,
    }


def command_argv(args: argparse.Namespace, experiment_id: str | None = None) -> list[str]:
    argv = [
        "python3",
        "scripts/gen_asm.py",
        "one",
        "--template",
        args.template,
    ]
    if getattr(args, "instr", None):
        argv += ["--instr", args.instr]
    if getattr(args, "lmul", None):
        argv += ["--lmul", args.lmul]
    if args.template == "T20_PAIRWISE_PIPE_CLASSIFICATION" and getattr(args, "other_instr", None):
        argv += ["--other-instr", args.other_instr]
    if args.template in {"T12_CONSUMER_RAW_GAP", "T30_LMUL_SCALING"} and getattr(args, "consumer", None):
        argv += ["--consumer", args.consumer]
    if args.template == "T30_LMUL_SCALING" and getattr(args, "shape", None):
        argv += ["--shape", args.shape]
    if getattr(args, "iterations", None) is not None:
        argv += ["--iterations", str(args.iterations)]
    if getattr(args, "filler_count", None) is not None:
        argv += ["--filler-count", str(args.filler_count)]
    argv += ["--output-root", relpath(repo_path(args.output_root))]
    if experiment_id:
        argv += ["--experiment-id", experiment_id]
    return argv


def base_metadata(
    *,
    experiment_id: str,
    template_id: str,
    markers: list[str],
    args: argparse.Namespace,
    lmul: str | None,
) -> dict[str, Any]:
    argv = command_argv(args, experiment_id)
    return {
        "schema_version": 1,
        "experiment": {
            "id": experiment_id,
            "template_id": template_id,
            "purpose": TEMPLATE_PURPOSES[template_id],
            "files": {
                "assembly": "test.s",
                "metadata": "experiment.yaml",
            },
            "markers": [{"label": marker} for marker in markers],
        },
        "parameters": {
            "sew": SEW,
            "lmul": lmul,
            "vl_register": "x5",
            "vl_value": VL_VALUE if lmul else None,
        },
        "generation": {
            "generator": "scripts/gen_asm.py",
            "generator_version": GENERATOR_VERSION,
            "stdlib_only": True,
            "deterministic": True,
            "template_file": relpath(repo_path(args.asm_template)),
            "reproduce": {
                "argv": argv,
                "command": " ".join(argv),
            },
        },
    }


def default_other_instr(instr: str) -> str:
    ids = list(INSTRUCTION_IDS)
    index = ids.index(instr)
    return ids[(index + 1) % len(ids)]


def default_consumer(instr: str) -> str:
    spec = require_instruction(instr)
    if spec.result_kind == "scalar":
        return "scalar_add"
    if spec.result_kind == "mask":
        return "vcpop_m"
    return "vadd_vv"


def default_iterations(template_id: str, lmul: str, requested: int | None) -> tuple[int, str | None]:
    if requested is not None:
        return requested, None
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        capacity = len(output_groups(lmul)) // 2
        value = min(4, capacity)
        if value < 4:
            return value, "reduced from 4 because LMUL m4 exposes only six independent output groups"
        return value, None
    if template_id == "T21_PAIR_WITH_SCALAR":
        return 4, None
    return 6, None


def make_experiment_id(args: argparse.Namespace) -> str:
    template_id = args.template
    parts = [short_template(template_id)]
    if template_id == "T00_BASELINE_MARKER":
        parts.append("marker")
    elif template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        other = args.other_instr or default_other_instr(args.instr)
        parts.extend([args.instr, other, args.lmul])
    elif template_id == "T30_LMUL_SCALING":
        parts.extend([args.instr, short_template(args.shape), args.lmul])
    else:
        if getattr(args, "instr", None):
            parts.append(args.instr)
        if getattr(args, "lmul", None):
            parts.append(args.lmul)
    if template_id in {
        "T10_INDEPENDENT_STREAM_THROUGHPUT",
        "T11_SELF_RAW_CHAIN",
        "T20_PAIRWISE_PIPE_CLASSIFICATION",
        "T21_PAIR_WITH_SCALAR",
    }:
        iterations, _ = default_iterations(template_id, args.lmul, args.iterations)
        parts.append(f"n{iterations}")
    if template_id == "T12_CONSUMER_RAW_GAP":
        filler_count = args.filler_count if args.filler_count is not None else 0
        parts.extend([f"k{filler_count}", args.consumer or default_consumer(args.instr)])
    if template_id == "T30_LMUL_SCALING":
        if args.shape == "T12_CONSUMER_RAW_GAP":
            filler_count = args.filler_count if args.filler_count is not None else 0
            parts.append(f"k{filler_count}")
        else:
            iterations, _ = default_iterations(args.shape, args.lmul, args.iterations)
            parts.append(f"n{iterations}")
    return "-".join(sanitize_part(part) for part in parts)


def body_t00() -> tuple[list[str], list[str], dict[str, Any]]:
    markers = ["t0", "t1"]
    lines = [
        "# Adjacent markers define the baseline marker delta.",
        "TIMESTAMP_MARK t0",
        "TIMESTAMP_MARK t1",
    ]
    return markers, lines, {}


def body_t01(spec: InstructionSpec, lmul: str) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    dest = scalar_reg(10) if spec.result_kind == "scalar" else output_vectors(lmul, 1)[0][0]
    lines = [
        "# Kill-check body: one instruction under test between markers.",
        "TIMESTAMP_MARK before",
        emit_instruction(spec, dest=dest, src_a=src_a, src_b=src_b, scalar="x6"),
        "TIMESTAMP_MARK after",
    ]
    return ["before", "after"], lines, {"destination": dest, "source_a": src_a, "source_b": src_b}


def body_t10(
    spec: InstructionSpec,
    lmul: str,
    iterations: int,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    vector_dests, reused = output_vectors(
        lmul,
        iterations if spec.result_kind != "scalar" else 1,
        allow_reuse=False,
    )
    scalar_dests = scalar_outputs(iterations)
    lines = [
        "# Independent stream: sources are read-only and destinations rotate.",
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index in range(iterations):
        dest = scalar_dests[index] if spec.result_kind == "scalar" else vector_dests[index]
        lines.append(emit_instruction(spec, dest=dest, src_a=src_a, src_b=src_b, scalar="x6"))
        instances.append({"index": index, "destination": dest, "source_a": src_a, "source_b": src_b})
    lines.append("TIMESTAMP_MARK end")
    return ["start", "end"], lines, {"iterations": iterations, "instances": instances, "register_reuse": reused}


def body_t11(
    spec: InstructionSpec,
    lmul: str,
    iterations: int,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    dest = scalar_reg(10) if spec.result_kind == "scalar" else output_vectors(lmul, 1)[0][0]
    lines = [
        "# Self RAW chain. Non-chainable instructions are emitted as a",
        "# documented placeholder; use T12 for their true dependency probe.",
        "TIMESTAMP_MARK start",
    ]
    instances = []
    chain_source = dest if spec.chainable else src_a
    for index in range(iterations):
        if index == 0:
            line_src_a = src_a
        else:
            line_src_a = chain_source
        lines.append(emit_instruction(spec, dest=dest, src_a=line_src_a, src_b=src_b, scalar="x6"))
        instances.append({"index": index, "destination": dest, "source_a": line_src_a, "source_b": src_b})
    lines.append("TIMESTAMP_MARK end")
    return ["start", "end"], lines, {
        "iterations": iterations,
        "destination": dest,
        "chainable": spec.chainable,
        "dependency_note": "direct self RAW chain" if spec.chainable else "not directly self-chainable; prefer T12",
        "instances": instances,
    }


def body_t12(
    spec: InstructionSpec,
    lmul: str,
    filler_count: int,
    consumer: str,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    dests, _ = output_vectors(lmul, 2 + max(filler_count, 1), allow_reuse=True)
    producer_dest = scalar_reg(10) if spec.result_kind == "scalar" else dests[0]
    consumer_dest = scalar_reg(11) if spec.result_kind in {"scalar", "mask"} else dests[1]
    filler_destinations = dests[2:]
    lines = [
        "# Producer-consumer gap probe. Fillers are independent of the producer result.",
        "TIMESTAMP_MARK start",
        emit_instruction(spec, dest=producer_dest, src_a=src_a, src_b=src_b, scalar="x6"),
    ]
    for index in range(filler_count):
        filler_dest = filler_destinations[index]
        lines.append(f"vadd.vv {filler_dest}, {src_a}, {src_b}  # independent filler {index}")
    if consumer == "scalar_add" or spec.result_kind == "scalar":
        lines.append(emit_consumer("scalar", producer_dest, consumer_dest, src_b))
    elif consumer == "vcpop_m" or spec.result_kind == "mask":
        lines.append(emit_consumer("mask", producer_dest, consumer_dest, src_b))
    else:
        consumer_spec = require_instruction(consumer)
        if consumer_spec.result_kind == "scalar":
            lines.append(emit_instruction(consumer_spec, dest=consumer_dest, src_a=producer_dest, src_b=src_b, scalar="x6"))
        else:
            lines.append(emit_consumer("vector", producer_dest, consumer_dest, src_b))
    lines.append("TIMESTAMP_MARK end")
    return ["start", "end"], lines, {
        "filler_count": filler_count,
        "producer_destination": producer_dest,
        "consumer": consumer,
        "consumer_destination": consumer_dest,
    }


def body_t20(
    spec_a: InstructionSpec,
    spec_b: InstructionSpec,
    lmul: str,
    iterations: int,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    vector_dests, reused = output_vectors(lmul, iterations * 2, allow_reuse=True)
    scalar_dests = scalar_outputs(iterations * 2)
    lines = [
        "# Pairwise pipe classification. A and B share read-only sources.",
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index in range(iterations):
        for side, spec in (("A", spec_a), ("B", spec_b)):
            slot = (index * 2) + (0 if side == "A" else 1)
            dest = scalar_dests[slot] if spec.result_kind == "scalar" else vector_dests[slot]
            lines.append(emit_instruction(spec, dest=dest, src_a=src_a, src_b=src_b, scalar="x6"))
            instances.append(
                {
                    "index": index,
                    "side": side,
                    "instruction": spec.instr_id,
                    "destination": dest,
                }
            )
    lines.append("TIMESTAMP_MARK end")
    return ["start", "end"], lines, {"iterations": iterations, "instances": instances, "register_reuse": reused}


def body_t21(
    spec: InstructionSpec,
    lmul: str,
    iterations: int,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    vector_dests, reused = output_vectors(lmul, iterations, allow_reuse=False)
    scalar_dests = scalar_outputs(iterations)
    scalar_pairs = [("x20", "x21", "x22"), ("x23", "x24", "x25"), ("x26", "x27", "x28"), ("x29", "x30", "x31")]
    lines = [
        "# Scalar pairing probe. Each vector instruction is followed by an add.",
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index in range(iterations):
        dest = scalar_dests[index] if spec.result_kind == "scalar" else vector_dests[index]
        lines.append(emit_instruction(spec, dest=dest, src_a=src_a, src_b=src_b, scalar="x6"))
        scalar_dest, scalar_a, scalar_b = scalar_pairs[index % len(scalar_pairs)]
        lines.append(f"add {scalar_dest}, {scalar_a}, {scalar_b}")
        instances.append({"index": index, "destination": dest, "scalar_add_destination": scalar_dest})
    lines.append("TIMESTAMP_MARK end")
    return ["start", "end"], lines, {"iterations": iterations, "instances": instances, "register_reuse": reused}


def body_for_args(args: argparse.Namespace) -> tuple[list[str], list[str], dict[str, Any]]:
    template_id = args.template
    if template_id == "T00_BASELINE_MARKER":
        return body_t00()

    spec = require_instruction(args.instr)
    validate_lmul(args.lmul)

    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return body_t01(spec, args.lmul)
    if template_id == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t10(spec, args.lmul, iterations)
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T11_SELF_RAW_CHAIN":
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t11(spec, args.lmul, iterations)
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T12_CONSUMER_RAW_GAP":
        filler_count = args.filler_count if args.filler_count is not None else 0
        consumer = args.consumer or default_consumer(args.instr)
        return body_t12(spec, args.lmul, filler_count, consumer)
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        other = require_instruction(args.other_instr or default_other_instr(args.instr))
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t20(spec, other, args.lmul, iterations)
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T21_PAIR_WITH_SCALAR":
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t21(spec, args.lmul, iterations)
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T30_LMUL_SCALING":
        shape = args.shape
        if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
            iterations, note = default_iterations(shape, args.lmul, args.iterations)
            markers, lines, meta = body_t10(spec, args.lmul, iterations)
        elif shape == "T11_SELF_RAW_CHAIN":
            iterations, note = default_iterations(shape, args.lmul, args.iterations)
            markers, lines, meta = body_t11(spec, args.lmul, iterations)
        elif shape == "T12_CONSUMER_RAW_GAP":
            note = None
            filler_count = args.filler_count if args.filler_count is not None else 0
            markers, lines, meta = body_t12(spec, args.lmul, filler_count, args.consumer or default_consumer(args.instr))
        else:
            raise SystemExit(f"T30 shape must be one of: {', '.join(T30_SHAPES)}")
        meta["scaling_shape"] = shape
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    raise AssertionError(f"unhandled template {template_id}")


def render_assembly(
    *,
    experiment_id: str,
    template_id: str,
    lmul: str | None,
    markers: list[str],
    body_lines: list[str],
    template_path: Path,
) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    body = indent_lines(body_lines)
    marker_summary = ", ".join(markers)
    return template.safe_substitute(
        experiment_id=experiment_id,
        template_id=template_id,
        sew=SEW,
        lmul=lmul or "none",
        marker_summary=marker_summary,
        setup_block=setup_block(lmul),
        body_block=body,
    )


def build_metadata(
    args: argparse.Namespace,
    *,
    experiment_id: str,
    markers: list[str],
    body_metadata: dict[str, Any],
) -> dict[str, Any]:
    lmul = None if args.template == "T00_BASELINE_MARKER" else args.lmul
    meta = base_metadata(
        experiment_id=experiment_id,
        template_id=args.template,
        markers=markers,
        args=args,
        lmul=lmul,
    )
    if getattr(args, "instr", None):
        meta["instruction"] = metadata_instruction(require_instruction(args.instr))
    if args.template == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        other = args.other_instr or default_other_instr(args.instr)
        meta["pair_instruction"] = metadata_instruction(require_instruction(other))
    if args.template == "T30_LMUL_SCALING":
        meta["scaling"] = {
            "shape": args.shape,
            "fit_form": "base_plus_lmul_times_k",
            "suite_values": list(LMUL_FACTORS),
        }
    meta["body"] = body_metadata
    return meta


def generate_one(args: argparse.Namespace) -> dict[str, Path]:
    if args.template not in TEMPLATE_IDS:
        raise SystemExit(f"unknown template id {args.template!r}; valid ids: {', '.join(TEMPLATE_IDS)}")
    if args.template != "T00_BASELINE_MARKER":
        if not args.instr:
            raise SystemExit(f"{args.template} requires --instr")
        if not args.lmul:
            raise SystemExit(f"{args.template} requires --lmul")
    if args.template == "T30_LMUL_SCALING" and args.shape not in T30_SHAPES:
        raise SystemExit(f"T30 --shape must be one of: {', '.join(T30_SHAPES)}")
    if args.iterations is not None and args.iterations <= 0:
        raise SystemExit("--iterations must be positive")
    if args.filler_count is not None and args.filler_count < 0:
        raise SystemExit("--filler-count must be non-negative")

    output_root = repo_path(args.output_root)
    template_path = repo_path(args.asm_template)
    experiment_id = args.experiment_id or make_experiment_id(args)
    experiment_dir = output_root / experiment_id
    markers, body_lines, body_meta = body_for_args(args)
    assembly = render_assembly(
        experiment_id=experiment_id,
        template_id=args.template,
        lmul=None if args.template == "T00_BASELINE_MARKER" else args.lmul,
        markers=markers,
        body_lines=body_lines,
        template_path=template_path,
    )
    metadata = build_metadata(args, experiment_id=experiment_id, markers=markers, body_metadata=body_meta)

    experiment_dir.mkdir(parents=True, exist_ok=True)
    asm_path = experiment_dir / "test.s"
    yaml_path = experiment_dir / "experiment.yaml"
    asm_path.write_text(assembly, encoding="utf-8")
    write_yaml(yaml_path, metadata)
    return {"experiment_dir": experiment_dir, "assembly": asm_path, "metadata": yaml_path}


def suite_entries(args: argparse.Namespace) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def add(template: str, instr: str | None = None, lmul: str | None = None, **extra: Any) -> None:
        ns = argparse.Namespace(
            template=template,
            instr=instr,
            lmul=lmul,
            other_instr=extra.get("other_instr"),
            consumer=extra.get("consumer"),
            shape=extra.get("shape", "T10_INDEPENDENT_STREAM_THROUGHPUT"),
            iterations=extra.get("iterations"),
            filler_count=extra.get("filler_count"),
            output_root=args.output_root,
            asm_template=args.asm_template,
            experiment_id=None,
        )
        experiment_id = make_experiment_id(ns)
        entries.append(
            {
                "id": experiment_id,
                "template_id": template,
                "instruction_id": instr,
                "lmul": lmul,
                "argv": command_argv(ns, experiment_id),
            }
        )

    add("T00_BASELINE_MARKER")
    for instr in INSTRUCTION_IDS:
        for lmul in LMUL_FACTORS:
            add("T01_DECODE_EXEC_KILLCHECK", instr, lmul)
            add("T10_INDEPENDENT_STREAM_THROUGHPUT", instr, lmul)
            add("T11_SELF_RAW_CHAIN", instr, lmul)
            add("T12_CONSUMER_RAW_GAP", instr, lmul, filler_count=0, consumer=default_consumer(instr))
            add("T21_PAIR_WITH_SCALAR", instr, lmul)
            for shape in T30_SHAPES:
                add("T30_LMUL_SCALING", instr, lmul, shape=shape, filler_count=0, consumer=default_consumer(instr))

    ids = list(INSTRUCTION_IDS)
    for left_index, left in enumerate(ids):
        for right in ids[left_index + 1 :]:
            for lmul in LMUL_FACTORS:
                add("T20_PAIRWISE_PIPE_CLASSIFICATION", left, lmul, other_instr=right)
    return entries


def write_suite_manifest(args: argparse.Namespace, entries: list[dict[str, Any]]) -> Path:
    output_root = repo_path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "suite": {
            "id": "rvv-profile-generated-suite",
            "description": "Deterministic manifest for Phase 2-5 RVV assembly experiments.",
            "entry_count": len(entries),
            "instruction_ids": list(INSTRUCTION_IDS),
            "lmul_values": list(LMUL_FACTORS),
            "sew": SEW,
        },
        "generation": {
            "generator": "scripts/gen_asm.py",
            "generator_version": GENERATOR_VERSION,
            "manifest_only": args.manifest_only,
        },
        "experiments": entries,
    }
    path = output_root / "suite_manifest.yaml"
    write_yaml(path, manifest)
    return path


def generate_suite(args: argparse.Namespace) -> dict[str, Any]:
    entries = suite_entries(args)
    manifest_path = write_suite_manifest(args, entries)
    generated = []
    if not args.manifest_only:
        for entry in entries:
            argv = entry["argv"][2:]
            one_args = build_parser().parse_args(argv)
            generated.append(generate_one(one_args)["experiment_dir"])
    return {"manifest": manifest_path, "entry_count": len(entries), "generated_count": len(generated)}


def print_paths(paths: dict[str, Path]) -> None:
    for key, path in paths.items():
        print(f"{key}: {relpath(path)}")


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="output root for generated experiments")
    parser.add_argument("--asm-template", default=str(DEFAULT_TEMPLATE_PATH), help="assembly wrapper template path")


def build_parser() -> argparse.ArgumentParser:
    examples = """examples:
  Generate one kill-check:
    python3 scripts/gen_asm.py one --template T01_DECODE_EXEC_KILLCHECK --instr vadd_vv --lmul m1

  Generate the marker baseline:
    python3 scripts/gen_asm.py one --template T00_BASELINE_MARKER

  Generate only a suite manifest:
    python3 scripts/gen_asm.py suite --manifest-only
"""
    parser = argparse.ArgumentParser(
        description="Generate deterministic RVV assembly experiment scaffolding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    one = subparsers.add_parser("one", help="generate one experiment directory")
    one.add_argument("--template", required=True, choices=TEMPLATE_IDS, help="experiment template id")
    one.add_argument("--instr", choices=INSTRUCTION_IDS, help="instruction id from docs/plan.md")
    one.add_argument("--lmul", choices=tuple(LMUL_FACTORS), help="LMUL value; SEW is fixed at e32")
    one.add_argument("--other-instr", choices=INSTRUCTION_IDS, help="second instruction for T20")
    one.add_argument("--consumer", help="consumer id for T12/T30; default is result-kind aware")
    one.add_argument("--shape", choices=T30_SHAPES, default="T10_INDEPENDENT_STREAM_THROUGHPUT", help="base shape for T30")
    one.add_argument("--iterations", type=int, help="instance count for stream/chain/pair templates")
    one.add_argument("--filler-count", type=int, help="independent filler count for T12")
    one.add_argument("--experiment-id", help="override deterministic experiment id")
    add_common_options(one)

    suite = subparsers.add_parser("suite", help="generate a deterministic suite manifest and optionally all files")
    suite.add_argument("--manifest-only", action="store_true", help="write only suite_manifest.yaml")
    add_common_options(suite)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "one":
        paths = generate_one(args)
        print_paths(paths)
        return 0
    if args.command == "suite":
        result = generate_suite(args)
        print(f"manifest: {relpath(result['manifest'])}")
        print(f"entry_count: {result['entry_count']}")
        print(f"generated_count: {result['generated_count']}")
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
