import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_CODE_LINES = 2000


class FileLineLimitTest(unittest.TestCase):
    def test_search_model_entrypoint_stays_under_line_limit(self):
        path = REPO_ROOT / "scripts" / "search_model.py"
        line_count = len(path.read_text(encoding="utf-8").splitlines())

        self.assertLessEqual(line_count, MAX_CODE_LINES)


if __name__ == "__main__":
    unittest.main()
