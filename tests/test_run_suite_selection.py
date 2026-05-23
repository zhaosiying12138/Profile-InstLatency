import argparse
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_script_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_suite = load_script_module("run_suite_under_test", "scripts/run_suite.py")


def write_manifest(generated_root, entries):
    generated_root.mkdir(parents=True)
    lines = [
        "schema_version: 1",
        "experiments:",
    ]
    for entry in entries:
        lines.extend(
            [
                "  -",
                f"    id: {entry['id']}",
                f"    template_id: {entry['template_id']}",
                f"    result_group: {entry['result_group']}",
                f"    instruction_id: {entry['instruction_id']}",
                f"    lmul: {entry['lmul']}",
            ]
        )
    (generated_root / "suite_manifest.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def args_for(generated_root, results_root, **overrides):
    defaults = {
        "generated_root": generated_root,
        "results_root": results_root,
        "killcheck": False,
        "all": True,
        "id_regex": [],
        "template_id": [],
        "missing": False,
        "repeat": 1,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class RunSuiteSelectionTest(unittest.TestCase):
    def test_template_and_id_regex_filters_select_only_matching_entries(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            generated_root = root / "generated"
            entries = [
                {
                    "id": "t20-vadd-vv-vsll-vv-m4-n3-resource-noreuse",
                    "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    "result_group": "vadd_vv",
                    "instruction_id": "vadd_vv",
                    "lmul": "m4",
                },
                {
                    "id": "t20-vadd-vv-vsll-vv-m4-n3",
                    "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    "result_group": "vadd_vv",
                    "instruction_id": "vadd_vv",
                    "lmul": "m4",
                },
                {
                    "id": "t12-vadd-vv-m4-k1-resource-noreuse",
                    "template_id": "T12_CONSUMER_RAW_GAP",
                    "result_group": "vadd_vv",
                    "instruction_id": "vadd_vv",
                    "lmul": "m4",
                },
            ]
            write_manifest(generated_root, entries)

            selected = run_suite.selected_entries(
                args_for(
                    generated_root,
                    root / "results",
                    template_id=["T20_PAIRWISE_PIPE_CLASSIFICATION"],
                    id_regex=["resource-noreuse$"],
                )
            )

            self.assertEqual(
                [entry["id"] for entry in selected],
                ["t20-vadd-vv-vsll-vv-m4-n3-resource-noreuse"],
            )

    def test_missing_filters_to_absent_repeat_trace_paths(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            generated_root = root / "generated"
            results_root = root / "results"
            entries = [
                {
                    "id": "t20-complete-resource-noreuse",
                    "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    "result_group": "vadd_vv",
                    "instruction_id": "vadd_vv",
                    "lmul": "m4",
                },
                {
                    "id": "t20-partial-resource-noreuse",
                    "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    "result_group": "vsll_vv",
                    "instruction_id": "vsll_vv",
                    "lmul": "m4",
                },
                {
                    "id": "t20-absent-resource-noreuse",
                    "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                    "result_group": "vmul_vv",
                    "instruction_id": "vmul_vv",
                    "lmul": "m4",
                },
            ]
            write_manifest(generated_root, entries)
            for repeat in ("r01", "r02"):
                trace_path = (
                    results_root
                    / repeat
                    / "vadd_vv"
                    / "experiments"
                    / "t20-complete-resource-noreuse"
                    / "trace.json"
                )
                trace_path.parent.mkdir(parents=True)
                trace_path.write_text("{}\n", encoding="utf-8")
            partial_trace = (
                results_root
                / "r01"
                / "vsll_vv"
                / "experiments"
                / "t20-partial-resource-noreuse"
                / "trace.json"
            )
            partial_trace.parent.mkdir(parents=True)
            partial_trace.write_text("{}\n", encoding="utf-8")

            selected = run_suite.selected_run_items(
                args_for(
                    generated_root,
                    results_root,
                    template_id=["T20_PAIRWISE_PIPE_CLASSIFICATION"],
                    id_regex=["resource-noreuse$"],
                    missing=True,
                    repeat=2,
                )
            )

            self.assertEqual(
                [(repeat, entry["id"]) for repeat, entry in selected],
                [
                    (1, "t20-absent-resource-noreuse"),
                    (2, "t20-partial-resource-noreuse"),
                    (2, "t20-absent-resource-noreuse"),
                ],
            )

    def test_filters_that_match_nothing_raise_clear_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            generated_root = root / "generated"
            write_manifest(
                generated_root,
                [
                    {
                        "id": "t20-vadd-vv-vsll-vv-m4-n3",
                        "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                        "result_group": "vadd_vv",
                        "instruction_id": "vadd_vv",
                        "lmul": "m4",
                    }
                ],
            )

            with self.assertRaisesRegex(run_suite.ExperimentError, "selection filters matched no experiments"):
                run_suite.selected_entries(
                    args_for(generated_root, root / "results", id_regex=["does-not-match"])
                )

    def test_killcheck_selection_behavior_is_preserved_without_filters(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            generated_root = root / "generated"
            write_manifest(
                generated_root,
                [
                    {
                        "id": "t01-vadd-vv-m1",
                        "template_id": "T01_DECODE_EXEC_KILLCHECK",
                        "result_group": "common",
                        "instruction_id": "vadd_vv",
                        "lmul": "m1",
                    },
                    {
                        "id": "t20-vadd-vv-vsll-vv-m4-n3",
                        "template_id": "T20_PAIRWISE_PIPE_CLASSIFICATION",
                        "result_group": "vadd_vv",
                        "instruction_id": "vadd_vv",
                        "lmul": "m4",
                    },
                ],
            )

            selected = run_suite.selected_entries(
                args_for(generated_root, root / "results", killcheck=True, all=False)
            )

            self.assertEqual([entry["id"] for entry in selected], ["t01-vadd-vv-m1"])


if __name__ == "__main__":
    unittest.main()
