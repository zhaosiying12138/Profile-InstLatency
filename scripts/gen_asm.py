#!/usr/bin/env python3
"""Generate deterministic, assembler-legal RVV profiling experiments.

Body builders use ``TIMESTAMP_MARK <label>`` as an internal marker notation.
Rendering lowers each marker to zero-cost labels at the next-instruction PC and
records the marker symbols in experiment metadata.
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
GENERATOR_VERSION = 3

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("experiments/generated")
DEFAULT_TEMPLATE_PATH = Path("templates/rvv_program.s.tpl")

LMUL_FACTORS = {
    "m1": 1,
    "m2": 2,
    "m4": 4,
}

BASE_STREAM_ITERATIONS = (2, 4, 6)
EXTENDED_STREAM_ITERATIONS = (8, 12)
T12_FILLER_COUNTS = tuple(range(41))
T12_FOCUSED_FILLER_COUNTS = tuple(range(9))
T12_DEFAULT_FILLER = "vadd_vv"
T12_SCALAR_FILLER = "scalar_add"
T12_FILLERS = (T12_DEFAULT_FILLER, T12_SCALAR_FILLER)
T12_DEFAULT_CONSUMER_ROLE = "dependent"
T12_CONSUMER_ROLES = (T12_DEFAULT_CONSUMER_ROLE, "control")
T12_SCALAR_FILLER_TARGETS = frozenset(
    {
        ("vcpop_m", "m1"),
        ("vcpop_m", "m2"),
        ("vcpop_m", "m4"),
        ("viota_m", "m4"),
        ("vrgather_vv", "m4"),
        ("vslideup_vx", "m4"),
    }
)
T12_CONTROL_TARGETS = frozenset(
    {
        ("vcpop_m", "m1"),
        ("vcpop_m", "m2"),
        ("vcpop_m", "m4"),
        ("vrgather_vv", "m4"),
        ("vslideup_vx", "m4"),
    }
)
T20_BASE_PAIR_COUNTS = (2, 3, 4)
T20_EXTENDED_PAIR_COUNTS = (6,)
T20_RESOURCE_NOREUSE_PAIR_COUNTS = (1, 2, 3)
T20_RESOURCE_NOREUSE_POLICY = "resource_noreuse_prefix"
DEFAULT_SCALAR_DEST_POLICY = "rotated"
SCALAR_DEST_POLICIES = (DEFAULT_SCALAR_DEST_POLICY, "fixed")
T20_REGISTER_POLICIES = ("default", T20_RESOURCE_NOREUSE_POLICY)
DIAGNOSTIC_ROUNDS = ("r11",)
MASK_SOURCE_POLICIES = ("v0", "v4", "rot")
DEFAULT_MASK_SOURCE_POLICY = "v0"
DEFAULT_MARKER_PADDING_BYTES = 0
TIMED_BODY_BASE_PC_MOD32 = 4


TEMPLATE_IDS = (
    "T00_BASELINE_MARKER",
    "T01_DECODE_EXEC_KILLCHECK",
    "T10_INDEPENDENT_STREAM_THROUGHPUT",
    "T11_SELF_RAW_CHAIN",
    "T12_CONSUMER_RAW_GAP",
    "T20_PAIRWISE_PIPE_CLASSIFICATION",
    "T21_PAIR_WITH_SCALAR",
    "T30_LMUL_SCALING",
    "T40_COMMON_VLSU_LOAD_HIT",
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
    "T40_COMMON_VLSU_LOAD_HIT": "Record a common vector load-hit timing reference.",
}

COMMON_RESULT_TEMPLATES = {
    "T00_BASELINE_MARKER",
    "T01_DECODE_EXEC_KILLCHECK",
    "T40_COMMON_VLSU_LOAD_HIT",
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
        False,
        "Vector slide-up with a scalar offset operand; assembler forbids destination/source overlap.",
    ),
    "vrgather_vv": InstructionSpec(
        "vrgather_vv",
        "vrgather.vv",
        "WriteVRGatherVV",
        "vector",
        False,
        "Vector gather using vector indices; assembler forbids destination/source overlap.",
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


def sanitize_symbol_part(part: str) -> str:
    sanitized = "".join(char if char.isalnum() else "_" for char in part)
    sanitized = sanitized.strip("_")
    return sanitized or "marker"


def marker_symbol(experiment_id: str, label: str) -> str:
    exp = sanitize_symbol_part(experiment_id)
    marker = sanitize_symbol_part(label)
    return f"__rvv_profile_marker_{exp}_{marker}"


def marker_local_label(experiment_id: str, label: str) -> str:
    exp = sanitize_symbol_part(experiment_id)
    marker = sanitize_symbol_part(label)
    return f".Lrvv_profile_marker_{exp}_{marker}"


def marker_metadata(experiment_id: str, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "symbol": marker_symbol(experiment_id, label),
        "local_label": marker_local_label(experiment_id, label),
        "zero_cost": True,
        "occupies_issue_slot": False,
        "pc_anchor": "next_instruction",
    }


def marker_metadata_entries(experiment_id: str, markers: Iterable[str]) -> list[dict[str, Any]]:
    return [marker_metadata(experiment_id, marker) for marker in markers]


def marker_label_from_line(line: str) -> str | None:
    parts = line.strip().split()
    if len(parts) == 2 and parts[0] == "TIMESTAMP_MARK":
        return parts[1]
    return None


def lower_marker_lines(body_lines: Iterable[str], experiment_id: str) -> list[str]:
    lowered: list[str] = []
    for line in body_lines:
        label = marker_label_from_line(line)
        if label is None:
            lowered.append(line)
            continue
        meta = marker_metadata(experiment_id, label)
        lowered.extend(
            [
                f"# marker {label}: zero-cost timestamp point at the next instruction PC.",
                f".globl {meta['symbol']}",
                f"{meta['symbol']}:",
                f"{meta['local_label']}:",
            ]
        )
    return lowered


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


def output_vectors_excluding(
    lmul: str,
    count: int,
    excluded: set[str],
    *,
    allow_reuse: bool = False,
) -> tuple[list[str], bool]:
    regs = [vector_reg(group) for group in output_groups(lmul) if vector_reg(group) not in excluded]
    if count <= len(regs):
        return regs[:count], False
    if not allow_reuse:
        raise SystemExit(
            f"LMUL {lmul} has {len(regs)} independent output groups after exclusions, "
            f"but {count} were requested"
        )
    if not regs:
        raise SystemExit(f"LMUL {lmul} has no reusable output groups after exclusions")
    return [regs[index % len(regs)] for index in range(count)], True


def scalar_outputs(count: int, start: int = 10) -> list[str]:
    regs = []
    for index in range(count):
        reg = start + index
        if reg > 31:
            reg = 10 + (index % 22)
        regs.append(scalar_reg(reg))
    return regs


def scalar_output_sequence(count: int, policy: str, start: int = 10) -> tuple[list[str], bool]:
    if count <= 0:
        return [], False
    if policy == "fixed":
        return [scalar_reg(start)] * count, count > 1
    if policy == "rotated":
        regs = scalar_outputs(count, start=start)
        return regs, len(set(regs)) != len(regs)
    valid = ", ".join(SCALAR_DEST_POLICIES)
    raise SystemExit(f"unknown scalar destination policy {policy!r}; valid values: {valid}")


def scalar_dest_policy(args: argparse.Namespace) -> str:
    return getattr(args, "scalar_dest_policy", None) or DEFAULT_SCALAR_DEST_POLICY


def diagnostic_round(args: argparse.Namespace) -> str | None:
    return getattr(args, "diagnostic_round", None) or None


def mask_source_policy(args: argparse.Namespace) -> str:
    return getattr(args, "mask_source_policy", None) or DEFAULT_MASK_SOURCE_POLICY


def marker_padding_bytes(args: argparse.Namespace) -> int:
    value = getattr(args, "marker_padding_bytes", None)
    return DEFAULT_MARKER_PADDING_BYTES if value is None else int(value)


def scalar_dest_policy_suffix(policy: str) -> str:
    if policy == "rotated":
        return "rot"
    if policy == "fixed":
        return "fix"
    valid = ", ".join(SCALAR_DEST_POLICIES)
    raise SystemExit(f"unknown scalar destination policy {policy!r}; valid values: {valid}")


def marker_padding_lines(byte_count: int) -> list[str]:
    if byte_count <= 0:
        return []
    if byte_count % 4 != 0:
        raise SystemExit("--marker-padding-bytes must be a non-negative multiple of 4")
    return ["addi x0, x0, 0  # r11 marker padding"] * (byte_count // 4)


def target_start_pc_mod32(byte_count: int) -> int:
    return (TIMED_BODY_BASE_PC_MOD32 + byte_count) % 32


def expected_fetch_boundary_crossings(start_pc_mod32: int, body_instruction_count: int) -> int:
    if body_instruction_count <= 0:
        return 0
    return (start_pc_mod32 + 4 * (body_instruction_count - 1)) // 32


def mask_sources(lmul: str, count: int, policy: str) -> list[str]:
    if count <= 0:
        return []
    if policy == "v0":
        return ["v0"] * count
    if policy == "v4":
        return ["v4"] * count
    if policy == "rot":
        groups = aligned_groups(lmul)
        return [vector_reg(groups[index % len(groups)]) for index in range(count)]
    valid = ", ".join(MASK_SOURCE_POLICIES)
    raise SystemExit(f"unknown mask source policy {policy!r}; valid values: {valid}")


def add_r11_metadata(
    body_meta: dict[str, Any],
    *,
    scalar_policy: str,
    source_policy: str,
    source_registers: Iterable[str],
    padding_bytes: int,
    body_instruction_count: int,
) -> None:
    start_mod32 = target_start_pc_mod32(padding_bytes)
    body_meta.update(
        {
            "diagnostic_round": "r11",
            "scalar_dest_policy": scalar_policy,
            "mask_source_policy": source_policy,
            "source_registers": list(dict.fromkeys(source_registers)),
            "marker_padding_bytes": padding_bytes,
            "target_start_pc_mod32": start_mod32,
            "body_instruction_count": body_instruction_count,
            "expected_fetch_boundary_crossings": expected_fetch_boundary_crossings(
                start_mod32,
                body_instruction_count,
            ),
        }
    )


def t12_filler(args: argparse.Namespace) -> str:
    return getattr(args, "t12_filler", None) or T12_DEFAULT_FILLER


def t12_consumer_role(args: argparse.Namespace) -> str:
    return getattr(args, "t12_consumer_role", None) or T12_DEFAULT_CONSUMER_ROLE


def vector_destination_slots(specs: Iterable[InstructionSpec]) -> int:
    return sum(1 for spec in specs if spec.result_kind != "scalar")


def supports_t20_extended_pair_count(
    spec_a: InstructionSpec,
    spec_b: InstructionSpec,
    lmul: str,
    pair_count: int,
) -> bool:
    vector_slots = pair_count * vector_destination_slots((spec_a, spec_b))
    scalar_slots = (pair_count * 2) - vector_slots
    return vector_slots <= len(output_groups(lmul)) and scalar_slots <= 22


def suite_t20_pair_counts(left: str, right: str, lmul: str) -> tuple[int, ...]:
    spec_a = require_instruction(left)
    spec_b = require_instruction(right)
    counts = list(T20_BASE_PAIR_COUNTS)
    counts.extend(
        count
        for count in T20_EXTENDED_PAIR_COUNTS
        if supports_t20_extended_pair_count(spec_a, spec_b, lmul, count)
    )
    return tuple(dict.fromkeys(counts))


def t20_register_policy(args: argparse.Namespace) -> str:
    return getattr(args, "t20_register_policy", None) or "default"


def is_t20_resource_noreuse(args: argparse.Namespace) -> bool:
    return t20_register_policy(args) == T20_RESOURCE_NOREUSE_POLICY


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


def t12_consumer_destination(spec: InstructionSpec, consumer: str, vector_dest: str) -> str:
    if consumer in {"scalar_add", "vcpop_m"} or spec.result_kind in {"scalar", "mask"}:
        return scalar_reg(11)
    consumer_spec = require_instruction(consumer)
    if consumer_spec.result_kind == "scalar":
        return scalar_reg(11)
    return vector_dest


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
    if args.template == "T20_PAIRWISE_PIPE_CLASSIFICATION" and is_t20_resource_noreuse(args):
        argv += ["--t20-register-policy", T20_RESOURCE_NOREUSE_POLICY]
    if args.template in {"T12_CONSUMER_RAW_GAP", "T30_LMUL_SCALING"} and getattr(args, "consumer", None):
        argv += ["--consumer", args.consumer]
    if (
        args.template in {"T12_CONSUMER_RAW_GAP", "T30_LMUL_SCALING"}
        and t12_filler(args) != T12_DEFAULT_FILLER
    ):
        argv += ["--t12-filler", t12_filler(args)]
    if args.template == "T12_CONSUMER_RAW_GAP" and t12_consumer_role(args) != T12_DEFAULT_CONSUMER_ROLE:
        argv += ["--t12-consumer-role", t12_consumer_role(args)]
    if args.template == "T30_LMUL_SCALING" and getattr(args, "shape", None):
        argv += ["--shape", args.shape]
    policy = scalar_dest_policy(args)
    if policy != DEFAULT_SCALAR_DEST_POLICY:
        argv += ["--scalar-dest-policy", policy]
    if diagnostic_round(args):
        argv += ["--diagnostic-round", diagnostic_round(args)]
        argv += ["--mask-source-policy", mask_source_policy(args)]
        argv += ["--marker-padding-bytes", str(marker_padding_bytes(args))]
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
    instruction_id = getattr(args, "instr", None)
    result_group = "common" if template_id in COMMON_RESULT_TEMPLATES else instruction_id or "common"
    marker_entries = marker_metadata_entries(experiment_id, markers)
    return {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "template_id": template_id,
        "result_group": result_group,
        "instruction_id": instruction_id,
        "lmul": lmul,
        "sew": SEW,
        "markers": markers,
        "marker_metadata": marker_entries,
        "experiment": {
            "id": experiment_id,
            "template_id": template_id,
            "purpose": TEMPLATE_PURPOSES[template_id],
            "files": {
                "assembly": "test.s",
                "metadata": "experiment.yaml",
            },
            "markers": marker_entries,
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


def supports_stream_iterations(template_id: str, instr: str, lmul: str, iterations: int) -> bool:
    spec = require_instruction(instr)
    if template_id == "T11_SELF_RAW_CHAIN":
        return spec.chainable
    if template_id != "T10_INDEPENDENT_STREAM_THROUGHPUT":
        raise AssertionError(f"unhandled stream template {template_id}")
    if spec.result_kind == "scalar":
        return True
    return iterations <= len(output_groups(lmul))


def suite_stream_iterations(template_id: str, instr: str, lmul: str) -> tuple[int, ...]:
    values = [
        iterations
        for iterations in BASE_STREAM_ITERATIONS
        if supports_stream_iterations(template_id, instr, lmul, iterations)
    ]
    values.extend(
        iterations
        for iterations in EXTENDED_STREAM_ITERATIONS
        if supports_stream_iterations(template_id, instr, lmul, iterations)
    )
    return tuple(values)


def make_experiment_id(args: argparse.Namespace) -> str:
    template_id = args.template
    parts = [short_template(template_id)]
    if template_id == "T00_BASELINE_MARKER":
        parts.append("marker")
    elif template_id == "T40_COMMON_VLSU_LOAD_HIT":
        parts.extend(["common-vlsu-load-hit", args.lmul or "m1"])
    elif template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        other = args.other_instr or default_other_instr(args.instr)
        parts.extend([args.instr, other, args.lmul])
    elif template_id == "T30_LMUL_SCALING":
        parts.extend([args.instr, short_template(args.shape), args.lmul])
        if (
            args.shape == "T10_INDEPENDENT_STREAM_THROUGHPUT"
            and scalar_dest_policy(args) != DEFAULT_SCALAR_DEST_POLICY
        ):
            parts.append(f"scalar-{scalar_dest_policy(args)}")
    else:
        if getattr(args, "instr", None):
            parts.append(args.instr)
        if getattr(args, "lmul", None):
            parts.append(args.lmul)
    if (
        template_id == "T10_INDEPENDENT_STREAM_THROUGHPUT"
        and not diagnostic_round(args)
        and scalar_dest_policy(args) != DEFAULT_SCALAR_DEST_POLICY
    ):
        parts.append(f"scalar-{scalar_dest_policy(args)}")
    if template_id in {
        "T10_INDEPENDENT_STREAM_THROUGHPUT",
        "T11_SELF_RAW_CHAIN",
        "T20_PAIRWISE_PIPE_CLASSIFICATION",
        "T21_PAIR_WITH_SCALAR",
    }:
        iterations, _ = default_iterations(template_id, args.lmul, args.iterations)
        parts.append(f"n{iterations}")
    if diagnostic_round(args) and template_id in {
        "T10_INDEPENDENT_STREAM_THROUGHPUT",
        "T21_PAIR_WITH_SCALAR",
    }:
        parts.append(diagnostic_round(args))
        parts.append(f"sd-{scalar_dest_policy_suffix(scalar_dest_policy(args))}")
        parts.append(f"src-{mask_source_policy(args)}")
        parts.append(f"pad{marker_padding_bytes(args):02d}")
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION" and is_t20_resource_noreuse(args):
        parts.append("resource-noreuse")
    if template_id == "T12_CONSUMER_RAW_GAP":
        filler_count = args.filler_count if args.filler_count is not None else 0
        parts.extend([f"k{filler_count}", args.consumer or default_consumer(args.instr)])
        if t12_filler(args) != T12_DEFAULT_FILLER:
            parts.append(f"f{t12_filler(args)}")
        if t12_consumer_role(args) == "control":
            parts.append("control")
    if template_id == "T30_LMUL_SCALING":
        if args.shape == "T12_CONSUMER_RAW_GAP":
            filler_count = args.filler_count if args.filler_count is not None else 0
            parts.extend([f"k{filler_count}", args.consumer or default_consumer(args.instr)])
            if t12_filler(args) != T12_DEFAULT_FILLER:
                parts.append(f"f{t12_filler(args)}")
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
        "TIMESTAMP_MARK program_end",
    ]
    return ["before", "after", "program_end"], lines, {"destination": dest, "source_a": src_a, "source_b": src_b}


def body_t10(
    spec: InstructionSpec,
    lmul: str,
    iterations: int,
    scalar_policy: str = DEFAULT_SCALAR_DEST_POLICY,
    source_policy: str = DEFAULT_MASK_SOURCE_POLICY,
    padding_bytes: int = DEFAULT_MARKER_PADDING_BYTES,
    r11_diagnostic: bool = False,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    source_sequence = (
        mask_sources(lmul, iterations, source_policy)
        if spec.instr_id == "vcpop_m" and r11_diagnostic
        else [src_a] * iterations
    )
    if spec.result_kind == "scalar":
        vector_dests: list[str] = []
        vector_reused = False
        scalar_dests, scalar_reused = scalar_output_sequence(iterations, scalar_policy)
    else:
        vector_dests, vector_reused = output_vectors(lmul, iterations, allow_reuse=False)
        scalar_dests = []
        scalar_reused = False
    stream_note = (
        f"# Independent stream: sources are read-only and scalar destinations are {scalar_policy}."
        if spec.result_kind == "scalar"
        else "# Independent stream: sources are read-only and destinations rotate."
    )
    lines = [
        stream_note,
        *marker_padding_lines(padding_bytes),
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index in range(iterations):
        dest = scalar_dests[index] if spec.result_kind == "scalar" else vector_dests[index]
        line_src_a = source_sequence[index]
        lines.append(emit_instruction(spec, dest=dest, src_a=line_src_a, src_b=src_b, scalar="x6"))
        instances.append(
            {
                "index": index,
                "destination": dest,
                "source_a": line_src_a,
                "source_b": src_b,
                "destination_reused": scalar_reused if spec.result_kind == "scalar" else vector_reused,
            }
        )
    lines.append("TIMESTAMP_MARK end")
    body_meta: dict[str, Any] = {
        "iterations": iterations,
        "instances": instances,
        "register_reuse": vector_reused or scalar_reused,
        "destination_policy": "scalar_" + scalar_policy if spec.result_kind == "scalar" else "rotated_vector",
    }
    if spec.result_kind == "scalar":
        body_meta["scalar_dest_policy"] = scalar_policy
    if r11_diagnostic:
        add_r11_metadata(
            body_meta,
            scalar_policy=scalar_policy,
            source_policy=source_policy,
            source_registers=source_sequence,
            padding_bytes=padding_bytes,
            body_instruction_count=iterations,
        )
    return ["start", "end"], lines, body_meta


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
        "true_raw_chain": spec.chainable,
        "scalar_raw_chain": spec.result_kind == "scalar" and spec.chainable,
        "latency_evidence": spec.chainable,
        "dependency_note": "direct self RAW chain" if spec.chainable else "not directly self-chainable; prefer T12",
        "instances": instances,
    }


def body_t12(
    spec: InstructionSpec,
    lmul: str,
    filler_count: int,
    consumer: str,
    filler: str = T12_DEFAULT_FILLER,
    consumer_role: str = T12_DEFAULT_CONSUMER_ROLE,
    matched_dependent_experiment_id: str | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    if consumer == T12_SCALAR_FILLER and spec.result_kind != "scalar":
        raise SystemExit(
            "T12 scalar_add consumer requires a scalar-result producer; "
            "use a vector or mask consumer for vector/mask producer results"
        )
    src_a, src_b = base_vector_sources(lmul)
    vector_filler_count = filler_count if filler == T12_DEFAULT_FILLER else 0
    if spec.result_kind == "scalar":
        dests, _ = output_vectors(lmul, max(2, 2 + vector_filler_count), allow_reuse=True)
        filler_destinations = dests[2:]
        producer_dest = scalar_reg(10)
        consumer_dest = scalar_reg(11)
    else:
        dests, _ = output_vectors(lmul, 2, allow_reuse=False)
        producer_dest = dests[0]
        consumer_dest = t12_consumer_destination(spec, consumer, dests[1])
        filler_destinations, _ = output_vectors_excluding(
            lmul,
            vector_filler_count,
            set(dests),
            allow_reuse=True,
        )
    lines = [
        "# Producer-consumer gap probe. Fillers are independent of the producer result.",
        "TIMESTAMP_MARK start",
        emit_instruction(spec, dest=producer_dest, src_a=src_a, src_b=src_b, scalar="x6"),
    ]
    if filler == T12_DEFAULT_FILLER:
        for index in range(filler_count):
            filler_dest = filler_destinations[index]
            lines.append(f"vadd.vv {filler_dest}, {src_a}, {src_b}  # independent filler {index}")
    elif filler == T12_SCALAR_FILLER:
        scalar_dests = scalar_outputs(filler_count, start=20)
        for index, filler_dest in enumerate(scalar_dests):
            lines.append(f"add {filler_dest}, x6, x7  # independent scalar filler {index}")
    else:
        valid = ", ".join(T12_FILLERS)
        raise SystemExit(f"unknown T12 filler {filler!r}; valid values: {valid}")
    consumer_kind = "scalar_add"
    consumer_source = producer_dest
    fallback_source = src_b
    independent_consumer_source: dict[str, Any] | None = None
    if consumer_role == "control":
        if consumer == "scalar_add" or spec.result_kind == "scalar":
            consumer_source = "x28"
            fallback_source = "x0"
            independent_consumer_source = {
                "register": consumer_source,
                "kind": "scalar",
                "initialized_by": "setup_block",
            }
        elif consumer == "vcpop_m" or spec.result_kind == "mask":
            consumer_source = "v0"
            fallback_source = src_b
            independent_consumer_source = {
                "register": consumer_source,
                "kind": "mask",
                "initialized_by": "setup_block_all_true_mask",
            }
        else:
            consumer_source = src_b
            fallback_source = src_a
            independent_consumer_source = {
                "register": consumer_source,
                "kind": "vector",
                "initialized_by": "setup_block",
            }
    if consumer == "scalar_add" or spec.result_kind == "scalar":
        lines.append(emit_consumer("scalar", consumer_source, consumer_dest, fallback_source))
    elif consumer == "vcpop_m" or spec.result_kind == "mask":
        consumer_kind = "mask_popcount"
        lines.append(emit_consumer("mask", consumer_source, consumer_dest, fallback_source))
    else:
        consumer_spec = require_instruction(consumer)
        consumer_kind = consumer_spec.result_kind
        if consumer_spec.result_kind == "scalar":
            lines.append(
                emit_instruction(
                    consumer_spec,
                    dest=consumer_dest,
                    src_a=consumer_source,
                    src_b=fallback_source,
                    scalar="x6",
                )
            )
        else:
            lines.append(
                emit_instruction(
                    consumer_spec,
                    dest=consumer_dest,
                    src_a=consumer_source,
                    src_b=fallback_source,
                    scalar="x6",
                )
            )
    lines.append("TIMESTAMP_MARK end")
    raw_path = f"{spec.result_kind}_result_to_{consumer_kind}"
    filler_kind = "scalar" if filler == T12_SCALAR_FILLER else "vector"
    filler_cadence = 1 if filler == T12_SCALAR_FILLER else None
    gap_sweep: dict[str, Any] = {
        "parameter": "filler_count",
        "value": filler_count,
        "independent_filler_instruction": filler,
        "independent_filler_count": filler_count,
    }
    if filler_cadence is not None:
        gap_sweep["independent_filler_cadence_cycles"] = filler_cadence
    body_meta: dict[str, Any] = {
        "filler_count": filler_count,
        "filler_instruction_id": filler,
        "independent_filler_kind": filler_kind,
        **({"filler_cadence_cycles": filler_cadence} if filler_cadence is not None else {}),
        "producer_destination": producer_dest,
        "producer_result_kind": spec.result_kind,
        "consumer": consumer,
        "consumer_kind": consumer_kind,
        "consumer_destination": consumer_dest,
        "consumer_reads_producer": consumer_role == T12_DEFAULT_CONSUMER_ROLE,
        "raw_path": raw_path,
        "gap_sweep": gap_sweep,
    }
    if consumer_role == "control":
        body_meta.update(
            {
                "t12_consumer_role": "control",
                "matched_dependent_experiment_id": matched_dependent_experiment_id,
                "independent_consumer_source": independent_consumer_source,
            }
        )
    return ["start", "end"], lines, body_meta


def t12_dependent_experiment_id(args: argparse.Namespace) -> str:
    ns = argparse.Namespace(**vars(args))
    ns.t12_consumer_role = T12_DEFAULT_CONSUMER_ROLE
    ns.experiment_id = None
    return make_experiment_id(ns)


def body_t20(
    spec_a: InstructionSpec,
    spec_b: InstructionSpec,
    lmul: str,
    iterations: int,
    register_policy: str = "default",
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    schedule = [
        (index, side, spec)
        for index in range(iterations)
        for side, spec in (("A", spec_a), ("B", spec_b))
    ]
    vector_slots = vector_destination_slots(spec for _, _, spec in schedule)
    scalar_slots = len(schedule) - vector_slots
    if register_policy == T20_RESOURCE_NOREUSE_POLICY and scalar_slots:
        raise SystemExit(f"{T20_RESOURCE_NOREUSE_POLICY} requires two non-scalar-result T20 instructions")
    vector_dests, vector_reused = output_vectors(
        lmul,
        vector_slots,
        allow_reuse=register_policy != T20_RESOURCE_NOREUSE_POLICY,
    )
    scalar_dests, scalar_reused = scalar_output_sequence(scalar_slots, DEFAULT_SCALAR_DEST_POLICY)
    vector_index = 0
    scalar_index = 0
    lines = [
        "# Pairwise pipe classification. A and B share read-only sources.",
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index, side, spec in schedule:
        if spec.result_kind == "scalar":
            dest = scalar_dests[scalar_index]
            scalar_index += 1
        else:
            dest = vector_dests[vector_index]
            vector_index += 1
        lines.append(emit_instruction(spec, dest=dest, src_a=src_a, src_b=src_b, scalar="x6"))
        instances.append(
            {
                "index": index,
                "side": side,
                "instruction": spec.instr_id,
                "destination": dest,
                "source_a": src_a,
                "source_b": src_b,
            }
        )
    lines.append("TIMESTAMP_MARK end")
    destinations = [str(instance["destination"]) for instance in instances]
    for instance in instances:
        instance["destination_reused"] = destinations.count(str(instance["destination"])) > 1
    register_reuse = vector_reused or scalar_reused
    body_meta: dict[str, Any] = {
        "iterations": iterations,
        "pair_count": iterations,
        "instruction_pair": {
            "A": spec_a.instr_id,
            "B": spec_b.instr_id,
        },
        "instances": instances,
        "destinations": destinations,
        "register_reuse": register_reuse,
        "destination_allocation": {
            "vector_destination_count": vector_slots,
            "scalar_destination_count": scalar_slots,
            "available_vector_output_groups": len(output_groups(lmul)),
            "available_scalar_outputs": 22,
            "vector_register_reuse": vector_reused,
            "scalar_register_reuse": scalar_reused,
        },
    }
    if register_policy == T20_RESOURCE_NOREUSE_POLICY:
        body_meta["register_policy"] = T20_RESOURCE_NOREUSE_POLICY
        body_meta["resource_disambiguation"] = {
            "usable_for_proc_resource": True,
            "count_set_id": "m4_vector_vector_noreuse",
            "symmetry_breaker": False,
        }
    return ["start", "end"], lines, body_meta


def body_t21(
    spec: InstructionSpec,
    lmul: str,
    iterations: int,
    scalar_policy: str = DEFAULT_SCALAR_DEST_POLICY,
    source_policy: str = DEFAULT_MASK_SOURCE_POLICY,
    padding_bytes: int = DEFAULT_MARKER_PADDING_BYTES,
    r11_diagnostic: bool = False,
) -> tuple[list[str], list[str], dict[str, Any]]:
    src_a, src_b = base_vector_sources(lmul)
    if spec.result_kind == "scalar":
        vector_dests, reused = [], False
    else:
        vector_dests, reused = output_vectors(lmul, iterations, allow_reuse=False)
    scalar_dests, scalar_reused = scalar_output_sequence(iterations, scalar_policy)
    source_sequence = (
        mask_sources(lmul, iterations, source_policy)
        if spec.instr_id == "vcpop_m" and r11_diagnostic
        else [src_a] * iterations
    )
    scalar_pairs = [("x20", "x21", "x22"), ("x23", "x24", "x25"), ("x26", "x27", "x28"), ("x29", "x30", "x31")]
    lines = [
        "# Scalar pairing probe. Each vector instruction is followed by an add.",
        *marker_padding_lines(padding_bytes),
        "TIMESTAMP_MARK start",
    ]
    instances = []
    for index in range(iterations):
        dest = scalar_dests[index] if spec.result_kind == "scalar" else vector_dests[index]
        line_src_a = source_sequence[index]
        lines.append(emit_instruction(spec, dest=dest, src_a=line_src_a, src_b=src_b, scalar="x6"))
        scalar_dest, scalar_a, scalar_b = scalar_pairs[index % len(scalar_pairs)]
        lines.append(f"add {scalar_dest}, {scalar_a}, {scalar_b}")
        instances.append(
            {
                "index": index,
                "destination": dest,
                "source_a": line_src_a,
                "source_b": src_b,
                "scalar_add_destination": scalar_dest,
                "destination_reused": scalar_reused if spec.result_kind == "scalar" else reused,
            }
        )
    lines.append("TIMESTAMP_MARK end")
    body_meta = {
        "iterations": iterations,
        "instances": instances,
        "register_reuse": reused or scalar_reused,
    }
    if spec.result_kind == "scalar":
        body_meta["scalar_dest_policy"] = scalar_policy
    if r11_diagnostic:
        add_r11_metadata(
            body_meta,
            scalar_policy=scalar_policy,
            source_policy=source_policy,
            source_registers=source_sequence,
            padding_bytes=padding_bytes,
            body_instruction_count=iterations * 2,
        )
    return ["start", "end"], lines, body_meta


def body_t40(lmul: str) -> tuple[list[str], list[str], dict[str, Any]]:
    lines = [
        "# Common load-hit reference: warm an aligned vector load, then time",
        "# a repeated load plus dependent vector consumer.",
        "la x8, __rvv_load_hit_data",
        "vle32.v v2, (x8)",
        "TIMESTAMP_MARK start",
        "vle32.v v3, (x8)",
        "vadd.vv v4, v3, v2",
        "TIMESTAMP_MARK end",
    ]
    return ["start", "end"], lines, {
        "load_width_bits": SEW,
        "load_register": "v3",
        "consumer": "vadd_vv",
        "consumer_destination": "v4",
        "address_register": "x8",
        "data_label": "__rvv_load_hit_data",
        "cache_state": "synthetic_load_hit",
    }


def body_for_args(args: argparse.Namespace) -> tuple[list[str], list[str], dict[str, Any]]:
    template_id = args.template
    if template_id == "T00_BASELINE_MARKER":
        return body_t00()
    if template_id == "T40_COMMON_VLSU_LOAD_HIT":
        validate_lmul(args.lmul)
        return body_t40(args.lmul)

    spec = require_instruction(args.instr)
    validate_lmul(args.lmul)

    if template_id == "T01_DECODE_EXEC_KILLCHECK":
        return body_t01(spec, args.lmul)
    if template_id == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t10(
            spec,
            args.lmul,
            iterations,
            scalar_dest_policy(args),
            mask_source_policy(args),
            marker_padding_bytes(args),
            diagnostic_round(args) == "r11",
        )
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
        return body_t12(
            spec,
            args.lmul,
            filler_count,
            consumer,
            t12_filler(args),
            t12_consumer_role(args),
            t12_dependent_experiment_id(args) if t12_consumer_role(args) == "control" else None,
        )
    if template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        other = require_instruction(args.other_instr or default_other_instr(args.instr))
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t20(spec, other, args.lmul, iterations, t20_register_policy(args))
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T21_PAIR_WITH_SCALAR":
        iterations, note = default_iterations(template_id, args.lmul, args.iterations)
        markers, lines, meta = body_t21(
            spec,
            args.lmul,
            iterations,
            scalar_dest_policy(args),
            mask_source_policy(args),
            marker_padding_bytes(args),
            diagnostic_round(args) == "r11",
        )
        if note:
            meta["iteration_note"] = note
        return markers, lines, meta
    if template_id == "T30_LMUL_SCALING":
        shape = args.shape
        if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
            iterations, note = default_iterations(shape, args.lmul, args.iterations)
            markers, lines, meta = body_t10(spec, args.lmul, iterations, scalar_dest_policy(args))
        elif shape == "T11_SELF_RAW_CHAIN":
            iterations, note = default_iterations(shape, args.lmul, args.iterations)
            markers, lines, meta = body_t11(spec, args.lmul, iterations)
        elif shape == "T12_CONSUMER_RAW_GAP":
            note = None
            filler_count = args.filler_count if args.filler_count is not None else 0
            markers, lines, meta = body_t12(
                spec,
                args.lmul,
                filler_count,
                args.consumer or default_consumer(args.instr),
                t12_filler(args),
            )
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
    lowered_body_lines = lower_marker_lines(body_lines, experiment_id)
    body = indent_lines(lowered_body_lines)
    marker_summary = ", ".join(
        f"{entry['label']}={entry['symbol']}" for entry in marker_metadata_entries(experiment_id, markers)
    )
    return template.safe_substitute(
        experiment_id=experiment_id,
        template_id=template_id,
        sew=SEW,
        lmul=lmul or "none",
        marker_summary=marker_summary,
        setup_block=setup_block(lmul),
        body_block=body,
        data_block=data_block_for_template(template_id),
    )


def data_block_for_template(template_id: str) -> str:
    if template_id != "T40_COMMON_VLSU_LOAD_HIT":
        return ""
    values = ", ".join(str(index + 1) for index in range(VL_VALUE))
    return "\n".join(
        [
            "",
            "    .section .data",
            "    .balign 64",
            "__rvv_load_hit_data:",
            f"    .word {values}",
        ]
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
        shape_parameters: dict[str, Any] = {}
        if args.shape in {"T10_INDEPENDENT_STREAM_THROUGHPUT", "T11_SELF_RAW_CHAIN"}:
            iterations, _ = default_iterations(args.shape, args.lmul, args.iterations)
            shape_parameters["iterations"] = iterations
        elif args.shape == "T12_CONSUMER_RAW_GAP":
            shape_parameters["filler_count"] = args.filler_count if args.filler_count is not None else 0
            shape_parameters["consumer"] = args.consumer or default_consumer(args.instr)
            if t12_filler(args) != T12_DEFAULT_FILLER:
                shape_parameters["t12_filler"] = t12_filler(args)
        meta["scaling"] = {
            "shape": args.shape,
            "shape_parameters": shape_parameters,
            "fit_form": "base_plus_lmul_times_k",
            "suite_values": list(LMUL_FACTORS),
        }
    meta["body"] = body_metadata
    return meta


def generate_one(args: argparse.Namespace) -> dict[str, Path]:
    if args.template not in TEMPLATE_IDS:
        raise SystemExit(f"unknown template id {args.template!r}; valid ids: {', '.join(TEMPLATE_IDS)}")
    if args.template not in {"T00_BASELINE_MARKER", "T40_COMMON_VLSU_LOAD_HIT"}:
        if not args.instr:
            raise SystemExit(f"{args.template} requires --instr")
    if args.template != "T00_BASELINE_MARKER":
        if not args.lmul:
            raise SystemExit(f"{args.template} requires --lmul")
    if args.template == "T30_LMUL_SCALING" and args.shape not in T30_SHAPES:
        raise SystemExit(f"T30 --shape must be one of: {', '.join(T30_SHAPES)}")
    if args.iterations is not None and args.iterations <= 0:
        raise SystemExit("--iterations must be positive")
    if args.filler_count is not None and args.filler_count < 0:
        raise SystemExit("--filler-count must be non-negative")
    if diagnostic_round(args) is not None and diagnostic_round(args) not in DIAGNOSTIC_ROUNDS:
        raise SystemExit(f"--diagnostic-round must be one of: {', '.join(DIAGNOSTIC_ROUNDS)}")
    if mask_source_policy(args) not in MASK_SOURCE_POLICIES:
        raise SystemExit(f"--mask-source-policy must be one of: {', '.join(MASK_SOURCE_POLICIES)}")
    if marker_padding_bytes(args) < 0 or marker_padding_bytes(args) % 4 != 0:
        raise SystemExit("--marker-padding-bytes must be a non-negative multiple of 4")
    if t12_filler(args) not in T12_FILLERS:
        raise SystemExit(f"--t12-filler must be one of: {', '.join(T12_FILLERS)}")
    if t12_consumer_role(args) not in T12_CONSUMER_ROLES:
        raise SystemExit(f"--t12-consumer-role must be one of: {', '.join(T12_CONSUMER_ROLES)}")
    if args.template != "T12_CONSUMER_RAW_GAP" and t12_consumer_role(args) != T12_DEFAULT_CONSUMER_ROLE:
        raise SystemExit("--t12-consumer-role=control is only valid for T12_CONSUMER_RAW_GAP")

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
    asm_path.write_text(assembly.rstrip() + "\n", encoding="utf-8")
    write_yaml(yaml_path, metadata)
    return {"experiment_dir": experiment_dir, "assembly": asm_path, "metadata": yaml_path}


def suite_entries(args: argparse.Namespace) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    def add(template: str, instr: str | None = None, lmul: str | None = None, **extra: Any) -> None:
        ns = argparse.Namespace(
            template=template,
            instr=instr,
            lmul=lmul,
            other_instr=extra.get("other_instr"),
            consumer=extra.get("consumer"),
            shape=extra.get("shape", "T10_INDEPENDENT_STREAM_THROUGHPUT"),
            scalar_dest_policy=extra.get("scalar_dest_policy"),
            diagnostic_round=extra.get("diagnostic_round"),
            mask_source_policy=extra.get("mask_source_policy"),
            marker_padding_bytes=extra.get("marker_padding_bytes", DEFAULT_MARKER_PADDING_BYTES),
            t20_register_policy=extra.get("t20_register_policy"),
            t12_filler=extra.get("t12_filler", T12_DEFAULT_FILLER),
            t12_consumer_role=extra.get("t12_consumer_role", T12_DEFAULT_CONSUMER_ROLE),
            iterations=extra.get("iterations"),
            filler_count=extra.get("filler_count"),
            output_root=args.output_root,
            asm_template=args.asm_template,
            experiment_id=None,
        )
        experiment_id = make_experiment_id(ns)
        if experiment_id in seen_ids:
            raise SystemExit(f"duplicate generated experiment id: {experiment_id}")
        seen_ids.add(experiment_id)
        result_group = "common" if template in COMMON_RESULT_TEMPLATES else instr or "common"
        entry = {
            "id": experiment_id,
            "template_id": template,
            "result_group": result_group,
            "instruction_id": instr,
            "lmul": lmul,
            "argv": command_argv(ns, experiment_id),
        }
        for key in (
            "other_instr",
            "consumer",
            "shape",
            "scalar_dest_policy",
            "diagnostic_round",
            "mask_source_policy",
            "marker_padding_bytes",
            "t20_register_policy",
            "t12_filler",
            "t12_consumer_role",
            "iterations",
            "filler_count",
        ):
            value = getattr(ns, key)
            if value is None:
                continue
            if key == "marker_padding_bytes" and value == DEFAULT_MARKER_PADDING_BYTES and not diagnostic_round(ns):
                continue
            if key == "mask_source_policy" and value == DEFAULT_MASK_SOURCE_POLICY and not diagnostic_round(ns):
                continue
            if key == "t12_filler" and value == T12_DEFAULT_FILLER:
                continue
            if key == "t12_consumer_role" and value == T12_DEFAULT_CONSUMER_ROLE:
                continue
            entry[key] = value
        entries.append(entry)

    add("T00_BASELINE_MARKER")
    add("T40_COMMON_VLSU_LOAD_HIT", lmul="m1")
    for instr in INSTRUCTION_IDS:
        for lmul in LMUL_FACTORS:
            add("T01_DECODE_EXEC_KILLCHECK", instr, lmul)
            for iterations in suite_stream_iterations("T10_INDEPENDENT_STREAM_THROUGHPUT", instr, lmul):
                add("T10_INDEPENDENT_STREAM_THROUGHPUT", instr, lmul, iterations=iterations)
            if instr == "vcpop_m" and lmul == "m4":
                for iterations in suite_stream_iterations("T10_INDEPENDENT_STREAM_THROUGHPUT", instr, lmul):
                    add(
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instr,
                        lmul,
                        iterations=iterations,
                        scalar_dest_policy="fixed",
                    )
            for iterations in suite_stream_iterations("T11_SELF_RAW_CHAIN", instr, lmul):
                add("T11_SELF_RAW_CHAIN", instr, lmul, iterations=iterations)
            for filler_count in T12_FILLER_COUNTS:
                add("T12_CONSUMER_RAW_GAP", instr, lmul, filler_count=filler_count, consumer=default_consumer(instr))
            if (instr, lmul) in T12_SCALAR_FILLER_TARGETS:
                for filler_count in T12_FOCUSED_FILLER_COUNTS:
                    add(
                        "T12_CONSUMER_RAW_GAP",
                        instr,
                        lmul,
                        filler_count=filler_count,
                        consumer=default_consumer(instr),
                        t12_filler=T12_SCALAR_FILLER,
                    )
            if (instr, lmul) in T12_CONTROL_TARGETS:
                for filler_count in T12_FOCUSED_FILLER_COUNTS:
                    add(
                        "T12_CONSUMER_RAW_GAP",
                        instr,
                        lmul,
                        filler_count=filler_count,
                        consumer=default_consumer(instr),
                        t12_filler=T12_SCALAR_FILLER,
                        t12_consumer_role="control",
                    )
            add("T21_PAIR_WITH_SCALAR", instr, lmul)
            if instr == "vcpop_m" and lmul == "m4":
                for iterations in (7, 9):
                    add(
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instr,
                        lmul,
                        iterations=iterations,
                        diagnostic_round="r11",
                        scalar_dest_policy="rotated",
                        mask_source_policy="v0",
                        marker_padding_bytes=0,
                    )
                for iterations in (7, 9):
                    add(
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instr,
                        lmul,
                        iterations=iterations,
                        diagnostic_round="r11",
                        scalar_dest_policy="fixed",
                        mask_source_policy="v0",
                        marker_padding_bytes=0,
                    )
                for iterations in (7, 8, 9):
                    add(
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instr,
                        lmul,
                        iterations=iterations,
                        diagnostic_round="r11",
                        scalar_dest_policy="rotated",
                        mask_source_policy="v4",
                        marker_padding_bytes=0,
                    )
                for iterations in (7, 8, 9):
                    add(
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instr,
                        lmul,
                        iterations=iterations,
                        diagnostic_round="r11",
                        scalar_dest_policy="rotated",
                        mask_source_policy="v0",
                        marker_padding_bytes=28,
                    )
                for source_policy, scalar_policy in (("v0", "rotated"), ("v4", "rotated"), ("v0", "fixed")):
                    add(
                        "T21_PAIR_WITH_SCALAR",
                        instr,
                        lmul,
                        diagnostic_round="r11",
                        scalar_dest_policy=scalar_policy,
                        mask_source_policy=source_policy,
                        marker_padding_bytes=28,
                    )
            for iterations in suite_stream_iterations("T10_INDEPENDENT_STREAM_THROUGHPUT", instr, lmul):
                add("T30_LMUL_SCALING", instr, lmul, shape="T10_INDEPENDENT_STREAM_THROUGHPUT", iterations=iterations)
            for iterations in suite_stream_iterations("T11_SELF_RAW_CHAIN", instr, lmul):
                add("T30_LMUL_SCALING", instr, lmul, shape="T11_SELF_RAW_CHAIN", iterations=iterations)
            for filler_count in T12_FILLER_COUNTS:
                add(
                    "T30_LMUL_SCALING",
                    instr,
                    lmul,
                    shape="T12_CONSUMER_RAW_GAP",
                    filler_count=filler_count,
                    consumer=default_consumer(instr),
                )

    ids = list(INSTRUCTION_IDS)
    for left_index, left in enumerate(ids):
        for right in ids[left_index + 1 :]:
            for lmul in LMUL_FACTORS:
                for pair_count in suite_t20_pair_counts(left, right, lmul):
                    add("T20_PAIRWISE_PIPE_CLASSIFICATION", left, lmul, other_instr=right, iterations=pair_count)

    resource_ids = [instr for instr in INSTRUCTION_IDS if require_instruction(instr).result_kind != "scalar"]
    for left_index, left in enumerate(resource_ids):
        for right in resource_ids[left_index + 1 :]:
            for pair_count in T20_RESOURCE_NOREUSE_PAIR_COUNTS:
                add(
                    "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    left,
                    "m4",
                    other_instr=right,
                    iterations=pair_count,
                    t20_register_policy=T20_RESOURCE_NOREUSE_POLICY,
                )
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
        description="Generate deterministic RVV assembly profiling experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    one = subparsers.add_parser("one", help="generate one experiment directory")
    one.add_argument("--template", required=True, choices=TEMPLATE_IDS, help="experiment template id")
    one.add_argument("--instr", choices=INSTRUCTION_IDS, help="instruction id from docs/plan.md")
    one.add_argument("--lmul", choices=tuple(LMUL_FACTORS), help="LMUL value; SEW is fixed at e32")
    one.add_argument("--other-instr", choices=INSTRUCTION_IDS, help="second instruction for T20")
    one.add_argument(
        "--t20-register-policy",
        choices=T20_REGISTER_POLICIES,
        default="default",
        help="T20 register allocation policy; resource_noreuse_prefix uses distinct m4 vector destinations",
    )
    one.add_argument("--consumer", help="consumer id for T12/T30; default is result-kind aware")
    one.add_argument("--shape", choices=T30_SHAPES, default="T10_INDEPENDENT_STREAM_THROUGHPUT", help="base shape for T30")
    one.add_argument(
        "--t12-filler",
        choices=T12_FILLERS,
        default=T12_DEFAULT_FILLER,
        help="independent filler instruction for T12 gap probes",
    )
    one.add_argument(
        "--t12-consumer-role",
        choices=T12_CONSUMER_ROLES,
        default=T12_DEFAULT_CONSUMER_ROLE,
        help="T12 consumer role; control reads an independent initialized source instead of the producer result",
    )
    one.add_argument(
        "--scalar-dest-policy",
        choices=SCALAR_DEST_POLICIES,
        default=DEFAULT_SCALAR_DEST_POLICY,
        help="scalar-result destination allocation for T10/T30 throughput diagnostics",
    )
    one.add_argument("--diagnostic-round", choices=DIAGNOSTIC_ROUNDS, help="focused diagnostic round tag")
    one.add_argument(
        "--mask-source-policy",
        choices=MASK_SOURCE_POLICIES,
        default=DEFAULT_MASK_SOURCE_POLICY,
        help="mask source allocation for focused vcpop_m diagnostics",
    )
    one.add_argument(
        "--marker-padding-bytes",
        type=int,
        default=DEFAULT_MARKER_PADDING_BYTES,
        help="padding bytes inserted before the timed start marker",
    )
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
