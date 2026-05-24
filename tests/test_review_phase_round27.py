import importlib.util
import json
import shutil
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


analyze_quality = load_script_module("analyze_quality_round27_under_test", "scripts/analyze_quality.py")
build_blog_assets = load_script_module("build_blog_assets_round27_under_test", "scripts/build_blog_assets.py")


BLOG_EXPERIMENTS = (
    ("common", "t00-marker"),
    ("vdivu_vv", "t10-vdivu-vv-m1-n4"),
    ("vdivu_vv", "t10-vdivu-vv-m2-n4"),
    ("vdivu_vv", "t10-vdivu-vv-m4-n4"),
    ("vdivu_vv", "t11-vdivu-vv-m1-n4"),
    ("vdivu_vv", "t12-vdivu-vv-m1-k2-vadd-vv"),
    ("vdivu_vv", "t12-vdivu-vv-m1-k4-vadd-vv"),
    ("vdivu_vv", "t20-vdivu-vv-vredsum-vs-m1-n4"),
    ("vdivu_vv", "t21-vdivu-vv-m1-n4"),
    ("vdivu_vv_composite", "vdivu-vv-composite-real"),
)


def quality_item(*, experiment_id, template_id, instruction_id, lmul):
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


def complete_field_status_rows(instruction_id: str, lmul: str) -> list[dict[str, str]]:
    return [
        {
            "instruction_id": instruction_id,
            "lmul": lmul,
            "field": field,
            "status": "ready",
        }
        for field in analyze_quality.REQUIRED_REAL_LLVM_FIELDS
    ]


def copy_blog_inputs_without_exec_logs(root: Path) -> None:
    for group, exp_id in BLOG_EXPERIMENTS:
        source = REPO_ROOT / "results" / "blog" / group / "experiments" / exp_id
        target = root / "results" / "blog" / group / "experiments" / exp_id
        target.mkdir(parents=True)
        for name in ("trace.json", "test.s"):
            shutil.copy2(source / name, target / name)


class ReviewPhaseRound27Test(unittest.TestCase):
    def test_quality_inventory_requires_field_status_for_each_covered_pair(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            common = root / "common"
            common.mkdir()
            (common / "real_platform_field_status.json").write_text(
                json.dumps({"rows": complete_field_status_rows("vadd_vv", "m1")}, indent=2) + "\n",
                encoding="utf-8",
            )

            inventory = analyze_quality.build_quality_inventory(
                [
                    quality_item(
                        experiment_id="t10-vadd-vv-m1-n2",
                        template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instruction_id="vadd_vv",
                        lmul="m1",
                    ),
                    quality_item(
                        experiment_id="t10-vadd-vv-m2-n2",
                        template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
                        instruction_id="vadd_vv",
                        lmul="m2",
                    ),
                ],
                root,
            )

        field_status = inventory["field_status"]
        missing_pairs = {
            (record["instruction_id"], record["lmul"])
            for record in field_status["missing_required"]
        }
        self.assertEqual(field_status["status"], "blocked")
        self.assertIn(("vadd_vv", "m2"), missing_pairs)
        self.assertEqual(field_status["missing_required_total"], len(analyze_quality.REQUIRED_REAL_LLVM_FIELDS))

    def test_blog_asset_builder_leaves_evidence_unchanged_when_exec_logs_are_missing(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            copy_blog_inputs_without_exec_logs(root)
            evidence = root / "blogs" / "assets" / "reference" / "evidence.json"
            evidence.parent.mkdir(parents=True)
            original = {"degraded": False, "source": "committed-reference"}
            evidence.write_text(json.dumps(original, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with (
                mock.patch.object(build_blog_assets, "ROOT", root),
                mock.patch.object(build_blog_assets, "ASSET_ROOT", root / "blogs" / "assets"),
                mock.patch.object(build_blog_assets, "REF_ROOT", root / "blogs" / "assets" / "reference"),
                mock.patch.object(build_blog_assets, "BLOG_RESULTS", root / "results" / "blog"),
            ):
                build_blog_assets.build()

            self.assertEqual(json.loads(evidence.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()
