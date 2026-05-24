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


analyze_core = load_script_module("analyze_core_round16_under_test", "scripts/analyze_core.py")


def analysis(
    *,
    experiment_id,
    template_id,
    delta,
    body,
    scaling_shape=None,
    instruction_id="vsubject",
    lmul="m1",
):
    return analyze_core.ExperimentAnalysis(
        trace_path=Path(f"/tmp/{experiment_id}/trace.json"),
        experiment_path=Path(f"/tmp/{experiment_id}/experiment.yaml"),
        experiment_id=experiment_id,
        template_id=template_id,
        backend="unit",
        mode="unit",
        dry_run_trace=False,
        marker_baseline_cycles=0,
        instruction_id=instruction_id,
        asm=None,
        llvm_sched_write=None,
        lmul=lmul,
        body=dict(body),
        pair_instruction_id=None,
        scaling_shape=scaling_shape,
        timestamp_model_kind=None,
        timestamp_model_occupies_issue_slot=None,
        marker_definitions=(),
        synthetic={},
        markers=(),
        adjacent_deltas=(),
        named_deltas=(("start", "end", delta),),
        warnings=(),
    )


class ReviewPhaseRound16Test(unittest.TestCase):
    def test_t30_throughput_release_uses_slope_with_startup_overhead(self):
        items = [
            analysis(
                experiment_id="t30-vsubject-t10-m1-n2",
                template_id="T30_LMUL_SCALING",
                scaling_shape="T10_INDEPENDENT_STREAM_THROUGHPUT",
                delta=8,
                body={"iterations": 2},
            ),
            analysis(
                experiment_id="t30-vsubject-t10-m1-n4",
                template_id="T30_LMUL_SCALING",
                scaling_shape="T10_INDEPENDENT_STREAM_THROUGHPUT",
                delta=14,
                body={"iterations": 4},
            ),
        ]

        record = analyze_core.infer_release_record(items)

        self.assertTrue(record["claimed"])
        self.assertEqual(record["value"], 3)

    def test_t12_readiness_subtracts_filler_cadence(self):
        items = [
            analysis(
                experiment_id="t12-vsubject-m1-k0",
                template_id="T12_CONSUMER_RAW_GAP",
                delta=7,
                body={"filler_count": 0, "filler_cadence_cycles": 2},
            ),
            analysis(
                experiment_id="t12-vsubject-m1-k2",
                template_id="T12_CONSUMER_RAW_GAP",
                delta=11,
                body={"filler_count": 2, "filler_cadence_cycles": 2},
            ),
        ]

        record = analyze_core.infer_latency_record(items)

        self.assertTrue(record["claimed"])
        self.assertEqual(record["value"], 7)

    def test_t12_readiness_fails_closed_without_nonzero_filler_cadence(self):
        items = [
            analysis(
                experiment_id="t12-vsubject-m1-k0",
                template_id="T12_CONSUMER_RAW_GAP",
                delta=7,
                body={"filler_count": 0},
            ),
            analysis(
                experiment_id="t12-vsubject-m1-k2",
                template_id="T12_CONSUMER_RAW_GAP",
                delta=11,
                body={"filler_count": 2},
            ),
        ]

        record = analyze_core.infer_latency_record(items)

        self.assertFalse(record["claimed"])
        self.assertEqual(record["confidence"], "insufficient_raw_marker_evidence")
        self.assertTrue(any("raw_gap_missing_filler_cadence" in entry for entry in record["evidence"]))


if __name__ == "__main__":
    unittest.main()
