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


gen_asm = load_script_module("gen_asm_round25_under_test", "scripts/gen_asm.py")


class ReviewPhaseRound25Test(unittest.TestCase):
    def test_t12_rejects_scalar_add_consumer_for_vector_producer(self):
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
                "scalar_add",
                "--output-root",
                "experiments/generated",
            ]
        )

        with self.assertRaises(SystemExit) as raised:
            gen_asm.body_for_args(args)

        message = str(raised.exception)
        self.assertIn("scalar_add", message)
        self.assertIn("scalar-result producer", message)

    def test_t30_t12_shape_rejects_scalar_add_consumer_for_vector_producer(self):
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
                "m1",
                "--filler-count",
                "0",
                "--consumer",
                "scalar_add",
                "--output-root",
                "experiments/generated",
            ]
        )

        with self.assertRaises(SystemExit) as raised:
            gen_asm.body_for_args(args)

        self.assertIn("scalar_add", str(raised.exception))

    def test_t12_keeps_scalar_add_consumer_for_scalar_producer(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vcpop_m",
                "--lmul",
                "m1",
                "--filler-count",
                "0",
                "--consumer",
                "scalar_add",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["producer_destination"], "x10")
        self.assertEqual(meta["consumer_destination"], "x11")
        self.assertIn("add x11, x10, x0", lines)


if __name__ == "__main__":
    unittest.main()
