import argparse
import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_ASM_PATH = REPO_ROOT / "scripts" / "gen_asm.py"


def load_gen_asm():
    spec = importlib.util.spec_from_file_location("gen_asm_vcpop_r11_under_test", GEN_ASM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen_asm = load_gen_asm()


class GenAsmVcpopR11Test(unittest.TestCase):
    def suite_args(self):
        return argparse.Namespace(
            output_root=Path("experiments/generated"),
            asm_template=Path("templates/rvv_program.s.tpl"),
            manifest_only=True,
        )

    def test_suite_adds_r11_vcpop_m4_diagnostics_without_renaming_old_ids(self):
        entries = gen_asm.suite_entries(self.suite_args())
        by_id = {entry["id"]: entry for entry in entries}

        self.assertIn("t10-vcpop-m-m4-n8", by_id)
        self.assertIn("t10-vcpop-m-m4-scalar-fixed-n8", by_id)
        self.assertIn("t21-vcpop-m-m4-n4", by_id)

        expected_ids = {
            "t10-vcpop-m-m4-n7-r11-sd-rot-src-v0-pad00",
            "t10-vcpop-m-m4-n9-r11-sd-rot-src-v0-pad00",
            "t10-vcpop-m-m4-n7-r11-sd-fix-src-v0-pad00",
            "t10-vcpop-m-m4-n9-r11-sd-fix-src-v0-pad00",
            "t10-vcpop-m-m4-n7-r11-sd-rot-src-v4-pad00",
            "t10-vcpop-m-m4-n8-r11-sd-rot-src-v4-pad00",
            "t10-vcpop-m-m4-n9-r11-sd-rot-src-v4-pad00",
            "t10-vcpop-m-m4-n7-r11-sd-rot-src-v0-pad28",
            "t10-vcpop-m-m4-n8-r11-sd-rot-src-v0-pad28",
            "t10-vcpop-m-m4-n9-r11-sd-rot-src-v0-pad28",
            "t21-vcpop-m-m4-n4-r11-sd-rot-src-v0-pad28",
            "t21-vcpop-m-m4-n4-r11-sd-rot-src-v4-pad28",
            "t21-vcpop-m-m4-n4-r11-sd-fix-src-v0-pad28",
        }
        self.assertLessEqual(expected_ids, set(by_id))

        for experiment_id in expected_ids:
            entry = by_id[experiment_id]
            self.assertEqual(entry["instruction_id"], "vcpop_m")
            self.assertEqual(entry["lmul"], "m4")
            self.assertEqual(entry["diagnostic_round"], "r11")
            self.assertIn("--diagnostic-round", entry["argv"])
            self.assertIn("--mask-source-policy", entry["argv"])
            self.assertIn("--marker-padding-bytes", entry["argv"])

    def test_r11_t10_records_source_padding_and_boundary_metadata(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T10_INDEPENDENT_STREAM_THROUGHPUT",
                "--instr",
                "vcpop_m",
                "--lmul",
                "m4",
                "--iterations",
                "8",
                "--diagnostic-round",
                "r11",
                "--mask-source-policy",
                "v4",
                "--marker-padding-bytes",
                "28",
                "--output-root",
                "experiments/generated",
            ]
        )

        self.assertEqual(gen_asm.make_experiment_id(args), "t10-vcpop-m-m4-n8-r11-sd-rot-src-v4-pad28")
        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["diagnostic_round"], "r11")
        self.assertEqual(meta["scalar_dest_policy"], "rotated")
        self.assertEqual(meta["mask_source_policy"], "v4")
        self.assertEqual(meta["source_registers"], ["v4"])
        self.assertEqual(meta["marker_padding_bytes"], 28)
        self.assertEqual(meta["target_start_pc_mod32"], 0)
        self.assertEqual(meta["body_instruction_count"], 8)
        self.assertEqual(meta["expected_fetch_boundary_crossings"], 0)
        self.assertEqual(lines.count("addi x0, x0, 0  # r11 marker padding"), 7)
        self.assertTrue(any(line == "vcpop.m x10, v4" for line in lines))

    def test_r11_t21_supports_fixed_scalar_destinations_and_padding_metadata(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T21_PAIR_WITH_SCALAR",
                "--instr",
                "vcpop_m",
                "--lmul",
                "m4",
                "--diagnostic-round",
                "r11",
                "--scalar-dest-policy",
                "fixed",
                "--mask-source-policy",
                "v0",
                "--marker-padding-bytes",
                "28",
                "--output-root",
                "experiments/generated",
            ]
        )

        self.assertEqual(gen_asm.make_experiment_id(args), "t21-vcpop-m-m4-n4-r11-sd-fix-src-v0-pad28")
        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["diagnostic_round"], "r11")
        self.assertEqual(meta["scalar_dest_policy"], "fixed")
        self.assertEqual(meta["mask_source_policy"], "v0")
        self.assertEqual(meta["source_registers"], ["v0"])
        self.assertEqual(meta["marker_padding_bytes"], 28)
        self.assertEqual(meta["target_start_pc_mod32"], 0)
        self.assertEqual(meta["body_instruction_count"], 8)
        self.assertEqual(meta["expected_fetch_boundary_crossings"], 0)
        self.assertEqual(lines.count("vcpop.m x10, v0"), 4)


if __name__ == "__main__":
    unittest.main()
