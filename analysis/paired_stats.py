"""Paired statistics for same-stream condition comparisons.
같은 스트림 조건 비교를 위한 paired 통계.

Implements the machinery fixed in ANALYSIS_PLAN.md §7:
ANALYSIS_PLAN.md 7절에 고정된 방법을 구현한다:

- paired permutation test (two-sided, sign-flip, 10,000 permutations)
  paired permutation 검정 (양측, 부호 반전, 10,000회)
- paired bootstrap 95% CI of the mean within-pair difference
  짝 내 차이 평균의 paired bootstrap 95% CI
- matched-pairs rank-biserial correlation
  matched-pairs rank-biserial 상관
- Holm correction within a family
  family 내 Holm 보정

All randomness is seeded explicitly: identical inputs give identical
p-values and intervals.
모든 난수는 명시적으로 시드된다: 같은 입력이면 같은 p값과 구간이 나온다.

Usage on Study 1 output / Study 1 산출물에 대한 사용:
    python -m analysis.paired_stats results/study1_summary.csv
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]

N_PERMUTATIONS = 10_000
N_BOOTSTRAP = 10_000
SEED = 20260715


# ---------------------------------------------------------------------------
# Core statistics / 핵심 통계
# ---------------------------------------------------------------------------

def paired_permutation_p(diffs: Sequence[float], seed: int = SEED) -> float:
    """Two-sided sign-flip permutation p-value for mean(diffs) != 0.
    mean(diffs) != 0에 대한 양측 부호 반전 permutation p값.

    Zero differences carry no sign information but stay in the mean, so
    they shrink the statistic honestly rather than being dropped.
    0인 차이는 부호 정보는 없지만 평균에는 남는다 — 제거하지 않고 통계량을
    정직하게 줄이는 쪽을 택한다.
    """
    n = len(diffs)
    if n == 0:
        return float("nan")
    observed = abs(sum(diffs) / n)
    rng = random.Random(seed)
    hits = 0
    for _ in range(N_PERMUTATIONS):
        s = 0.0
        for d in diffs:
            s += d if rng.random() < 0.5 else -d
        if abs(s / n) >= observed - 1e-12:
            hits += 1
    # Add-one smoothing keeps p > 0 (a permutation p-value can never be
    # exactly zero with finite permutations).
    # add-one 보정으로 p > 0을 유지한다 (유한 permutation에서 p가 정확히
    # 0이 될 수는 없다).
    return (hits + 1) / (N_PERMUTATIONS + 1)


def paired_bootstrap_ci(diffs: Sequence[float], seed: int = SEED) -> Tuple[float, float]:
    """Percentile bootstrap 95% CI of the mean within-pair difference.
    짝 내 차이 평균의 백분위 bootstrap 95% CI."""
    n = len(diffs)
    if n == 0:
        return float("nan"), float("nan")
    rng = random.Random(seed + 1)  # decorrelated from the permutation RNG / permutation 난수와 분리
    means = []
    for _ in range(N_BOOTSTRAP):
        means.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int(0.025 * N_BOOTSTRAP)]
    hi = means[min(N_BOOTSTRAP - 1, int(0.975 * N_BOOTSTRAP))]
    return lo, hi


def rank_biserial(diffs: Sequence[float]) -> float:
    """Matched-pairs rank-biserial correlation from signed ranks.
    부호 순위 기반 matched-pairs rank-biserial 상관.

    Zero differences are excluded, following the Wilcoxon convention.
    0인 차이는 Wilcoxon 관례에 따라 제외한다.
    """
    nonzero = [d for d in diffs if d != 0.0]
    if not nonzero:
        return 0.0
    ranked = sorted(nonzero, key=abs)
    # Average ranks for ties on |d|. / |d| 동점에는 평균 순위를 부여.
    ranks: Dict[int, float] = {}
    i = 0
    while i < len(ranked):
        j = i
        while j + 1 < len(ranked) and abs(ranked[j + 1]) == abs(ranked[i]):
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    w_plus = sum(ranks[k] for k, d in enumerate(ranked) if d > 0)
    w_minus = sum(ranks[k] for k, d in enumerate(ranked) if d < 0)
    total = w_plus + w_minus
    return (w_plus - w_minus) / total if total else 0.0


def holm_correct(pvalues: List[float]) -> List[float]:
    """Holm step-down adjusted p-values (monotone, capped at 1).
    Holm step-down 보정 p값 (단조 유지, 최대 1)."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, idx in enumerate(order):
        adj = min(1.0, (m - rank) * pvalues[idx])
        running_max = max(running_max, adj)
        adjusted[idx] = running_max
    return adjusted


# ---------------------------------------------------------------------------
# Study-summary comparison driver / 요약 파일 비교 실행기
# ---------------------------------------------------------------------------

def load_summary(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def paired_values(
    rows: List[Dict[str, str]], model: str, condition_a: str, condition_b: str, metric: str
) -> Tuple[List[float], int]:
    """Within-pair differences (a - b), paired by rep on the same stream.
    같은 스트림의 rep로 짝지은 짝 내 차이 (a - b).

    Undefined metric values (coded -1, e.g. productive_rate with zero
    interventions) drop the PAIR, and the count of dropped pairs is
    returned for reporting (plan §6).
    정의 불가 지표값(-1로 코딩, 예: 개입 0회의 productive_rate)은 해당
    짝을 제외하며, 제외 수는 보고를 위해 반환한다 (계획 6절).
    """
    a_by_rep = {
        int(r["rep"]): float(r[metric])
        for r in rows
        if r["model"] == model and r["condition"] == condition_a
    }
    b_by_rep = {
        int(r["rep"]): float(r[metric])
        for r in rows
        if r["model"] == model and r["condition"] == condition_b
    }
    diffs, dropped = [], 0
    for rep in sorted(set(a_by_rep) & set(b_by_rep)):
        va, vb = a_by_rep[rep], b_by_rep[rep]
        if va < 0 or vb < 0:
            dropped += 1
            continue
        diffs.append(va - vb)
    return diffs, dropped


def run_comparisons(summary_path: Path, label: str) -> List[Dict[str, object]]:
    """Run the plan §7 comparison set on one summary file.
    요약 파일 하나에 계획 7절의 비교 집합을 적용한다."""
    rows = load_summary(summary_path)
    models = sorted({r["model"] for r in rows})

    # (comparison, family): H1/H2 on primary metrics form the primary
    # family; everything else is secondary (plan §7).
    # (비교, family): 1차 지표에 대한 H1/H2가 primary family, 나머지는
    # 전부 secondary (계획 7절).
    comparison_specs = [
        ("RuleBlindFull", "RawLLM", "total_accuracy", "primary"),
        ("RuleBlindFull", "RawLLM", "persistence_error_count", "primary"),
        ("RuleBlindFull", "YokedRandom", "total_accuracy", "primary"),
        ("RuleBlindFull", "YokedRandom", "persistence_error_count", "primary"),
        ("RuleBlindFull", "NoVeto", "total_accuracy", "secondary"),
        ("RuleBlindFull", "NoVeto", "persistence_error_count", "secondary"),
        ("TrajectoryOnly", "RawLLM", "total_accuracy", "secondary"),
        ("TrajectoryOnly", "RawLLM", "persistence_error_count", "secondary"),
        ("OracleFull", "RawLLM", "total_accuracy", "ceiling"),
        ("OracleFull", "RawLLM", "persistence_error_count", "ceiling"),
        # NOTE: productive_rate is intentionally NOT a paired comparison
        # against RawLLM — the baseline never intervenes, so its rate is
        # undefined on every repetition and all pairs would drop. It is
        # reported descriptively instead (see descriptive_productive_rate).
        # 참고: productive_rate는 의도적으로 RawLLM과의 paired 비교에서
        # 제외한다 — 기준선은 개입이 없어 모든 repetition에서 정의 불가라
        # 짝이 전부 제외되기 때문이다. 대신 기술 통계로 보고한다
        # (descriptive_productive_rate 참조).
    ]

    out: List[Dict[str, object]] = []
    for model in models:
        results = []
        for cond_a, cond_b, metric, family in comparison_specs:
            diffs, dropped = paired_values(rows, model, cond_a, cond_b, metric)
            p = paired_permutation_p(diffs)
            lo, hi = paired_bootstrap_ci(diffs)
            results.append(
                {
                    "label": label,
                    "model": model,
                    "comparison": f"{cond_a} vs {cond_b}",
                    "metric": metric,
                    "family": family,
                    "n_pairs": len(diffs),
                    "n_dropped": dropped,
                    "mean_diff": round(sum(diffs) / len(diffs), 4) if diffs else float("nan"),
                    "ci_low": round(lo, 4),
                    "ci_high": round(hi, 4),
                    "rank_biserial": round(rank_biserial(diffs), 4),
                    "p_raw": round(p, 5),
                }
            )
        # Holm within each family, within each model (plan §7).
        # 모델별·family별 Holm 보정 (계획 7절).
        for family in ("primary", "secondary", "ceiling"):
            fam = [r for r in results if r["family"] == family]
            adjusted = holm_correct([float(r["p_raw"]) for r in fam])
            for r, adj in zip(fam, adjusted):
                r["p_holm"] = round(adj, 5)
        out.extend(results)
    return out


def descriptive_productive_rate(rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Descriptive productive-rate summary per model and condition,
    excluding undefined (-1) repetitions per plan §6 and reporting how
    many were excluded.
    모델·조건별 productive rate 기술 통계. 계획 6절에 따라 정의 불가(-1)
    repetition은 제외하고 제외 수를 함께 보고한다."""
    out: List[Dict[str, object]] = []
    models = sorted({r["model"] for r in rows})
    conditions = sorted({r["condition"] for r in rows})
    for model in models:
        for condition in conditions:
            values = [
                float(r["productive_rate"])
                for r in rows
                if r["model"] == model and r["condition"] == condition
            ]
            defined = [v for v in values if v >= 0]
            if not defined:
                continue
            out.append(
                {
                    "model": model,
                    "condition": condition,
                    "n_defined": len(defined),
                    "n_excluded_zero_interventions": len(values) - len(defined),
                    "productive_rate_mean": round(sum(defined) / len(defined), 4),
                }
            )
    return out


def main() -> None:
    summary_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "results" / "study1_summary.csv"
    results = run_comparisons(summary_path, label="study1_exploratory")

    out_path = PROJECT_ROOT / "results" / "study1_paired_stats.csv"
    columns = [
        "label", "model", "comparison", "metric", "family",
        "n_pairs", "n_dropped", "mean_diff", "ci_low", "ci_high",
        "rank_biserial", "p_raw", "p_holm",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"{'model':<8}{'comparison':<28}{'metric':<26}{'fam':<10}{'mdiff':>8}{'CI':>18}{'rrb':>7}{'p_holm':>9}")
    for r in results:
        ci = f"[{r['ci_low']}, {r['ci_high']}]"
        print(
            f"{r['model']:<8}{r['comparison']:<28}{r['metric']:<26}{r['family']:<10}"
            f"{r['mean_diff']:>8}{ci:>18}{r['rank_biserial']:>7}{r['p_holm']:>9}"
        )
    print("\nproductive rate (descriptive) / 생산적 개입 비율 (기술 통계):")
    desc = descriptive_productive_rate(load_summary(summary_path))
    desc_path = PROJECT_ROOT / "results" / "study1_productive_rate.csv"
    with open(desc_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "condition",
                "n_defined",
                "n_excluded_zero_interventions",
                "productive_rate_mean",
            ],
        )
        writer.writeheader()
        writer.writerows(desc)
    for d in desc:
        print(
            f"  {d['model']:<8}{d['condition']:<16}rate={d['productive_rate_mean']:<8}"
            f"n={d['n_defined']} excluded={d['n_excluded_zero_interventions']}"
        )

    print(f"\nwritten / 저장됨: {out_path}")
    print(f"written / 저장됨: {desc_path}")


if __name__ == "__main__":
    main()
