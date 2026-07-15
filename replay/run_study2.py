"""Study 2 — confirmatory replay of frozen model streams.
Study 2 — 동결 모델 스트림의 확증 재생.

Replays the 4 x 130 confirmatory raw streams (data/public_study2/)
through the eight conditions of ANALYSIS_PLAN.md §3, each repetition on
its own committed randomized schedule (plan §6). The condition wiring is
IDENTICAL to replay/run_study1.py and to the gate-tested end-to-end dry
run (tests/test_study2_dryrun.py); this file only supplies the real
paths. Every condition consumes the SAME stream, so comparisons are
repetition-level paired by construction.

확증 원 스트림 4 x 130개(data/public_study2/)를 계획 3절의 여덟 조건에
재생한다. repetition마다 커밋된 자기 무작위 일정을 사용한다(6절). 조건
배선은 replay/run_study1.py 및 게이트의 end-to-end dry run과 동일하며,
이 파일은 실제 경로만 공급한다. 모든 조건이 같은 스트림을 소비하므로
비교는 구성상 repetition 단위 paired다.

Outputs / 산출:
    results/study2_summary.csv  one row per (model, rep, condition)
    results/study2_trials.csv   one row per replayed trial (diagnostics)

Usage / 사용:
    python -m replay.run_study2
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
    TrajectoryOnlyController,
    WSLSController,
)
from controller.yoked_random import YokedRandomController  # noqa: E402
from evaluator import Evaluator  # noqa: E402
from oracle import OracleFullController  # noqa: E402
from replay import load_public_stream, run_replay, summarize  # noqa: E402

DATA_STUDY2 = PROJECT_ROOT / "data" / "public_study2"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth_study2"
RESULTS_DIR = PROJECT_ROOT / "results"

# Frozen confirmatory roster (plan v2.0 §5; OpenAI IDs pinned at
# pilot-freeze-v2). Directory names as written by study2/runner.py.
# 동결된 확증 로스터 (계획 v2.0 5절; OpenAI ID는 pilot-freeze-v2에서
# 고정). study2/runner.py가 기록한 디렉터리명 그대로.
MODELS = (
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gpt-5.5-2026-04-23",
    "gpt-5.4-mini-2026-03-17",
)
N_REPS = 130

# Same fixed convention as Study 1: seed = YOKED_SEED_BASE + rep index,
# shared across models at the same rep (bit-for-bit reproducible).
# Study 1과 동일한 고정 규약: seed = YOKED_SEED_BASE + rep. 같은 rep의
# 모델 간 공유 (비트 단위 재현 가능).
YOKED_SEED_BASE = 20260715


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
        for rep in range(1, N_REPS + 1):
            stream = load_public_stream(
                DATA_STUDY2 / model / f"rep_{rep:02d}_public.csv"
            )
            schedule_path = GROUND_TRUTH_DIR / f"rep_{rep:02d}_ground_truth.csv"
            evaluator = Evaluator(schedule_path)

            # Full first — YokedRandom copies its intervention schedule.
            # Full 먼저 — YokedRandom이 그 개입 일정을 복사한다.
            full_result = run_replay(RuleBlindFullController(), stream, evaluator)

            conditions = [
                ("RawLLM", run_replay(PassthroughController(), stream, evaluator)),
                ("RuleBlindFull", full_result),
                ("NoVeto", run_replay(RuleBlindFullController(veto_window=0), stream, evaluator)),
                ("TrajectoryOnly", run_replay(TrajectoryOnlyController(), stream, evaluator)),
                (
                    "YokedRandom",
                    run_replay(
                        YokedRandomController(
                            full_result.intervention_trials(), seed=YOKED_SEED_BASE + rep
                        ),
                        stream,
                        evaluator,
                    ),
                ),
                ("WSLSBudgeted", run_replay(WSLSController(max_interventions_per_rep=9), stream, evaluator)),
                ("WSLSUnlimited", run_replay(WSLSController(max_interventions_per_rep=None), stream, evaluator)),
                ("OracleFull", run_replay(OracleFullController(schedule_path), stream, evaluator)),
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

    write_rows(
        RESULTS_DIR / "study2_summary.csv",
        summary_rows,
        [
            "model",
            "rep",
            "condition",
            "n_trials",
            "total_accuracy",
            "prev_rule_error_count",
            "old_rule_reentry_count",
            "choice_entropy",
            "unparsable_count",
            "recovery_latency_mean",
            "latency_censored_count",
            "intervention_count",
            "intervention_coverage",
            "corrective_override_count",
            "harmful_override_count",
            "net_correction",
            "intervention_precision",
            "subsequent_success_rate",
        ],
    )
    write_rows(
        RESULTS_DIR / "study2_trials.csv",
        trial_rows,
        [
            "model",
            "rep",
            "condition",
            "trial_number",
            "block",
            "rule_shift",
            "raw_choice",
            "final_choice",
            "intervened",
            "correct",
            "prev_rule_error",
        ],
    )

    conditions_order = (
        "RawLLM", "RuleBlindFull", "NoVeto", "TrajectoryOnly",
        "YokedRandom", "WSLSBudgeted", "WSLSUnlimited", "OracleFull",
    )
    print("model                    condition       acc     prevrule interv  corr/harm  precision")
    for model in MODELS:
        for condition in conditions_order:
            rows = [r for r in summary_rows if r["model"] == model and r["condition"] == condition]
            acc = sum(r["total_accuracy"] for r in rows) / len(rows)
            per = sum(r["prev_rule_error_count"] for r in rows) / len(rows)
            itv = sum(r["intervention_count"] for r in rows) / len(rows)
            cor = sum(r["corrective_override_count"] for r in rows)
            hrm = sum(r["harmful_override_count"] for r in rows)
            prec = [r["intervention_precision"] for r in rows if r["intervention_precision"] >= 0]
            prec_m = sum(prec) / len(prec) if prec else float("nan")
            print(
                f"{model:<24} {condition:<15} {acc:.4f}  {per:6.2f}  {itv:6.2f}  "
                f"{cor:4.0f}/{hrm:<4.0f}  {prec_m:.3f}"
            )

    print(f"\nsummary: {RESULTS_DIR / 'study2_summary.csv'} ({len(summary_rows)} rows)")
    print(f"trials:  {RESULTS_DIR / 'study2_trials.csv'} ({len(trial_rows)} rows)")


if __name__ == "__main__":
    main()
