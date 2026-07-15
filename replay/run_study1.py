"""Study 1 — archived-stream retrospective replay (EXPLORATORY).
Study 1 — 보관 스트림 회고 재생 (탐색적).

Replays all 60 archived raw streams (30 claude + 30 gpt) through the six
conditions fixed in ANALYSIS_PLAN.md §3. Because every condition consumes
the SAME stream, comparisons are repetition-level paired by construction.

보관된 원 스트림 60개(claude 30 + gpt 30)를 ANALYSIS_PLAN.md 3절에 고정된
여섯 조건에 재생한다. 모든 조건이 '같은' 스트림을 소비하므로 비교는
구성상 repetition 단위 paired가 된다.

Outputs / 산출:
    results/study1_summary.csv  one row per (model, rep, condition)
    results/study1_trials.csv   one row per replayed trial (diagnostics)

Usage / 사용:
    python -m replay.run_study1
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

DATA_PUBLIC = PROJECT_ROOT / "data" / "public"
GROUND_TRUTH = PROJECT_ROOT / "data" / "ground_truth" / "wcst_ground_truth.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

MODELS = ("claude", "gpt")
N_REPS = 30

# Fixed base for YokedRandom seeds: seed = YOKED_SEED_BASE + rep index.
# Explicit constants keep the whole replay bit-for-bit reproducible.
# YokedRandom 시드의 고정 기저: seed = YOKED_SEED_BASE + rep 번호.
# 명시적 상수로 replay 전체를 비트 단위로 재현 가능하게 유지한다.
YOKED_SEED_BASE = 20260715


def write_rows(path: Path, rows: List[Dict], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    evaluator = Evaluator(GROUND_TRUTH)
    summary_rows: List[Dict] = []
    trial_rows: List[Dict] = []

    for model in MODELS:
        for rep in range(1, N_REPS + 1):
            stream = load_public_stream(DATA_PUBLIC / f"{model}_rep_{rep:02d}_public.csv")

            # The Full run comes first because YokedRandom must copy its
            # intervention schedule (yoking).
            # Full을 먼저 실행한다 — YokedRandom이 그 개입 일정을 복사해야
            # 하기 때문이다(yoking).
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
                # Information-matched baselines (Amendment B §11.2):
                # same per-trial outcome information as Full.
                # 정보량 동일 기준선 (수정안 B 11.2절): Full과 동일한
                # trial별 정오 정보를 받는다.
                ("WSLSBudgeted", run_replay(WSLSController(max_interventions_per_rep=9), stream, evaluator)),
                ("WSLSUnlimited", run_replay(WSLSController(max_interventions_per_rep=None), stream, evaluator)),
                # Oracle-assisted policy reference (NOT a ceiling — the
                # theoretical ceiling is 1.0; Amendment B §11.6).
                # oracle 보조 정책 참조 (상한선이 아님 — 이론적 상한은
                # 1.0; 수정안 B 11.6절).
                ("OracleFull", run_replay(OracleFullController(GROUND_TRUTH), stream, evaluator)),
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
        RESULTS_DIR / "study1_summary.csv",
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
        RESULTS_DIR / "study1_trials.csv",
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

    # Console overview: per-condition means per model.
    # 콘솔 개요: 모델별·조건별 평균.
    conditions_order = (
        "RawLLM", "RuleBlindFull", "NoVeto", "TrajectoryOnly",
        "YokedRandom", "WSLSBudgeted", "WSLSUnlimited", "OracleFull",
    )
    print("model    condition       acc     prevrule interv  corr/harm  precision")
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
                f"{model:<8} {condition:<15} {acc:.4f}  {per:6.2f}  {itv:6.2f}  "
                f"{cor:4.0f}/{hrm:<4.0f}  {prec_m:.3f}"
            )

    print(f"\nsummary: {RESULTS_DIR / 'study1_summary.csv'} ({len(summary_rows)} rows)")
    print(f"trials:  {RESULTS_DIR / 'study1_trials.csv'} ({len(trial_rows)} rows)")


if __name__ == "__main__":
    main()
