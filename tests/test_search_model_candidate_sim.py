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


def t20_proc_observations(
    deltas_by_count,
    *,
    subject="vsubject",
    peer="vpeer",
    lmul="m4",
    register_policy="resource_noreuse_prefix",
    register_reuse=False,
    suffix="resource-noreuse",
):
    return [
        raw_observation(
            instruction_id=subject,
            lmul=lmul,
            template_id="T20_PAIRWISE_PIPE_CLASSIFICATION",
            delta_cycles=delta,
            experiment_id=f"t20-{subject}-{peer}-{lmul}-n{count}-{suffix}",
            body={
                "pair_count": count,
                "register_policy": register_policy,
                "register_reuse": register_reuse,
                "resource_disambiguation": {
                    "usable_for_proc_resource": True,
                    "count_set_id": "m4_vector_vector_noreuse",
                    "symmetry_breaker": False,
                },
            },
            pair_instruction_id=peer,
        )
        for count, delta in deltas_by_count
    ]


def t10_observations(deltas_by_iterations, *, instruction_id="vfiller", lmul="m1"):
    return [
        raw_observation(
            instruction_id=instruction_id,
            lmul=lmul,
            template_id="T10_INDEPENDENT_STREAM_THROUGHPUT",
            delta_cycles=delta,
            experiment_id=f"t10-{instruction_id}-{lmul}-n{iterations}",
            body={"iterations": iterations},
        )
        for iterations, delta in deltas_by_iterations
    ]


def t12_observations(
    deltas_by_gap,
    *,
    instruction_id="vproducer",
    lmul="m1",
    filler_instruction_id="vadd_vv",
    body_extra=None,
    experiment_suffix="",
):
    extra = dict(body_extra or {})
    return [
        raw_observation(
            instruction_id=instruction_id,
            lmul=lmul,
            template_id="T12_CONSUMER_RAW_GAP",
            delta_cycles=delta,
            experiment_id=f"t12-{instruction_id}-{lmul}-k{gap}{experiment_suffix}",
            body={
                "filler_count": gap,
                "consumer": "vconsumer",
                "filler_instruction_id": filler_instruction_id,
                **extra,
            },
        )
        for gap, delta in deltas_by_gap
    ]


def t12_matched_control_observations(
    dependent_deltas_by_gap,
    control_deltas_by_gap,
    *,
    instruction_id="vproducer",
    lmul="m1",
    filler_instruction_id="scalar_add",
    cadence=1,
):
    dependent = t12_observations(
        dependent_deltas_by_gap,
        instruction_id=instruction_id,
        lmul=lmul,
        filler_instruction_id=filler_instruction_id,
        body_extra={
            "filler_cadence_cycles": cadence,
            "t12_consumer_role": "dependent",
            "consumer_reads_producer": True,
        },
        experiment_suffix="-dependent",
    )
    control = t12_observations(
        control_deltas_by_gap,
        instruction_id=instruction_id,
        lmul=lmul,
        filler_instruction_id=filler_instruction_id,
        body_extra={
            "filler_cadence_cycles": cadence,
            "t12_consumer_role": "control",
            "consumer_reads_producer": False,
            "matched_dependent_experiment_id": "t12-vproducer-m1-k0-dependent",
        },
        experiment_suffix="-control",
    )
    return dependent + control


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


def solve_candidate_fields(observations, *, max_value=8):
    key = (observations[0].instruction_id, observations[0].lmul)
    result = search_model.solve_candidate_sets({key: list(observations)}, max_value)[key]
    return {
        field: search_model.candidate_field_result(field, result, max_value=max_value)
        for field in search_model.FIELD_ORDER
    }


def solve_latency_field_from_groups(grouped, key, *, max_value=8):
    result = search_model.solve_candidate_sets(grouped, max_value)[key]
    return search_model.candidate_field_result("Latency", result, max_value=max_value)


def solve_global_proc(observations, release_values, candidate_domains):
    return search_model.solve_global_proc_resources(
        observations,
        release_values,
        candidate_domains,
    )


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

    def test_t20_peer_side_observation_constrains_peer_only_row(self):
        observations = t20_observations([(2, 3), (3, 5), (4, 7)], subject="vsubject", peer="vpeer")
        observations.append(
            raw_observation(
                instruction_id="vpeer",
                template_id="T11_SELF_RAW_CHAIN",
                delta_cycles=0,
                experiment_id="t11-vpeer-placeholder",
                body={"iterations": 2, "latency_evidence": False},
            )
        )
        grouped = search_model.group_observations(observations)
        peer_items = grouped[("vpeer", "m1")]
        mirrored_t20_items = [
            item
            for item in peer_items
            if item.effective_template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION"
        ]

        self.assertEqual(len(mirrored_t20_items), 3)
        self.assertTrue(all(item.instruction_id == "vpeer" for item in mirrored_t20_items))
        self.assertTrue(all(item.pair_instruction_id == "vsubject" for item in mirrored_t20_items))

        subject = candidate(proc_resource="pipe0")
        matching_peer = candidate(proc_resource="pipe0")
        mismatching_peer = candidate(proc_resource="pipe1")
        result = search_model.candidate_result_for_group(
            ("vpeer", "m1"),
            peer_items,
            grouped,
            4,
            base_candidates={
                ("vsubject", "m1"): (subject,),
                ("vpeer", "m1"): (matching_peer, mismatching_peer),
            },
        )

        self.assertEqual(result.candidates, (matching_peer,))
        self.assertTrue(
            any(
                item.effective_template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION"
                for item in result.evidence
            )
        )

    def test_t12_clean_threshold_infers_exact_latency(self):
        field = solve_latency_field(t12_observations([(0, 4), (1, 4), (2, 4), (3, 4), (4, 5), (5, 6)]))

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)

    def test_t12_two_point_short_sweep_does_not_claim_exact_latency(self):
        field = solve_latency_field(t12_observations([(0, 4), (1, 4)]))

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertNotEqual(field.get("value"), 2)
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("insufficient_post_transition_coverage", field["t12_latency_constraints"][0]["reason"])

    def test_t12_upper_bound_does_not_render_fake_exact_zero(self):
        field = solve_latency_field(t12_observations([(0, 7), (1, 11), (2, 15)], lmul="m4"))

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertEqual(field["upper_bound"], 4)
        self.assertEqual(field["candidates"], [0, 1, 2, 3, 4])
        self.assertEqual(field["candidate_count"], 5)

    def test_t12_metadata_cadence_narrows_upper_bound_without_exact_claim(self):
        wide = t12_observations([(0, 7), (1, 11), (2, 15)], lmul="m4")
        focused = t12_observations(
            [(0, 7), (1, 8), (2, 9), (3, 10)],
            lmul="m4",
            filler_instruction_id="scalar_add",
            body_extra={"filler_cadence_cycles": 1},
        )

        field = solve_latency_field(wide + focused)

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertEqual(field["upper_bound"], 1)
        self.assertEqual(field["candidate_domain"], "0..1")
        self.assertEqual(field["candidates"], [0, 1])
        self.assertTrue(
            any(
                constraint["status"] == "upper_bound"
                and constraint["upper_bound"] == 1
                and "metadata_filler_cadence:scalar_add" in constraint["reason"]
                for constraint in field["t12_latency_constraints"]
            )
        )

    def test_t12_metadata_cadence_short_transition_remains_non_identifiable(self):
        focused = t12_observations(
            [(0, 4), (1, 4)],
            lmul="m4",
            filler_instruction_id="scalar_add",
            body_extra={"filler_cadence_cycles": 1},
        )

        field = solve_latency_field(focused)

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertNotEqual(field.get("value"), 4)
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("insufficient_post_transition_coverage", field["t12_latency_constraints"][0]["reason"])

    def test_t12_regime_break_uses_clean_prefix(self):
        deltas = [(0, 4), (1, 4), (2, 4), (3, 4)]
        deltas.extend((gap, gap + 1) for gap in range(4, 13))
        deltas.append((13, 44))

        field = solve_latency_field(t12_observations(deltas))

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)
        self.assertIn("t12_latency_constraints", field)
        for entry in field["evidence"]:
            if "k13" in entry:
                self.assertNotIn("candidate_simulator:Latency", entry)

    def test_t12_report_uses_solver_candidate_context_for_filler_cadence(self):
        producer = t12_observations(
            [(0, 4), (1, 4), (2, 6)],
            instruction_id="vproducer",
            filler_instruction_id="vfiller",
        )
        filler = t10_observations([(2, 10), (3, 12)], instruction_id="vfiller")
        grouped = {
            ("vproducer", "m1"): producer,
            ("vfiller", "m1"): filler,
        }

        field = solve_latency_field_from_groups(grouped, ("vproducer", "m1"))

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 4)
        self.assertEqual(field["t12_latency_constraints"][0]["filler_cadence"], 2)
        self.assertIn("candidate_options:vfiller", field["t12_latency_constraints"][0]["reason"])

    def test_t12_matched_control_convergence_infers_exact_latency(self):
        field = solve_latency_field(
            t12_matched_control_observations(
                [(0, 7), (1, 7), (2, 7), (3, 7), (4, 8), (5, 9)],
                [(0, 4), (1, 5), (2, 6), (3, 7), (4, 8), (5, 9)],
            )
        )

        self.assertEqual(field["status"], "exact_fit")
        self.assertEqual(field["value"], 3)
        constraint = field["t12_latency_constraints"][0]
        self.assertEqual(constraint["status"], "exact")
        self.assertIn("matched_control_convergence", constraint["reason"])
        self.assertIn("converged_gap=3", constraint["reason"])

    def test_t12_matched_control_repeat_disagreement_fails_closed(self):
        observations = t12_matched_control_observations(
            [(0, 7), (1, 7), (2, 7), (3, 7)],
            [(0, 4), (1, 5), (2, 6), (3, 7)],
        )
        observations.append(
            raw_observation(
                instruction_id="vproducer",
                lmul="m1",
                template_id="T12_CONSUMER_RAW_GAP",
                delta_cycles=8,
                experiment_id="t12-vproducer-m1-k3-control-repeat-disagree",
                body={
                    "filler_count": 3,
                    "consumer": "vconsumer",
                    "filler_instruction_id": "scalar_add",
                    "filler_cadence_cycles": 1,
                    "t12_consumer_role": "control",
                    "consumer_reads_producer": False,
                },
            )
        )

        field = solve_latency_field(observations)

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("repeated_gap_delta_disagreement", field["t12_latency_constraints"][0]["reason"])

    def test_t12_matched_control_non_monotonic_control_fails_closed(self):
        field = solve_latency_field(
            t12_matched_control_observations(
                [(0, 7), (1, 7), (2, 7), (3, 7)],
                [(0, 4), (1, 6), (2, 5), (3, 7)],
            )
        )

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("control_non_monotonic_or_exceeds_cadence", field["t12_latency_constraints"][0]["reason"])

    def test_t12_matched_control_last_only_convergence_fails_closed(self):
        field = solve_latency_field(
            t12_matched_control_observations(
                [(0, 6), (1, 6), (2, 6)],
                [(0, 4), (1, 5), (2, 6)],
            )
        )

        self.assertEqual(field["status"], "non_identifiable")
        self.assertIsNone(field["value"])
        self.assertEqual(field["t12_latency_constraints"][0]["status"], "skipped")
        self.assertIn("insufficient_post_convergence_coverage", field["t12_latency_constraints"][0]["reason"])

    def test_non_affine_vcpop_m4_issue_fields_keep_stream_diagnostics(self):
        observations = t10_observations(
            [(2, 6), (4, 10), (6, 18)],
            instruction_id="vcpop_m",
            lmul="m4",
        )

        fields = solve_candidate_fields(observations)

        for field in ("ReleaseAtCycles", "ProcResource", "NumMicroOps", "SingleIssue"):
            row = fields[field]
            self.assertEqual(row["status"], "non_identifiable", field)
            self.assertIsNone(row["value"], field)
            self.assertIn("not affine", row["reason"])
            self.assertEqual(
                row["non_affine_stream_observations"],
                [
                    {"experiment_id": "t10-vcpop_m-m4-n2", "iterations": 2, "delta_cycles": 6},
                    {"experiment_id": "t10-vcpop_m-m4-n4", "iterations": 4, "delta_cycles": 10},
                    {"experiment_id": "t10-vcpop_m-m4-n6", "iterations": 6, "delta_cycles": 18},
                ],
            )
            self.assertIn("observed_points=n2=delta6,n4=delta10,n6=delta18", row["follow_up"])

    def test_field_status_counts_non_identifiable_as_blocking(self):
        report = {
            "filters": {"mode": "real_platform_profile", "backend": "gem5_minor"},
            "instructions": {
                "vsubject": {
                    "lmuls": {
                        "m1": {
                            "fields": {
                                "Latency": {"status": "exact_fit", "value": 4},
                                "ReleaseAtCycles": {"status": "exact_fit", "value": 1},
                                "ProcResource": {
                                    "status": "non_identifiable",
                                    "value": None,
                                    "reason": "unit test unresolved row",
                                },
                                "NumMicroOps": {"status": "exact_fit", "value": 1},
                                "SingleIssue": {"status": "exact_fit", "value": False},
                            }
                        }
                    }
                }
            },
        }

        field_status = search_model.build_field_status(report)

        self.assertEqual(
            field_status["summary"]["blocking_status_counts"].get("non_identifiable"),
            1,
        )
        self.assertEqual(field_status["summary"]["blocking_total"], 1)

    def test_global_proc_uses_clean_t20_subset_amid_reused_observations(self):
        reused = t20_proc_observations(
            [(2, 9), (3, 11), (4, 13)],
            subject="vanchor",
            peer="vtarget",
            register_policy="prefer",
            register_reuse=True,
            suffix="old-reused",
        )
        clean = t20_proc_observations(
            [(1, 5), (2, 7), (3, 9)],
            subject="vanchor",
            peer="vtarget",
        )
        result = solve_global_proc(
            reused + clean,
            {("vanchor", "m4"): 1, ("vtarget", "m4"): 1},
            {("vanchor", "m4"): ("pipe0",), ("vtarget", "m4"): ("pipe0", "pipe1")},
        )

        row = result["rows"][("vtarget", "m4")]

        self.assertEqual(row["status"], "exact_fit")
        self.assertEqual(row["value"], "YuShuXinVPipe0")
        self.assertEqual(row["global_solution_count"], 1)
        self.assertTrue(
            any(item["status"] == "skipped_register_reuse" for item in result["skipped_constraints"])
        )

    def test_global_proc_mirror_solutions_canonicalize_to_exact(self):
        observations = t20_proc_observations(
            [(1, 4), (2, 6), (3, 8)],
            subject="vleft",
            peer="vright",
        )

        result = solve_global_proc(
            observations,
            {("vleft", "m4"): 1, ("vright", "m4"): 1},
            {("vleft", "m4"): ("pipe0", "pipe1"), ("vright", "m4"): ("pipe0", "pipe1")},
        )

        row = result["rows"][("vleft", "m4")]

        self.assertEqual(row["status"], "exact_fit")
        self.assertEqual(row["value"], "YuShuXinVPipe0")
        self.assertEqual(row["candidates"], ["YuShuXinVPipe0"])
        self.assertEqual(row["global_solution_count"], 2)
        self.assertEqual(row["surviving_candidates"], ["YuShuXinVPipe0"])
        self.assertEqual(
            row["symmetry_breaking_assumption"]["type"],
            "global_pipe_label_mirror",
        )
        self.assertEqual(
            row["symmetry_breaking_assumption"]["canonical_assignment"],
            {
                "vleft:m4": "YuShuXinVPipe0",
                "vright:m4": "YuShuXinVPipe0",
            },
        )

    def test_global_proc_non_mirror_ambiguity_remains_non_identifiable(self):
        observations = t20_proc_observations(
            [(1, 3), (2, 4), (3, 5)],
            subject="vleft",
            peer="vright",
        )

        result = solve_global_proc(
            observations,
            {("vleft", "m4"): 1, ("vright", "m4"): 1},
            {("vleft", "m4"): ("pipe0", "pipe1"), ("vright", "m4"): ("any", "pipe0", "pipe1")},
        )

        row = result["rows"][("vright", "m4")]

        self.assertEqual(row["status"], "non_identifiable")
        self.assertIsNone(row["value"])
        self.assertEqual(row["global_solution_count"], 4)
        self.assertNotIn("symmetry_breaking_assumption", row)

    def test_global_proc_conflict_remains_fail_closed(self):
        observations = t20_proc_observations(
            [(1, 3), (2, 4), (3, 5)],
            subject="vleft",
            peer="vright",
        )

        result = solve_global_proc(
            observations,
            {("vleft", "m4"): 1, ("vright", "m4"): 1},
            {("vleft", "m4"): ("pipe0",), ("vright", "m4"): ("pipe0",)},
        )

        row = result["rows"][("vleft", "m4")]

        self.assertEqual(row["status"], "conflict")
        self.assertIsNone(row["value"])
        self.assertEqual(row["global_solution_count"], 0)
        self.assertEqual(row["candidates"], [])
        self.assertNotIn("symmetry_breaking_assumption", row)

    def test_global_proc_fixed_candidate_permits_exact_propagation(self):
        observations = t20_proc_observations(
            [(1, 4), (2, 6), (3, 8)],
            subject="vanchor",
            peer="vtarget",
        )

        result = solve_global_proc(
            observations,
            {("vanchor", "m4"): 1, ("vtarget", "m4"): 1},
            {("vanchor", "m4"): ("pipe1",), ("vtarget", "m4"): ("pipe0", "pipe1")},
        )

        row = result["rows"][("vtarget", "m4")]

        self.assertEqual(row["status"], "exact_fit")
        self.assertEqual(row["value"], "YuShuXinVPipe1")
        self.assertEqual(row["candidates"], ["YuShuXinVPipe1"])

    def test_global_proc_empty_peer_domain_does_not_create_false_conflict(self):
        observations = t20_proc_observations(
            [(1, 4), (2, 6), (3, 8)],
            subject="vsubject",
            peer="vempty",
        )

        result = solve_global_proc(
            observations,
            {("vsubject", "m4"): 1, ("vempty", "m4"): 1},
            {("vsubject", "m4"): ("pipe0", "pipe1"), ("vempty", "m4"): ()},
        )

        self.assertNotIn(("vsubject", "m4"), result["rows"])
        self.assertEqual(result["conflict_constraints"], [])
        self.assertTrue(
            any(
                item["status"] == "skipped_empty_candidate_domain"
                for item in result["skipped_constraints"]
            )
        )

    def test_field_status_and_profile_preserve_symmetry_breaking_assumption(self):
        assumption = {
            "type": "global_pipe_label_mirror",
            "equivalence": "pipe0_pipe1_global_swap",
            "canonical_assignment": {"vsubject:m4": "YuShuXinVPipe0"},
            "alternate_assignments": [{"vsubject:m4": "YuShuXinVPipe1"}],
        }
        report = {
            "filters": {"mode": "real_platform_profile", "backend": "gem5_minor"},
            "instructions": {
                "vsubject": {
                    "lmuls": {
                        "m4": {
                            "fields": {
                                "Latency": {"status": "exact_fit", "value": 4},
                                "ReleaseAtCycles": {"status": "exact_fit", "value": 1},
                                "ProcResource": {
                                    "status": "exact_fit",
                                    "value": "YuShuXinVPipe0",
                                    "candidates": ["YuShuXinVPipe0"],
                                    "candidate_count": 1,
                                    "constraint_count": 1,
                                    "reason": "unit test canonicalized mirror ambiguity",
                                    "symmetry_breaking_assumption": assumption,
                                },
                                "NumMicroOps": {"status": "exact_fit", "value": 1},
                                "SingleIssue": {"status": "exact_fit", "value": False},
                            }
                        }
                    }
                }
            },
        }

        field_status = search_model.build_field_status(report)
        proc_rows = [
            row
            for row in field_status["rows"]
            if row["instruction_id"] == "vsubject" and row["field"] == "ProcResource"
        ]
        profile = search_model.profile_for_instruction("vsubject", field_status["rows"], report)

        self.assertEqual(proc_rows[0]["symmetry_breaking_assumption"], assumption)
        self.assertEqual(
            profile["llvm_facing_fields"]["m4"]["ProcResource"]["symmetry_breaking_assumption"],
            assumption,
        )


if __name__ == "__main__":
    unittest.main()
