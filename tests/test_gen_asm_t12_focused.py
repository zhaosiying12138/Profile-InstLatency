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

    def test_suite_adds_control_t12_focus_only_for_remaining_latency_risks(self):
        args = argparse.Namespace(
            output_root=Path("experiments/generated"),
            asm_template=Path("templates/rvv_program.s.tpl"),
            manifest_only=True,
        )

        entries = gen_asm.suite_entries(args)
        control_entries = [entry for entry in entries if entry["id"].endswith("-control")]
        control_rows = {(entry["instruction_id"], entry["lmul"]) for entry in control_entries}

        self.assertIn("t12-vcpop-m-m1-k0-scalar-add-fscalar-add", {entry["id"] for entry in entries})
        self.assertIn(
            "t12-vcpop-m-m1-k0-scalar-add-fscalar-add-control",
            {entry["id"] for entry in control_entries},
        )
        self.assertEqual(
            control_rows,
            {
                ("vcpop_m", "m1"),
                ("vcpop_m", "m2"),
                ("vcpop_m", "m4"),
                ("vrgather_vv", "m4"),
                ("vslideup_vx", "m4"),
            },
        )
        self.assertEqual(len(control_entries), 5 * len(gen_asm.T12_FOCUSED_FILLER_COUNTS))
        self.assertTrue(all(entry["template_id"] == "T12_CONSUMER_RAW_GAP" for entry in control_entries))
        self.assertTrue(all(entry["t12_consumer_role"] == "control" for entry in control_entries))
        self.assertTrue(all(entry["t12_filler"] == "scalar_add" for entry in control_entries))
        self.assertFalse(any(entry["instruction_id"] == "viota_m" for entry in control_entries))

    def test_generated_control_t12_scalar_consumer_reads_independent_scalar_source(self):
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
                "--t12-filler",
                "scalar_add",
                "--t12-consumer-role",
                "control",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["t12_consumer_role"], "control")
        self.assertFalse(meta["consumer_reads_producer"])
        self.assertEqual(
            meta["matched_dependent_experiment_id"],
            "t12-vcpop-m-m1-k0-scalar-add-fscalar-add",
        )
        self.assertEqual(meta["producer_destination"], "x10")
        self.assertEqual(meta["consumer_destination"], "x11")
        self.assertEqual(meta["independent_consumer_source"]["register"], "x28")
        self.assertEqual(meta["filler_cadence_cycles"], 1)
        self.assertIn("add x11, x28, x0", lines)
        self.assertNotIn("add x11, x10, x0", lines)

    def test_generated_control_t12_vector_consumer_reads_independent_vector_source(self):
        args = gen_asm.build_parser().parse_args(
            [
                "one",
                "--template",
                "T12_CONSUMER_RAW_GAP",
                "--instr",
                "vrgather_vv",
                "--lmul",
                "m4",
                "--filler-count",
                "0",
                "--consumer",
                "vadd_vv",
                "--t12-filler",
                "scalar_add",
                "--t12-consumer-role",
                "control",
                "--output-root",
                "experiments/generated",
            ]
        )

        _markers, lines, meta = gen_asm.body_for_args(args)

        self.assertEqual(meta["t12_consumer_role"], "control")
        self.assertFalse(meta["consumer_reads_producer"])
        self.assertEqual(
            meta["matched_dependent_experiment_id"],
            "t12-vrgather-vv-m4-k0-vadd-vv-fscalar-add",
        )
        self.assertEqual(meta["producer_destination"], "v8")
        self.assertEqual(meta["consumer_destination"], "v12")
        self.assertEqual(meta["independent_consumer_source"]["register"], "v4")
        self.assertIn("vadd.vv v12, v4, v0", lines)
        self.assertNotIn("vadd.vv v12, v8, v4", lines)


if __name__ == "__main__":
    unittest.main()
