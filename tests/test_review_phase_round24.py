import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = load_script_module("check_calibration_gate_round24_under_test", "scripts/check_calibration_gate.py")


def write_real_trace(root: Path, trace_dir_name: str, experiment_id: str) -> None:
    exp_dir = root / "vadd_vv" / "experiments" / trace_dir_name
    exp_dir.mkdir(parents=True)
    (exp_dir / "trace.json").write_text(
        json.dumps(
            {
                "mode": "real_platform_profile",
                "backend": "gem5_minor",
                "dry_run_trace": False,
                "experiment_id": experiment_id,
                "template_id": "T30_LMUL_SCALING",
                "result_group": "vadd_vv",
                "instruction_id": "vadd_vv",
                "lmul": "m1",
                "entries": [
                    {"marker": "start", "cycle": 10, "pc": "0x80000000"},
                    {"marker": "end", "cycle": 14, "pc": "0x80000004"},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_t00_trace(root: Path, trace_dir_name: str) -> None:
    exp_dir = root / "common" / "experiments" / trace_dir_name
    exp_dir.mkdir(parents=True)
    (exp_dir / "trace.json").write_text(
        json.dumps(
            {
                "mode": "real_platform_profile",
                "backend": "gem5_minor",
                "dry_run_trace": False,
                "experiment_id": "t00-marker",
                "template_id": "T00_BASELINE_MARKER",
                "result_group": "common",
                "instruction_id": None,
                "lmul": "m1",
                "entries": [
                    {"marker": "t0", "cycle": 10, "pc": "0x80000000"},
                    {"marker": "t1", "cycle": 10, "pc": "0x80000004"},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


class ReviewPhaseRound24Test(unittest.TestCase):
    def test_real_gate_uses_grouped_manifest_coverage(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "focused"
            root.mkdir()
            (root / "suite_manifest.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "experiments:",
                        "  -",
                        "    id: t30-vadd-vv-t10-m1-n2",
                        "    template_id: T30_LMUL_SCALING",
                        "    result_group: vadd_vv",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                        "  -",
                        "    id: t30-vadd-vv-t12-m1-k7",
                        "    template_id: T30_LMUL_SCALING",
                        "    result_group: vadd_vv",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            write_real_trace(root, "repeat-a", "t30-vadd-vv-t10-m1-n2")
            write_real_trace(root, "repeat-b", "t30-vadd-vv-t10-m1-n2")

            with (
                mock.patch.object(gate, "load_inventory", return_value=(root / "common" / "real_platform_inventory.json", {}, [])),
                mock.patch.object(gate, "human_approval_failures", return_value=(True, [], {"status": "approved"})),
                mock.patch.object(gate, "real_platform_field_status_failures", return_value=[]),
                mock.patch.object(gate, "marker_contract_failures", return_value=[]),
                mock.patch.object(gate, "confidence_failures", return_value=[]),
                mock.patch.object(gate, "conflict_status_failures", return_value=[]),
                mock.patch.object(gate, "has_documented_assumptions", return_value=True),
            ):
                failures = gate.real_platform_failures(
                    "Mode: real_platform_profile\nGate status: PASS\n## Assumptions\nGrouped coverage.",
                    root,
                )

        joined = "\n".join(failures)
        self.assertNotIn("real gem5 coverage", joined)
        self.assertNotIn("repeatability/stability", joined)
        self.assertEqual(failures, [])

    def test_manifest_null_lmul_group_is_covered_by_real_t00_lmul_trace(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "focused"
            root.mkdir()
            (root / "suite_manifest.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "experiments:",
                        "  -",
                        "    id: t00-marker",
                        "    template_id: T00_BASELINE_MARKER",
                        "    result_group: common",
                        "    instruction_id: null",
                        "    lmul: null",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            write_t00_trace(root, "repeat-a")
            write_t00_trace(root, "repeat-b")

            with (
                mock.patch.object(gate, "load_inventory", return_value=(root / "common" / "real_platform_inventory.json", {}, [])),
                mock.patch.object(gate, "human_approval_failures", return_value=(True, [], {"status": "approved"})),
                mock.patch.object(gate, "real_platform_field_status_failures", return_value=[]),
                mock.patch.object(gate, "marker_contract_failures", return_value=[]),
                mock.patch.object(gate, "confidence_failures", return_value=[]),
                mock.patch.object(gate, "conflict_status_failures", return_value=[]),
                mock.patch.object(gate, "has_documented_assumptions", return_value=True),
            ):
                failures = gate.real_platform_failures(
                    "Mode: real_platform_profile\nGate status: PASS\n## Assumptions\nGrouped coverage.",
                    root,
                )

        joined = "\n".join(failures)
        self.assertNotIn("real gem5 coverage", joined)
        self.assertNotIn("repeatability/stability", joined)
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
