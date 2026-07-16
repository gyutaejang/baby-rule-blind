"""Exploratory intervention-efficiency and recovery-survival analysis.

This module extends the completed Study 2 replay without changing the frozen
confirmatory analysis.  It answers two post-hoc questions:

1. How much paired accuracy, target mutual information, and choice entropy
   change is observed per intervention?
2. After a shifted block first enters an error state, how long does it take
   to produce the next correct choice, allowing right censoring?

Accuracy gain per intervention is an extensive paired count ratio.  Mutual
information and entropy are distributional quantities, so their ratios are
explicitly descriptive intervention-normalized lifts, not causal effects of
an individual intervention.

Usage:
    python -m analysis.exploratory_efficiency_survival
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Mapping, Sequence, Tuple

from analysis.exploratory_information_processing import (
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    CONDITIONS,
    MODELS,
    N_REPS,
    N_TRIALS,
    PROJECT_ROOT,
    RESULTS_DIR,
    add_sequential_fields,
    bias_corrected_mi,
    fmt,
    load_enriched_trials,
    shannon_entropy,
    write_csv,
)


POLICY_FAMILY = {
    "RawLLM": "raw",
    "RuleBlindFull": "rule_blind_feedback",
    "NoVeto": "rule_blind_ablation",
    "TrajectoryOnly": "trajectory_placebo",
    "YokedRandom": "yoked_placebo",
    "WSLSBudgeted": "wsls_budgeted",
    "WSLSUnlimited": "wsls_unlimited",
    "OracleFull": "oracle_assisted",
}


def percentile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def bootstrap_ratio_ci(
    numerators: Sequence[float],
    denominators: Sequence[float],
    seed: int,
) -> Tuple[float, float]:
    if len(numerators) != len(denominators):
        raise ValueError("bootstrap ratio inputs must have equal length")
    rng = random.Random(seed)
    draws = []
    n = len(numerators)
    for _ in range(BOOTSTRAP_DRAWS):
        indices = [rng.randrange(n) for _ in range(n)]
        denominator = sum(denominators[i] for i in indices)
        if denominator:
            draws.append(sum(numerators[i] for i in indices) / denominator)
    return percentile(draws, 0.025), percentile(draws, 0.975)


def repetition_metrics(
    rows: Sequence[Mapping[str, object]],
) -> Dict[Tuple[str, int, str], Dict[str, float]]:
    grouped: Dict[Tuple[str, int, str], List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["model"]), int(row["rep"]), str(row["condition"]))].append(row)

    output = {}
    for key, cell in grouped.items():
        choices = [str(row["final_choice"]) for row in cell if row["final_choice"]]
        output[key] = {
            "correct_count": float(sum(int(row["correct"]) for row in cell)),
            "entropy_bits": shannon_entropy(choices),
            "interventions": float(sum(int(row["intervened"]) for row in cell)),
        }
    return output


def pareto_flags(
    rows: List[Dict[str, object]],
    outcome_field: str,
    eligible_field: str,
) -> Dict[Tuple[str, str], int]:
    flags: Dict[Tuple[str, str], int] = {}
    for model in MODELS:
        candidates = [
            row
            for row in rows
            if row["model"] == model and int(row[eligible_field]) == 1
        ]
        for row in candidates:
            cost = float(row["intervention_rate"])
            outcome = float(row[outcome_field])
            dominated = any(
                float(other["intervention_rate"]) <= cost
                and float(other[outcome_field]) >= outcome
                and (
                    float(other["intervention_rate"]) < cost
                    or float(other[outcome_field]) > outcome
                )
                for other in candidates
                if other is not row
            )
            flags[(model, str(row["condition"]))] = int(not dominated)
    return flags


def intervention_efficiency(
    rows: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    metrics = repetition_metrics(rows)
    pooled_target_mi = {}
    pooled_cells: Dict[Tuple[str, str], List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        pooled_cells[(str(row["model"]), str(row["condition"]))].append(row)
    for key, cell in pooled_cells.items():
        choices = [str(row["final_choice"]) for row in cell if row["final_choice"]]
        targets = [str(row["target_rule"]) for row in cell if row["final_choice"]]
        pooled_target_mi[key] = bias_corrected_mi(choices, targets)

    output: List[Dict[str, object]] = []

    for model_idx, model in enumerate(MODELS):
        for condition_idx, condition in enumerate(CONDITIONS):
            accuracy_numerators = []
            entropy_numerators = []
            denominators = []
            for rep in range(1, N_REPS + 1):
                raw = metrics[(model, rep, "RawLLM")]
                current = metrics[(model, rep, condition)]
                accuracy_numerators.append(
                    current["correct_count"] - raw["correct_count"]
                )
                entropy_numerators.append(
                    current["entropy_bits"] - raw["entropy_bits"]
                )
                denominators.append(current["interventions"])

            total_interventions = sum(denominators)
            mean_interventions = total_interventions / N_REPS
            accuracy_gain = sum(accuracy_numerators) / (N_REPS * N_TRIALS)
            entropy_gain = sum(entropy_numerators) / N_REPS
            mi_gain = (
                pooled_target_mi[(model, condition)]
                - pooled_target_mi[(model, "RawLLM")]
            )
            seed_base = (
                BOOTSTRAP_SEED
                + 10_000
                + model_idx * len(CONDITIONS) * 10
                + condition_idx * 10
            )

            if total_interventions:
                accuracy_ratio = sum(accuracy_numerators) / total_interventions
                entropy_ratio = sum(entropy_numerators) / total_interventions
                mi_ratio = mi_gain / mean_interventions
                accuracy_ci = bootstrap_ratio_ci(
                    accuracy_numerators, denominators, seed_base
                )
                entropy_ci = bootstrap_ratio_ci(
                    entropy_numerators, denominators, seed_base + 1
                )
            else:
                accuracy_ratio = entropy_ratio = mi_ratio = math.nan
                accuracy_ci = entropy_ci = (math.nan, math.nan)

            output.append(
                {
                    "model": model,
                    "condition": condition,
                    "policy_family": POLICY_FAMILY[condition],
                    "n_reps": N_REPS,
                    "n_trials": N_REPS * N_TRIALS,
                    "total_interventions": int(total_interventions),
                    "mean_interventions_per_rep": fmt(mean_interventions),
                    "intervention_rate": fmt(
                        total_interventions / (N_REPS * N_TRIALS)
                    ),
                    "sparse_nonoracle_eligible": int(
                        condition != "OracleFull"
                        and total_interventions / (N_REPS * N_TRIALS) <= 0.25
                    ),
                    "paired_extra_correct": int(sum(accuracy_numerators)),
                    "accuracy_gain_vs_raw": fmt(accuracy_gain),
                    "extra_correct_per_intervention": fmt(accuracy_ratio),
                    "extra_correct_per_intervention_ci_low": fmt(accuracy_ci[0]),
                    "extra_correct_per_intervention_ci_high": fmt(accuracy_ci[1]),
                    "entropy_gain_vs_raw_bits": fmt(entropy_gain),
                    "entropy_lift_bits_per_intervention": fmt(entropy_ratio),
                    "entropy_lift_per_intervention_ci_low": fmt(entropy_ci[0]),
                    "entropy_lift_per_intervention_ci_high": fmt(entropy_ci[1]),
                    "target_mi_gain_vs_raw_bits": fmt(mi_gain),
                    "target_mi_lift_bits_per_intervention": fmt(mi_ratio),
                }
            )

    accuracy_flags = pareto_flags(
        output, "accuracy_gain_vs_raw", "sparse_nonoracle_eligible"
    )
    target_flags = pareto_flags(
        output, "target_mi_gain_vs_raw_bits", "sparse_nonoracle_eligible"
    )
    for row in output:
        key = (str(row["model"]), str(row["condition"]))
        row["sparse_accuracy_pareto"] = accuracy_flags.get(key, 0)
        row["sparse_target_mi_pareto"] = target_flags.get(key, 0)
    return output


def recovery_episodes(
    rows: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    grouped: Dict[
        Tuple[str, int, str, int], List[Mapping[str, object]]
    ] = defaultdict(list)
    for row in rows:
        if int(row["block"]) > 1:
            grouped[
                (
                    str(row["model"]),
                    int(row["rep"]),
                    str(row["condition"]),
                    int(row["block"]),
                )
            ].append(row)

    episodes = []
    for (model, rep, condition, block), cell in sorted(grouped.items()):
        ordered = sorted(cell, key=lambda row: int(row["trial_in_block"]))
        first_error_index = next(
            (index for index, row in enumerate(ordered) if int(row["correct"]) == 0),
            None,
        )
        if first_error_index is None:
            episodes.append(
                {
                    "model": model,
                    "rep": rep,
                    "condition": condition,
                    "block": block,
                    "block_length": len(ordered),
                    "entered_error_state": 0,
                    "first_error_position": "",
                    "duration": "",
                    "event": "",
                }
            )
            continue

        first_error_position = int(
            ordered[first_error_index]["trial_in_block"]
        )
        recovery_index = next(
            (
                index
                for index in range(first_error_index + 1, len(ordered))
                if int(ordered[index]["correct"]) == 1
            ),
            None,
        )
        if recovery_index is None:
            duration = len(ordered) - first_error_index - 1
            event = 0
        else:
            duration = recovery_index - first_error_index
            event = 1
        episodes.append(
            {
                "model": model,
                "rep": rep,
                "condition": condition,
                "block": block,
                "block_length": len(ordered),
                "entered_error_state": 1,
                "first_error_position": first_error_position,
                "available_followup": len(ordered) - first_error_index - 1,
                "duration": duration,
                "event": event,
            }
        )
    return episodes


def kaplan_meier(
    episodes: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    entered = [episode for episode in episodes if int(episode["entered_error_state"]) == 1]
    if not entered:
        return []
    max_duration = max(int(episode["duration"]) for episode in entered)
    survival = 1.0
    curve = [
        {
            "lag_after_first_error": 0,
            "at_risk": len(entered),
            "recovery_events": 0,
            "censored": sum(
                int(episode["event"]) == 0 and int(episode["duration"]) == 0
                for episode in entered
            ),
            "recovery_hazard": 0.0,
            "survival_unrecovered": 1.0,
            "cumulative_recovery": 0.0,
        }
    ]
    for lag in range(1, max_duration + 1):
        at_risk = sum(int(episode["duration"]) >= lag for episode in entered)
        events = sum(
            int(episode["event"]) == 1 and int(episode["duration"]) == lag
            for episode in entered
        )
        censored = sum(
            int(episode["event"]) == 0 and int(episode["duration"]) == lag
            for episode in entered
        )
        hazard = events / at_risk if at_risk else math.nan
        if at_risk:
            survival *= 1 - hazard
        curve.append(
            {
                "lag_after_first_error": lag,
                "at_risk": at_risk,
                "recovery_events": events,
                "censored": censored,
                "recovery_hazard": fmt(hazard),
                "survival_unrecovered": fmt(survival),
                "cumulative_recovery": fmt(1 - survival),
            }
        )
    return curve


def curve_value(
    curve: Sequence[Mapping[str, object]],
    lag: int,
    field: str,
) -> float:
    available = [
        row for row in curve if int(row["lag_after_first_error"]) <= lag
    ]
    if not available:
        return math.nan
    return float(available[-1][field])


def restricted_mean_unrecovered(
    curve: Sequence[Mapping[str, object]],
    horizon: int,
) -> float:
    return sum(
        curve_value(curve, lag, "survival_unrecovered")
        for lag in range(horizon)
    )


def complete_case_recovery(
    episodes: Sequence[Mapping[str, object]],
    horizon: int,
) -> Tuple[int, float]:
    known = [
        episode
        for episode in episodes
        if (
            int(episode["event"]) == 1
            and int(episode["duration"]) <= horizon
        )
        or int(episode["available_followup"]) >= horizon
    ]
    recovered = sum(
        int(episode["event"]) == 1
        and int(episode["duration"]) <= horizon
        for episode in known
    )
    return len(known), recovered / len(known) if known else math.nan


def survival_outputs(
    episodes: Sequence[Mapping[str, object]],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    grouped: Dict[Tuple[str, str], List[Mapping[str, object]]] = defaultdict(list)
    for episode in episodes:
        grouped[(str(episode["model"]), str(episode["condition"]))].append(episode)

    summary = []
    curves = []
    for model in MODELS:
        for condition in CONDITIONS:
            cell = grouped[(model, condition)]
            entered = [
                episode
                for episode in cell
                if int(episode["entered_error_state"]) == 1
            ]
            curve = kaplan_meier(cell)
            for row in curve:
                curves.append(
                    {
                        "model": model,
                        "condition": condition,
                        **row,
                    }
                )
            median = next(
                (
                    int(row["lag_after_first_error"])
                    for row in curve
                    if float(row["survival_unrecovered"]) <= 0.5
                ),
                None,
            )
            known_1, complete_1 = complete_case_recovery(entered, 1)
            known_2, complete_2 = complete_case_recovery(entered, 2)
            known_3, complete_3 = complete_case_recovery(entered, 3)
            recovery_events = sum(int(episode["event"]) for episode in entered)
            right_censored = sum(
                int(episode["event"]) == 0 for episode in entered
            )
            summary.append(
                {
                    "model": model,
                    "condition": condition,
                    "n_shift_blocks": len(cell),
                    "no_error_blocks": sum(
                        int(episode["entered_error_state"]) == 0
                        for episode in cell
                    ),
                    "no_error_block_rate": fmt(
                        sum(
                            int(episode["entered_error_state"]) == 0
                            for episode in cell
                        )
                        / len(cell)
                    ),
                    "entered_error_state": len(entered),
                    "mean_first_error_position": fmt(
                        sum(float(episode["first_error_position"]) for episode in entered)
                        / len(entered)
                        if entered
                        else math.nan
                    ),
                    "recovery_events": recovery_events,
                    "right_censored": right_censored,
                    "right_censoring_rate": fmt(
                        right_censored / len(entered) if entered else math.nan
                    ),
                    "observed_recovery_fraction": fmt(
                        recovery_events / len(entered) if entered else math.nan
                    ),
                    "zero_followup_censored": sum(
                        int(episode["event"]) == 0
                        and int(episode["duration"]) == 0
                        for episode in entered
                    ),
                    "km_recovery_by_1": fmt(
                        curve_value(curve, 1, "cumulative_recovery")
                    ),
                    "km_recovery_by_2": fmt(
                        curve_value(curve, 2, "cumulative_recovery")
                    ),
                    "km_recovery_by_3": fmt(
                        curve_value(curve, 3, "cumulative_recovery")
                    ),
                    "km_recovery_by_4": fmt(
                        curve_value(curve, 4, "cumulative_recovery")
                    ),
                    "known_status_by_1": known_1,
                    "complete_case_recovery_by_1": fmt(complete_1),
                    "known_status_by_2": known_2,
                    "complete_case_recovery_by_2": fmt(complete_2),
                    "known_status_by_3": known_3,
                    "complete_case_recovery_by_3": fmt(complete_3),
                    "median_recovery_lag": "" if median is None else median,
                    "rmst_unrecovered_4_trials": fmt(
                        restricted_mean_unrecovered(curve, 4)
                    ),
                }
            )

    lookup = {
        (str(row["model"]), str(row["condition"])): row
        for row in summary
    }
    for row in summary:
        raw = lookup[(str(row["model"]), "RawLLM")]
        row["recovery_by_2_gain_vs_raw"] = fmt(
            float(row["km_recovery_by_2"]) - float(raw["km_recovery_by_2"])
        )
        row["rmst_4_reduction_vs_raw"] = fmt(
            float(raw["rmst_unrecovered_4_trials"])
            - float(row["rmst_unrecovered_4_trials"])
        )
    return summary, curves


def run_self_checks() -> None:
    fixture = [
        {"entered_error_state": 1, "duration": 1, "event": 1},
        {"entered_error_state": 1, "duration": 2, "event": 1},
        {"entered_error_state": 1, "duration": 2, "event": 0},
    ]
    curve = kaplan_meier(fixture)
    if not math.isclose(
        float(curve[1]["survival_unrecovered"]), 2 / 3, abs_tol=1e-6
    ):
        raise ValueError("Kaplan-Meier lag-1 self-check failed")
    if not math.isclose(
        float(curve[2]["survival_unrecovered"]), 1 / 3, abs_tol=1e-6
    ):
        raise ValueError("Kaplan-Meier lag-2 self-check failed")


def main() -> None:
    run_self_checks()
    rows = load_enriched_trials()
    add_sequential_fields(rows)
    efficiency_rows = intervention_efficiency(rows)
    episodes = recovery_episodes(rows)
    survival_summary, survival_curves = survival_outputs(episodes)

    outputs = {
        RESULTS_DIR / "exploratory_intervention_efficiency.csv": efficiency_rows,
        RESULTS_DIR / "exploratory_recovery_survival_summary.csv": survival_summary,
        RESULTS_DIR / "exploratory_recovery_survival_curve.csv": survival_curves,
    }
    for path, output_rows in outputs.items():
        write_csv(path, output_rows, list(output_rows[0]))
        print(
            f"wrote {path.relative_to(PROJECT_ROOT)} "
            f"({len(output_rows)} rows)"
        )
    print("efficiency and Kaplan-Meier self-checks passed")


if __name__ == "__main__":
    main()
