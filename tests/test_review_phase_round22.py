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


gen_asm = load_script_module("gen_asm_round22_under_test", "scripts/gen_asm.py")


class ReviewPhaseRound22Test(unittest.TestCase):
    def test_t12_vcpop_consumer_uses_scalar_destination_for_vector_producer(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vadd_vv",
                "--lmul",
                "m1",
                "--filler-count",
                "0",
                "--consumer",
                "vcpop_m",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["producer_destination"], "v2")
        self.assertEqual(meta["consumer_kind"], "mask_popcount")
        self.assertEqual(meta["consumer_destination"], "x11")
        self.assertIn("vcpop.m x11, v2", lines)
        self.assertNotIn("vcpop.m v3, v2", lines)


if __name__ == "__main__":
    unittest.main()
