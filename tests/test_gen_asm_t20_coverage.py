import argparse
import importlib.util
import sys
import tempfile
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


gen_asm = load_script_module("gen_asm_under_test", "scripts/gen_asm.py")
search_model = load_script_module("search_model_for_gen_asm_test", "scripts/search_model.py")


class GenAsmT20CoverageTest(unittest.TestCase):
    def suite_args(self, output_root):
        return argparse.Namespace(
            output_root=str(output_root),
            asm_template=str(REPO_ROOT / "templates" / "rvv_program.s.tpl"),
            manifest_only=False,
        )

    def test_t20_m4_resource_noreuse_suite_entries_extend_without_renaming_old_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.suite_args(Path(tmp) / "generated")
            entries = gen_asm.suite_entries(args)
            ids = {entry["id"] for entry in entries}

            self.assertIn("t20-vadd-vv-vsll-vv-m4-n2", ids)
            self.assertIn("t20-vadd-vv-vsll-vv-m4-n3", ids)
            self.assertIn("t20-vadd-vv-vsll-vv-m4-n4", ids)
            self.assertIn("t20-vadd-vv-vsll-vv-m4-n1-resource-noreuse", ids)
            self.assertIn("t20-vadd-vv-vsll-vv-m4-n2-resource-noreuse", ids)
            self.assertIn("t20-vadd-vv-vsll-vv-m4-n3-resource-noreuse", ids)

            resource_entries = [
                entry
                for entry in entries
                if entry["template_id"] == "T20_PAIRWISE_PIPE_CLASSIFICATION"
                and entry["id"].endswith("-resource-noreuse")
            ]

            self.assertEqual(len(resource_entries), 108)
            self.assertTrue(all(entry["lmul"] == "m4" for entry in resource_entries))
            self.assertFalse(any("vcpop-m" in entry["id"] for entry in resource_entries))

    def test_t20_m4_resource_noreuse_metadata_marks_proc_resource_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "generated"
            gen_asm.generate_suite(self.suite_args(output_root))

            new_doc = search_model.parse_yamlish(
                output_root / "t20-vadd-vv-vsll-vv-m4-n3-resource-noreuse" / "experiment.yaml"
            )
            old_doc = search_model.parse_yamlish(
                output_root / "t20-vadd-vv-vsll-vv-m4-n3" / "experiment.yaml"
            )

            self.assertEqual(new_doc["body"]["register_policy"], "resource_noreuse_prefix")
            self.assertFalse(new_doc["body"]["register_reuse"])
            self.assertEqual(
                new_doc["body"]["resource_disambiguation"],
                {
                    "usable_for_proc_resource": True,
                    "count_set_id": "m4_vector_vector_noreuse",
                    "symmetry_breaker": False,
                },
            )
            self.assertNotIn("resource_disambiguation", old_doc["body"])


if __name__ == "__main__":
    unittest.main()
