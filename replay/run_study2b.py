"""Study 2b — confirmatory replay of the fresh streams (reps 131–260).
Study 2b — 신규 스트림(rep 131–260)의 확증 재생.

Replays the 4 x 130 fresh confirmatory streams through the four
conditions frozen in STUDY2B_PLAN.md §5: RawLLM, WCDMinimal (frozen A0
parameters = constructor defaults), RuleBlindFull (v1 frozen defaults),
and WSLSBudgeted. Every condition consumes the SAME stream, so all
comparisons are repetition-level paired by construction. Full and WSLS
are re-run on the new streams so every comparison stays within-dataset;
their locked Study 2 results are not re-litigated.

STUDY2B_PLAN.md 5절에 동결된 네 조건(RawLLM, WCDMinimal(동결 A0
파라미터 = 생성자 기본값), RuleBlindFull(v1 동결 기본값),
WSLSBudgeted)에 신규 확증 스트림 4 x 130개를 재생한다. 모든 조건이 같은
스트림을 소비하므로 비교는 구성상 repetition 단위 paired다. Full·WSLS는
새 스트림에서 재실행해 모든 비교를 동일 데이터셋 내로 한정하며, 이들의
잠긴 Study 2 결과는 재론되지 않는다.

This driver was written and committed BEFORE any Study 2b stream was
generated (STUDY2B_PLAN.md §7 audit item 5: no analyst degrees of
freedom remain after the streams exist).
이 드라이버는 Study 2b 스트림 생성 '이전'에 작성·커밋되었다 (계획 7절
감사 항목 5: 스트림 존재 이후 분석자 자유도 제거).

Outputs / 산출:
    results/study2b_summary.csv  one row per (model, rep, condition)
    results/study2b_trials.csv   one row per replayed trial (diagnostics)

Usage / 사용:
    python -m replay.run_study2b
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import (  # noqa: E402
    PassthroughController,
    RuleBlindFullController,
    WCDMinimalController,
    WSLSController,
)
from evaluator import Evaluator  # noqa: E402
from replay import load_public_stream, run_replay, summarize  # noqa: E402

DATA_STUDY2 = PROJECT_ROOT / "data" / "public_study2"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth_study2"
RESULTS_DIR = PROJECT_ROOT / "results"

# Frozen confirmatory roster, unchanged from study2-freeze (plan v2.0 §5;
# STUDY2B_PLAN.md §4). Directory names as written by study2/runner.py.
# study2-freeze에서 변경 없는 동결 확증 로스터. study2/runner.py가 기록한
# 디렉터리명 그대로.
MODELS = (
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.5-2026-04-23",
    "gpt-5.4-mini-2026-03-17",
)

# Study 2b confirmatory range (STUDY2B_PLAN.md §4): fresh reps only.
# Study 2b 확증 범위 (계획 4절): 신규 rep만.
REP_START = 131
REP_END = 260

SUMMARY_COLUMNS = [
    "model", "rep", "condition",
    "n_trials", "total_accuracy", "prev_rule_error_count",
    "old_rule_reentry_count", "choice_entropy", "unparsable_count",
    "recovery_latency_mean", "latency_censored_count",
    "intervention_count", "intervention_coverage",
    "corrective_override_count", "harmful_override_count",
    "net_correction", "intervention_precision", "subsequent_success_rate",
]

TRIAL_COLUMNS = [
    "model", "rep", "condition", "trial_number", "block", "rule_shift",
    "raw_choice", "final_choice", "intervened", "correct", "prev_rule_error",
]


def write_rows(path: Path, rows: List[Dict], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    summary_rows: List[Dict] = []
    trial_rows: List[Dict] = []

    for model in MODELS:
        for rep in range(REP_START, REP_END + 1):
            stream = load_public_stream(
                DATA_STUDY2 / model / f"rep_{rep:02d}_public.csv"
            )
            evaluator = Evaluator(GROUND_TRUTH_DIR / f"rep_{rep:02d}_ground_truth.csv")

            # Fresh controller per (stream, condition) — controllers are
            # stateful. / (스트림, 조건)마다 새 컨트롤러 — 상태 보유.
            conditions = [
                ("RawLLM", run_replay(PassthroughController(), stream, evaluator)),
                ("WCDMinimal", run_replay(WCDMinimalController(), stream, evaluator)),
                ("RuleBlindFull", run_replay(RuleBlindFullController(), stream, evaluator)),
                ("WSLSBudgeted", run_replay(WSLSController(max_interventions_per_rep=9), stream, evaluator)),
            ]

            for condition, result in conditions:
                s = summarize(result)
                s.update({"model": model, "rep": rep, "condition": condition})
                summary_rows.append(s)
                for r in result.records:
                    trial_rows.append(
                        {
                            "model": model,
                            "rep": rep,
                            "condition": condition,
                            "trial_number": r.trial_number,
                            "block": r.block,
                            "rule_shift": int(r.rule_shift),
                            "raw_choice": r.raw_choice,
                            "final_choice": r.final_choice,
                            "intervened": int(r.intervened),
                            "correct": int(r.correct),
                            "prev_rule_error": int(r.prev_rule_error),
                        }
                    )

    write_rows(RESULTS_DIR / "study2b_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_rows(RESULTS_DIR / "study2b_trials.csv", trial_rows, TRIAL_COLUMNS)

    conditions_order = ("RawLLM", "WCDMinimal", "RuleBlindFull", "WSLSBudgeted")
    print("model                    condition       acc     prevrule interv")
    for model in MODELS:
        for condition in conditions_order:
            rows = [r for r in summary_rows if r["model"] == model and r["condition"] == condition]
            acc = sum(r["total_accuracy"] for r in rows) / len(rows)
            per = sum(r["prev_rule_error_count"] for r in rows) / len(rows)
            itv = sum(r["intervention_count"] for r in rows) / len(rows)
            print(f"{model:<24} {condition:<15} {acc:.4f}  {per:6.2f}  {itv:6.2f}")

    print(f"\nsummary: {RESULTS_DIR / 'study2b_summary.csv'} ({len(summary_rows)} rows)")
    print(f"trials:  {RESULTS_DIR / 'study2b_trials.csv'} ({len(trial_rows)} rows)")


if __name__ == "__main__":
    main()
