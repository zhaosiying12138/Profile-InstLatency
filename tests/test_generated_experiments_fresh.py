import importlib.util
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GEN_ASM_PATH = REPO_ROOT / "scripts" / "gen_asm.py"


def load_gen_asm():
    spec = importlib.util.spec_from_file_location("gen_asm_freshness_under_test", GEN_ASM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen_asm = load_gen_asm()


class GeneratedExperimentsFreshnessTest(unittest.TestCase):
    def test_checked_in_experiments_match_generator_version(self):
        experiment_paths = sorted((REPO_ROOT / "experiments" / "generated").glob("*/experiment.yaml"))
        self.assertTrue(experiment_paths, "expected checked-in generated experiments")
        expected = str(gen_asm.GENERATOR_VERSION)
        mismatches = []
        for path in experiment_paths:
            match = re.search(r"(?m)^  generator_version: (.+)$", path.read_text(encoding="utf-8"))
            actual = match.group(1).strip().strip("'\"") if match else "<missing>"
            if actual != expected:
                mismatches.append(f"{path.relative_to(REPO_ROOT)}:{actual}")

        self.assertEqual([], mismatches[:20])


if __name__ == "__main__":
    unittest.main()
