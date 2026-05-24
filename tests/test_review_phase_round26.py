import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen_asm = load_script_module("gen_asm_round26_under_test", "scripts/gen_asm.py")


class ReviewPhaseRound26Test(unittest.TestCase):
    def test_t12_default_vector_filler_omits_fixed_cadence_metadata(self):
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
        self.assertNotIn("filler_cadence_cycles", meta)
        self.assertNotIn("independent_filler_cadence_cycles", meta["gap_sweep"])

    def test_t30_t12_shape_omits_default_vector_filler_cadence_metadata(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T30_LMUL_SCALING",
                "--shape",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vadd_vv",
                "--lmul",
                "m2",
                "--filler-count",
                "3",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, _lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["filler_instruction_id"], "vadd_vv")
        self.assertNotIn("filler_cadence_cycles", meta)
        self.assertNotIn("independent_filler_cadence_cycles", meta["gap_sweep"])


if __name__ == "__main__":
    unittest.main()
