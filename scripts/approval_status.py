#!/usr/bin/env python3
"""Shared top-level human approval status parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Any


HUMAN_APPROVAL_FILENAMES = ("human_approval.json", "human_approval.yaml", "human_approval.yml")
APPROVAL_STATUS_KEYS = frozenset(
    {
        "approved",
        "human_approved",
        "human_approval",
        "status",
        "human_approval_status",
        "approval_status",
    }
)
APPROVAL_STATUS_TEXT_KEYS = frozenset({"status", "human_approval_status", "approval_status"})
PASS_APPROVAL_VALUES = frozenset({"approved", "accepted", "pass", "passed", "granted", "yes", "true"})


def canonical_json_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def top_level_values_by_key(data: Any, names: set[str] | frozenset[str]) -> list[Any]:
    if not isinstance(data, dict):
        return []
    return [value for key, value in data.items() if canonical_json_key(key) in names]


def truthy_approval_status(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    lowered = str(value).strip().lower()
    return lowered in PASS_APPROVAL_VALUES or lowered.startswith(("approved ", "granted "))


def top_level_approval_decision(data: Any) -> dict[str, Any]:
    approval_values = top_level_values_by_key(data, APPROVAL_STATUS_KEYS)
    status_value = next(
        (
            str(value).strip().lower()
            for value in top_level_values_by_key(data, APPROVAL_STATUS_TEXT_KEYS)
            if str(value).strip()
        ),
        "",
    )
    approved = bool(approval_values) and all(truthy_approval_status(value) for value in approval_values)
    return {
        "approved": approved,
        "status": "approved" if approved else status_value or "present_unapproved",
        "values": approval_values,
    }


def common_result_root(profile_root: Path) -> Path:
    if profile_root.name == "common":
        return profile_root
    candidate = profile_root / "common"
    if candidate.exists():
        return candidate
    return profile_root


def human_approval_file(profile_root: Path) -> Path | None:
    root = common_result_root(profile_root)
    for name in HUMAN_APPROVAL_FILENAMES:
        path = root / name
        if path.exists():
            return path
    return None
