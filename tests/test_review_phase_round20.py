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


analyze_core = load_script_module("analyze_core_round20_under_test", "scripts/analyze_core.py")
run_experiment = load_script_module("run_experiment_round20_under_test", "scripts/run_experiment.py")


def analysis(
    *,
    experiment_id,
    delta,
    body,
    template_id="T12_CONSUMER_RAW_GAP",
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


def t12_metadata(*, role, reads_producer, filler_count=2, cadence=3):
    return {
        "experiment_id": f"t12-vsubject-{role}",
        "template_id": "T12_CONSUMER_RAW_GAP",
        "instruction_id": "vsubject",
        "lmul": "m1",
        "body": {
            "filler_count": filler_count,
            "filler_cadence_cycles": cadence,
            "t12_consumer_role": role,
            "consumer_reads_producer": reads_producer,
        },
    }


def timing_model(*, latency=7, release=2):
    return {
        "instructions": {
            "vsubject": {
                "latency_base": latency,
                "release_base": release,
            }
        }
    }


class ReviewPhaseRound20Test(unittest.TestCase):
    def test_t12_synthetic_control_delta_excludes_producer_latency(self):
        model = timing_model(latency=7)

        dependent = run_experiment.synthetic_delta_cycles(
            t12_metadata(role="dependent", reads_producer=True),
            model,
        )
        control = run_experiment.synthetic_delta_cycles(
            t12_metadata(role="control", reads_producer=False),
            model,
        )

        self.assertEqual(dependent, 13)
        self.assertEqual(control, 6)

    def test_t30_t12_synthetic_control_delta_excludes_producer_latency(self):
        model = timing_model(latency=7)
        metadata = t12_metadata(role="control", reads_producer=False, filler_count=2, cadence=3)
        metadata["template_id"] = "T30_LMUL_SCALING"
        metadata["scaling"] = {"shape": "T12_CONSUMER_RAW_GAP"}

        self.assertEqual(run_experiment.synthetic_delta_cycles(metadata, model), 6)

    def test_t12_latency_inference_skips_control_probes(self):
        items = [
            analysis(
                experiment_id="t12-vsubject-m1-k0-dependent",
                delta=7,
                body={
                    "filler_count": 0,
                    "filler_cadence_cycles": 3,
                    "t12_consumer_role": "dependent",
                    "consumer_reads_producer": True,
                },
            ),
            analysis(
                experiment_id="t12-vsubject-m1-k2-dependent",
                delta=13,
                body={
                    "filler_count": 2,
                    "filler_cadence_cycles": 3,
                    "t12_consumer_role": "dependent",
                    "consumer_reads_producer": True,
                },
            ),
            analysis(
                experiment_id="t12-vsubject-m1-k0-control",
                delta=0,
                body={
                    "filler_count": 0,
                    "filler_cadence_cycles": 3,
                    "t12_consumer_role": "control",
                    "consumer_reads_producer": False,
                },
            ),
            analysis(
                experiment_id="t12-vsubject-m1-k2-control",
                delta=6,
                body={
                    "filler_count": 2,
                    "filler_cadence_cycles": 3,
                    "t12_consumer_role": "control",
                    "consumer_reads_producer": False,
                },
            ),
        ]

        record = analyze_core.infer_latency_record(items)

        self.assertTrue(record["claimed"])
        self.assertEqual(record["value"], 7)
        self.assertTrue(any("raw_gap_control_probe_skipped" in entry for entry in record["evidence"]))


if __name__ == "__main__":
    unittest.main()
