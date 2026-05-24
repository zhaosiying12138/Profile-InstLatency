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


gen_asm = load_script_module("gen_asm_round23_under_test", "scripts/gen_asm.py")
search_support = load_script_module("search_model_support_round23_under_test", "scripts/search_model_support.py")


def write_result_group(root: Path, group: str, experiment_id: str) -> None:
    group_dir = root / group
    exp_dir = group_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True)
    (group_dir / "profile.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    (exp_dir / "trace.json").write_text('{"entries": []}\n', encoding="utf-8")


class ReviewPhaseRound23Test(unittest.TestCase):
    def test_directory_inputs_only_scan_selected_result_root_layout(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "results"
            write_result_group(root, "vadd_vv", "top-t10")
            write_result_group(root / "r01", "vadd_vv", "nested-r01-t10")
            write_result_group(root / "blog", "vdivu_vv", "nested-blog-t10")

            profile_paths = search_support.profile_files_from_path(root.as_posix())
            trace_paths = search_support.trace_files_from_path(root.as_posix())

            self.assertEqual(profile_paths, [root / "vadd_vv" / "profile.yaml"])
            self.assertEqual(trace_paths, [root / "vadd_vv" / "experiments" / "top-t10" / "trace.json"])

            nested_profiles = search_support.profile_files_from_path((root / "r01").as_posix())
            nested_traces = search_support.trace_files_from_path((root / "r01").as_posix())

            self.assertEqual(nested_profiles, [root / "r01" / "vadd_vv" / "profile.yaml"])
            self.assertEqual(nested_traces, [root / "r01" / "vadd_vv" / "experiments" / "nested-r01-t10" / "trace.json"])

    def test_default_vector_filler_emits_regeneration_cadence_metadata(self):
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

    def test_scalar_filler_keeps_fixed_cadence_metadata(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vcpop_m",
                "--lmul",
                "m4",
                "--filler-count",
                "2",
                "--t12-filler",
                "scalar_add",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, _lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["filler_instruction_id"], "scalar_add")
        self.assertEqual(meta["filler_cadence_cycles"], 1)
        self.assertEqual(meta["gap_sweep"]["independent_filler_cadence_cycles"], 1)


if __name__ == "__main__":
    unittest.main()
