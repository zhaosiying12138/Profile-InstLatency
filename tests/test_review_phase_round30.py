import importlib.util
import json
import sys
import tempfile
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


gate = load_script_module("check_calibration_gate_round30_under_test", "scripts/check_calibration_gate.py")
gen_asm = load_script_module("gen_asm_round30_under_test", "scripts/gen_asm.py")
search_model = load_script_module("search_model_round30_under_test", "scripts/search_model.py")


def write_real_trace(root: Path, trace_dir_name: str, experiment_id: str) -> None:
    exp_dir = root / "vadd_vv" / "experiments" / trace_dir_name
    exp_dir.mkdir(parents=True)
    (exp_dir / "trace.json").write_text(
        json.dumps(
            {
                "mode": "real_platform_profile",
                "backend": "gem5_minor",
                "dry_run_trace": False,
                "experiment_id": experiment_id,
                "template_id": "T12_CONSUMER_RAW_GAP",
                "result_group": "vadd_vv",
                "instruction_id": "vadd_vv",
                "lmul": "m1",
                "entries": [
                    {"marker": "start", "cycle": 10, "pc": "0x80000000"},
                    {"marker": "end", "cycle": 14, "pc": "0x80000004"},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def raw_t12_observation() -> search_model.RawObservation:
    return search_model.RawObservation(
        trace_path=Path("/tmp/t12-vadd-vv-m4-k2/trace.json"),
        experiment_path=Path("/tmp/t12-vadd-vv-m4-k2/experiment.yaml"),
        experiment_id="t12-vadd-vv-m4-k2",
        instruction_id="vproducer",
        lmul="m4",
        template_id="T12_CONSUMER_RAW_GAP",
        effective_template_id="T12_CONSUMER_RAW_GAP",
        marker_pair="start/end",
        delta_cycles=9,
        marker_baseline_cycles=0,
        parameters={},
        body={
            "filler_count": 2,
            "consumer": "vconsumer",
            "filler_instruction_id": "vadd_vv",
            "filler_cadence_cycles": 1,
        },
        pair_instruction_id=None,
        raw_pipe_labels=(),
        synthetic_reference={},
        mode="real_platform_profile",
        backend="gem5_minor",
        dry_run_trace=False,
        trace_sha256="sha-t12",
    )


def timing_candidate(release_at_cycles: int) -> search_model.TimingCandidate:
    return search_model.TimingCandidate(
        latency=1,
        release_at_cycles=release_at_cycles,
        proc_resource="pipe0",
        num_micro_ops=1,
        single_issue=False,
    )


class ReviewPhaseRound30Test(unittest.TestCase):
    def test_real_gate_does_not_count_distinct_experiments_as_repeats(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "focused"
            root.mkdir()
            (root / "suite_manifest.yaml").write_text(
                "\n".join(
                    [
                        "schema_version: 1",
                        "experiments:",
                        "  -",
                        "    id: t12-vadd-vv-m1-k2-vadd-vv",
                        "    template_id: T12_CONSUMER_RAW_GAP",
                        "    result_group: vadd_vv",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                        "  -",
                        "    id: t12-vadd-vv-m1-k4-vadd-vv",
                        "    template_id: T12_CONSUMER_RAW_GAP",
                        "    result_group: vadd_vv",
                        "    instruction_id: vadd_vv",
                        "    lmul: m1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            write_real_trace(root, "k2-once", "t12-vadd-vv-m1-k2-vadd-vv")
            write_real_trace(root, "k4-once", "t12-vadd-vv-m1-k4-vadd-vv")

            with (
                mock.patch.object(gate, "load_inventory", return_value=(root / "common" / "real_platform_inventory.json", {}, [])),
                mock.patch.object(gate, "human_approval_failures", return_value=(True, [], {"status": "approved"})),
                mock.patch.object(gate, "real_platform_field_status_failures", return_value=[]),
                mock.patch.object(gate, "marker_contract_failures", return_value=[]),
                mock.patch.object(gate, "confidence_failures", return_value=[]),
                mock.patch.object(gate, "conflict_status_failures", return_value=[]),
                mock.patch.object(gate, "has_documented_assumptions", return_value=True),
            ):
                failures = gate.real_platform_failures(
                    "Mode: real_platform_profile\nGate status: PASS\n## Assumptions\nGrouped coverage.",
                    root,
                )

        joined = "\n".join(failures)
        self.assertNotIn("real gem5 coverage", joined)
        self.assertIn("repeatability/stability", joined)

    def test_default_vector_filler_does_not_emit_fixed_cadence_metadata(self):
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

    def test_vector_filler_metadata_does_not_override_measured_candidate_cadence(self):
        cadence, source = search_model.t12_filler_cadence(
            raw_t12_observation(),
            {},
            {("vadd_vv", "m4"): timing_candidate(release_at_cycles=4)},
        )

        self.assertEqual(cadence, 4)
        self.assertEqual(source, "fixed_candidate:vadd_vv")


if __name__ == "__main__":
    unittest.main()
