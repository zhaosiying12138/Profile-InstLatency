import importlib.util
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


analyze = load_script_module("analyze_round12_under_test", "scripts/analyze.py")
export_llvm_draft = load_script_module(
    "export_llvm_draft_round12_under_test", "scripts/export_llvm_draft.py"
)
run_experiment = load_script_module("run_experiment_round12_under_test", "scripts/run_experiment.py")


class ReviewPhaseRound12Test(unittest.TestCase):
    def test_export_llvm_draft_loads_profile_contents(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            profile_path = root / "vadd_vv" / "profile.yaml"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(
                "\n".join(
                    [
                        "instruction:",
                        "  id: vadd_vv",
                        "  asm: vadd.vv",
                        "  llvm_sched_write: WriteVADD",
                        "measurements:",
                        "  m1:",
                        "    llvm:",
                        "      latency:",
                        "        value: 4",
                        "      release_at_cycles:",
                        "        value: 1",
                        "      resource_group:",
                        "        value: YuShuXinVPipe0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = export_llvm_draft.build_rows(export_llvm_draft.load_profiles(root))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["profile"], profile_path.as_posix())
            self.assertEqual(rows[0]["instruction"], "vadd_vv")
            self.assertEqual(rows[0]["latency"], 4)

    def test_dry_run_gem5_backend_writes_synthetic_trace_without_launching_gem5(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source_dir = root / "source"
            source_dir.mkdir()
            metadata = {
                "id": "t01-vadd-vv-m1",
                "template_id": "T01_DECODE_EXEC_KILLCHECK",
                "result_group": "common",
                "instruction_id": "vadd_vv",
                "lmul": "m1",
                "markers": [{"label": "before"}, {"label": "after"}],
            }

            with mock.patch.object(
                run_experiment,
                "run_gem5_minor_trace",
                side_effect=AssertionError("dry-run must not launch gem5"),
            ):
                output_dir = run_experiment.run_experiment_from_metadata(
                    metadata,
                    dry_run=True,
                    results_root=root / "results",
                    timing_model_path=REPO_ROOT / "config" / "rvv_timing_model.yaml",
                    mode="real_platform_profile",
                    backend="gem5_minor",
                    source_dir=source_dir,
                )

            trace_text = (output_dir / "trace.json").read_text(encoding="utf-8")
            self.assertIn('"dry_run_trace": true', trace_text)
            self.assertIn('"backend": "synthetic_cmodel"', trace_text)

    def test_analyze_default_report_paths_follow_selected_root(self):
        args = analyze.parse_args(["--root", "results_repeat/r01"])

        self.assertEqual(args.aggregate, "results_repeat/r01/common/experiment_quality.md")
        self.assertEqual(args.mismatch_report, "results_repeat/r01/common/mismatch_report.md")

    def test_analyze_explicit_report_paths_are_preserved(self):
        args = analyze.parse_args(
            [
                "--root",
                "results_repeat/r01",
                "--aggregate",
                "/tmp/quality.md",
                "--mismatch-report",
                "/tmp/mismatch.md",
            ]
        )

        self.assertEqual(args.aggregate, "/tmp/quality.md")
        self.assertEqual(args.mismatch_report, "/tmp/mismatch.md")


if __name__ == "__main__":
    unittest.main()
