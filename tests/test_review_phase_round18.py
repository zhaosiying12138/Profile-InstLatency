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


analyze_quality = load_script_module("analyze_quality_round18_under_test", "scripts/analyze_quality.py")
gen_asm = load_script_module("gen_asm_round18_under_test", "scripts/gen_asm.py")


def quality_item(*, experiment_id, template_id, mode, backend, instruction_id="vadd_vv", lmul="m1"):
    return analyze_quality.ExperimentAnalysis(
        trace_path=Path(f"/tmp/{experiment_id}/trace.json"),
        experiment_path=Path(f"/tmp/{experiment_id}/experiment.yaml"),
        experiment_id=experiment_id,
        template_id=template_id,
        backend=backend,
        mode=mode,
        dry_run_trace="synthetic" in mode,
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


class ReviewPhaseRound18Test(unittest.TestCase):
    def test_quality_inventory_excludes_deferred_t40_from_required_coverage(self):
        real_t10 = quality_item(
            experiment_id="t10-vadd-vv-m1-n2",
            template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
            mode="real_platform_profile",
            backend="gem5_minor",
        )
        synthetic_t10 = quality_item(
            experiment_id="synthetic-t10-vadd-vv-m1-n2",
            template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
            mode="synthetic_calibration",
            backend="synthetic",
        )
        synthetic_t40 = quality_item(
            experiment_id="synthetic-t40-load-hit",
            template_id="T40_COMMON_VLSU_LOAD_HIT",
            mode="synthetic_calibration",
            backend="synthetic",
        )

        inventory = analyze_quality.build_quality_inventory(
            [real_t10, synthetic_t10, synthetic_t40],
            Path("/tmp/round18-quality"),
        )

        self.assertEqual(inventory["coverage"]["required_templates"], ["T10_INDEPENDENT_STREAM_THROUGHPUT"])
        self.assertNotIn("T40_COMMON_VLSU_LOAD_HIT", inventory["coverage"]["missing_real_templates"])
        self.assertNotIn(
            "T40_COMMON_VLSU_LOAD_HIT",
            {
                group["template_id"]
                for group in inventory["coverage"]["missing_real_template_instruction_lmul"]
            },
        )

    def test_quality_manifest_excludes_deferred_t40_from_required_coverage(self):
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
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                        "  -",
                        "    id: t40-common-load-hit",
                        "    template_id: T40_COMMON_VLSU_LOAD_HIT",
                        "    instruction_id: common_load_hit",
                        "    lmul: m1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            inventory = analyze_quality.build_quality_inventory(
                [
                    quality_item(
                        experiment_id="t10-vadd-vv-m1-n2",
                        template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
                        mode="real_platform_profile",
                        backend="gem5_minor",
                    )
                ],
                root,
            )

            self.assertEqual(inventory["coverage"]["required_template_source"], "suite_manifest")
            self.assertEqual(inventory["coverage"]["required_templates"], ["T10_INDEPENDENT_STREAM_THROUGHPUT"])
            self.assertEqual(inventory["coverage"]["missing_real_templates"], [])

    def test_t21_scalar_result_probe_does_not_allocate_vector_destinations(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T21_PAIR_WITH_SCALAR",
                "--instr",
                "vcpop_m",
                "--lmul",
                "m4",
                "--iterations",
                "7",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["iterations"], 7)
        self.assertTrue(all(instance["destination"].startswith("x") for instance in meta["instances"]))
        self.assertFalse(any("vcpop.m v" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
