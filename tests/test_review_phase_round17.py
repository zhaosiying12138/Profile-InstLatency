import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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


analyze_quality = load_script_module("analyze_quality_round17_under_test", "scripts/analyze_quality.py")
gen_asm = load_script_module("gen_asm_round17_under_test", "scripts/gen_asm.py")
search_model = load_script_module("search_model_round17_under_test", "scripts/search_model.py")


def quality_item(*, experiment_id, template_id, instruction_id="vadd_vv", lmul="m1"):
    return analyze_quality.ExperimentAnalysis(
        trace_path=Path(f"/tmp/{experiment_id}/trace.json"),
        experiment_path=Path(f"/tmp/{experiment_id}/experiment.yaml"),
        experiment_id=experiment_id,
        template_id=template_id,
        backend="gem5_minor",
        mode="real_platform_profile",
        dry_run_trace=False,
        marker_baseline_cycles=0,
        instruction_id=instruction_id,
        asm=None,
        llvm_sched_write=None,
        lmul=lmul,
        body={"iterations": 2},
        pair_instruction_id=None,
        scaling_shape=None,
        timestamp_model_kind=None,
        timestamp_model_occupies_issue_slot=None,
        marker_definitions=(),
        synthetic={},
        markers=(),
        adjacent_deltas=(),
        named_deltas=(("start", "end", 3),),
        warnings=(),
    )


def write_real_trace(root):
    exp_dir = root / "vadd_vv" / "experiments" / "t10-vadd-vv-m1-n2"
    exp_dir.mkdir(parents=True)
    (root / "common").mkdir()
    (exp_dir / "trace.json").write_text(
        json.dumps(
            {
                "mode": "real_platform_profile",
                "backend": "gem5_minor",
                "dry_run_trace": False,
                "experiment_id": "t10-vadd-vv-m1-n2",
                "template_id": "T10_INDEPENDENT_STREAM_THROUGHPUT",
                "instruction_id": "vadd_vv",
                "lmul": "m1",
                "marker_baseline_cycles": 0,
                "observation": {"iterations": 2},
                "entries": [
                    {"marker": "start", "cycle": 10, "pc": "0x80000000"},
                    {"marker": "end", "cycle": 13, "pc": "0x80000004"},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


class ReviewPhaseRound17Test(unittest.TestCase):
    def test_quality_requirements_use_manifest_without_synthetic_traces(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "suite_manifest.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "experiments:",
                        "  -",
                        "    id: t10-vadd-vv-m1-n2",
                        "    template_id: T10_INDEPENDENT_STREAM_THROUGHPUT",
                        "    result_group: vadd_vv",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            inventory = analyze_quality.build_quality_inventory(
                [quality_item(experiment_id="t10-vadd-vv-m1-n2", template_id="T10_INDEPENDENT_STREAM_THROUGHPUT")],
                root,
            )

            self.assertEqual(inventory["coverage"]["required_template_source"], "suite_manifest")
            self.assertEqual(inventory["coverage"]["required_templates"], ["T10_INDEPENDENT_STREAM_THROUGHPUT"])
            self.assertEqual(inventory["coverage"]["required_template_instruction_lmul_total"], 1)
            self.assertTrue(inventory["gate"]["checks"]["required_templates_covered_by_real_gem5"])
            self.assertTrue(inventory["gate"]["checks"]["required_template_instruction_lmul_covered_by_real_gem5"])

    def test_search_model_writes_real_platform_artifacts_from_selected_trace_metadata(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "results_repeat" / "r01"
            write_real_trace(root)

            with (
                mock.patch.object(sys, "argv", ["search_model.py", "--profile", root.as_posix(), "--format", "markdown"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                status = search_model.main()

            self.assertEqual(status, 0)
            self.assertTrue((root / "common" / "real_platform_field_status.json").exists())
            self.assertTrue((root / "vadd_vv" / "profile.real_platform.yaml").exists())

    def test_default_t12_vector_filler_records_regeneration_cadence(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vadd_vv",
                "--lmul",
                "m4",
                "--filler-count",
                "2",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, _lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["filler_instruction_id"], "vadd_vv")
        self.assertEqual(meta["filler_cadence_cycles"], 1)
        self.assertEqual(meta["gap_sweep"]["independent_filler_cadence_cycles"], 1)


if __name__ == "__main__":
    unittest.main()
