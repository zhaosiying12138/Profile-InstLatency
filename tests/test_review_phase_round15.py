import importlib.util
import os
import shutil
import stat
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


run_experiment = load_script_module("run_experiment_round15_under_test", "scripts/run_experiment.py")
build_blog_assets = load_script_module(
    "build_blog_assets_round15_under_test", "scripts/build_blog_assets.py"
)


class ReviewPhaseRound15Test(unittest.TestCase):
    def test_runner_resolves_bare_tool_names_from_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            bindir = root / "bin"
            bindir.mkdir()
            tool = bindir / "rvv-test-tool"
            tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            tool.chmod(tool.stat().st_mode | stat.S_IXUSR)

            with mock.patch.dict(os.environ, {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}):
                resolved = run_experiment.require_executable({"assembler": "rvv-test-tool"}, "assembler")

            self.assertEqual(resolved, tool)

    def test_blog_asset_builder_skips_reference_evidence_when_exec_logs_are_missing(self):
        required_experiments = [
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
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            for group, exp_id in required_experiments:
                source = REPO_ROOT / "results" / "blog" / group / "experiments" / exp_id
                target = root / "results" / "blog" / group / "experiments" / exp_id
                target.mkdir(parents=True)
                for name in ("trace.json", "test.s"):
                    shutil.copy2(source / name, target / name)

            with (
                mock.patch.object(build_blog_assets, "ROOT", root),
                mock.patch.object(build_blog_assets, "ASSET_ROOT", root / "blogs" / "assets"),
                mock.patch.object(build_blog_assets, "REF_ROOT", root / "blogs" / "assets" / "reference"),
                mock.patch.object(build_blog_assets, "BLOG_RESULTS", root / "results" / "blog"),
            ):
                build_blog_assets.build()

            evidence = root / "blogs" / "assets" / "reference" / "evidence.json"
            self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main()
