import importlib.util
import json
import shutil
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


build_blog_assets = load_script_module("build_blog_assets_round21_under_test", "scripts/build_blog_assets.py")
gate = load_script_module("check_calibration_gate_round21_under_test", "scripts/check_calibration_gate.py")


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


def copy_blog_inputs_without_exec_logs(root: Path) -> None:
    for group, exp_id in BLOG_EXPERIMENTS:
        source = REPO_ROOT / "results" / "blog" / group / "experiments" / exp_id
        target = root / "results" / "blog" / group / "experiments" / exp_id
        target.mkdir(parents=True)
        for name in ("trace.json", "test.s"):
            shutil.copy2(source / name, target / name)


class ReviewPhaseRound21Test(unittest.TestCase):
    def test_real_gate_expected_experiments_use_focused_suite_manifest(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "focused-root"
            root.mkdir()
            (root / "suite_manifest.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "experiments:",
                        "  -",
                        "    id: focused-t10",
                        "    template_id: T10_INDEPENDENT_STREAM_THROUGHPUT",
                        "    result_group: focused",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                        "  -",
                        "    id: focused-t40",
                        "    template_id: T40_COMMON_VLSU_LOAD_HIT",
                        "    result_group: focused",
                        "    instruction_id: common_load_hit",
                        "    lmul: m1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            required, deferred = gate.load_expected_experiments(root)

            self.assertEqual([item.experiment_id for item in required], ["focused-t10"])
            self.assertEqual([item.experiment_id for item in deferred], ["focused-t40"])

    def test_blog_asset_builder_rewrites_stale_degraded_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            copy_blog_inputs_without_exec_logs(root)
            evidence = root / "blogs" / "assets" / "reference" / "evidence.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps({"degraded": False, "missing_exec_logs": []}) + "\n",
                encoding="utf-8",
            )

            with (
                mock.patch.object(build_blog_assets, "ROOT", root),
                mock.patch.object(build_blog_assets, "ASSET_ROOT", root / "blogs" / "assets"),
                mock.patch.object(build_blog_assets, "REF_ROOT", root / "blogs" / "assets" / "reference"),
                mock.patch.object(build_blog_assets, "BLOG_RESULTS", root / "results" / "blog"),
            ):
                build_blog_assets.build()

            rewritten = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertTrue(rewritten["degraded"])
            self.assertGreater(len(rewritten["missing_exec_logs"]), 0)


if __name__ == "__main__":
    unittest.main()
