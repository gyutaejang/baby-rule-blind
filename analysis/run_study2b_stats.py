"""Study 2b confirmatory statistics (STUDY2B_PLAN.md §5).
Study 2b 확증 통계 (STUDY2B_PLAN.md 5절).

Reuses the FROZEN primitives of analysis/paired_stats.py (paired
permutation, paired bootstrap CIs, rank-biserial, Holm, pairing-grid
validation) and adds only the Study 2b hypothesis wiring:
동결된 analysis/paired_stats.py의 프리미티브를 재사용하고 Study 2b 고유
가설 배선만 추가한다:

- P1 (primary, one test per model): WCDMinimal < RawLLM on
  prev_rule_error_count; success = Holm p < .05 AND negative observed
  direction; headroom gate = RawLLM mean prev_rule_error >= 3.0 on the
  Study 2b streams.
- S1 (key secondary, non-inferiority): WCDMinimal non-inferior to
  RuleBlindFull on prev_rule_error_count iff the paired-bootstrap 95% CI
  UPPER bound of (WCDMinimal - Full) < DELTA = 1.9917 (frozen at the
  study2b-freeze tag from the pre-registered anchor rule).
- Secondary family (Holm within family, per model): S2 accuracy vs
  RawLLM (+ direction; do-no-harm CI lower bound > -0.02), S3
  prev_rule_error vs WSLSBudgeted (two-sided, no direction), S4 accuracy
  vs Full (two-sided; do-no-harm bound -0.02).
- Exploratory (labeled, no confirmatory claim): WCDMinimal vs Full on
  prev_rule_error.
- Per-model interpretation verdict from the FIXED map of plan §5.

This module was written and committed BEFORE any Study 2b stream was
generated (audit item 5).
이 모듈은 Study 2b 스트림 생성 '이전'에 작성·커밋되었다 (감사 항목 5).

Usage / 사용:
    python -m analysis.run_study2b_stats
Outputs / 산출:
    results/study2b_paired_stats.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.paired_stats import (  # noqa: E402
    holm_correct,
    load_summary,
    paired_bootstrap_ci_level,
    paired_permutation_p,
    paired_values,
    rank_biserial,
    validate_pairing_grid,
)

EXPECTED_MODELS = (
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.5-2026-04-23",
    "gpt-5.4-mini-2026-03-17",
)
EXPECTED_CONDITIONS = ("RawLLM", "WCDMinimal", "RuleBlindFull", "WSLSBudgeted")
REP_START = 131
REP_END = 260

# Frozen at the study2b-freeze tag (STUDY2B_PLAN.md §5-S1): the
# pre-registered anchor rule evaluated on the A0 calibration corpus.
# study2b-freeze 태그에서 동결 (계획 5절-S1): 사전 등록 앵커 규칙을 A0
# calibration 코퍼스에서 산출한 값.
DELTA_PREV_RULE_ERROR = 1.9917
DO_NO_HARM_ACCURACY = -0.02
HEADROOM_MIN_PREV = 3.0


def assert_confirmatory_grid(summary_path: Path) -> None:
    """Exact-grid check: every (model, condition) cell must contain reps
    131..260 exactly once (same discipline as run_study2_stats).
    정확한 grid 검증: 모든 (model, condition) 칸에 rep 131..260이 정확히
    한 번씩 있어야 한다 (run_study2_stats와 동일한 규율)."""
    rows = load_summary(summary_path)
    expected_reps = set(range(REP_START, REP_END + 1))
    cells: Dict[Tuple[str, str], List[int]] = {}
    for r in rows:
        cells.setdefault((r["model"], r["condition"]), []).append(int(r["rep"]))
    expected_cells = {(m, c) for m in EXPECTED_MODELS for c in EXPECTED_CONDITIONS}
    if set(cells) != expected_cells:
        raise SystemExit(
            f"grid cells mismatch: missing={sorted(expected_cells - set(cells))} "
            f"unexpected={sorted(set(cells) - expected_cells)} / grid 칸 불일치"
        )
    for key, reps in cells.items():
        if sorted(reps) != sorted(expected_reps):
            raise SystemExit(
                f"cell {key} does not contain reps {REP_START}..{REP_END} "
                f"exactly once ({len(reps)} rows) / rep 집합 불일치"
            )


def run_study2b_comparisons(summary_path: Path) -> List[Dict[str, object]]:
    rows = load_summary(summary_path)
    validate_pairing_grid(rows)
    label = "study2b_confirmatory"
    out: List[Dict[str, object]] = []

    # (cond_a, cond_b, metric, family, direction): direction is the
    # pre-registered sign of mean_diff (0 = two-sided, no direction).
    # direction은 사전 등록된 mean_diff 부호 (0 = 방향 없음).
    specs = [
        ("WCDMinimal", "RawLLM", "prev_rule_error_count", "primary", -1),
        ("WCDMinimal", "RawLLM", "total_accuracy", "secondary", +1),
        ("WCDMinimal", "WSLSBudgeted", "prev_rule_error_count", "secondary", 0),
        ("WCDMinimal", "RuleBlindFull", "total_accuracy", "secondary", 0),
        ("WCDMinimal", "RuleBlindFull", "prev_rule_error_count", "exploratory", 0),
    ]

    for model in EXPECTED_MODELS:
        # Headroom gate (STUDY2B_PLAN.md §5-P1, same rule as plan §8):
        # P1 runs confirmatorily only if RawLLM mean prev_rule_error on
        # the Study 2b streams >= 3.0.
        # headroom 게이트: Study 2b 스트림의 RawLLM 평균 prev_rule_error
        # >= 3.0일 때만 P1을 확증 검정한다.
        raw_prev = [
            float(r["prev_rule_error_count"])
            for r in rows
            if r["model"] == model and r["condition"] == "RawLLM"
        ]
        headroom = sum(raw_prev) / len(raw_prev) if raw_prev else 0.0
        gate_open = headroom >= HEADROOM_MIN_PREV

        results: List[Dict[str, object]] = []
        pvalues: List[float] = []
        for cond_a, cond_b, metric, family, direction in specs:
            if family == "primary" and not gate_open:
                out.append(
                    {
                        "label": label, "model": model,
                        "comparison": f"{cond_a} vs {cond_b}", "metric": metric,
                        "family": family, "n_pairs": 0, "n_dropped": 0,
                        "mean_diff": "", "ci_low": "", "ci_high": "",
                        "rank_biserial": "", "p_raw": "",
                        "p_holm": "not_tested_headroom",
                    }
                )
                continue
            diffs, dropped = paired_values(rows, model, cond_a, cond_b, metric)
            p = paired_permutation_p(diffs)
            lo, hi = paired_bootstrap_ci_level(diffs, level=0.95)
            pvalues.append(p)
            results.append(
                {
                    "label": label, "model": model,
                    "comparison": f"{cond_a} vs {cond_b}", "metric": metric,
                    "family": family, "n_pairs": len(diffs), "n_dropped": dropped,
                    "mean_diff": round(sum(diffs) / len(diffs), 4) if diffs else float("nan"),
                    "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                    "rank_biserial": round(rank_biserial(diffs), 4),
                    # Rounded for display; Holm uses full precision.
                    # 표시용 반올림; Holm은 원정밀도 사용.
                    "p_raw": round(p, 5),
                    "_p_full": p, "_direction": direction,
                }
            )

        # Holm within each family, per model, on full-precision p-values.
        # Primary is a single-test family; exploratory is corrected within
        # itself and never grounds a confirmatory claim.
        # 모델별·family별 원정밀도 Holm. primary는 단일 검정 family;
        # exploratory는 자체 보정하며 확증 주장 근거가 될 수 없다.
        p1_success = False
        for family in ("primary", "secondary", "exploratory"):
            idxs = [i for i, r in enumerate(results) if r["family"] == family]
            adjusted = holm_correct([results[i]["_p_full"] for i in idxs])
            for i, adj in zip(idxs, adjusted):
                r = results[i]
                r["p_holm"] = "<.001" if adj < 0.001 else round(adj, 5)
                direction = r.pop("_direction")
                r.pop("_p_full")
                if direction != 0:
                    md = r["mean_diff"]
                    ok = isinstance(md, float) and md * direction > 0 and adj < 0.05
                    r["success"] = "PASS" if ok else "fail"
                    if family == "primary":
                        p1_success = ok
        out.extend(results)

        # S1 — non-inferiority (STUDY2B_PLAN.md §5-S1): 95% CI UPPER
        # bound of (WCDMinimal - Full) prev_rule_error < DELTA.
        # Directional by CI bound; superiority over Full is not required.
        # S1 — 비열등성: (WCDMinimal - Full) prev_rule_error 차이의 95%
        # CI '상한' < DELTA. CI 경계 단측 판정; Full 대비 우월성은 요구
        # 되지 않는다.
        diffs, dropped = paired_values(
            rows, model, "WCDMinimal", "RuleBlindFull", "prev_rule_error_count"
        )
        lo95, hi95 = paired_bootstrap_ci_level(diffs, level=0.95)
        s1_noninferior = hi95 < DELTA_PREV_RULE_ERROR
        out.append(
            {
                "label": label, "model": model,
                "comparison": "WCDMinimal vs RuleBlindFull",
                "metric": f"prev_rule_error_count (non-inferiority, Delta {DELTA_PREV_RULE_ERROR})",
                "family": "noninferiority",
                "n_pairs": len(diffs), "n_dropped": dropped,
                "mean_diff": round(sum(diffs) / len(diffs), 4) if diffs else float("nan"),
                "ci_low": round(lo95, 4), "ci_high": round(hi95, 4),
                "rank_biserial": "", "p_raw": "",
                "p_holm": "noninferior" if s1_noninferior else "not_established",
            }
        )

        # Do-no-harm accuracy bounds (plan §5-S2/S4, same SESOI as the
        # frozen plan): CI lower bound of the accuracy difference > -0.02.
        # do-no-harm 정확도 경계: 정확도 차이 CI 하한 > -0.02.
        for opponent in ("RawLLM", "RuleBlindFull"):
            diffs, _ = paired_values(rows, model, "WCDMinimal", opponent, "total_accuracy")
            lo, hi = paired_bootstrap_ci_level(diffs, level=0.95)
            out.append(
                {
                    "label": label, "model": model,
                    "comparison": f"WCDMinimal vs {opponent}",
                    "metric": "total_accuracy (do-no-harm, margin -0.02)",
                    "family": "noninferiority",
                    "n_pairs": len(diffs), "n_dropped": 0,
                    "mean_diff": round(sum(diffs) / len(diffs), 4) if diffs else float("nan"),
                    "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                    "rank_biserial": "", "p_raw": "",
                    "p_holm": "noninferior" if lo > DO_NO_HARM_ACCURACY else "not_established",
                }
            )

        # Per-model verdict from the FIXED interpretation map (plan §5).
        # 계획 5절의 고정 해석 지도에 따른 모델별 판정.
        if not gate_open:
            verdict = "gate_closed_insufficient_headroom"
        elif p1_success and s1_noninferior:
            verdict = "minimal_sufficient_stack_unnecessary"
        elif p1_success and not s1_noninferior:
            verdict = "scaffold_works_stack_adds_protection"
        elif (not p1_success) and s1_noninferior:
            verdict = "no_effect_beyond_noise_on_endpoint"
        else:
            verdict = "minimal_harmful_protections_load_bearing"
        out.append(
            {
                "label": label, "model": model,
                "comparison": "(P1 x S1 interpretation map)",
                "metric": "confirmatory verdict", "family": "verdict",
                "n_pairs": "", "n_dropped": "", "mean_diff": "",
                "ci_low": "", "ci_high": "", "rank_biserial": "",
                "p_raw": "", "p_holm": verdict,
            }
        )
    return out


def main() -> None:
    summary_path = PROJECT_ROOT / "results" / "study2b_summary.csv"
    assert_confirmatory_grid(summary_path)
    results = run_study2b_comparisons(summary_path)

    out_path = PROJECT_ROOT / "results" / "study2b_paired_stats.csv"
    columns = [
        "label", "model", "comparison", "metric", "family",
        "n_pairs", "n_dropped", "mean_diff", "ci_low", "ci_high",
        "rank_biserial", "p_raw", "p_holm", "success",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"{'model':<24}{'comparison':<34}{'metric':<44}{'fam':<15}{'mdiff':>8}{'CI':>20}{'p_holm':>26}{'success':>9}")
    for r in results:
        ci = f"[{r['ci_low']}, {r['ci_high']}]"
        print(
            f"{r['model']:<24}{r['comparison']:<34}{str(r['metric']):<44}{r['family']:<15}"
            f"{r['mean_diff']:>8}{ci:>20}{str(r['p_holm']):>26}{r.get('success', ''):>9}"
        )
    print(f"\nstats: {out_path}")


if __name__ == "__main__":
    main()
