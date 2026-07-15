"""Study 2 confirmatory statistics — thin entry point.
Study 2 확증 통계 — 얇은 진입점.

Applies the FROZEN machinery of analysis/paired_stats.py (plan v2.0
§7–8: paired permutation, bootstrap CIs, rank-biserial, Holm per family,
endpoint-split headroom gates, directional success, per-model verdicts,
non-inferiority and equivalence) to the confirmatory summary produced by
replay/run_study2.py. No statistical logic lives here — only paths and
the confirmatory label.

동결된 analysis/paired_stats.py의 방법(계획 v2.0 7–8절)을
replay/run_study2.py가 만든 확증 요약에 적용한다. 통계 로직은 여기 없다
— 경로와 확증 라벨만 공급한다.

Usage / 사용:
    python -m analysis.run_study2_stats
Outputs / 산출:
    results/study2_paired_stats.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.paired_stats import (  # noqa: E402
    descriptive_subsequent_success,
    load_summary,
    run_comparisons,
)


EXPECTED_MODELS = (
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.5-2026-04-23",
    "gpt-5.4-mini-2026-03-17",
)
EXPECTED_CONDITIONS = (
    "RawLLM", "RuleBlindFull", "NoVeto", "TrajectoryOnly",
    "YokedRandom", "WSLSBudgeted", "WSLSUnlimited", "OracleFull",
)
EXPECTED_REPS = 130


def assert_confirmatory_grid(summary_path: Path) -> None:
    """Exact-grid check for the confirmatory dataset (review P2): every
    (model, condition) cell must contain reps 1..130 exactly once.
    확증 데이터의 정확한 grid 검증 (검토 P2): 모든 (model, condition)
    칸에 rep 1..130이 정확히 한 번씩 있어야 한다."""
    rows = load_summary(summary_path)
    expected_reps = set(range(1, EXPECTED_REPS + 1))
    cells = {}
    for r in rows:
        cells.setdefault((r["model"], r["condition"]), []).append(int(r["rep"]))
    expected_cells = {
        (m, c) for m in EXPECTED_MODELS for c in EXPECTED_CONDITIONS
    }
    if set(cells) != expected_cells:
        raise SystemExit(
            f"grid cells mismatch: missing={sorted(expected_cells - set(cells))} "
            f"unexpected={sorted(set(cells) - expected_cells)} / grid 칸 불일치"
        )
    for key, reps in cells.items():
        if sorted(reps) != sorted(expected_reps):
            raise SystemExit(
                f"cell {key} does not contain reps 1..{EXPECTED_REPS} exactly "
                f"once ({len(reps)} rows) / rep 집합 불일치"
            )


def main() -> None:
    summary_path = PROJECT_ROOT / "results" / "study2_summary.csv"
    assert_confirmatory_grid(summary_path)
    results = run_comparisons(summary_path, label="study2_confirmatory")

    out_path = PROJECT_ROOT / "results" / "study2_paired_stats.csv"
    columns = [
        "label", "model", "comparison", "metric", "family",
        "n_pairs", "n_dropped", "mean_diff", "ci_low", "ci_high",
        "rank_biserial", "p_raw", "p_holm", "success",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"{'model':<24}{'comparison':<30}{'metric':<28}{'fam':<10}{'mdiff':>8}{'CI':>20}{'p_holm':>12}{'success':>9}")
    for r in results:
        ci = f"[{r['ci_low']}, {r['ci_high']}]"
        print(
            f"{r['model']:<24}{r['comparison']:<30}{r['metric']:<28}{r['family']:<10}"
            f"{r['mean_diff']:>8}{ci:>20}{r['p_holm']:>12}{r.get('success', ''):>9}"
        )

    rows = load_summary(summary_path)
    print("\nsubsequent success (descriptive) / 후속 성공 (기술 통계):")
    for r in descriptive_subsequent_success(rows):
        print(
            f"  {r['model']:<24}{r['condition']:<15}"
            f"n={r['n_defined']:<4} excluded={r['n_excluded_zero_interventions']:<4}"
            f"mean={r['subsequent_success_rate_mean']}"
        )
    print(f"\nstats: {out_path}")


if __name__ == "__main__":
    main()
