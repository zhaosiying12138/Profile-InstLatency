import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


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


search_model = load_script_module("search_model_round28_under_test", "scripts/search_model.py")
search_support = load_script_module("search_model_support_round28_under_test", "scripts/search_model_support.py")


def write_result_group(root: Path, group: str, experiment_id: str) -> None:
    group_dir = root / group
    exp_dir = group_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True)
    (group_dir / "profile.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    (exp_dir / "trace.json").write_text('{"entries": []}\n', encoding="utf-8")


def raw_observation(*, template_id, delta_cycles, experiment_id, body, instruction_id="vadd_vv", lmul="m1"):
    return search_model.RawObservation(
        trace_path=Path(f"/tmp/{experiment_id}/trace.json"),
        experiment_path=Path(f"/tmp/{experiment_id}/experiment.yaml"),
        experiment_id=experiment_id,
        instruction_id=instruction_id,
        lmul=lmul,
        template_id=template_id,
        effective_template_id=template_id,
        marker_pair="start/end",
        delta_cycles=delta_cycles,
        marker_baseline_cycles=0,
        parameters={},
        body=dict(body),
        pair_instruction_id=None,
        raw_pipe_labels=(),
        synthetic_reference={},
        mode="unit",
        backend="unit",
        dry_run_trace=False,
        trace_sha256=f"sha-{experiment_id}",
    )


def t12_linear_observations(latency: int, cadence: int, gaps=range(4)):
    return [
        raw_observation(
            template_id="T12_CONSUMER_RAW_GAP",
            delta_cycles=latency + gap * cadence,
            experiment_id=f"t12-vadd-vv-m1-k{gap}",
            body={
                "filler_count": gap,
                "consumer": "vadd_vv",
                "filler_instruction_id": "vadd_vv",
                "filler_cadence_cycles": cadence,
            },
        )
        for gap in gaps
    ]


def solve_latency_field(observations, *, max_value=8):
    key = (observations[0].instruction_id, observations[0].lmul)
    result = search_model.solve_candidate_sets({key: list(observations)}, max_value)[key]
    return search_model.candidate_field_result("Latency", result, max_value=max_value)


class ReviewPhaseRound28Test(unittest.TestCase):
    def test_trace_discovery_recurses_into_repeat_result_roots_only(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir) / "results"
            write_result_group(root, "vadd_vv", "top-t10")
            write_result_group(root / "r01", "vadd_vv", "repeat-r01-t10")
            write_result_group(root / "r02", "vadd_vv", "repeat-r02-t10")
            write_result_group(root / "blog", "vdivu_vv", "blog-t10")

            trace_paths = search_support.trace_files_from_path(root.as_posix())

        self.assertEqual(
            trace_paths,
            [
                root / "r01" / "vadd_vv" / "experiments" / "repeat-r01-t10" / "trace.json",
                root / "r02" / "vadd_vv" / "experiments" / "repeat-r02-t10" / "trace.json",
                root / "vadd_vv" / "experiments" / "top-t10" / "trace.json",
            ],
        )

    def test_t12_linear_positive_residual_does_not_bound_latency(self):
        field = solve_latency_field(t12_linear_observations(latency=4, cadence=1))

        self.assertEqual(field["status"], "non_identifiable")
        self.assertNotIn("upper_bound", field)
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("linear_positive_residual", field["t12_latency_constraints"][0]["reason"])

    def test_t12_linear_residual_does_not_reject_direct_t11_latency(self):
        observations = [
            raw_observation(
                template_id="T11_SELF_RAW_CHAIN",
                delta_cycles=8,
                experiment_id="t11-vadd-vv-m1-n3",
                body={"iterations": 3, "latency_evidence": True, "true_raw_chain": True},
            ),
            raw_observation(
                template_id="T11_SELF_RAW_CHAIN",
                delta_cycles=12,
                experiment_id="t11-vadd-vv-m1-n4",
                body={"iterations": 4, "latency_evidence": True, "true_raw_chain": True},
            ),
            *t12_linear_observations(latency=4, cadence=1),
        ]

        field = solve_latency_field(observations)

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)


if __name__ == "__main__":
    unittest.main()
