"""Mandatory leak-prevention tests (ANALYSIS_PLAN.md §2.3).
필수 누출 방지 테스트 (ANALYSIS_PLAN.md 2.3절).

No result may be reported unless all three tests pass:
아래 세 테스트를 모두 통과하지 않으면 어떤 결과도 보고할 수 없다:

1. Ground-truth invariance / 정답 불변성
2. Shuffle invariance for feedback-free controllers / 셔플 불변성
3. Feedback ordering / 피드백 순서

Runnable standalone (python -m tests.test_leak_prevention) or via pytest.
단독 실행(python -m tests.test_leak_prevention)과 pytest 모두 지원한다.
"""

from __future__ import annotations

import csv
import random
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

# Allow running from the project root without installation.
# 설치 없이 프로젝트 루트에서 바로 실행할 수 있게 한다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import (  # noqa: E402
    RULES,
    PassthroughController,
    RuleBlindFullController,
    TrajectoryOnlyController,
)
from controller.yoked_random import YokedRandomController  # noqa: E402
from evaluator import Evaluator  # noqa: E402
from replay import PublicStreamRow, run_replay  # noqa: E402

N_TRIALS = 36
BLOCK = 12  # trials per rule block in the synthetic session / 합성 세션의 블록 길이


# ---------------------------------------------------------------------------
# Synthetic fixtures / 합성 데이터
# ---------------------------------------------------------------------------

def synthetic_schedule() -> List[Dict[str, str]]:
    """Three blocks: color -> shape -> number.
    세 블록: color -> shape -> number."""
    rows = []
    order = ["color", "shape", "number"]
    for t in range(1, N_TRIALS + 1):
        block = (t - 1) // BLOCK + 1
        rule = order[block - 1]
        prev = order[block - 2] if block > 1 else rule
        rows.append(
            {
                "trial_number": str(t),
                "block": str(block),
                "trial_in_block": str((t - 1) % BLOCK + 1),
                "rule_shift": "1" if (block > 1 and (t - 1) % BLOCK == 0) else "0",
                "hidden_rule": rule,
                "previous_hidden_rule": prev,
                "lure_rule": "",
                "old_rule_lure": "0",
            }
        )
    return rows


def synthetic_stream() -> List[PublicStreamRow]:
    """A worst-case fixated LLM: it answers 'color' on every trial.
    최악의 고착 LLM: 모든 trial에서 'color'만 답한다."""
    return [
        PublicStreamRow(
            trial_number=t,
            prompt=f"synthetic card prompt {t}",
            raw_response="color",
            parsed_choice="color",
            ambiguous=False,
        )
        for t in range(1, N_TRIALS + 1)
    ]


def evaluator_from(rows: List[Dict[str, str]]) -> Evaluator:
    """Write schedule rows to a temp CSV and load an Evaluator, matching
    the production path (evaluators are always file-backed).
    일정을 임시 CSV로 저장한 뒤 Evaluator를 로드한다. 운영 경로와 동일하게
    평가기는 항상 파일 기반으로 만든다."""
    tmp = Path(tempfile.mkstemp(suffix=".csv")[1])
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Evaluator(tmp)


def fresh_controllers() -> Dict[str, object]:
    """One fresh instance of every feedback-free controller under test.
    테스트 대상 feedback-free 컨트롤러들의 새 인스턴스."""
    return {
        "passthrough": PassthroughController(),
        "trajectory_only": TrajectoryOnlyController(),
        "yoked_random": YokedRandomController(intervention_trials={5, 17, 29}, seed=1234),
    }


# ---------------------------------------------------------------------------
# Test 1 — ground-truth invariance / 정답 불변성
# ---------------------------------------------------------------------------

def test_ground_truth_invariance() -> None:
    """Changing trial t's ground truth must not change any final choice
    up to and including trial t (feedback for t arrives only after t's
    choice is frozen; earlier trials are untouched).
    trial t의 ground truth를 바꿔도 t까지의(당 trial 포함) 최종 선택은
    변하면 안 된다 (t의 피드백은 t의 선택이 동결된 뒤에야 도착하고, 그
    이전 trial들은 건드리지 않았으므로)."""
    schedule = synthetic_schedule()
    stream = synthetic_stream()
    baseline = run_replay(RuleBlindFullController(), stream, evaluator_from(schedule))
    base_choices = [r.final_choice for r in baseline.records]

    for t in range(1, N_TRIALS + 1):
        mutated = [dict(row) for row in schedule]
        current = mutated[t - 1]["hidden_rule"]
        # Replace with a different dimension. / 다른 차원으로 교체.
        current_idx = RULES.index(current)
        mutated[t - 1]["hidden_rule"] = RULES[(current_idx + 1) % len(RULES)]

        run = run_replay(RuleBlindFullController(), stream, evaluator_from(mutated))
        got = [r.final_choice for r in run.records][:t]
        assert got == base_choices[:t], (
            f"leak: final choices up to trial {t} changed when trial {t}'s "
            f"ground truth changed / 누출: trial {t}의 ground truth 변경이 "
            f"trial {t} 이전(포함)의 최종 선택을 바꿈"
        )


# ---------------------------------------------------------------------------
# Test 2 — shuffle invariance (feedback-free) / 셔플 불변성
# ---------------------------------------------------------------------------

def test_shuffle_invariance_feedback_free() -> None:
    """For feedback-free controllers, shuffling the ENTIRE ground-truth
    schedule must leave every output identical: no information channel
    from ground truth into these controllers may exist at all.
    feedback-free 컨트롤러에서는 ground truth 일정 전체를 섞어도 모든
    출력이 동일해야 한다: 이 컨트롤러들로 통하는 ground truth 정보 채널이
    아예 존재하지 않아야 하기 때문이다."""
    schedule = synthetic_schedule()
    shuffled = [dict(row) for row in schedule]
    rng = random.Random(42)
    rules = [row["hidden_rule"] for row in shuffled]
    rng.shuffle(rules)
    for row, rule in zip(shuffled, rules):
        row["hidden_rule"] = rule

    stream = synthetic_stream()
    for name in fresh_controllers():
        run_a = run_replay(fresh_controllers()[name], stream, evaluator_from(schedule))
        run_b = run_replay(fresh_controllers()[name], stream, evaluator_from(shuffled))
        choices_a = [r.final_choice for r in run_a.records]
        choices_b = [r.final_choice for r in run_b.records]
        assert choices_a == choices_b, (
            f"leak: feedback-free controller '{name}' output changed under "
            f"ground-truth shuffle / 누출: feedback-free 컨트롤러 '{name}'의 "
            f"출력이 ground truth 셔플에 반응함"
        )


# ---------------------------------------------------------------------------
# Test 3 — feedback ordering / 피드백 순서
# ---------------------------------------------------------------------------

def test_feedback_ordering() -> None:
    """In feedback-aware runs the per-trial call order must be exactly
    decide(t) -> score(t) -> feedback(t) -> decide(t+1): correctness may
    influence behaviour only from the NEXT trial onward.
    feedback-aware 실행의 trial별 호출 순서는 정확히
    decide(t) -> score(t) -> feedback(t) -> decide(t+1)이어야 한다: 정오는
    '다음' trial부터만 행동에 영향을 줄 수 있다."""
    schedule = synthetic_schedule()
    result = run_replay(RuleBlindFullController(), synthetic_stream(), evaluator_from(schedule))

    expected = []
    for t in range(1, N_TRIALS + 1):
        expected.extend([("decide", t), ("score", t), ("feedback", t)])
    assert result.call_log == expected, (
        "leak: harness call order violates freeze-before-feedback / 누출: "
        "harness 호출 순서가 '동결 후 피드백' 규약을 위반함"
    )


# ---------------------------------------------------------------------------
# Standalone runner / 단독 실행기
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        ("ground-truth invariance / 정답 불변성", test_ground_truth_invariance),
        ("shuffle invariance / 셔플 불변성", test_shuffle_invariance_feedback_free),
        ("feedback ordering / 피드백 순서", test_feedback_ordering),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name}\n      {exc}")
    if failed:
        print(f"\n{failed} test(s) failed / 실패")
        return 1
    print("\nall leak-prevention tests passed / 누출 방지 테스트 전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
