#!/usr/bin/env python3
"""Entrypoint for the RVV decode/execute kill-check suite."""

from __future__ import annotations

import sys

import run_suite


def main(argv: list[str] | None = None) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    if "--killcheck" not in forwarded:
        forwarded.insert(0, "--killcheck")
    return run_suite.main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
