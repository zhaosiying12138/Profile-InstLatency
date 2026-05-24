import importlib.util
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_script_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen_asm = load_script_module("gen_asm_round19_under_test", "scripts/gen_asm.py")
run_experiment = load_script_module("run_experiment_round19_under_test", "scripts/run_experiment.py")


def executable(path: Path) -> Path:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def t12_args(*, filler_count: int):
    return gen_asm.build_parser().parse_args(
        [
            "one",
            "--template",
            "T12_CONSUMER_RAW_GAP",
            "--instr",
            "vadd_vv",
            "--lmul",
            "m4",
            "--filler-count",
            str(filler_count),
            "--output-root",
            "experiments/generated",
        ]
    )


class ReviewPhaseRound19Test(unittest.TestCase):
    def test_t12_vector_fillers_never_overwrite_producer_or_consumer_registers(self):
        _markers, lines, meta = gen_asm.body_for_args(t12_args(filler_count=5))

        filler_destinations = [
            line.split()[1].rstrip(",")
            for line in lines
            if "# independent filler" in line
        ]

        self.assertEqual(len(filler_destinations), 5)
        self.assertNotIn(meta["producer_destination"], filler_destinations)
        self.assertNotIn(meta["consumer_destination"], filler_destinations)

    def test_marker_addresses_resolves_bare_llvm_nm_from_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            bindir = Path(tempdir)
            llvm_nm = executable(bindir / "llvm-nm")

            with (
                mock.patch.object(run_experiment, "load_paths_config", return_value={"llvm_nm": "llvm-nm"}),
                mock.patch.dict(os.environ, {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}),
                mock.patch.object(
                    run_experiment,
                    "checked_command",
                    return_value=types.SimpleNamespace(stdout="80000000 T __marker_start\n"),
                ) as checked,
            ):
                addresses = run_experiment.marker_addresses(
                    Path("test.elf"),
                    [{"symbol": "__marker_start", "label": "start"}],
                )

            self.assertEqual(addresses, {"start": 0x80000000})
            self.assertEqual(Path(checked.call_args.args[0][0]), llvm_nm)

    def test_marker_addresses_resolves_bare_assembler_sibling_llvm_nm_from_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            bindir = Path(tempdir)
            executable(bindir / "llvm-mc")
            llvm_nm = executable(bindir / "llvm-nm")

            with (
                mock.patch.object(run_experiment, "load_paths_config", return_value={"assembler": "llvm-mc"}),
                mock.patch.dict(os.environ, {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"}),
                mock.patch.object(
                    run_experiment,
                    "checked_command",
                    return_value=types.SimpleNamespace(stdout="80000004 T __marker_end\n"),
                ) as checked,
            ):
                addresses = run_experiment.marker_addresses(
                    Path("test.elf"),
                    [{"symbol": "__marker_end", "label": "end"}],
                )

            self.assertEqual(addresses, {"end": 0x80000004})
            self.assertEqual(Path(checked.call_args.args[0][0]), llvm_nm)


if __name__ == "__main__":
    unittest.main()
