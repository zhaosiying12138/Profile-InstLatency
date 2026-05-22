#!/usr/bin/env python3
"""Prepare the gated LLVM YuShuXin schedule-model worktree.

Default mode is dry-run. The script verifies the requested LLVM tag/commit
exists before printing the exact worktree command. It mutates state only when
`--execute` is provided.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


DEFAULT_LLVM_ROOT = "/home/zhaosiying/codebase/compiler/llvm-project-21"
DEFAULT_WORKTREE = "/home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model"
DEFAULT_BRANCH = "riscv-yushuxin-sched-model"


def run_git(llvm_root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(llvm_root), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def shell_join(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the gated LLVM YuShuXin worktree.")
    parser.add_argument("--llvm-root", default=DEFAULT_LLVM_ROOT, help="Existing LLVM git checkout.")
    parser.add_argument("--tag", default="llvmorg-22.1.3", help="LLVM tag or commit to verify.")
    parser.add_argument("--worktree-path", default=DEFAULT_WORKTREE, help="Destination worktree path.")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="New branch name for the worktree.")
    parser.add_argument("--cpu", default="YuShuXin", help="CPU spelling expected by the downstream LLVM patch.")
    parser.add_argument("--execute", action="store_true", help="Actually run git worktree add.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    llvm_root = Path(args.llvm_root)
    worktree_path = Path(args.worktree_path)

    if not llvm_root.exists():
        print(f"FAIL: LLVM root does not exist: {llvm_root}")
        return 2
    inside = run_git(llvm_root, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        print(f"FAIL: LLVM root is not a git worktree: {llvm_root}")
        if inside.stderr:
            print(inside.stderr.strip())
        return 2

    resolved = run_git(llvm_root, ["rev-parse", f"{args.tag}^{{commit}}"])
    if resolved.returncode != 0:
        print(f"FAIL: tag/commit is not available in {llvm_root}: {args.tag}")
        print("Do not guess an alternate tag such as v22.1.3; fetch or verify the local tag name first.")
        if resolved.stderr:
            print(resolved.stderr.strip())
        return 1

    commit = resolved.stdout.strip()
    command = [
        "git",
        "-C",
        str(llvm_root),
        "worktree",
        "add",
        "-b",
        args.branch,
        str(worktree_path),
        args.tag,
    ]

    print(f"LLVM root: {llvm_root}")
    print(f"Verified {args.tag} -> {commit}")
    print(f"Target CPU spelling for downstream tests: {args.cpu}")
    print(f"Worktree command: {shell_join(command)}")
    print("Calibration reminder: run `python3 scripts/check_calibration_gate.py --mode synthetic_calibration` before LLVM edits.")

    if not args.execute:
        print("Dry-run only. Re-run with --execute to create the worktree.")
        return 0

    if worktree_path.exists():
        print(f"FAIL: worktree path already exists: {worktree_path}")
        return 1

    result = subprocess.run(command, text=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
