"""Exploratory information-processing analysis for Study 2.

This module does not alter the frozen confirmatory analysis.  It derives
descriptive, exploratory measures from the committed Study 2 trial stream:

* output-choice entropy and effective number of choices;
* coupling between the hidden target dimension and the emitted choice;
* target-specific accuracy and response distributions;
* sensitivity to visible stimulus attributes in the memoryless raw stream;
* switching and accuracy profiles across positions within a rule block;
* the association between raw entropy and supervisory accuracy headroom.

All calculations use the Python standard library and write separate files
whose names begin with ``exploratory_``.

Usage:
    python -m analysis.exploratory_information_processing
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRIALS_PATH = PROJECT_ROOT / "results" / "study2_trials.csv"
SUMMARY_PATH = PROJECT_ROOT / "results" / "study2_summary.csv"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth_study2"
STIMULUS_DIR = PROJECT_ROOT / "data" / "stimuli_study2"
RESULTS_DIR = PROJECT_ROOT / "results"

MODELS = (
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.5-2026-04-23",
    "gpt-5.4-mini-2026-03-17",
)
CONDITIONS = (
    "RawLLM",
    "RuleBlindFull",
    "NoVeto",
    "TrajectoryOnly",
    "YokedRandom",
    "WSLSBudgeted",
    "WSLSUnlimited",
    "OracleFull",
)
DIMENSIONS = ("color", "shape", "number")
N_REPS = 130
N_TRIALS = 36
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 20260716


def read_csv(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_mean(values: Iterable[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return statistics.fmean(vals) if vals else math.nan


def shannon_entropy(values: Iterable[str]) -> float:
    counts = Counter(v for v in values if v)
    total = sum(counts.values())
    if not total:
        return math.nan
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def mutual_information(xs: Sequence[str], ys: Sequence[str]) -> float:
    pairs = [(x, y) for x, y in zip(xs, ys) if x and y]
    if not pairs:
        return math.nan
    joint = Counter(pairs)
    x_counts = Counter(x for x, _ in pairs)
    y_counts = Counter(y for _, y in pairs)
    n = len(pairs)
    mi = 0.0
    for (x, y), n_xy in joint.items():
        p_xy = n_xy / n
        p_x = x_counts[x] / n
        p_y = y_counts[y] / n
        mi += p_xy * math.log2(p_xy / (p_x * p_y))
    return mi


def bias_corrected_mi(xs: Sequence[str], ys: Sequence[str]) -> float:
    """First-order finite-sample correction for plug-in mutual information."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x and y]
    if not pairs:
        return math.nan
    raw = mutual_information(
        [x for x, _ in pairs],
        [y for _, y in pairs],
    )
    k_x = len({x for x, _ in pairs})
    k_y = len({y for _, y in pairs})
    correction = ((k_x - 1) * (k_y - 1)) / (2 * len(pairs) * math.log(2))
    return max(0.0, raw - correction)


def pearson_r(xs: Sequence[float], ys: Sequence[float]) -> float:
    pairs = [(x, y) for x, y in zip(xs, ys) if not math.isnan(x) and not math.isnan(y)]
    if len(pairs) < 2:
        return math.nan
    x_vals = [x for x, _ in pairs]
    y_vals = [y for _, y in pairs]
    x_mean = statistics.fmean(x_vals)
    y_mean = statistics.fmean(y_vals)
    x_ss = sum((x - x_mean) ** 2 for x in x_vals)
    y_ss = sum((y - y_mean) ** 2 for y in y_vals)
    if x_ss == 0 or y_ss == 0:
        return math.nan
    return sum((x - x_mean) * (y - y_mean) for x, y in pairs) / math.sqrt(x_ss * y_ss)


def average_ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[order[k]] = rank
        i = j
    return ranks


def spearman_r(xs: Sequence[float], ys: Sequence[float]) -> float:
    pairs = [(x, y) for x, y in zip(xs, ys) if not math.isnan(x) and not math.isnan(y)]
    if len(pairs) < 2:
        return math.nan
    return pearson_r(
        average_ranks([x for x, _ in pairs]),
        average_ranks([y for _, y in pairs]),
    )


def percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return math.nan
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    weight = pos - lo
    return sorted_values[lo] * (1 - weight) + sorted_values[hi] * weight


def bootstrap_mean_ci(values: Sequence[float], seed: int) -> Tuple[float, float]:
    rng = random.Random(seed)
    n = len(values)
    draws = []
    for _ in range(BOOTSTRAP_DRAWS):
        draws.append(statistics.fmean(values[rng.randrange(n)] for _ in range(n)))
    draws.sort()
    return percentile(draws, 0.025), percentile(draws, 0.975)


def js_divergence_bits(p_values: Sequence[str], q_values: Sequence[str]) -> float:
    p_counts = Counter(v for v in p_values if v)
    q_counts = Counter(v for v in q_values if v)
    p_total = sum(p_counts.values())
    q_total = sum(q_counts.values())
    if not p_total or not q_total:
        return math.nan
    support = set(p_counts) | set(q_counts)
    p = {v: p_counts[v] / p_total for v in support}
    q = {v: q_counts[v] / q_total for v in support}
    m = {v: (p[v] + q[v]) / 2 for v in support}

    def kl(a: Mapping[str, float], b: Mapping[str, float]) -> float:
        return sum(a[v] * math.log2(a[v] / b[v]) for v in support if a[v] > 0)

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def fmt(value: float, digits: int = 6) -> object:
    return "" if math.isnan(value) else round(value, digits)


def load_context() -> Tuple[Dict[Tuple[int, int], Dict[str, str]], Dict[Tuple[int, int], Dict[str, str]]]:
    truth: Dict[Tuple[int, int], Dict[str, str]] = {}
    stimuli: Dict[Tuple[int, int], Dict[str, str]] = {}
    for rep in range(1, N_REPS + 1):
        for row in read_csv(GROUND_TRUTH_DIR / f"rep_{rep:02d}_ground_truth.csv"):
            key = (rep, int(row["trial_number"]))
            if key in truth:
                raise ValueError(f"duplicate ground-truth key: {key}")
            truth[key] = row
        for row in read_csv(STIMULUS_DIR / f"rep_{rep:02d}_prompts.csv"):
            key = (rep, int(row["trial_number"]))
            if key in stimuli:
                raise ValueError(f"duplicate stimulus key: {key}")
            stimuli[key] = row
    expected = N_REPS * N_TRIALS
    if len(truth) != expected or len(stimuli) != expected:
        raise ValueError(
            f"context grid mismatch: truth={len(truth)}, stimuli={len(stimuli)}, expected={expected}"
        )
    return truth, stimuli


def load_enriched_trials() -> List[Dict[str, object]]:
    truth, stimuli = load_context()
    rows = read_csv(TRIALS_PATH)
    expected = len(MODELS) * len(CONDITIONS) * N_REPS * N_TRIALS
    if len(rows) != expected:
        raise ValueError(f"trial row count mismatch: {len(rows)} != {expected}")

    seen = set()
    enriched: List[Dict[str, object]] = []
    raw_choice_by_trial: Dict[Tuple[str, int, int], str] = {}
    for row in rows:
        model = row["model"]
        condition = row["condition"]
        rep = int(row["rep"])
        trial = int(row["trial_number"])
        record_key = (model, rep, condition, trial)
        if record_key in seen:
            raise ValueError(f"duplicate trial key: {record_key}")
        seen.add(record_key)
        context_key = (rep, trial)
        if context_key not in truth or context_key not in stimuli:
            raise ValueError(f"missing context for {context_key}")
        gt = truth[context_key]
        stimulus = stimuli[context_key]
        raw_choice = row["raw_choice"]
        stream_key = (model, rep, trial)
        prior_raw = raw_choice_by_trial.setdefault(stream_key, raw_choice)
        if prior_raw != raw_choice:
            raise ValueError(f"raw choice differs across replay conditions: {stream_key}")
        enriched.append(
            {
                "model": model,
                "condition": condition,
                "rep": rep,
                "trial_number": trial,
                "block": int(row["block"]),
                "trial_in_block": int(gt["trial_in_block"]),
                "rule_shift": int(row["rule_shift"]),
                "target_rule": gt["hidden_rule"],
                "previous_rule": gt["previous_hidden_rule"],
                "raw_choice": raw_choice,
                "final_choice": row["final_choice"],
                "intervened": int(row["intervened"]),
                "correct": int(row["correct"]),
                "prev_rule_error": int(row["prev_rule_error"]),
                "stimulus_color": stimulus["color"],
                "stimulus_shape": stimulus["shape"],
                "stimulus_number": stimulus["number"],
            }
        )
    return enriched


def add_sequential_fields(rows: List[Dict[str, object]]) -> None:
    groups: Dict[Tuple[str, int, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["model"]), int(row["rep"]), str(row["condition"]))].append(row)
    for group in groups.values():
        group.sort(key=lambda r: int(r["trial_number"]))
        previous = None
        for row in group:
            if previous is None:
                row["choice_switched"] = None
                row["previous_correct"] = None
            else:
                row["choice_switched"] = int(row["final_choice"] != previous["final_choice"])
                row["previous_correct"] = int(previous["correct"])
            previous = row


def condition_summary(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["model"]), str(row["condition"]))].append(row)

    raw_choices = {
        model: [str(r["final_choice"]) for r in grouped[(model, "RawLLM")] if r["final_choice"]]
        for model in MODELS
    }
    output = []
    for model in MODELS:
        for condition in CONDITIONS:
            cell = grouped[(model, condition)]
            per_rep: Dict[int, List[Dict[str, object]]] = defaultdict(list)
            for row in cell:
                per_rep[int(row["rep"])].append(row)
            entropies = []
            max_shares = []
            for rep_rows in per_rep.values():
                choices = [str(r["final_choice"]) for r in rep_rows if r["final_choice"]]
                entropies.append(shannon_entropy(choices))
                counts = Counter(choices)
                max_shares.append(max(counts.values()) / len(choices) if choices else math.nan)
            entropy = safe_mean(entropies)
            choices = [str(r["final_choice"]) for r in cell if r["final_choice"]]
            targets = [str(r["target_rule"]) for r in cell if r["final_choice"]]
            target_h = shannon_entropy(targets)
            target_mi = mutual_information(choices, targets)
            target_mi_bc = bias_corrected_mi(choices, targets)
            by_target = defaultdict(list)
            for row in cell:
                by_target[str(row["target_rule"])].append(int(row["correct"]))
            target_accuracies = [safe_mean(by_target[d]) for d in DIMENSIONS]
            shift_switch = [
                int(r["choice_switched"])
                for r in cell
                if r["choice_switched"] is not None and int(r["rule_shift"]) == 1
            ]
            stable_switch = [
                int(r["choice_switched"])
                for r in cell
                if r["choice_switched"] is not None and int(r["rule_shift"]) == 0
            ]
            after_error = [
                int(r["choice_switched"])
                for r in cell
                if r["choice_switched"] is not None and int(r["previous_correct"]) == 0
            ]
            after_correct = [
                int(r["choice_switched"])
                for r in cell
                if r["choice_switched"] is not None and int(r["previous_correct"]) == 1
            ]
            shifted_blocks = [r for r in cell if int(r["block"]) > 1]
            shift_trial_accuracy = safe_mean(
                int(r["correct"]) for r in shifted_blocks if int(r["trial_in_block"]) == 1
            )
            early_post_shift_accuracy = safe_mean(
                int(r["correct"])
                for r in shifted_blocks
                if int(r["trial_in_block"]) in (2, 3)
            )
            late_block_accuracy = safe_mean(
                int(r["correct"])
                for r in shifted_blocks
                if int(r["trial_in_block"]) >= 4
            )
            post_shift_switch_rate = safe_mean(
                int(r["choice_switched"])
                for r in shifted_blocks
                if int(r["trial_in_block"]) == 2 and r["choice_switched"] is not None
            )
            interventions = sum(int(r["intervened"]) for r in cell)
            corrections = sum(
                int(r["intervened"])
                and str(r["raw_choice"]) != str(r["target_rule"])
                and str(r["final_choice"]) == str(r["target_rule"])
                for r in cell
            )
            harms = sum(
                int(r["intervened"])
                and str(r["raw_choice"]) == str(r["target_rule"])
                and str(r["final_choice"]) != str(r["target_rule"])
                for r in cell
            )
            shift_rate = safe_mean(shift_switch)
            stable_rate = safe_mean(stable_switch)
            error_rate = safe_mean(after_error)
            correct_rate = safe_mean(after_correct)
            output.append(
                {
                    "model": model,
                    "condition": condition,
                    "n_reps": len(per_rep),
                    "n_trials": len(cell),
                    "n_parseable": len(choices),
                    "parseable_rate": fmt(len(choices) / len(cell)),
                    "accuracy": fmt(safe_mean(int(r["correct"]) for r in cell)),
                    "choice_entropy_bits": fmt(entropy),
                    "normalized_choice_entropy": fmt(entropy / math.log2(3)),
                    "effective_choice_count": fmt(2**entropy),
                    "max_choice_share": fmt(safe_mean(max_shares)),
                    "target_mi_bits": fmt(target_mi),
                    "target_mi_bias_corrected_bits": fmt(target_mi_bc),
                    "normalized_target_mi": fmt(target_mi_bc / target_h if target_h else math.nan),
                    "balanced_target_accuracy": fmt(safe_mean(target_accuracies)),
                    "target_accuracy_range": fmt(max(target_accuracies) - min(target_accuracies)),
                    "switch_rate_on_shift": fmt(shift_rate),
                    "switch_rate_without_shift": fmt(stable_rate),
                    "shift_switch_lift": fmt(shift_rate - stable_rate),
                    "change_after_error": fmt(error_rate),
                    "change_after_correct": fmt(correct_rate),
                    "feedback_change_lift": fmt(error_rate - correct_rate),
                    "shift_trial_accuracy": fmt(shift_trial_accuracy),
                    "early_post_shift_accuracy": fmt(early_post_shift_accuracy),
                    "early_post_shift_gain": fmt(
                        early_post_shift_accuracy - shift_trial_accuracy
                    ),
                    "late_block_accuracy": fmt(late_block_accuracy),
                    "post_shift_trial2_switch_rate": fmt(post_shift_switch_rate),
                    "intervention_rate": fmt(interventions / len(cell)),
                    "corrective_overrides": corrections,
                    "harmful_overrides": harms,
                    "net_correction_per_intervention": fmt(
                        (corrections - harms) / interventions if interventions else math.nan
                    ),
                    "choice_js_from_raw_bits": fmt(js_divergence_bits(raw_choices[model], choices)),
                }
            )
    return output


def target_profiles(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[Tuple[str, str, str], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["model"]), str(row["condition"]), str(row["target_rule"]))].append(row)
    output = []
    for model in MODELS:
        for condition in CONDITIONS:
            for target in DIMENSIONS:
                cell = grouped[(model, condition, target)]
                choices = Counter(str(r["final_choice"]) for r in cell if r["final_choice"])
                n_choices = sum(choices.values())
                output.append(
                    {
                        "model": model,
                        "condition": condition,
                        "target_rule": target,
                        "n_trials": len(cell),
                        "accuracy": fmt(safe_mean(int(r["correct"]) for r in cell)),
                        "choice_color_share": fmt(choices["color"] / n_choices if n_choices else math.nan),
                        "choice_shape_share": fmt(choices["shape"] / n_choices if n_choices else math.nan),
                        "choice_number_share": fmt(choices["number"] / n_choices if n_choices else math.nan),
                    }
                )
    return output


def transition_profiles(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[Tuple[str, str, int], List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        if int(row["block"]) == 1:
            continue
        grouped[(str(row["model"]), str(row["condition"]), int(row["trial_in_block"]))].append(row)
    positions = sorted({int(r["trial_in_block"]) for r in rows if int(r["block"]) > 1})
    output = []
    for model in MODELS:
        for condition in CONDITIONS:
            for position in positions:
                cell = grouped[(model, condition, position)]
                if not cell:
                    continue
                switch_values = [
                    int(r["choice_switched"])
                    for r in cell
                    if r["choice_switched"] is not None
                ]
                output.append(
                    {
                        "model": model,
                        "condition": condition,
                        "trial_in_block": position,
                        "n_trials": len(cell),
                        "accuracy": fmt(safe_mean(int(r["correct"]) for r in cell)),
                        "choice_entropy_bits": fmt(
                            shannon_entropy(str(r["final_choice"]) for r in cell if r["final_choice"])
                        ),
                        "choice_switch_rate": fmt(safe_mean(switch_values)),
                        "prev_rule_error_rate": fmt(
                            safe_mean(int(r["prev_rule_error"]) for r in cell)
                        ),
                    }
                )
    return output


def stimulus_sensitivity(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    output = []
    for model in MODELS:
        cell = [r for r in rows if r["model"] == model and r["condition"] == "RawLLM"]
        choices = [str(r["final_choice"]) for r in cell if r["final_choice"]]
        choice_h = shannon_entropy(choices)
        for attribute in ("color", "shape", "number"):
            pairs = [
                (str(r["final_choice"]), str(r[f"stimulus_{attribute}"]))
                for r in cell
                if r["final_choice"]
            ]
            xs = [x for x, _ in pairs]
            ys = [y for _, y in pairs]
            mi = mutual_information(xs, ys)
            mi_bc = bias_corrected_mi(xs, ys)
            output.append(
                {
                    "model": model,
                    "visible_attribute": attribute,
                    "n_trials": len(pairs),
                    "attribute_levels": len(set(ys)),
                    "raw_choice_entropy_bits": fmt(choice_h),
                    "choice_attribute_mi_bits": fmt(mi),
                    "choice_attribute_mi_bias_corrected_bits": fmt(mi_bc),
                    "fraction_choice_entropy_explained": fmt(
                        mi_bc / choice_h if choice_h > 0 else 0.0
                    ),
                }
            )
    return output


def entropy_headroom(summary_rows: List[Dict[str, str]], condition_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    lookup = {
        (row["model"], row["condition"]): row
        for row in condition_rows
    }
    by_key = {
        (row["model"], int(row["rep"]), row["condition"]): row
        for row in summary_rows
    }
    output = []
    for model_idx, model in enumerate(MODELS):
        raw_entropy = []
        raw_accuracy = []
        accuracy_gain = []
        for rep in range(1, N_REPS + 1):
            raw = by_key[(model, rep, "RawLLM")]
            full = by_key[(model, rep, "RuleBlindFull")]
            raw_entropy.append(float(raw["choice_entropy"]))
            raw_accuracy.append(float(raw["total_accuracy"]))
            accuracy_gain.append(float(full["total_accuracy"]) - float(raw["total_accuracy"]))
        ci_low, ci_high = bootstrap_mean_ci(
            accuracy_gain,
            BOOTSTRAP_SEED + model_idx,
        )
        raw_cell = lookup[(model, "RawLLM")]
        full_cell = lookup[(model, "RuleBlindFull")]
        output.append(
            {
                "model": model,
                "n_reps": N_REPS,
                "raw_entropy_mean_bits": fmt(safe_mean(raw_entropy)),
                "ruleblind_entropy_mean_bits": full_cell["choice_entropy_bits"],
                "entropy_gain_bits": fmt(
                    float(full_cell["choice_entropy_bits"]) - safe_mean(raw_entropy)
                ),
                "accuracy_gain_mean": fmt(safe_mean(accuracy_gain)),
                "accuracy_gain_ci_low": fmt(ci_low),
                "accuracy_gain_ci_high": fmt(ci_high),
                "pearson_raw_entropy_vs_accuracy_gain": fmt(
                    pearson_r(raw_entropy, accuracy_gain)
                ),
                "spearman_raw_entropy_vs_accuracy_gain": fmt(
                    spearman_r(raw_entropy, accuracy_gain)
                ),
                "pearson_raw_entropy_vs_raw_accuracy": fmt(
                    pearson_r(raw_entropy, raw_accuracy)
                ),
                "target_mi_gain_bits": fmt(
                    float(full_cell["target_mi_bias_corrected_bits"])
                    - float(raw_cell["target_mi_bias_corrected_bits"])
                ),
                "choice_js_raw_to_ruleblind_bits": full_cell["choice_js_from_raw_bits"],
            }
        )
    return output


def validate_against_frozen_summary(
    summary_rows: List[Dict[str, str]],
    exploratory_rows: List[Dict[str, object]],
) -> None:
    frozen = defaultdict(list)
    for row in summary_rows:
        frozen[(row["model"], row["condition"])].append(row)
    for row in exploratory_rows:
        key = (str(row["model"]), str(row["condition"]))
        expected_accuracy = safe_mean(float(r["total_accuracy"]) for r in frozen[key])
        expected_entropy = safe_mean(float(r["choice_entropy"]) for r in frozen[key])
        if not math.isclose(float(row["accuracy"]), expected_accuracy, abs_tol=1e-6):
            raise ValueError(f"accuracy reconciliation failed for {key}")
        # The frozen summary stores each repetition's entropy rounded to four
        # decimals, whereas this analysis retains the exact trial-level value.
        if not math.isclose(float(row["choice_entropy_bits"]), expected_entropy, abs_tol=5e-5):
            raise ValueError(f"entropy reconciliation failed for {key}")


def run_self_checks() -> None:
    if not math.isclose(shannon_entropy(DIMENSIONS), math.log2(3), abs_tol=1e-12):
        raise ValueError("entropy self-check failed")
    repeated = list(DIMENSIONS) * 3
    if not math.isclose(mutual_information(repeated, repeated), math.log2(3), abs_tol=1e-12):
        raise ValueError("mutual-information identity self-check failed")
    independent_x = [x for x in DIMENSIONS for _ in DIMENSIONS]
    independent_y = list(DIMENSIONS) * len(DIMENSIONS)
    if not math.isclose(mutual_information(independent_x, independent_y), 0.0, abs_tol=1e-12):
        raise ValueError("mutual-information independence self-check failed")


def main() -> None:
    run_self_checks()
    rows = load_enriched_trials()
    add_sequential_fields(rows)
    summary_rows = condition_summary(rows)
    frozen_summary = read_csv(SUMMARY_PATH)
    validate_against_frozen_summary(frozen_summary, summary_rows)

    outputs = {
        RESULTS_DIR / "exploratory_information_processing_summary.csv": (
            summary_rows,
            list(summary_rows[0]),
        ),
        RESULTS_DIR / "exploratory_target_sensitivity.csv": (
            (target_rows := target_profiles(rows)),
            list(target_rows[0]),
        ),
        RESULTS_DIR / "exploratory_transition_profile.csv": (
            (transition_rows := transition_profiles(rows)),
            list(transition_rows[0]),
        ),
        RESULTS_DIR / "exploratory_stimulus_sensitivity.csv": (
            (stimulus_rows := stimulus_sensitivity(rows)),
            list(stimulus_rows[0]),
        ),
        RESULTS_DIR / "exploratory_entropy_headroom.csv": (
            (headroom_rows := entropy_headroom(frozen_summary, summary_rows)),
            list(headroom_rows[0]),
        ),
    }
    for path, (output_rows, columns) in outputs.items():
        write_csv(path, output_rows, columns)
        print(f"wrote {path.relative_to(PROJECT_ROOT)} ({len(output_rows)} rows)")
    print("self-checks and frozen-summary reconciliation passed")


if __name__ == "__main__":
    main()
