#!/usr/bin/env python3
"""Implementation entrypoint for RVV timing-parameter search."""

from search_model_support import *  # noqa: F401,F403

def t12_consumer_key(item: RawObservation) -> str:
    consumer = first_metadata_value(item, "consumer", "consumer_instruction_id", "consumer_instruction")
    if consumer is None:
        consumer = item.pair_instruction_id
    return str(consumer) if consumer is not None else "unknown"


def t12_filler_instruction(item: RawObservation) -> str:
    filler = first_metadata_value(item, "filler_instruction_id", "filler_instruction", "filler", "filler_op")
    return str(filler) if filler is not None else "vadd_vv"


def t12_register_policy(item: RawObservation) -> str:
    policy = first_metadata_value(item, "register_policy", "source_register_policy", "dst_register_policy")
    return str(policy) if policy is not None else "unspecified"


def t12_consumer_role(item: RawObservation) -> str:
    role = first_metadata_value(item, "t12_consumer_role", "consumer_role")
    if role is not None:
        role_text = str(role)
        if role_text in {"dependent", "control"}:
            return role_text
    reads_producer = body_bool(item, "consumer_reads_producer")
    if reads_producer is False:
        return "control"
    return "dependent"


def t12_trailing_min_residual_gaps(clean_gaps: list[int], residuals: dict[int, int]) -> tuple[int, ...]:
    if not clean_gaps:
        return ()
    minimum_residual = min(residuals.values())
    plateau: list[int] = []
    for gap in reversed(clean_gaps):
        if residuals[gap] != minimum_residual:
            break
        plateau.append(gap)
    return tuple(reversed(plateau))


def t12_observation_group_key(item: RawObservation) -> tuple[str, str, str, str, str]:
    return (
        item.instruction_id,
        item.lmul,
        t12_consumer_key(item),
        t12_filler_instruction(item),
        t12_register_policy(item),
    )


def matching_t12_group(item: RawObservation, group_items: Iterable[RawObservation]) -> tuple[RawObservation, ...]:
    key = t12_observation_group_key(item)
    return tuple(
        candidate
        for candidate in group_items
        if candidate.effective_template_id == "T12_CONSUMER_RAW_GAP" and t12_observation_group_key(candidate) == key
    )


def unique_release_from_options(candidates: Iterable[TimingCandidate]) -> int | None:
    releases = {candidate.release_at_cycles for candidate in candidates}
    if len(releases) != 1:
        return None
    return max(1, next(iter(releases)))


def t12_filler_cadence(
    item: RawObservation,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
) -> tuple[int | None, str]:
    filler = t12_filler_instruction(item)
    metadata_cadence = body_int(
        item,
        "filler_cadence_cycles",
        "independent_filler_cadence_cycles",
        "filler_release_at_cycles",
    )
    if filler == "scalar_add" and metadata_cadence is not None and metadata_cadence > 0:
        return metadata_cadence, f"metadata_filler_cadence:{filler}"
    key = (filler, item.lmul)
    fixed = fixed_candidates.get(key)
    if fixed is not None:
        return max(1, fixed.release_at_cycles), f"fixed_candidate:{filler}"
    option_release = unique_release_from_options(candidate_options.get(key, ()))
    if option_release is not None:
        return option_release, f"candidate_options:{filler}"
    if filler == "scalar_add":
        return 1, "known_scalar_add_cadence"
    return None, f"missing_filler_cadence:{filler}"


def t12_matched_control_constraint(
    item: RawObservation,
    group: tuple[RawObservation, ...],
    cadence: int,
    cadence_source: str,
) -> T12LatencyConstraint | None:
    roles = {t12_consumer_role(member) for member in group}
    if "control" not in roles:
        return None
    if "dependent" not in roles:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:matched_control_missing_dependent;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)}"
            ),
            group,
            filler_cadence=cadence,
        )

    deltas_by_role_gap: dict[str, dict[int, set[int]]] = {
        "dependent": defaultdict(set),
        "control": defaultdict(set),
    }
    observations_by_role_gap: dict[str, dict[int, list[RawObservation]]] = {
        "dependent": defaultdict(list),
        "control": defaultdict(list),
    }
    for member in group:
        role = t12_consumer_role(member)
        if role not in deltas_by_role_gap:
            continue
        gap = body_int(member, "filler_count")
        if gap is None or gap < 0:
            continue
        deltas_by_role_gap[role][gap].add(member.delta_cycles)
        observations_by_role_gap[role][gap].append(member)

    for role in ("dependent", "control"):
        disagreeing_gaps = sorted(gap for gap, deltas in deltas_by_role_gap[role].items() if len(deltas) != 1)
        if disagreeing_gaps:
            evidence = tuple(
                member
                for gap in disagreeing_gaps
                for member in observations_by_role_gap[role][gap]
            )
            return T12LatencyConstraint(
                "skipped",
                (
                    "T12 skipped:repeated_gap_delta_disagreement;"
                    f"role={role};instruction={item.instruction_id};lmul={item.lmul};"
                    f"consumer={t12_consumer_key(item)};gaps={disagreeing_gaps}"
                ),
                evidence,
                filler_cadence=cadence,
            )

    dependent_gaps = set(deltas_by_role_gap["dependent"])
    control_gaps = set(deltas_by_role_gap["control"])
    matched_gaps = sorted(dependent_gaps & control_gaps)
    if not matched_gaps or matched_gaps[0] != 0:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:matched_control_missing_gap0;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"dependent_gaps={sorted(dependent_gaps)};control_gaps={sorted(control_gaps)}"
            ),
            group,
            filler_cadence=cadence,
        )
    expected_gaps = list(range(matched_gaps[-1] + 1))
    if matched_gaps != expected_gaps:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:matched_control_non_contiguous_gaps;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"matched_gaps={matched_gaps}"
            ),
            group,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
        )
    if len(matched_gaps) < 2:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:matched_control_insufficient_coverage;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"matched_gaps={matched_gaps}"
            ),
            group,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
        )

    dependent_delta = {gap: next(iter(deltas_by_role_gap["dependent"][gap])) for gap in matched_gaps}
    control_delta = {gap: next(iter(deltas_by_role_gap["control"][gap])) for gap in matched_gaps}
    control_cadence_gaps: list[int] = []
    for previous, current in zip(matched_gaps, matched_gaps[1:]):
        slope = control_delta[current] - control_delta[previous]
        if slope < 0 or slope > cadence:
            return T12LatencyConstraint(
                "skipped",
                (
                    "T12 skipped:control_non_monotonic_or_exceeds_cadence;"
                    f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                    f"previous_gap={previous};current_gap={current};slope={slope};filler_cadence={cadence}"
                ),
                group,
                filler_cadence=cadence,
                clean_gaps=tuple(matched_gaps),
            )
        if slope == cadence:
            control_cadence_gaps.append(current)

    stalls = {gap: dependent_delta[gap] - control_delta[gap] for gap in matched_gaps}
    negative_gaps = [gap for gap, stall in stalls.items() if stall < 0]
    if negative_gaps:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:matched_control_negative_stall;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"gaps={negative_gaps}"
            ),
            group,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )
    for previous, current in zip(matched_gaps, matched_gaps[1:]):
        if stalls[current] > stalls[previous]:
            return T12LatencyConstraint(
                "skipped",
                (
                    "T12 skipped:matched_control_stall_not_non_increasing;"
                    f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                    f"previous_gap={previous};current_gap={current};"
                    f"previous_stall={stalls[previous]};current_stall={stalls[current]}"
                ),
                group,
                filler_cadence=cadence,
                clean_gaps=tuple(matched_gaps),
                observed_cadence_gaps=tuple(control_cadence_gaps),
            )

    converged_gaps = [gap for gap in matched_gaps if stalls[gap] == 0]
    reason_prefix = (
        f"T12 matched_control_convergence;instruction={item.instruction_id};lmul={item.lmul};"
        f"consumer={t12_consumer_key(item)};filler_cadence={cadence};"
        f"cadence_source={cadence_source};matched_gaps={matched_gaps};"
        f"stalls={[stalls[gap] for gap in matched_gaps]};"
        f"control_cadence_gaps={control_cadence_gaps}"
    )
    evidence = tuple(
        member
        for gap in matched_gaps
        for role in ("dependent", "control")
        for member in observations_by_role_gap[role][gap]
    )
    if not converged_gaps:
        return T12LatencyConstraint(
            "skipped",
            f"{reason_prefix};no_matched_control_convergence",
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )
    converged_gap = converged_gaps[0]
    if not any(gap > converged_gap and stalls[gap] == 0 for gap in matched_gaps):
        return T12LatencyConstraint(
            "skipped",
            f"{reason_prefix};insufficient_post_convergence_coverage;converged_gap={converged_gap}",
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )

    positive_stall_latency = {
        gap * cadence + stall
        for gap, stall in stalls.items()
        if stall > 0
    }
    if not positive_stall_latency:
        return T12LatencyConstraint(
            "skipped",
            f"{reason_prefix};no_positive_stall_latency_equation",
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )
    if len(positive_stall_latency) != 1:
        return T12LatencyConstraint(
            "skipped",
            f"{reason_prefix};positive_stall_latency_disagreement;latencies={sorted(positive_stall_latency)}",
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )

    latency = next(iter(positive_stall_latency))
    inconsistent_zero_gaps = [
        gap for gap in converged_gaps if gap * cadence < latency
    ]
    if inconsistent_zero_gaps:
        return T12LatencyConstraint(
            "skipped",
            (
                f"{reason_prefix};zero_stall_before_positive_latency;"
                f"latency={latency};zero_gaps={inconsistent_zero_gaps}"
            ),
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(matched_gaps),
            observed_cadence_gaps=tuple(control_cadence_gaps),
        )

    return T12LatencyConstraint(
        "exact",
        (
            f"{reason_prefix};converged_gap={converged_gap};"
            f"positive_stall_latency={latency};exact_latency={latency}"
        ),
        evidence,
        latency=latency,
        filler_cadence=cadence,
        clean_gaps=tuple(matched_gaps),
        observed_cadence_gaps=tuple(control_cadence_gaps),
    )


def t12_constraint_for_group(
    item: RawObservation,
    group_items: Iterable[RawObservation],
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
) -> T12LatencyConstraint:
    group = matching_t12_group(item, group_items)
    cadence, cadence_source = t12_filler_cadence(item, candidate_options, fixed_candidates)
    if cadence is None:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:missing_filler_cadence;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"source={cadence_source}"
            ),
            group,
        )
    matched_control = t12_matched_control_constraint(item, group, cadence, cadence_source)
    if matched_control is not None:
        return matched_control
    deltas_by_gap: dict[int, set[int]] = defaultdict(set)
    observations_by_gap: dict[int, list[RawObservation]] = defaultdict(list)
    for member in group:
        if t12_consumer_role(member) != "dependent":
            continue
        gap = body_int(member, "filler_count")
        if gap is None or gap < 0:
            continue
        deltas_by_gap[gap].add(member.delta_cycles)
        observations_by_gap[gap].append(member)
    if not deltas_by_gap or 0 not in deltas_by_gap:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:missing_gap0;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)}"
            ),
            group,
            filler_cadence=cadence,
        )
    disagreeing_gaps = sorted(gap for gap, deltas in deltas_by_gap.items() if len(deltas) != 1)
    if disagreeing_gaps:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:repeated_gap_delta_disagreement;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"gaps={disagreeing_gaps}"
            ),
            tuple(member for gap in disagreeing_gaps for member in observations_by_gap[gap]),
            filler_cadence=cadence,
        )
    gap_to_delta = {gap: next(iter(deltas)) for gap, deltas in deltas_by_gap.items()}
    clean_gaps = [0]
    next_gap = 1
    while next_gap in gap_to_delta:
        previous_delta = gap_to_delta[next_gap - 1]
        current_delta = gap_to_delta[next_gap]
        diff = current_delta - previous_delta
        if diff < 0 or diff > cadence:
            break
        clean_gaps.append(next_gap)
        next_gap += 1
    if len(clean_gaps) < 2:
        return T12LatencyConstraint(
            "skipped",
            (
                "T12 skipped:no_stable_clean_prefix;"
                f"instruction={item.instruction_id};lmul={item.lmul};consumer={t12_consumer_key(item)};"
                f"clean_gaps={clean_gaps};filler_cadence={cadence}"
            ),
            group,
            filler_cadence=cadence,
            clean_gaps=tuple(clean_gaps),
        )
    residuals = {gap: gap_to_delta[gap] - gap * cadence for gap in clean_gaps}
    residual0 = residuals[0]
    minimum_residual = min(residuals.values())
    observed_cadence_gaps = tuple(
        gap
        for gap in clean_gaps[1:]
        if gap_to_delta[gap] - gap_to_delta[gap - 1] == cadence
    )
    reason_prefix = (
        f"T12 clean_prefix;instruction={item.instruction_id};lmul={item.lmul};"
        f"consumer={t12_consumer_key(item)};filler_cadence={cadence};"
        f"cadence_source={cadence_source};clean_gaps={clean_gaps};"
        f"observed_cadence_gaps={list(observed_cadence_gaps)}"
    )
    evidence = tuple(member for gap in clean_gaps for member in observations_by_gap[gap])
    if residual0 > minimum_residual:
        latency = cadence + residual0 - minimum_residual
        plateau_gaps = t12_trailing_min_residual_gaps(clean_gaps, residuals)
        if len(plateau_gaps) < 2:
            return T12LatencyConstraint(
                "skipped",
                (
                    f"{reason_prefix};insufficient_post_transition_coverage;"
                    f"candidate_latency={latency};minimum_residual={minimum_residual};"
                    f"no_stall_plateau_gaps={list(plateau_gaps)}"
                ),
                evidence,
                filler_cadence=cadence,
                clean_gaps=tuple(clean_gaps),
                observed_cadence_gaps=observed_cadence_gaps,
            )
        return T12LatencyConstraint(
            "exact",
            f"{reason_prefix};exact_latency={latency};no_stall_plateau_gaps={list(plateau_gaps)}",
            evidence,
            latency=latency,
            filler_cadence=cadence,
            clean_gaps=tuple(clean_gaps),
            observed_cadence_gaps=observed_cadence_gaps,
        )
    if not observed_cadence_gaps:
        return T12LatencyConstraint(
            "skipped",
            (
                f"{reason_prefix};no_observed_filler_cadence;"
                "cannot treat this filler stream as a conservative time-gap upper bound"
            ),
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(clean_gaps),
            observed_cadence_gaps=observed_cadence_gaps,
        )
    if residual0 == minimum_residual and residual0 > 0:
        return T12LatencyConstraint(
            "skipped",
            (
                f"{reason_prefix};linear_positive_residual={residual0};"
                "dependent delta grows exactly with filler cadence, so this sweep "
                "does not provide a conservative latency cap"
            ),
            evidence,
            filler_cadence=cadence,
            clean_gaps=tuple(clean_gaps),
            observed_cadence_gaps=observed_cadence_gaps,
        )
    return T12LatencyConstraint(
        "upper_bound",
        f"{reason_prefix};latency_upper_bound={cadence}",
        evidence,
        upper_bound=cadence,
        filler_cadence=cadence,
        clean_gaps=tuple(clean_gaps),
        observed_cadence_gaps=observed_cadence_gaps,
    )


def t12_constraints_for_items(
    items: Iterable[RawObservation],
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]] | None = None,
    fixed_candidates: dict[tuple[str, str], TimingCandidate] | None = None,
) -> tuple[T12LatencyConstraint, ...]:
    candidate_options = candidate_options or {}
    fixed_candidates = fixed_candidates or {}
    t12_items = [item for item in items if item.effective_template_id == "T12_CONSUMER_RAW_GAP"]
    seen: set[tuple[str, str, str, str, str]] = set()
    constraints: list[T12LatencyConstraint] = []
    for item in t12_items:
        key = t12_observation_group_key(item)
        if key in seen:
            continue
        seen.add(key)
        constraints.append(t12_constraint_for_group(item, t12_items, candidate_options, fixed_candidates))
    return tuple(constraints)


def check_t12_candidate_group(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
    group_items: Iterable[RawObservation],
) -> CandidateCheck:
    constraint = t12_constraint_for_group(item, group_items, candidate_options, fixed_candidates)
    if constraint.status in {"exact", "upper_bound"} and item not in constraint.evidence:
        return CandidateCheck(
            item,
            "skipped",
            f"T12 skipped:outside_clean_prefix;{constraint.reason}",
            None,
            item.delta_cycles,
        )
    if constraint.status == "exact":
        if candidate.latency == constraint.latency:
            return CandidateCheck(item, "match", constraint.reason, constraint.latency, item.delta_cycles)
        return CandidateCheck(item, "mismatch", constraint.reason, constraint.latency, item.delta_cycles)
    if constraint.status == "upper_bound":
        assert constraint.upper_bound is not None
        if candidate.latency <= constraint.upper_bound:
            return CandidateCheck(item, "match", constraint.reason, constraint.upper_bound, item.delta_cycles)
        return CandidateCheck(item, "mismatch", constraint.reason, constraint.upper_bound, item.delta_cycles)
    return CandidateCheck(item, "skipped", constraint.reason, None, item.delta_cycles)


def expected_delta_for_observation(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_lookup: dict[tuple[str, str], TimingCandidate],
) -> tuple[int | None, str]:
    shape = item.effective_template_id
    if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None or iterations <= 1:
            return None, "T10 skipped:missing_iterations"
        return None, (
            "T10 constrained collectively by delta=startup+(iterations-1)*ReleaseAtCycles;"
            f"iterations={iterations}"
        )
    if shape == "T11_SELF_RAW_CHAIN":
        if not t11_has_latency_evidence(item):
            return None, t11_latency_skip_reason(item)
        iterations = body_int(item, "iterations", "chain_length", "sample_count")
        if iterations is None or iterations <= 1:
            return None, "T11 skipped:missing_iterations"
        return None, (
            "T11 constrained collectively by delta=startup+(iterations-1)*Latency;"
            f"iterations={iterations}"
        )
    if shape == "T12_CONSUMER_RAW_GAP":
        consumer = item.body.get("consumer") or item.pair_instruction_id or "unknown"
        gap = body_int(item, "filler_count")
        return None, (
            "T12 grouped_constraint_requires_candidate_context;"
            f"template=T12_CONSUMER_RAW_GAP;instruction={item.instruction_id};"
            f"lmul={item.lmul};consumer={consumer};gap={gap};"
            "use solve_candidate_sets/check_candidate_against_options for conservative latency bounds"
        )
    if shape == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        if item.pair_instruction_id is None or iterations is None or iterations <= 0:
            return None, "T20 skipped:missing_pair_or_iterations"
        return None, (
            "T20 grouped_startup_free_slope_requires_peer_candidate_options;"
            f"slope;template=T20_PAIRWISE_PIPE_CLASSIFICATION;instruction={item.instruction_id};"
            f"lmul={item.lmul};pair={item.pair_instruction_id};counts=[{iterations}];"
            "use solve_candidate_sets/check_candidate_against_options for hard pair-slope constraints"
        )
    if shape == "T21_PAIR_WITH_SCALAR":
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        if iterations is None or iterations <= 0:
            return None, "T21 skipped:missing_iterations"
        if vcpop_m4_boundary_model_item(item, shape):
            penalty = boundary_fetch_penalty(item, shape, iterations)
            if penalty is None:
                return None, "T21 skipped:vcpop_m_m4_boundary_model_missing_start_pc"
            return iterations * expected_t21_pair_cycles(candidate) + penalty, (
                "T21 expected delta=iterations*scalar_pair_cycles+vcpop_m_m4_fetch_boundary_penalty;"
                f"iterations={iterations};boundary_penalty={penalty}"
            )
        if item.delta_cycles % iterations != 0:
            return None, (
                "T21 non_identifiable:marker delta is not divisible by pair count, "
                "so scalar-pair issue occupancy cannot be used as a hard constraint"
            )
        return iterations * expected_t21_pair_cycles(candidate), (
            f"T21 expected delta=iterations*scalar_pair_cycles;iterations={iterations}"
        )
    return None, f"{shape} recorded:not_used_by_candidate_simulator"


def check_candidate(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_lookup: dict[tuple[str, str], TimingCandidate],
) -> CandidateCheck:
    expected, reason = expected_delta_for_observation(item, candidate, candidate_lookup)
    if expected is None:
        return CandidateCheck(item, "skipped", reason, None, item.delta_cycles)
    if expected == item.delta_cycles:
        return CandidateCheck(item, "match", reason, expected, item.delta_cycles)
    return CandidateCheck(item, "mismatch", reason, expected, item.delta_cycles)


def check_candidate_against_options(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
    *,
    group_items: Iterable[RawObservation] | None = None,
) -> CandidateCheck:
    group_items = tuple(group_items) if group_items is not None else (item,)
    if item.effective_template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        return check_t20_candidate_group(item, candidate, candidate_options, fixed_candidates, group_items)
    if item.effective_template_id == "T12_CONSUMER_RAW_GAP":
        return check_t12_candidate_group(item, candidate, candidate_options, fixed_candidates, group_items)
    local_lookup = dict(fixed_candidates)
    local_lookup[(item.instruction_id, item.lmul)] = candidate
    return check_candidate(item, candidate, local_lookup)


def select_minimal_candidates(candidates: Iterable[TimingCandidate]) -> tuple[TimingCandidate, ...]:
    ordered = sorted(candidates, key=lambda item: (candidate_cost(item), candidate_sort_key(item)))
    if not ordered:
        return ()
    best_cost = candidate_cost(ordered[0])
    return tuple(candidate for candidate in ordered if candidate_cost(candidate) == best_cost)


def candidate_result_for_group(
    key: tuple[str, str],
    items: list[RawObservation],
    all_group_items: dict[tuple[str, str], list[RawObservation]],
    max_value: int,
    base_candidates: dict[tuple[str, str], tuple[TimingCandidate, ...]] | None = None,
) -> CandidateSearchResult:
    if base_candidates is None:
        base_candidates = {key: all_timing_candidates(max_value)}
    candidate_lookup: dict[tuple[str, str], TimingCandidate] = {}
    viable: list[TimingCandidate] = []
    evidence: list[RawObservation] = []
    skipped: list[str] = []
    conflicts: list[dict[str, Any]] = []

    for candidate in base_candidates.get(key, ()):
        candidate_lookup[key] = candidate
        ok = True
        for item in items:
            check = check_candidate_against_options(
                item,
                candidate,
                base_candidates,
                candidate_lookup,
                group_items=items,
            )
            if check.status == "skipped":
                skipped.append(evidence_entry(item, check.reason))
                continue
            evidence.append(item)
            if check.status == "mismatch":
                ok = False
                if len(conflicts) < 16:
                    conflicts.append(
                        {
                            "experiment_id": item.experiment_id,
                            "template_id": item.effective_template_id,
                            "trace": item.trace_path.as_posix(),
                            "candidate": candidate_to_dict(candidate),
                            "expected_delta": check.expected_delta,
                            "observed_delta": check.observed_delta,
                            "reason": check.reason,
                        }
                    )
                break
        if ok:
            viable.append(candidate)
    return CandidateSearchResult(
        candidates=select_minimal_candidates(viable),
        evidence=unique_observations(evidence),
        skipped=tuple(dict.fromkeys(skipped)),
        conflict_examples=tuple(conflicts),
        all_observations=tuple(items),
        t12_latency_constraints=t12_constraints_for_items(items, base_candidates, candidate_lookup),
    )


def solve_candidate_sets(
    grouped: dict[tuple[str, str], list[RawObservation]],
    max_value: int,
    *,
    max_passes: int = 8,
) -> dict[tuple[str, str], CandidateSearchResult]:
    base: dict[tuple[str, str], tuple[TimingCandidate, ...]] = {
        key: all_timing_candidates(
            max_value,
            latencies=direct_interval_candidates(
                items,
                "T11_SELF_RAW_CHAIN",
                ("iterations", "chain_length", "sample_count"),
                max_value,
            ),
            releases=direct_interval_candidates(
                items,
                "T10_INDEPENDENT_STREAM_THROUGHPUT",
                ("iterations", "stream_length", "sample_count"),
                max_value,
            ),
        )
        for key, items in grouped.items()
    }
    results: dict[tuple[str, str], CandidateSearchResult] = {}
    for _pass in range(max_passes):
        changed = False
        candidate_lookup = {
            key: candidates[0]
            for key, candidates in base.items()
            if len(candidates) == 1
        }
        next_base: dict[tuple[str, str], tuple[TimingCandidate, ...]] = {}
        for key, items in grouped.items():
            viable: list[TimingCandidate] = []
            evidence: list[RawObservation] = [
                item
                for item in items
                if item.effective_template_id
                in {"T10_INDEPENDENT_STREAM_THROUGHPUT", "T11_SELF_RAW_CHAIN"}
                and (item.effective_template_id != "T11_SELF_RAW_CHAIN" or t11_has_latency_evidence(item))
            ]
            skipped: list[str] = []
            conflicts: list[dict[str, Any]] = []
            if not base[key]:
                constrained_items = [
                    item
                    for item in items
                    if item.effective_template_id
                    in {
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        "T11_SELF_RAW_CHAIN",
                        "T12_CONSUMER_RAW_GAP",
                        "T20_PAIRWISE_PIPE_CLASSIFICATION",
                        "T21_PAIR_WITH_SCALAR",
                    }
                ]
                results[key] = CandidateSearchResult(
                    candidates=(),
                    evidence=tuple(constrained_items),
                    skipped=(),
                    conflict_examples=(
                        {
                            "experiment_id": constrained_items[0].experiment_id,
                            "template_id": constrained_items[0].effective_template_id,
                            "trace": constrained_items[0].trace_path.as_posix(),
                            "reason": "Direct interval constraints produced an empty candidate domain.",
                        },
                    )
                    if constrained_items
                    else (),
                    all_observations=tuple(items),
                    t12_latency_constraints=t12_constraints_for_items(items, base, candidate_lookup),
                )
                next_base[key] = ()
                continue
            for candidate in base[key]:
                ok = True
                for item in items:
                    check = check_candidate_against_options(
                        item,
                        candidate,
                        base,
                        candidate_lookup,
                        group_items=items,
                    )
                    if check.status == "skipped":
                        skipped.append(evidence_entry(item, check.reason))
                        continue
                    evidence.append(item)
                    if check.status == "mismatch":
                        ok = False
                        if len(conflicts) < 16:
                            conflicts.append(
                                {
                                    "experiment_id": item.experiment_id,
                                    "template_id": item.effective_template_id,
                                    "trace": item.trace_path.as_posix(),
                                    "candidate": candidate_to_dict(candidate),
                                    "expected_delta": check.expected_delta,
                                    "observed_delta": check.observed_delta,
                                    "reason": check.reason,
                                }
                            )
                        break
                if ok:
                    viable.append(candidate)
            minimal = select_minimal_candidates(viable)
            next_base[key] = minimal
            results[key] = CandidateSearchResult(
                candidates=minimal,
                evidence=unique_observations(evidence),
                skipped=tuple(dict.fromkeys(skipped)),
                conflict_examples=tuple(conflicts),
                all_observations=tuple(items),
                t12_latency_constraints=t12_constraints_for_items(items, base, candidate_lookup),
            )
            if set(minimal) != set(base[key]):
                changed = True
        base = next_base
        if not changed:
            break
    return results


def direct_interval_domain_conflict(result: CandidateSearchResult) -> bool:
    return any(
        str(item.get("reason", "")).startswith("Direct interval constraints produced an empty candidate domain")
        for item in result.conflict_examples
    )


def non_affine_stream_follow_up(observations: Iterable[RawObservation]) -> str:
    stream_points: list[str] = []
    for item in observations:
        if item.effective_template_id != "T10_INDEPENDENT_STREAM_THROUGHPUT":
            continue
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None:
            continue
        stream_points.append(f"n{iterations}=delta{item.delta_cycles}")
    suffix = "; observed_points=" + ",".join(stream_points[:16]) if stream_points else ""
    return (
        "Add a focused T10 stream-length and alignment sweep before claiming LLVM-facing "
        "issue fields; vary N around the first non-affine point, marker PC alignment, "
        "scalar destination policy, and source register policy."
        + suffix
    )


def non_affine_stream_observations(observations: Iterable[RawObservation]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for item in observations:
        if item.effective_template_id != "T10_INDEPENDENT_STREAM_THROUGHPUT":
            continue
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None:
            continue
        points.append(
            {
                "experiment_id": item.experiment_id,
                "iterations": iterations,
                "delta_cycles": item.delta_cycles,
            }
        )
    return sorted(points, key=lambda item: (item["iterations"], item["experiment_id"]))


def candidate_field_result(
    field: str,
    result: CandidateSearchResult,
    *,
    max_value: int,
    non_identifiable: bool = False,
) -> dict[str, Any]:
    evidence = [
        evidence_entry(item, f"candidate_simulator:{field}")
        for item in result.evidence
    ]
    evidence.extend(result.skipped[:16])
    values = sorted(
        {candidate_field_value(candidate, field) for candidate in result.candidates},
        key=lambda item: str(item),
    )
    if field in {"Latency", "ReleaseAtCycles"}:
        candidate_domain: Any = f"0..{max_value}"
    elif field == "ProcResource":
        candidate_domain = [proc_resource_for_label(label) for label in PROC_RESOURCE_DOMAIN]
    elif field == "NumMicroOps":
        candidate_domain = [1, 2, 3, 4]
    else:
        candidate_domain = [False, True]

    record: dict[str, Any] = {
        "field": field,
        "candidate_domain": candidate_domain,
        "evidence": evidence,
        "constraint_count": len(result.evidence),
        "candidate_count": len(values),
        "candidates": values,
    }
    if field in {"Latency", "ReleaseAtCycles"}:
        record["range"] = f"0..{max_value}"

    if field == "Latency":
        true_t11 = any(t11_has_latency_evidence(item) for item in result.all_observations)
        has_t12 = any(item.effective_template_id == "T12_CONSUMER_RAW_GAP" for item in result.all_observations)
        has_placeholder_t11 = any(
            item.effective_template_id == "T11_SELF_RAW_CHAIN" and not t11_has_latency_evidence(item)
            for item in result.all_observations
        )
        t12_constraints = result.t12_latency_constraints or t12_constraints_for_items(result.all_observations)
        if has_t12 and t12_constraints:
            record["t12_latency_constraints"] = [
                t12_constraint_to_dict(constraint) for constraint in t12_constraints
            ]
        exact_t12_latencies = {
            constraint.latency
            for constraint in t12_constraints
            if constraint.status == "exact" and constraint.latency is not None
        }
        t12_upper_bounds = [
            constraint.upper_bound
            for constraint in t12_constraints
            if constraint.status == "upper_bound" and constraint.upper_bound is not None
        ]
        if not true_t11 and has_t12 and not exact_t12_latencies and t12_upper_bounds:
            upper_bound = min(t12_upper_bounds)
            record.update(
                {
                    "status": "non_identifiable",
                    "value": None,
                    "reason": (
                        "T12 consumer-gap observations provide only a conservative upper bound "
                        f"for Latency (Latency <= {upper_bound}); the shared simulator filters "
                        "candidate tuples with that bound but does not render a fake exact value."
                    ),
                    "upper_bound": upper_bound,
                    "candidate_domain": f"0..{upper_bound}",
                    "candidate_count": upper_bound + 1,
                    "candidates": list(range(upper_bound + 1)),
                    "t12_latency_constraints": [
                        t12_constraint_to_dict(constraint) for constraint in t12_constraints
                    ],
                    "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
                    "candidate_tuple_count": len(result.candidates),
                }
            )
            return record
        if not true_t11 and (has_t12 or has_placeholder_t11) and not exact_t12_latencies:
            first = result.all_observations[0] if result.all_observations else None
            instruction_id = first.instruction_id if first is not None else "unknown"
            lmul = first.lmul if first is not None else "unknown"
            record.update(
                {
                    "status": "non_identifiable",
                    "value": None,
                    "reason": (
                        "T11 observations for this row are non-chainable placeholders or absent; "
                        "T12 consumer-gap observations do not provide a stable exact latency or "
                        "upper-bound constraint for this row, so Latency is not identifiable."
                    ),
                    "follow_up": t12_latency_follow_up(result.all_observations, instruction_id, lmul),
                    "t12_latency_constraints": [
                        t12_constraint_to_dict(constraint) for constraint in t12_constraints
                    ],
                    "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
                }
            )
            return record

    if non_identifiable:
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "Current T12 consumer-gap templates are recorded by the shared simulator, "
                    "but they do not identify bypass/read-advance latency without an explicit "
                    "bypass-gap model."
                ),
                "follow_up": "Implement a T12 bypass/read-advance readiness model before claiming Latency.",
            }
        )
        return record

    if not result.candidates and direct_interval_domain_conflict(result):
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "The real-platform stream observations are not affine under the "
                    "LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records "
                    "the evidence but does not claim this field without a follow-up model "
                    "for the extra platform effect."
                ),
                "follow_up": non_affine_stream_follow_up(result.all_observations),
                "non_affine_stream_observations": non_affine_stream_observations(result.all_observations),
                "conflict_examples": list(result.conflict_examples),
                "t20_startup_slope_groups": t20_startup_slope_groups(result.all_observations),
            }
        )
        return record

    if field == "ProcResource" and len(values) > 1 and result.candidates:
        first = result.all_observations[0] if result.all_observations else None
        instruction_id = first.instruction_id if first is not None else "unknown"
        lmul = first.lmul if first is not None else "unknown"
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "T20 pair timing is checked as startup-free slope groups, but the available "
                    "pair groups are underdetermined or contradictory for an exact ProcResource "
                    "claim without overclaiming a pipe."
                ),
                "follow_up": t20_proc_resource_follow_up(result.all_observations, instruction_id, lmul),
                "t20_startup_slope_groups": t20_startup_slope_groups(result.all_observations),
                "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
            }
        )
        return record

    if not result.evidence:
        record.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "reason": "No usable marker observation constrained this field in the shared candidate simulator.",
            }
        )
    elif not result.candidates:
        record.update(
            {
                "status": "conflict",
                "value": None,
                "reason": "No candidate tuple explains all real-platform marker observations in the shared simulator.",
                "conflict_examples": list(result.conflict_examples),
            }
        )
    elif len(values) == 1:
        record.update({"status": "exact_fit", "value": values[0]})
    else:
        record.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "reason": (
                    "Multiple minimal candidate tuples explain the observations; add a focused "
                    "experiment that separates issue occupancy, pipe identity, and RAW readiness."
                ),
                "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
            }
        )
    return record


def pairwise_checks(
    items: list[RawObservation],
    release_results: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in items:
        if item.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION":
            continue
        iterations = body_int(item, "iterations", "pair_count")
        other = item.pair_instruction_id
        detail: dict[str, Any] = {
            "experiment_id": item.experiment_id,
            "trace": item.trace_path.as_posix(),
            "other_instruction_id": other,
            "delta_cycles": item.delta_cycles,
            "iterations": iterations,
        }
        if other is None or iterations is None or iterations <= 0:
            detail["status"] = "skipped"
            detail["reason"] = "missing pair instruction or iteration count"
            checks.append(detail)
            continue
        subject_release = release_value(release_results, item.instruction_id, item.lmul)
        other_release = release_value(release_results, other, item.lmul)
        detail["cycles_per_pair"] = item.delta_cycles / iterations
        detail["subject_release"] = subject_release
        detail["other_release"] = other_release
        if subject_release is None or other_release is None:
            detail["status"] = "insufficient_evidence"
            detail["reason"] = "release candidates are required before T20 pair timing can be interpreted"
            checks.append(detail)
            continue
        pair_cycles = float(detail["cycles_per_pair"])
        if pair_cycles <= max(subject_release, other_release) and pair_cycles < subject_release + other_release:
            relation = "overlap"
        elif pair_cycles >= subject_release + other_release:
            relation = "serial"
        else:
            relation = "ambiguous"
        detail["status"] = "checked"
        detail["relation"] = relation
        detail["expected_delta_options"] = {
            "overlap": max(subject_release, other_release) * iterations,
            "serial": (subject_release + other_release) * iterations,
        }
        checks.append(detail)
    return checks


def enumerate_proc_resource(
    items: list[RawObservation],
    release_results: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checks = pairwise_checks(items, release_results)
    labels = sorted({label for item in items for label in item.raw_pipe_labels})
    evidence = [
        evidence_entry(item, f"observed_pipe_label={label}")
        for item in items
        for label in item.raw_pipe_labels
    ]
    evidence.extend(
        f"{check['experiment_id']}:T20 relation={check.get('relation', check['status'])}"
        for check in checks
    )

    result: dict[str, Any] = {
        "field": "ProcResource",
        "candidate_domain": [proc_resource_for_label(label) for label in labels] if labels else ["unknown"],
        "evidence": evidence,
        "constraint_count": len(labels),
        "t20_relation_counts": dict(Counter(str(check.get("relation", check["status"])) for check in checks)),
    }
    if not labels:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": ["unknown"],
                "candidate_count": 1,
                "reason": (
                    "No non-synthetic trace entry carries a pipe/proc_resource label. "
                    "T20 timing checks are recorded, but they do not name a ProcResource by themselves."
                ),
            }
        )
    elif len(labels) == 1:
        value = proc_resource_for_label(labels[0])
        result.update(
            {
                "status": "exact_fit",
                "value": value,
                "candidates": [value],
                "candidate_count": 1,
            }
        )
    else:
        result.update(
            {
                "status": "conflict",
                "value": None,
                "candidates": [proc_resource_for_label(label) for label in labels],
                "candidate_count": len(labels),
                "reason": "Raw trace entries contain multiple pipe/proc_resource labels for this instruction/LMUL.",
            }
        )
    return result, checks


def t21_expected_pair_cycles(release: int, num_micro_ops: int, single_issue: bool) -> int:
    vector_issue_cycles = max(release, num_micro_ops)
    if single_issue:
        return vector_issue_cycles + 1
    return max(vector_issue_cycles, 1)


def enumerate_issue_fields(
    items: list[RawObservation],
    release_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    candidate_pairs = {(num_micro_ops, single_issue) for num_micro_ops in range(1, 5) for single_issue in (False, True)}
    release = int_or_none(release_result.get("value")) if release_result.get("status") == "exact_fit" else None
    checks: list[dict[str, Any]] = []
    used = 0

    for item in items:
        if item.effective_template_id != "T21_PAIR_WITH_SCALAR":
            continue
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        check: dict[str, Any] = {
            "experiment_id": item.experiment_id,
            "trace": item.trace_path.as_posix(),
            "delta_cycles": item.delta_cycles,
            "iterations": iterations,
        }
        if release is None:
            check["status"] = "insufficient_evidence"
            check["reason"] = "ReleaseAtCycles must be uniquely identified before T21 scalar-pair timing is interpreted."
            checks.append(check)
            continue
        if iterations is None or iterations <= 0:
            check["status"] = "skipped"
            check["reason"] = "missing iteration count"
            checks.append(check)
            continue
        if item.delta_cycles % iterations != 0:
            check["status"] = "conflict"
            check["reason"] = "delta is not divisible by pair iteration count"
            candidate_pairs = set()
            checks.append(check)
            used += 1
            continue
        observed = item.delta_cycles // iterations
        valid = {
            pair
            for pair in candidate_pairs
            if t21_expected_pair_cycles(release, pair[0], pair[1]) == observed
        }
        candidate_pairs = valid
        check["status"] = "checked"
        check["cycles_per_pair"] = observed
        check["release"] = release
        check["candidate_pairs_after_check"] = [
            {"NumMicroOps": num_micro_ops, "SingleIssue": single_issue}
            for num_micro_ops, single_issue in sorted(candidate_pairs)
        ]
        checks.append(check)
        used += 1

    evidence = [
        f"{check['experiment_id']}:T21 status={check['status']}:cycles_per_pair={check.get('cycles_per_pair')}"
        for check in checks
    ]
    num_values = sorted({num_micro_ops for num_micro_ops, _single_issue in candidate_pairs})
    single_values = sorted({single_issue for _num_micro_ops, single_issue in candidate_pairs})

    num_result = discrete_field_result(
        "NumMicroOps",
        num_values,
        evidence,
        used,
        full_domain=[1, 2, 3, 4],
        empty_reason="No T21 scalar-pair marker constraint is available for NumMicroOps.",
    )
    single_result = discrete_field_result(
        "SingleIssue",
        single_values,
        evidence,
        used,
        full_domain=[False, True],
        empty_reason="No T21 scalar-pair marker constraint is available for SingleIssue.",
    )
    if release is None:
        reason = "ReleaseAtCycles is not uniquely identified, so T21 scalar-pair checks cannot distinguish issue fields."
        num_result.update({"status": "insufficient_evidence", "value": None, "reason": reason})
        single_result.update({"status": "insufficient_evidence", "value": None, "reason": reason})
    return num_result, single_result, checks


def discrete_field_result(
    field: str,
    candidates: list[Any],
    evidence: list[str],
    used_constraints: int,
    *,
    full_domain: list[Any],
    empty_reason: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "field": field,
        "candidate_domain": full_domain,
        "evidence": evidence,
        "constraint_count": used_constraints,
    }
    if used_constraints == 0:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": full_domain,
                "candidate_count": len(full_domain),
                "reason": empty_reason,
            }
        )
    elif not candidates:
        result.update(
            {
                "status": "conflict",
                "value": None,
                "candidates": [],
                "candidate_count": 0,
                "reason": "No candidate in the bounded domain satisfies all T21 checks.",
            }
        )
    elif len(candidates) == 1:
        result.update(
            {
                "status": "exact_fit",
                "value": candidates[0],
                "candidates": candidates,
                "candidate_count": 1,
            }
        )
    else:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": candidates,
                "candidate_count": len(candidates),
                "reason": "T21 checks leave multiple candidate values in the bounded domain.",
            }
        )
    return result


def fit_formula(points: dict[str, int], max_value: int) -> FormulaCandidate | None:
    numeric_points = [(LMUL_VALUE[key], value) for key, value in points.items() if key in LMUL_VALUE]
    if len(numeric_points) < 2:
        return None
    best: FormulaCandidate | None = None
    for base in range(max_value + 1):
        for k in range(max_value + 1):
            residual = sum(abs((base + k * lmul) - observed) for lmul, observed in numeric_points)
            candidate = FormulaCandidate(base, k, residual)
            if best is None or (candidate.residual, candidate.base, candidate.k) < (
                best.residual,
                best.base,
                best.k,
            ):
                best = candidate
    return best


def formula_fit_for(
    field_results: dict[str, dict[str, Any]],
    max_value: int,
    *,
    required_lmuls: tuple[str, ...] = LMUL_ORDER,
) -> dict[str, Any]:
    points = {
        lmul: int(result["value"])
        for lmul, result in field_results.items()
        if result.get("status") == "exact_fit" and int_or_none(result.get("value")) is not None
    }
    candidate = fit_formula(points, max_value)
    blocked_lmuls = []
    for lmul in required_lmuls:
        result = field_results.get(lmul)
        if result is None:
            blocked_lmuls.append(
                {
                    "lmul": lmul,
                    "status": "missing",
                    "source_status": "missing",
                    "value": None,
                    "reason": "Required LMUL row is absent from the formula-fit input.",
                }
            )
            continue
        if result.get("status") != "exact_fit" or int_or_none(result.get("value")) is None:
            blocked_lmuls.append(
                {
                    "lmul": lmul,
                    "status": result_status_for_field(result),
                    "source_status": result.get("status", "missing"),
                    "value": result.get("value"),
                    "reason": result.get("reason")
                    or "Required LMUL row is not an exact fit, so the cross-LMUL formula is not complete.",
                }
            )
    if blocked_lmuls:
        result = {
            "status": "partial_fit_blocked",
            "form": "base_plus_lmul_times_k",
            "base": None,
            "k": None,
            "residual": None,
            "points": points,
            "required_lmuls": list(required_lmuls),
            "blocked_lmuls": blocked_lmuls,
            "reason": "Required LMUL rows are not all exact, so this formula is diagnostic-only.",
        }
        if candidate is not None:
            residual = int(candidate.residual) if float(candidate.residual).is_integer() else candidate.residual
            result["provisional_fit"] = {
                "status": "exact_fit" if candidate.residual == 0 else "approximate_fit",
                "form": "base_plus_lmul_times_k",
                "base": candidate.base,
                "k": candidate.k,
                "residual": residual,
                "points": points,
            }
        return result
    if candidate is None:
        return {
            "status": "insufficient_evidence",
            "form": "base_plus_lmul_times_k",
            "base": None,
            "k": None,
            "residual": None,
            "points": points,
            "required_lmuls": list(required_lmuls),
            "blocked_lmuls": [],
            "reason": "At least two exact LMUL points are required for a formula fit.",
        }
    residual = int(candidate.residual) if float(candidate.residual).is_integer() else candidate.residual
    return {
        "status": "exact_fit" if candidate.residual == 0 else "approximate_fit",
        "form": "base_plus_lmul_times_k",
        "base": candidate.base,
        "k": candidate.k,
        "residual": residual,
        "points": points,
        "required_lmuls": list(required_lmuls),
        "blocked_lmuls": [],
    }


def observation_summary(items: list[RawObservation]) -> dict[str, Any]:
    by_template = Counter(item.effective_template_id for item in items)
    synthetic_reference_count = sum(1 for item in items if item.synthetic_reference)
    return {
        "count": len(items),
        "by_effective_template": dict(sorted(by_template.items())),
        "synthetic_reference_count": synthetic_reference_count,
    }


def proc_resource_domains_from_candidate_results(
    candidate_results: dict[tuple[str, str], CandidateSearchResult],
) -> dict[tuple[str, str], tuple[str, ...]]:
    return {
        key: proc_resource_domain_labels(candidate.proc_resource for candidate in result.candidates)
        for key, result in candidate_results.items()
    }


def merge_global_proc_resource_field(base: dict[str, Any], global_row: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    evidence = list(base.get("evidence", []))
    evidence.extend(entry for entry in global_row.get("evidence", []) if entry not in evidence)
    merged.update(
        {
            "status": global_row["status"],
            "value": global_row["value"],
            "candidates": global_row["candidates"],
            "candidate_count": global_row["candidate_count"],
            "constraint_count": global_row["constraint_count"],
            "evidence": evidence[:64],
            "reason": global_row["reason"],
            "global_solution_count": global_row["global_solution_count"],
            "global_candidates": global_row["global_candidates"],
            "surviving_candidates": global_row["surviving_candidates"],
        }
    )
    if global_row.get("conflict_constraints"):
        merged["conflict_constraints"] = global_row["conflict_constraints"]
    for key in ("symmetry_breaking_assumption", "pre_canonical_surviving_candidates"):
        if key in global_row:
            merged[key] = global_row[key]
    return merged


def group_observations(observations: list[RawObservation]) -> dict[tuple[str, str], list[RawObservation]]:
    grouped: dict[tuple[str, str], list[RawObservation]] = defaultdict(list)
    original_keys = {observation_key(observation) for observation in observations}
    for observation in observations:
        grouped[observation_key(observation)].append(observation)
    for observation in observations:
        mirrored = mirrored_t20_peer_observation(observation)
        if mirrored is None:
            continue
        key = observation_key(mirrored)
        if key not in original_keys:
            continue
        grouped[key].append(mirrored)
    return dict(grouped)


def all_trace_paths(paths: list[str]) -> list[Path]:
    trace_paths: list[Path] = []
    for raw in paths:
        trace_paths.extend(trace_files_from_path(raw))
    return sorted(dict.fromkeys(trace_paths), key=lambda item: item.as_posix())


def filter_description(mode: str | None, backend: str | None, include_dry_run: bool) -> dict[str, Any]:
    return {
        "mode": mode,
        "backend": backend,
        "include_dry_run": include_dry_run,
        "dry_run_trace_excluded": not include_dry_run and (mode == "real_platform_profile" or backend == "gem5_minor"),
    }


def build_report(
    profile_paths: list[Path],
    trace_paths: list[Path],
    observations: list[RawObservation],
    configs: list[tuple[Path, dict[str, Any]]],
    warnings: list[str],
    max_value: int,
    *,
    input_counts: dict[str, int] | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    grouped = group_observations(observations)
    candidate_results = solve_candidate_sets(grouped, max_value)
    field_results_by_key: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for key, candidate_result in candidate_results.items():
        field_results_by_key[key] = {
            "Latency": candidate_field_result("Latency", candidate_result, max_value=max_value),
            "ReleaseAtCycles": candidate_field_result("ReleaseAtCycles", candidate_result, max_value=max_value),
            "ProcResource": candidate_field_result("ProcResource", candidate_result, max_value=max_value),
            "NumMicroOps": candidate_field_result("NumMicroOps", candidate_result, max_value=max_value),
            "SingleIssue": candidate_field_result("SingleIssue", candidate_result, max_value=max_value),
        }
    release_values = {
        key: int(result["ReleaseAtCycles"]["value"])
        for key, result in field_results_by_key.items()
        if result["ReleaseAtCycles"].get("status") == "exact_fit"
        and int_or_none(result["ReleaseAtCycles"].get("value")) is not None
    }
    global_proc_resources = solve_global_proc_resources(
        observations,
        release_values,
        proc_resource_domains_from_candidate_results(candidate_results),
    )
    for key, global_row in global_proc_resources["rows"].items():
        if key in field_results_by_key:
            field_results_by_key[key]["ProcResource"] = merge_global_proc_resource_field(
                field_results_by_key[key]["ProcResource"],
                global_row,
            )

    instructions: dict[str, Any] = {}
    instruction_ids = sorted({instruction_id for instruction_id, _lmul in grouped})
    for instruction_id in instruction_ids:
        lmuls = sorted({lmul for instr, lmul in grouped if instr == instruction_id}, key=lmul_sort_key)
        lmul_results: dict[str, Any] = {}
        latency_by_lmul: dict[str, dict[str, Any]] = {}
        release_by_lmul: dict[str, dict[str, Any]] = {}
        for lmul in lmuls:
            key = (instruction_id, lmul)
            items = grouped[key]
            candidate_result = candidate_results[key]
            latency = field_results_by_key[key]["Latency"]
            release = field_results_by_key[key]["ReleaseAtCycles"]
            proc_resource = field_results_by_key[key]["ProcResource"]
            num_micro_ops = field_results_by_key[key]["NumMicroOps"]
            single_issue = field_results_by_key[key]["SingleIssue"]
            fields = {
                "Latency": latency,
                "ReleaseAtCycles": release,
                "ProcResource": proc_resource,
                "NumMicroOps": num_micro_ops,
                "SingleIssue": single_issue,
            }
            latency_by_lmul[lmul] = latency
            release_by_lmul[lmul] = release
            lmul_results[lmul] = {
                "observation_summary": observation_summary(items),
                "fields": fields,
                "candidate_search": {
                    "candidate_count": len(candidate_result.candidates),
                    "minimal_candidate_tuples": [
                        candidate_to_dict(candidate)
                        for candidate in sorted(candidate_result.candidates, key=candidate_sort_key)[:32]
                    ],
                    "conflict_examples": list(candidate_result.conflict_examples),
                    "skipped": list(candidate_result.skipped[:32]),
                    "t20_startup_slope_groups": t20_startup_slope_groups(candidate_result.all_observations),
                },
                "template_checks": {
                    "shared_candidate_simulator": [
                        {
                            "experiment_id": item.experiment_id,
                            "template_id": item.effective_template_id,
                            "delta_cycles": item.delta_cycles,
                            "trace": item.trace_path.as_posix(),
                        }
                        for item in candidate_result.evidence
                    ],
                },
            }
        instructions[instruction_id] = {
            "lmuls": lmul_results,
            "formula_fits": {
                "Latency": formula_fit_for(latency_by_lmul, max_value),
                "ReleaseAtCycles": formula_fit_for(release_by_lmul, max_value),
            },
        }

    global_assumptions = [
        "Only marker deltas from trace entries are used as calibration evidence.",
        "Known marker pairs are t0/t1, before/after, start/end, and begin/end; marker_baseline_cycles is subtracted.",
        "T10/T30 throughput check: marker deltas across repeated stream lengths fit startup + (N - 1) * ReleaseAtCycles.",
        "T11/T30 RAW-chain check: marker deltas constrain Latency only when body.latency_evidence, body.true_raw_chain, or body.chainable is true.",
        "T12/T30 consumer-gap checks use a conservative clean-prefix filler-cadence model to infer exact latency or upper-bound constraints.",
        "T20 pair checks are interpreted as startup-free slope groups; a single usable pair count per pair/LMUL cannot identify ProcResource.",
        "Global ProcResource solving uses only clean startup-free T20 pair slopes plus exact ReleaseAtCycles values; constraints with missing or empty peer domains are skipped.",
        "T21 scalar-pair checks are evaluated inside the same candidate tuple and assume a one-cycle scalar issue companion.",
        "trace.synthetic and generated profile.yaml timing claims are reference-only and are not used as evidence.",
    ]
    if global_proc_resources.get("symmetry_breaking_assumptions"):
        global_assumptions.append(
            "ProcResource components with exactly two pure global pipe0/pipe1 mirror assignments "
            "are reported under a deterministic pipe-label symmetry-breaking assumption."
        )

    return {
        "schema_version": 2,
        "status": "raw_observation_parameter_search",
        "candidate_domains": {
            "Latency": f"0..{max_value}",
            "ReleaseAtCycles": f"0..{max_value}",
            "ProcResource": "observed non-synthetic pipe/proc_resource labels, otherwise unknown",
            "NumMicroOps": [1, 2, 3, 4],
            "SingleIssue": [False, True],
        },
        "global_assumptions": global_assumptions,
        "source_profiles_reference_only": [path.as_posix() for path in profile_paths],
        "source_trace_files": [path.as_posix() for path in trace_paths],
        "config_files_reference_only": [path.as_posix() for path, _data in configs],
        "filters": filters or filter_description(None, None, False),
        "global_proc_resource_solver": {
            "usable_constraints": global_proc_resources["usable_constraints"],
            "skipped_constraints": global_proc_resources["skipped_constraints"],
            "conflict_constraints": global_proc_resources["conflict_constraints"],
            "symmetry_breaking_assumptions": global_proc_resources["symmetry_breaking_assumptions"],
        },
        "input_counts": input_counts or {
            "trace_files_before_filter": len(trace_paths),
            "trace_files_after_filter": len(trace_paths),
            "usable_marker_observations": len(observations),
        },
        "observation_summary": observation_summary(observations),
        "warnings": warnings,
        "instructions": instructions,
    }


def result_status_for_field(item: dict[str, Any]) -> str:
    status = str(item.get("status", "missing"))
    if status == "exact_fit":
        return "inferred"
    if status in {"conflict", "insufficient_evidence"}:
        return status
    if status in {"missing", "unknown", "invalid", "error", "not_set"}:
        return status
    return status


def first_evidence(item: dict[str, Any], limit: int = 8) -> list[str]:
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [str(entry) for entry in evidence[:limit]]


def field_status_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    instructions = report.get("instructions", {})
    for instruction_id in sorted(instructions):
        lmuls = instructions[instruction_id].get("lmuls", {})
        for lmul in sorted(lmuls, key=lmul_sort_key):
            fields = lmuls[lmul].get("fields", {})
            for field in FIELD_ORDER:
                item = fields.get(field, {})
                status = result_status_for_field(item)
                reason = item.get("reason")
                if not reason and status == "insufficient_evidence":
                    reason = "Current real-platform templates do not uniquely identify this LLVM-facing field."
                elif not reason and status == "conflict":
                    reason = "No bounded candidate explains all real-platform marker observations for this field."
                elif not reason and status == "inferred":
                    reason = "Unique candidate inferred from real-platform marker observations."
                follow_up = item.get("follow_up")
                if not follow_up and status in {"conflict", "insufficient_evidence", "non_identifiable", "missing", "unknown"}:
                    if field == "Latency":
                        follow_up = t12_latency_follow_up((), instruction_id, lmul)
                    elif field == "ProcResource":
                        follow_up = t20_proc_resource_follow_up((), instruction_id, lmul)
                    else:
                        follow_up = (
                            f"Add focused template coverage for instruction={instruction_id} "
                            f"lmul={lmul} field={field}; keep register policy explicit in metadata."
                        )
                row = {
                    "instruction_id": instruction_id,
                    "lmul": lmul,
                    "field": field,
                    "status": status,
                    "source_status": item.get("status", "missing"),
                    "candidate": item.get("value"),
                    "candidates": item.get("candidates", []),
                    "candidate_count": item.get("candidate_count"),
                    "constraint_count": item.get("constraint_count", 0),
                    "reason": reason,
                    "follow_up": follow_up,
                    "evidence": first_evidence(item),
                }
                if "symmetry_breaking_assumption" in item:
                    row["symmetry_breaking_assumption"] = item["symmetry_breaking_assumption"]
                if "pre_canonical_surviving_candidates" in item:
                    row["pre_canonical_surviving_candidates"] = item["pre_canonical_surviving_candidates"]
                rows.append(row)
    return rows


def build_field_status(report: dict[str, Any]) -> dict[str, Any]:
    rows = field_status_rows(report)
    status_counts = Counter(str(row.get("status", "missing")) for row in rows)
    blocking_counts = {
        status: count for status, count in sorted(status_counts.items()) if status in BLOCKING_FIELD_STATUSES
    }
    # The full trace list is already recorded in the search report; keep this
    # sidecar compact and hash the report inputs by path for approval binding.
    artifact_hash_inputs = [
        {"path": path, "sha256": file_sha256(Path(path))}
        for path in report.get("source_trace_files", [])
        if Path(path).exists()
    ]
    return {
        "schema_version": 1,
        "mode": report.get("filters", {}).get("mode"),
        "backend": report.get("filters", {}).get("backend"),
        "filters": report.get("filters", {}),
        "input_counts": report.get("input_counts", {}),
        "required_fields": list(FIELD_ORDER),
        "artifact_hash_inputs": artifact_hash_inputs,
        "summary": {
            "total_rows": len(rows),
            "required_fields": list(FIELD_ORDER),
            "status_counts": dict(sorted(status_counts.items())),
            "blocking_status_counts": blocking_counts,
            "blocking_total": sum(blocking_counts.values()),
        },
        "rows": rows,
    }


def profile_for_instruction(instruction_id: str, rows: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    by_lmul: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in rows:
        if row["instruction_id"] != instruction_id:
            continue
        by_lmul[row["lmul"]][row["field"]] = {
            "status": row["status"],
            "value": row["candidate"],
            "candidates": row["candidates"],
            "reason": row["reason"],
            "evidence": row["evidence"],
        }
        if "symmetry_breaking_assumption" in row:
            by_lmul[row["lmul"]][row["field"]]["symmetry_breaking_assumption"] = row[
                "symmetry_breaking_assumption"
            ]
        if "pre_canonical_surviving_candidates" in row:
            by_lmul[row["lmul"]][row["field"]]["pre_canonical_surviving_candidates"] = row[
                "pre_canonical_surviving_candidates"
            ]
    return {
        "schema_version": 1,
        "mode": "real_platform_profile",
        "backend": report.get("filters", {}).get("backend"),
        "instruction_id": instruction_id,
        "llvm_facing_fields": dict(sorted(by_lmul.items(), key=lambda item: lmul_sort_key(item[0]))),
        "hardware_interpretation": {
            "issue_width": 2,
            "issue_order": "in_order",
            "rob": "none",
            "vector_pipes": 2,
            "timestamp_marker_cost": 0,
        },
        "confidence": {
            "source": "mode_isolated_real_platform_marker_observations",
            "blocking_statuses": list(BLOCKING_FIELD_STATUSES),
        },
    }


def common_output_root(profile_args: list[str], output: str | None) -> Path:
    candidates = [Path(raw) for raw in profile_args]
    if output:
        candidates.append(Path(output))
    for path in candidates:
        current = path if path.is_dir() else path.parent
        for ancestor in (current, *current.parents):
            if ancestor.name == "common":
                return ancestor
            if (ancestor / "common").exists():
                return ancestor / "common"
    return Path("results/common")


def should_write_real_platform_artifacts(output: str | None, common_root: Path) -> bool:
    if output is None:
        return True
    output_path = Path(output).resolve()
    common_path = common_root.resolve()
    try:
        output_path.relative_to(common_path)
    except ValueError:
        return False
    return True


def observation_is_real_platform(observation: RawObservation) -> bool:
    mode = observation.mode.lower()
    backend = observation.backend.lower()
    return (
        not observation.dry_run_trace
        and ("real_platform" in mode or mode == "real" or mode.startswith("real_") or "gem5" in backend)
        and "synthetic" not in mode
        and "synthetic" not in backend
    )


def selected_observations_are_real_platform(observations: list[RawObservation]) -> bool:
    return bool(observations) and all(observation_is_real_platform(observation) for observation in observations)


def default_reference_config_args(config_args: list[str]) -> list[str]:
    if config_args:
        return config_args
    default_path = Path("config/rvv_timing_model.yaml")
    if default_path.exists():
        return [default_path.as_posix()]
    repo_default_path = Path(__file__).resolve().parents[1] / default_path
    if repo_default_path.exists():
        return [repo_default_path.as_posix()]
    return []


def write_real_platform_artifacts(report: dict[str, Any], common_root: Path) -> None:
    common_root.mkdir(parents=True, exist_ok=True)
    field_status = build_field_status(report)
    field_status_path = common_root / "real_platform_field_status.json"
    field_status_path.write_text(json.dumps(field_status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = field_status["rows"]
    result_root = common_root.parent if common_root.name == "common" else common_root
    for instruction_id in sorted({row["instruction_id"] for row in rows}):
        profile = profile_for_instruction(instruction_id, rows, report)
        instr_dir = result_root / instruction_id
        instr_dir.mkdir(parents=True, exist_ok=True)
        (instr_dir / "profile.real_platform.yaml").write_text(dump_yaml(profile) + "\n", encoding="utf-8")


def value_text(item: dict[str, Any]) -> str:
    if item.get("status") == "exact_fit":
        return str(item.get("value"))
    candidates = item.get("candidates")
    if isinstance(candidates, list) and 0 < len(candidates) <= 6:
        return ", ".join(str(candidate) for candidate in candidates)
    if isinstance(candidates, list) and len(candidates) > 6:
        return f"{len(candidates)} candidates"
    return "n/a"


def render_markdown(report: dict[str, Any]) -> str:
    input_counts = report.get("input_counts", {})
    filters = report.get("filters", {})
    lines = [
        "# Timing Parameter Search",
        "",
        f"Status: {report['status']}",
        "",
        "## Inputs",
        "",
        f"- trace files before filter: {input_counts.get('trace_files_before_filter', len(report.get('source_trace_files', [])))}",
        f"- trace files after filter: {input_counts.get('trace_files_after_filter', len(report.get('source_trace_files', [])))}",
        f"- usable marker observations: {report.get('observation_summary', {}).get('count', 0)}",
        f"- profile summaries reference-only: {len(report.get('source_profiles_reference_only', []))}",
        f"- mode filter: `{filters.get('mode')}`",
        f"- backend filter: `{filters.get('backend')}`",
        "",
        "## Global Assumptions",
        "",
    ]
    for assumption in report.get("global_assumptions", []):
        lines.append(f"- {assumption}")

    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:20]:
            lines.append(f"- {warning}")
        if len(warnings) > 20:
            lines.append(f"- ... {len(warnings) - 20} more warnings")

    lines.extend(
        [
            "",
            "## Candidates",
            "",
            "| Instruction | LMUL | Field | Status | Candidate | Evidence |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    instructions = report.get("instructions", {})
    if not instructions:
        lines.append("| n/a | n/a | n/a | insufficient_evidence | n/a | 0 |")
    for instruction_id in sorted(instructions):
        lmuls = instructions[instruction_id].get("lmuls", {})
        for lmul in sorted(lmuls, key=lmul_sort_key):
            fields = lmuls[lmul].get("fields", {})
            for field in FIELD_ORDER:
                item = fields.get(field, {})
                lines.append(
                    f"| `{instruction_id}` | `{lmul}` | `{field}` | "
                    f"{item.get('status', 'missing')} | `{value_text(item)}` | "
                    f"{item.get('constraint_count', 0)} |"
                )

    lines.extend(["", "## Formula Fits", ""])
    lines.append("| Instruction | Field | Status | Formula | Residual |")
    lines.append("| --- | --- | --- | --- | ---: |")
    for instruction_id in sorted(instructions):
        fits = instructions[instruction_id].get("formula_fits", {})
        for field in ("Latency", "ReleaseAtCycles"):
            fit = fits.get(field, {})
            if fit.get("base") is not None and fit.get("k") is not None:
                formula = f"{fit['base']} + {fit['k']} * LMUL"
            else:
                formula = "n/a"
            residual = fit.get("residual")
            lines.append(
                f"| `{instruction_id}` | `{field}` | {fit.get('status', 'missing')} | "
                f"`{formula}` | {residual if residual is not None else 'n/a'} |"
            )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search conservative RVV timing-model candidates.")
    parser.add_argument("--config", action="append", default=[], help="YAML-ish timing config file or directory.")
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Results root, profile.yaml, trace.json, or directory containing trace.json files.",
    )
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-value", type=int, default=128, help="Maximum integer candidate value to enumerate.")
    parser.add_argument("--mode", help="Optional trace JSON mode filter, e.g. real_platform_profile.")
    parser.add_argument("--backend", help="Optional trace JSON backend filter, e.g. gem5_minor.")
    parser.add_argument(
        "--include-dry-run",
        action="store_true",
        help="Include dry_run_trace entries even when selecting real-platform/gem5 traces.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_paths = load_profiles(args.profile)
    configs = load_configs(default_reference_config_args(args.config))
    before_filter = all_trace_paths(args.profile)
    observations, trace_paths, warnings = load_observations(
        args.profile,
        mode=args.mode,
        backend=args.backend,
        include_dry_run=args.include_dry_run,
    )
    filters = filter_description(args.mode, args.backend, args.include_dry_run)
    input_counts = {
        "trace_files_before_filter": len(before_filter),
        "trace_files_after_filter": len(trace_paths),
        "usable_marker_observations": len(observations),
    }
    report = build_report(
        profile_paths,
        trace_paths,
        observations,
        configs,
        warnings,
        args.max_value,
        input_counts=input_counts,
        filters=filters,
    )
    if args.format == "json":
        content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        content = render_markdown(report)

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    else:
        print(content, end="")

    real_platform_selected = (
        args.mode == "real_platform_profile"
        or args.backend == "gem5_minor"
        or selected_observations_are_real_platform(observations)
    )
    if real_platform_selected:
        common_root = common_output_root(args.profile, args.output)
        if should_write_real_platform_artifacts(args.output, common_root):
            write_real_platform_artifacts(report, common_root)
            summary_path = common_root / "search_model_real_platform_summary.md"
            summary_path.write_text(render_markdown(report), encoding="utf-8")
            json_path = common_root / "search_model_real_platform.json"
            if Path(args.output or "") != json_path:
                json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
