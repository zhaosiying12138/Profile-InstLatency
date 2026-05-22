#!/usr/bin/env python3
"""Extract LLVM RVV schedule-model fields for the profiling seed set.

The script intentionally uses only the Python standard library so it can run in
early repository bootstrap environments. It reads LLVM TableGen sources as
plain text and records deterministic evidence references instead of attempting
to be a full TableGen evaluator.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


DEFAULT_LLVM_ROOT = Path("/home/zhaosiying/codebase/compiler/llvm-project-21")
RISCV_DIR = Path("llvm/lib/Target/RISCV")
LLVM_FILES = (
    RISCV_DIR / "RISCVScheduleV.td",
    RISCV_DIR / "RISCVSchedSiFiveP800.td",
    RISCV_DIR / "RISCVInstrInfoV.td",
    RISCV_DIR / "RISCVInstrInfoVPseudos.td",
)


@dataclass(frozen=True)
class InstructionSpec:
    instr_id: str
    asm: str
    family: str
    td_names: tuple[str, ...]
    root_mnemonics: tuple[str, ...]
    lmul_dependent: bool
    sew_dependent: bool


SELECTED_INSTRUCTIONS: tuple[InstructionSpec, ...] = (
    InstructionSpec("vadd_vv", "vadd.vv", "WriteVIALUV", ("VADD_V",), ("vadd",), True, False),
    InstructionSpec("vsll_vv", "vsll.vv", "WriteVShiftV", ("VSLL_V",), ("vsll",), True, False),
    InstructionSpec("vmul_vv", "vmul.vv", "WriteVIMulV", ("VMUL_V",), ("vmul",), True, False),
    InstructionSpec("vdivu_vv", "vdivu.vv", "WriteVIDivV", ("VDIVU_V",), ("vdivu",), True, True),
    InstructionSpec("vmseq_vv", "vmseq.vv", "WriteVICmpV", ("VMSEQ_V",), ("vmseq",), True, False),
    InstructionSpec("vcpop_m", "vcpop.m", "WriteVMPopV", ("VCPOP_M",), ("vcpop.m",), True, False),
    InstructionSpec("viota_m", "viota.m", "WriteVIotaV", ("VIOTA_M",), ("viota.m",), True, False),
    InstructionSpec(
        "vslideup_vx",
        "vslideup.vx",
        "WriteVSlideUpX",
        ("VSLIDEUP_V",),
        ("vslideup",),
        True,
        False,
    ),
    InstructionSpec(
        "vrgather_vv",
        "vrgather.vv",
        "WriteVRGatherVV",
        ("VRGATHER_V",),
        ("vrgather",),
        True,
        True,
    ),
    InstructionSpec("vredsum_vs", "vredsum.vs", "WriteVIRedV_From", ("VREDSUM",), ("vredsum",), True, True),
)


PROFILE_FIELDS: tuple[Mapping[str, object], ...] = (
    OrderedDict(
        (
            ("name", "proc_resources"),
            ("llvm_source", "ProcResource or ProcResGroup used by WriteRes/SchedWriteRes"),
            ("profile_action", "infer"),
            ("reason", "identifies which execution pipe or resource group the write occupies"),
        )
    ),
    OrderedDict(
        (
            ("name", "latency"),
            ("llvm_source", "Latency"),
            ("profile_action", "infer"),
            ("reason", "models producer-to-consumer readiness for dependent scheduling"),
        )
    ),
    OrderedDict(
        (
            ("name", "release_at_cycles"),
            ("llvm_source", "ReleaseAtCycles"),
            ("profile_action", "infer"),
            ("reason", "models resource occupancy and independent-stream throughput"),
        )
    ),
    OrderedDict(
        (
            ("name", "acquire_at_cycles"),
            ("llvm_source", "AcquireAtCycles"),
            ("profile_action", "assume_default_empty_then_confirm_if_needed"),
            ("reason", "only needed if resource acquisition is delayed relative to issue"),
        )
    ),
    OrderedDict(
        (
            ("name", "num_micro_ops"),
            ("llvm_source", "NumMicroOps"),
            ("profile_action", "assume_one_then_probe"),
            ("reason", "feeds IssueWidth pressure and scalar-pairing behavior"),
        )
    ),
    OrderedDict(
        (
            ("name", "single_issue"),
            ("llvm_source", "SingleIssue, BeginGroup, EndGroup"),
            ("profile_action", "assume_false_then_probe"),
            ("reason", "captures instructions that must occupy a dispatch group alone"),
        )
    ),
    OrderedDict(
        (
            ("name", "read_advance"),
            ("llvm_source", "ReadAdvance or SchedReadAdvance"),
            ("profile_action", "infer_only_for_consumer_specific_bypass"),
            ("reason", "adjusts latency for particular producer and consumer read pairs"),
        )
    ),
)

PROCESSOR_FIELDS: tuple[Mapping[str, object], ...] = (
    OrderedDict(
        (
            ("name", "issue_width"),
            ("llvm_source", "MCSchedModel::IssueWidth"),
            ("profile_action", "common_processor_measurement"),
            ("reason", "hard limit on same-cycle scheduled micro-ops"),
        )
    ),
    OrderedDict(
        (
            ("name", "micro_op_buffer_size"),
            ("llvm_source", "MCSchedModel::MicroOpBufferSize"),
            ("profile_action", "common_processor_assumption"),
            ("reason", "0 or 1 models in-order scheduling; greater than 1 means out-of-order"),
        )
    ),
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a deterministic LLVM RVV schedule field map for the selected profiling instructions."
    )
    parser.add_argument(
        "--llvm-root",
        type=Path,
        default=DEFAULT_LLVM_ROOT,
        help=f"LLVM checkout root to read. Default: {DEFAULT_LLVM_ROOT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/common/llvm_field_map.yaml"),
        help="YAML output path.",
    )
    return parser.parse_args(argv)


def load_sources(llvm_root: Path) -> tuple[OrderedDict[str, list[str]], list[str]]:
    if not llvm_root.exists():
        raise FileNotFoundError(
            f"LLVM checkout not found at {llvm_root}. Pass --llvm-root /path/to/llvm-project-21 or create the checkout."
        )
    if not (llvm_root / RISCV_DIR).is_dir():
        raise FileNotFoundError(
            f"LLVM RISC-V target directory not found under {llvm_root / RISCV_DIR}. "
            "Pass --llvm-root pointing at an LLVM project checkout."
        )

    sources: OrderedDict[str, list[str]] = OrderedDict()
    missing: list[str] = []
    for rel in LLVM_FILES:
        path = llvm_root / rel
        key = rel.as_posix()
        if path.exists():
            sources[key] = path.read_text(encoding="utf-8").splitlines()
        else:
            missing.append(key)
    return sources, missing


def evidence_entry(relpath: str, line_no: int, text: str) -> OrderedDict[str, object]:
    return OrderedDict((("file", relpath), ("line", line_no), ("text", text.strip())))


def find_lines(
    sources: Mapping[str, Sequence[str]],
    regexes: Iterable[re.Pattern[str]],
    *,
    max_entries: int,
    preferred_files: Sequence[str] = (),
) -> list[OrderedDict[str, object]]:
    results: list[OrderedDict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    ordered_sources: list[tuple[str, Sequence[str]]] = []
    for preferred in preferred_files:
        if preferred in sources:
            ordered_sources.append((preferred, sources[preferred]))
    for item in sources.items():
        if item[0] not in preferred_files:
            ordered_sources.append(item)

    for relpath, lines in ordered_sources:
        for idx, line in enumerate(lines, start=1):
            if any(regex.search(line) for regex in regexes):
                key = (relpath, idx)
                if key not in seen:
                    results.append(evidence_entry(relpath, idx, line))
                    seen.add(key)
                    if len(results) >= max_entries:
                        return results
    return results


def statement_from_line(lines: Sequence[str], start_idx: int) -> str:
    parts: list[str] = []
    for idx in range(start_idx, min(start_idx + 8, len(lines))):
        text = lines[idx].strip()
        if text:
            parts.append(text)
        if ";" in text:
            break
    return " ".join(parts)


def family_statements(sources: Mapping[str, Sequence[str]], family: str) -> list[OrderedDict[str, object]]:
    preferred = (
        (RISCV_DIR / "RISCVInstrInfoV.td").as_posix(),
        (RISCV_DIR / "RISCVInstrInfoVPseudos.td").as_posix(),
    )
    entries: list[OrderedDict[str, object]] = []
    family_re = re.compile(rf"\b{re.escape(family)}\b")
    for relpath in preferred:
        lines = sources.get(relpath)
        if not lines:
            continue
        for idx, line in enumerate(lines):
            if family_re.search(line):
                entries.append(
                    OrderedDict(
                        (
                            ("file", relpath),
                            ("line", idx + 1),
                            ("statement", statement_from_line(lines, idx)),
                        )
                    )
                )
                if len(entries) >= 6:
                    return entries
    return entries


LET_RE = re.compile(r"let\s+Latency\s*=\s*(?P<lat>.*?),\s*ReleaseAtCycles\s*=\s*(?P<rel>\[[^\]]*\])\s+in")
RESOURCES_RE = re.compile(r"<\"(?P<family>[^\"]+)\",\s*\[(?P<resources>[^\]]*)\]")


def enclosing_latency(lines: Sequence[str], line_idx: int) -> tuple[str | None, str | None]:
    for idx in range(line_idx, max(-1, line_idx - 12), -1):
        match = LET_RE.search(lines[idx])
        if match:
            return match.group("lat").strip(), match.group("rel").strip()
    return None, None


def sifive_examples(sources: Mapping[str, Sequence[str]], family: str) -> list[OrderedDict[str, object]]:
    relpath = (RISCV_DIR / "RISCVSchedSiFiveP800.td").as_posix()
    lines = sources.get(relpath, ())
    examples: list[OrderedDict[str, object]] = []
    for idx, line in enumerate(lines):
        if f'"{family}"' not in line:
            continue
        resources_match = RESOURCES_RE.search(line)
        resources: list[str] = []
        if resources_match:
            resources = [item.strip() for item in resources_match.group("resources").split(",") if item.strip()]
        latency, release = enclosing_latency(lines, idx)
        examples.append(
            OrderedDict(
                (
                    ("file", relpath),
                    ("line", idx + 1),
                    ("resources", resources),
                    ("latency_expr", latency),
                    ("release_at_cycles_expr", release),
                    ("text", line.strip()),
                )
            )
        )
    return examples


def schedule_declarations(sources: Mapping[str, Sequence[str]], family: str) -> list[OrderedDict[str, object]]:
    preferred = ((RISCV_DIR / "RISCVScheduleV.td").as_posix(),)
    patterns = (
        re.compile(rf"LMUL\w*SchedWrites<\"{re.escape(family)}\""),
        re.compile(rf"LMUL\w*WriteRes<\"{re.escape(family)}\""),
    )
    return find_lines(sources, patterns, max_entries=8, preferred_files=preferred)


def instruction_definitions(sources: Mapping[str, Sequence[str]], spec: InstructionSpec) -> list[OrderedDict[str, object]]:
    escaped_td = "|".join(re.escape(name) for name in spec.td_names)
    escaped_roots = "|".join(re.escape(root) for root in spec.root_mnemonics)
    patterns = [
        re.compile(rf"\bdefm?\s+({escaped_td})\b"),
        re.compile(rf"\"({escaped_roots})\""),
        re.compile(re.escape(spec.asm)),
    ]
    preferred = (
        (RISCV_DIR / "RISCVInstrInfoV.td").as_posix(),
        (RISCV_DIR / "RISCVInstrInfoVPseudos.td").as_posix(),
    )
    return find_lines(sources, patterns, max_entries=8, preferred_files=preferred)


def discovery_status(spec: InstructionSpec, evidence: Mapping[str, Sequence[object]]) -> str:
    if evidence["instruction_definitions"] and evidence["sched_family_uses"]:
        return "found"
    if evidence["instruction_definitions"] or evidence["sched_family_uses"]:
        return "partial"
    return "not_found"


def make_instruction_record(
    sources: Mapping[str, Sequence[str]], spec: InstructionSpec
) -> OrderedDict[str, object]:
    source_evidence = OrderedDict(
        (
            ("instruction_definitions", instruction_definitions(sources, spec)),
            ("sched_family_uses", family_statements(sources, spec.family)),
            ("schedule_declarations", schedule_declarations(sources, spec.family)),
            ("sifive_p800_write_res_examples", sifive_examples(sources, spec.family)),
        )
    )
    return OrderedDict(
        (
            ("asm_mnemonic", spec.asm),
            ("sched_write_family", spec.family),
            ("discovery_status", discovery_status(spec, source_evidence)),
            (
                "profile_variant_space",
                OrderedDict(
                    (
                        ("selected_sew", 32),
                        ("selected_lmul", ["m1", "m2", "m4"]),
                        ("lmul_dependent_family", spec.lmul_dependent),
                        ("sew_dependent_family", spec.sew_dependent),
                    )
                ),
            ),
            ("source_evidence", source_evidence),
            ("llvm_fields_to_profile", [OrderedDict(field) for field in PROFILE_FIELDS]),
        )
    )


def make_map(llvm_root: Path, sources: Mapping[str, Sequence[str]], missing_files: Sequence[str]) -> OrderedDict[str, object]:
    instructions = OrderedDict(
        (spec.instr_id, make_instruction_record(sources, spec)) for spec in SELECTED_INSTRUCTIONS
    )
    return OrderedDict(
        (
            ("schema_version", 1),
            ("generated_by", "scripts/llvm_sched_extract.py"),
            ("llvm_root", str(llvm_root)),
            ("read_files", list(sources.keys())),
            ("missing_files", list(missing_files)),
            ("processor_fields_to_profile", [OrderedDict(field) for field in PROCESSOR_FIELDS]),
            ("instructions", instructions),
        )
    )


def yaml_scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def yaml_key(key: object) -> str:
    text = str(key)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        return text
    return yaml_scalar(text)


def to_yaml(value: object, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        if not value:
            return [prefix + "{}"]
        lines: list[str] = []
        for key, item in value.items():
            key_text = yaml_key(key)
            if isinstance(item, Mapping):
                if item:
                    lines.append(f"{prefix}{key_text}:")
                    lines.extend(to_yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key_text}: {{}}")
            elif isinstance(item, list):
                if item:
                    lines.append(f"{prefix}{key_text}:")
                    lines.extend(to_yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}{key_text}: []")
            else:
                lines.append(f"{prefix}{key_text}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [prefix + "[]"]
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                if not item:
                    lines.append(prefix + "- {}")
                    continue
                entries = list(item.items())
                first_key, first_value = entries[0]
                lines.append(f"{prefix}- {yaml_key(first_key)}: {yaml_scalar(first_value)}")
                rest = OrderedDict(entries[1:])
                if rest:
                    lines.extend(to_yaml(rest, indent + 2))
            elif isinstance(item, list):
                lines.append(prefix + "-")
                lines.extend(to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
        return lines
    return [prefix + yaml_scalar(value)]


def write_yaml(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    contents = "\n".join(to_yaml(data)) + "\n"
    path.write_text(contents, encoding="utf-8")


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    llvm_root = args.llvm_root.expanduser().resolve()
    output = args.output

    try:
        sources, missing_files = load_sources(llvm_root)
    except FileNotFoundError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if not sources:
        print(
            f"error: no expected LLVM RISC-V TableGen files were found under {llvm_root / RISCV_DIR}.",
            file=sys.stderr,
        )
        return 2

    data = make_map(llvm_root, sources, missing_files)
    write_yaml(output, data)
    print(f"wrote {output} with {len(SELECTED_INSTRUCTIONS)} instruction records")
    if missing_files:
        print("warning: missing optional LLVM files: " + ", ".join(missing_files), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
