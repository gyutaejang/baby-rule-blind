"""Exploratory parameter search for RuleBlindFull (Study 1 phase only).
RuleBlindFull의 탐색적 파라미터 탐색 (Study 1 단계 전용).

IMPORTANT / 중요: this search runs on the archived streams, which are a
development set — anything chosen here is EXPLORATORY and must be frozen
(study2-freeze tag) before the confirmatory Study 2 streams are ever
generated. The search is documented openly, including the objective and
the full grid, unlike the withdrawn manuscript's undocumented search.

이 탐색은 개발용인 보관 스트림에서 수행된다 — 여기서 선택되는 것은 모두
'탐색적'이며, 확증용 Study 2 스트림을 생성하기 전에 반드시 동결(study2-
freeze 태그)해야 한다. 철회 원고의 비공개 탐색과 달리, 목적함수와 전체
grid를 포함해 탐색 과정을 공개적으로 기록한다.

Objective / 목적함수: pooled mean accuracy over ALL 60 streams (both
models jointly). One configuration is chosen for both models — per-model
tuning would double the overfitting surface.
전체 60개 스트림(두 모델 합산)의 평균 정확도. 두 모델에 하나의 설정만
선택한다 — 모델별 튜닝은 과적합 표면을 두 배로 늘리기 때문이다.

Usage / 사용:
    python -m analysis.param_search
"""

from __future__ import annotations

import csv
import itertools
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import RuleBlindFullController  # noqa: E402
from evaluator import Evaluator  # noqa: E402
from replay import load_public_stream, run_replay, summarize  # noqa: E402

DATA_PUBLIC = PROJECT_ROOT / "data" / "public"
GROUND_TRUTH = PROJECT_ROOT / "data" / "ground_truth" / "wcst_ground_truth.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

MODELS = ("claude", "gpt")
N_REPS = 30

# The full grid, stated openly (288 configurations; rescue_cooldown is
# redundant when rescue_failure_threshold=0, and those duplicate rows are kept
# for transparency rather than silently deduplicated).
# 공개된 전체 grid (288개 설정; rescue_failure_threshold=0일 때 rescue_cooldown은
# 무의미하지만, 그 중복 행도 조용히 제거하지 않고 투명하게 남긴다).
GRID = {
    "error_streak_to_open": [1, 2, 3],
    "veto_window": [2, 3, 4, 5],
    "rescue_failure_threshold": [0, 2, 3, 4],  # 0 = rescue disabled / 0 = rescue 비활성화
    "rescue_cooldown": [4, 6, 8],
    "belief_confirm_streak": [1, 2],
}


def main() -> None:
    evaluator = Evaluator(GROUND_TRUTH)

    # Load all streams once. / 스트림 전체를 한 번만 로드한다.
    streams = [
        load_public_stream(DATA_PUBLIC / f"{model}_rep_{rep:02d}_public.csv")
        for model in MODELS
        for rep in range(1, N_REPS + 1)
    ]

    keys = list(GRID.keys())
    rows: List[Dict] = []
    for values in itertools.product(*(GRID[k] for k in keys)):
        params = dict(zip(keys, values))
        accs: List[float] = []
        persists: List[float] = []
        intervs: List[float] = []
        for stream in streams:
            # Fresh controller per stream — controllers are stateful.
            # 스트림마다 새 컨트롤러 — 컨트롤러는 상태를 가진다.
            s = summarize(run_replay(RuleBlindFullController(**params), stream, evaluator))
            accs.append(s["total_accuracy"])
            persists.append(s["prev_rule_error_count"])
            intervs.append(s["intervention_count"])
        row = dict(params)
        row.update(
            {
                "mean_accuracy": round(sum(accs) / len(accs), 4),
                "mean_prev_rule_error": round(sum(persists) / len(persists), 4),
                "mean_interventions": round(sum(intervs) / len(intervs), 4),
                "max_interventions": max(intervs),
            }
        )
        rows.append(row)

    # Constrained selection rule, CODIFIED (Amendment B §11.6):
    # maximize pooled accuracy subject to mean prev_rule_error <= 9.
    # The intervention constraint is enforced structurally by the hard
    # per-repetition budget inside the controller (§11.2), which the
    # max_interventions column verifies.
    # 제약 선정 규칙의 코드화 (수정안 B 11.6절): 평균 prev_rule_error <= 9
    # 제약 하에서 합산 정확도 최대화. 개입 제약은 컨트롤러 내부의 하드
    # repetition 예산(11.2절)이 구조적으로 강제하며 max_interventions
    # 열로 검증한다.
    rows.sort(key=lambda r: -r["mean_accuracy"])
    eligible = [r for r in rows if r["mean_prev_rule_error"] <= 9.0]
    selected = eligible[0] if eligible else None

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "param_search_rule_blind_full.csv"
    columns = keys + ["mean_accuracy", "mean_prev_rule_error", "mean_interventions", "max_interventions"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    header = "".join(f"{k[:12]:>14}" for k in columns)
    print("top 10 by accuracy (unconstrained view) / 정확도 상위 10 (제약 미적용 표시):")
    print(header)
    for row in rows[:10]:
        print("".join(f"{row[k]:>14}" for k in columns))
    print(f"\nSELECTED (constraint-filtered) / 선택된 설정 (제약 적용):")
    if selected is None:
        print("  no configuration satisfies the constraints / 제약을 만족하는 설정 없음")
    else:
        print("".join(f"{selected[k]:>14}" for k in columns))
    print(f"\n{len(rows)} configurations ({len(eligible)} eligible) -> {out_path}")


if __name__ == "__main__":
    main()
