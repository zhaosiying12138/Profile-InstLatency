import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_ASM_PATH = REPO_ROOT / "scripts" / "gen_asm.py"


def load_gen_asm():
    spec = importlib.util.spec_from_file_location("gen_asm_under_test", GEN_ASM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen_asm = load_gen_asm()


class GenAsmT12FocusedTest(unittest.TestCase):
    def test_suite_adds_scalar_filler_t12_focus_without_renaming_broad_ids(self):
        args = argparse.Namespace(
            output_root=Path("experiments/generated"),
            asm_template=Path("templates/rvv_program.s.tpl"),
            manifest_only=True,
        )

        entries = gen_asm.suite_entries(args)
        by_id = {entry["id"]: entry for entry in entries}

        self.assertIn("t12-vcpop-m-m4-k0-scalar-add", by_id)
        focused_id = "t12-vcpop-m-m4-k0-scalar-add-fscalar-add"
        self.assertIn(focused_id, by_id)
        self.assertEqual(by_id[focused_id]["template_id"], "T12_CONSUMER_RAW_GAP")
        self.assertEqual(by_id[focused_id]["instruction_id"], "vcpop_m")
        self.assertEqual(by_id[focused_id]["lmul"], "m4")
        self.assertEqual(by_id[focused_id]["consumer"], "scalar_add")
        self.assertEqual(by_id[focused_id]["filler_count"], 0)
        self.assertEqual(by_id[focused_id]["t12_filler"], "scalar_add")
        self.assertIn("--t12-filler", by_id[focused_id]["argv"])

    def test_generated_scalar_filler_t12_records_cadence_metadata(self):
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

        markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(markers, ["start", "end"])
        self.assertEqual(meta["filler_instruction_id"], "scalar_add")
        self.assertEqual(meta["filler_cadence_cycles"], 1)
        self.assertEqual(meta["independent_filler_kind"], "scalar")
        self.assertEqual(meta["gap_sweep"]["independent_filler_instruction"], "scalar_add")
        self.assertTrue(any("independent scalar filler 0" in line for line in lines))
        self.assertTrue(any("independent scalar filler 1" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
