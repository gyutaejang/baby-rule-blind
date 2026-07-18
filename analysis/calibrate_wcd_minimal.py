"""A0 — exploratory calibration of WCD-minimal (STUDY2B_PLAN.md).
A0 — WCD-minimal의 탐색적 calibration (STUDY2B_PLAN.md).

CALIBRATION CORPUS RULE / calibration 코퍼스 규칙:
This script reads ONLY the archived Study 1 streams (data/public + the
single archived schedule). It must never touch data/public_study2,
data/public_study2_pilot, or any Study 2b stream. The locked Study 2
results motivated the WCD-minimal HYPOTHESIS; to keep the confirmatory
evaluation independent, parameter values are chosen here on Study 1
data only, frozen (study2b-freeze tag), and then evaluated once on
FRESH Study 2b streams (reps 131+), never on any data that existed when
the hypothesis was formed... with the exception of this declared
calibration corpus, whose use is disclosed in the paper.

이 스크립트는 '보관된 Study 1 스트림'(data/public + 단일 보관 일정)만
읽는다. data/public_study2, data/public_study2_pilot, Study 2b 스트림은
절대 읽지 않는다. 잠금된 Study 2 결과는 WCD-minimal '가설'의 동기가
되었으므로, 확증 평가의 독립성을 위해 파라미터는 Study 1 자료에서만
선택하고 동결(study2b-freeze 태그)한 뒤 '신규' Study 2b 스트림(rep
131+)에서 단 한 번 평가한다. 선언된 calibration 코퍼스의 사용 사실은
논문에 공개한다.

Codified selection rule (frozen BEFORE this script is first run for
selection; same style as analysis/param_search.py):
코드화된 선정 규칙 (선정 목적의 첫 실행 전에 동결; param_search.py와
동일한 방식):

    minimize pooled mean prev_rule_error over all 60 archived streams
    subject to pooled mean accuracy >= pooled RawLLM mean accuracy
    (do-no-harm on the calibration corpus).
    Ties: higher mean accuracy, then smaller wait_threshold, then larger
    decay, then smaller switch_margin (fixed, deterministic).

    60개 보관 스트림 합산 평균 prev_rule_error 최소화,
    제약: 합산 평균 정확도 >= RawLLM 합산 평균 정확도 (calibration
    코퍼스에서의 do-no-harm).
    동점: 높은 정확도 -> 작은 wait_threshold -> 큰 decay -> 작은
    switch_margin 순 (고정·결정론적).

NON-INFERIORITY MARGIN ANCHOR (pre-registered rule, numeric value frozen
from this script's output): Delta = 0.5 * |pooled mean prev_rule_error
of RawLLM - of Full v1| on the calibration corpus, floored at 0.5
errors per 36-trial repetition.
비열등성 마진 앵커 (규칙 사전 등록, 수치는 이 스크립트 출력으로 동결):
Delta = calibration 코퍼스에서의 |RawLLM 합산 평균 prev_rule_error -
Full v1 값| * 0.5, 하한 0.5 오류/36-trial repetition.

Usage / 사용:
    python -m analysis.calibrate_wcd_minimal
Outputs / 산출:
    results/calibration_wcd_minimal.csv  (full grid, every configuration)
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

from controller import (  # noqa: E402
    PassthroughController,
    RuleBlindFullController,
    WCDMinimalController,
)
from evaluator import Evaluator  # noqa: E402
from replay import load_public_stream, run_replay, summarize  # noqa: E402

DATA_PUBLIC = PROJECT_ROOT / "data" / "public"
GROUND_TRUTH = PROJECT_ROOT / "data" / "ground_truth" / "wcst_ground_truth.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

MODELS = ("claude", "gpt")
N_REPS = 30

# Full grid, stated openly (48 configurations). score_clip and the
# intervention budget are fixed, not searched: clip=5.0 bounds scores
# without interacting with the margin scale, and budget=9 is matched to
# the co-primary supervisors by design (not a free parameter).
# 공개된 전체 grid (48개 설정). score_clip과 개입 예산은 탐색하지 않고
# 고정한다: clip=5.0은 마진 스케일과 상호작용 없이 점수를 유계로 만들고,
# 예산 9는 설계상 공동 주 감독자들과 일치시키는 값이다 (자유 파라미터
# 아님).
GRID = {
    "decay": [0.5, 0.7, 0.9, 1.0],
    "switch_margin": [0.0, 0.5, 1.0, 2.0],
    "wait_threshold": [1, 2, 3],
}


def pooled(streams, evaluator, make_controller) -> Dict[str, float]:
    """Pooled means over all streams for one controller factory.
    컨트롤러 팩토리 하나에 대한 전 스트림 합산 평균."""
    accs: List[float] = []
    persists: List[float] = []
    intervs: List[float] = []
    for stream in streams:
        # Fresh controller per stream — controllers are stateful.
        # 스트림마다 새 컨트롤러 — 컨트롤러는 상태를 가진다.
        s = summarize(run_replay(make_controller(), stream, evaluator))
        accs.append(s["total_accuracy"])
        persists.append(s["prev_rule_error_count"])
        intervs.append(s["intervention_count"])
    return {
        "mean_accuracy": sum(accs) / len(accs),
        "mean_prev_rule_error": sum(persists) / len(persists),
        "mean_interventions": sum(intervs) / len(intervs),
        "max_interventions": max(intervs),
    }


def main() -> None:
    evaluator = Evaluator(GROUND_TRUTH)
    streams = [
        load_public_stream(DATA_PUBLIC / f"{model}_rep_{rep:02d}_public.csv")
        for model in MODELS
        for rep in range(1, N_REPS + 1)
    ]

    # Reference conditions on the SAME corpus: RawLLM anchors the
    # do-no-harm constraint; Full v1 anchors the non-inferiority margin.
    # 같은 코퍼스의 참조 조건: RawLLM은 do-no-harm 제약의, Full v1은
    # 비열등성 마진의 앵커.
    raw = pooled(streams, evaluator, PassthroughController)
    full = pooled(streams, evaluator, RuleBlindFullController)

    keys = list(GRID.keys())
    rows: List[Dict] = []
    for values in itertools.product(*(GRID[k] for k in keys)):
        params = dict(zip(keys, values))
        stats = pooled(streams, evaluator, lambda: WCDMinimalController(**params))
        row = dict(params)
        row.update({k: round(v, 4) for k, v in stats.items()})
        rows.append(row)

    # Codified selection (see module docstring). / 코드화된 선정 규칙.
    eligible = [r for r in rows if r["mean_accuracy"] >= round(raw["mean_accuracy"], 4)]
    eligible.sort(
        key=lambda r: (
            r["mean_prev_rule_error"],
            -r["mean_accuracy"],
            r["wait_threshold"],
            -r["decay"],
            r["switch_margin"],
        )
    )
    selected = eligible[0] if eligible else None

    # Margin anchor rule (see module docstring). / 마진 앵커 규칙.
    delta = max(0.5, 0.5 * abs(raw["mean_prev_rule_error"] - full["mean_prev_rule_error"]))

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "calibration_wcd_minimal.csv"
    columns = keys + [
        "mean_accuracy", "mean_prev_rule_error", "mean_interventions", "max_interventions",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print("calibration corpus (archived Study 1, 60 streams) references:")
    print(f"  RawLLM : accuracy {raw['mean_accuracy']:.4f}, "
          f"prev_rule_error {raw['mean_prev_rule_error']:.4f}")
    print(f"  Full v1: accuracy {full['mean_accuracy']:.4f}, "
          f"prev_rule_error {full['mean_prev_rule_error']:.4f}, "
          f"interventions {full['mean_interventions']:.2f}")
    print(f"\nnon-inferiority margin anchor / 비열등성 마진 앵커:")
    print(f"  Delta = max(0.5, 0.5 * |{raw['mean_prev_rule_error']:.4f} - "
          f"{full['mean_prev_rule_error']:.4f}|) = {delta:.4f} errors/rep")

    header = "".join(f"{k[:13]:>15}" for k in columns)
    by_persist = sorted(rows, key=lambda r: r["mean_prev_rule_error"])
    print("\ntop 10 by prev_rule_error (unconstrained view) / 고착 오류 상위 10 (제약 미적용):")
    print(header)
    for row in by_persist[:10]:
        print("".join(f"{row[k]:>15}" for k in columns))
    print("\nSELECTED (constraint-filtered) / 선택된 설정 (제약 적용):")
    if selected is None:
        print("  no configuration satisfies the constraints / 제약을 만족하는 설정 없음")
    else:
        print(header)
        print("".join(f"{selected[k]:>15}" for k in columns))
    print(f"\n{len(rows)} configurations ({len(eligible)} eligible) -> {out_path}")


if __name__ == "__main__":
    main()
