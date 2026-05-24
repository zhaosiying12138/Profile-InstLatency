import argparse
import importlib.util
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


gen_asm = load_script_module("gen_asm_round29_under_test", "scripts/gen_asm.py")


class ReviewPhaseRound29Test(unittest.TestCase):
    def test_suite_entries_preserve_custom_asm_template_in_replay_argv(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            custom_template = root / "custom-rvv-program.s.tpl"
            custom_template.write_text(
                (REPO_ROOT / "templates" / "rvv_program.s.tpl").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                output_root=root / "generated",
                asm_template=custom_template,
                manifest_only=True,
            )

            first = gen_asm.suite_entries(args)[0]

        self.assertIn("--asm-template", first["argv"])
        index = first["argv"].index("--asm-template")
        self.assertEqual(first["argv"][index + 1], gen_asm.relpath(gen_asm.repo_path(custom_template)))

    def test_generate_suite_replays_custom_asm_template(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            custom_template = root / "custom-rvv-program.s.tpl"
            custom_template.write_text(
                "# ROUND29 CUSTOM TEMPLATE\n"
                + (REPO_ROOT / "templates" / "rvv_program.s.tpl").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            output_root = root / "generated"
            suite_args = argparse.Namespace(
                output_root=output_root,
                asm_template=custom_template,
                manifest_only=False,
            )
            one_args = argparse.Namespace(
                template="T00_BASELINE_MARKER",
                instr=None,
                lmul=None,
                other_instr=None,
                consumer=None,
                shape="T10_INDEPENDENT_STREAM_THROUGHPUT",
                scalar_dest_policy=None,
                diagnostic_round=None,
                mask_source_policy=None,
                marker_padding_bytes=gen_asm.DEFAULT_MARKER_PADDING_BYTES,
                t20_register_policy=None,
                t12_filler=gen_asm.T12_DEFAULT_FILLER,
                t12_consumer_role=gen_asm.T12_DEFAULT_CONSUMER_ROLE,
                iterations=None,
                filler_count=None,
                output_root=output_root,
                asm_template=custom_template,
                experiment_id=None,
            )
            entry = {
                "id": "round29-custom-template",
                "template_id": one_args.template,
                "result_group": "common",
                "instruction_id": None,
                "lmul": None,
                "argv": gen_asm.command_argv(one_args, "round29-custom-template"),
            }

            with mock.patch.object(gen_asm, "suite_entries", return_value=[entry]):
                gen_asm.generate_suite(suite_args)

            assembly = output_root / "round29-custom-template" / "test.s"
            self.assertIn("# ROUND29 CUSTOM TEMPLATE", assembly.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
