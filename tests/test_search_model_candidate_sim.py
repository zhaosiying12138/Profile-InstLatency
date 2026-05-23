import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_MODEL_PATH = REPO_ROOT / "scripts" / "search_model.py"


def load_search_model():
    spec = importlib.util.spec_from_file_location("search_model_under_test", SEARCH_MODEL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


search_model = load_search_model()


def raw_observation(
    *,
    instruction_id="vsubject",
    lmul="m1",
    template_id,
    delta_cycles,
    experiment_id,
    body=None,
    parameters=None,
    pair_instruction_id=None,
):
    body = dict(body or {})
    parameters = dict(parameters or {})
    return search_model.RawObservation(
        trace_path=Path(f"/tmp/{experiment_id}/trace.json"),
        experiment_path=Path(f"/tmp/{experiment_id}/experiment.yaml"),
        experiment_id=experiment_id,
        instruction_id=instruction_id,
        lmul=lmul,
        template_id=template_id,
        effective_template_id=template_id,
        marker_pair="t0/t1",
        delta_cycles=delta_cycles,
        marker_baseline_cycles=0,
        parameters=parameters,
        body=body,
        pair_instruction_id=pair_instruction_id,
        raw_pipe_labels=(),
        synthetic_reference={},
        mode="unit",
        backend="unit",
        dry_run_trace=False,
        trace_sha256=f"sha-{experiment_id}",
    )


def t20_observations(deltas_by_count, *, subject="vsubject", peer="vpeer", lmul="m1"):
    return [
        raw_observation(
            instruction_id=subject,
            lmul=lmul,
            template_id="T20_PAIRWISE_PIPE_CLASSIFICATION",
            delta_cycles=delta,
            experiment_id=f"t20-{subject}-{peer}-{lmul}-n{count}",
            body={"pair_count": count, "register_policy": "prefer", "register_reuse": False},
            pair_instruction_id=peer,
        )
        for count, delta in deltas_by_count
    ]


def t12_observations(deltas_by_gap, *, instruction_id="vproducer", lmul="m1"):
    return [
        raw_observation(
            instruction_id=instruction_id,
            lmul=lmul,
            template_id="T12_CONSUMER_RAW_GAP",
            delta_cycles=delta,
            experiment_id=f"t12-{instruction_id}-{lmul}-k{gap}",
            body={"filler_count": gap, "consumer": "vconsumer", "filler_instruction_id": "vadd_vv"},
        )
        for gap, delta in deltas_by_gap
    ]


def candidate(*, proc_resource="pipe0", release_at_cycles=1, num_micro_ops=1, single_issue=False, latency=1):
    return search_model.TimingCandidate(
        latency=latency,
        release_at_cycles=release_at_cycles,
        proc_resource=proc_resource,
        num_micro_ops=num_micro_ops,
        single_issue=single_issue,
    )


def check_t20(observations, subject_candidate, peer_candidate):
    first = observations[0]
    return search_model.check_candidate_against_options(
        first,
        subject_candidate,
        {(first.pair_instruction_id, first.lmul): (peer_candidate,)},
        {},
        group_items=observations,
    )


def solve_latency_field(observations, *, max_value=8):
    key = (observations[0].instruction_id, observations[0].lmul)
    result = search_model.solve_candidate_sets({key: list(observations)}, max_value)[key]
    return search_model.candidate_field_result("Latency", result, max_value=max_value)


class SearchModelCandidateSimulatorTest(unittest.TestCase):
    def test_t20_startup_free_slope_accepts_nonzero_intercept(self):
        observations = t20_observations([(2, 3), (3, 5), (4, 7)])

        check = check_t20(observations, candidate(proc_resource="pipe0"), candidate(proc_resource="pipe0"))

        self.assertEqual(check.status, "match")

    def test_t20_uses_peer_candidate_options(self):
        observations = t20_observations([(2, 3), (3, 5), (4, 7)])

        check = check_t20(observations, candidate(proc_resource="pipe0"), candidate(proc_resource="pipe1"))

        self.assertEqual(check.status, "mismatch")

    def test_t20_any_allocates_to_free_pipe(self):
        observations = t20_observations([(2, 3), (3, 4), (4, 5)])

        check = check_t20(observations, candidate(proc_resource="any"), candidate(proc_resource="pipe0"))

        self.assertEqual(check.status, "match")

    def test_t20_single_count_remains_skipped(self):
        observations = t20_observations([(2, 3)])

        check = check_t20(observations, candidate(proc_resource="pipe0"), candidate(proc_resource="pipe0"))

        self.assertEqual(check.status, "skipped")
        self.assertIn("single_count", check.reason)

    def test_t12_clean_threshold_infers_exact_latency(self):
        field = solve_latency_field(t12_observations([(0, 4), (1, 4), (2, 4), (3, 4), (4, 5), (5, 6)]))

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)

    def test_t12_upper_bound_does_not_render_fake_exact_zero(self):
        field = solve_latency_field(t12_observations([(0, 7), (1, 11), (2, 15)], lmul="m4"))

        self.assertIn(field["status"], {"insufficient_evidence", "non_identifiable"})
        self.assertIsNone(field["value"])
        self.assertNotEqual(field.get("value"), 0)

    def test_t12_regime_break_uses_clean_prefix(self):
        deltas = [(0, 4), (1, 4), (2, 4), (3, 4)]
        deltas.extend((gap, gap + 1) for gap in range(4, 13))
        deltas.append((13, 44))

        field = solve_latency_field(t12_observations(deltas))

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)


if __name__ == "__main__":
    unittest.main()
