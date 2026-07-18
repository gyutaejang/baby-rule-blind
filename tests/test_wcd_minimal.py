"""WCD-minimal policy tests (Study 2b) — hand-worked fixtures.
WCD-minimal 정책 테스트 (Study 2b) — 수작업 fixture 기반.

Verifies the frozen scaffold semantics against hand calculations:
WAIT (no switch below the error-streak threshold), CONSIDER (decay/clip
score arithmetic), DISCRIMINATE (margin-gated switch with deterministic
tie-breaking), ACT (budgeted steering, unparsable pass-through), plus
the freeze-before-feedback contract under the replay harness.

동결된 비계 의미론을 수작업 계산과 대조해 검증한다: WAIT(오류 연속
문턱 미만이면 전환 없음), CONSIDER(감쇠·clip 점수 산술), DISCRIMINATE
(마진 게이트 전환과 결정론적 동점 해소), ACT(예산 내 유도, 파싱 불가
통과), 그리고 replay harness 하의 동결-후-피드백 규약.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import WCDMinimalController  # noqa: E402
from controller.base import PublicTrial  # noqa: E402
from replay import run_replay, summarize  # noqa: E402
from tests.test_leak_prevention import (  # noqa: E402
    evaluator_from,
    synthetic_schedule,
    synthetic_stream,
)


def trial(n: int) -> PublicTrial:
    return PublicTrial(trial_number=n, prompt=f"synthetic card prompt {n}")


# ---------------------------------------------------------------------------
# 1. Adoption: pass-through before the first correct outcome; the first
#    success installs the hypothesis.
# 1. 채택: 첫 정답 전에는 통과; 첫 성공이 가설을 설치한다.
# ---------------------------------------------------------------------------

def test_adoption_and_passthrough_before_first_success() -> None:
    c = WCDMinimalController()
    assert c.decide(trial(1), "shape") == "shape"  # no hypothesis yet / 아직 가설 없음
    c.observe_feedback(False)
    assert c.hypothesis == ""
    assert c.decide(trial(2), "color") == "color"
    c.observe_feedback(True)
    assert c.hypothesis == "color"
    # Now steering is active. / 이제 유도가 활성화된다.
    assert c.decide(trial(3), "number") == "color"


# ---------------------------------------------------------------------------
# 2. WAIT + DISCRIMINATE: hand-worked switch sequence (decay=1, margin=1,
#    wait=2). A lead EQUAL to the margin must NOT switch (strict >).
# 2. WAIT + DISCRIMINATE: 수작업 전환 시퀀스 (decay=1, margin=1, wait=2).
#    마진과 '같은' 우세로는 전환 금지 (엄격 초과).
# ---------------------------------------------------------------------------

def test_wait_then_margin_gated_switch() -> None:
    c = WCDMinimalController(decay=1.0, switch_margin=1.0, wait_threshold=2)

    c.decide(trial(1), "color")
    c.observe_feedback(True)   # color=1, hypothesis=color / 가설 채택
    assert c.hypothesis == "color" and c.scores["color"] == 1.0

    c.decide(trial(2), "color")
    c.observe_feedback(False)  # color=0, streak=1 -> WAIT holds / 보류
    assert c.hypothesis == "color" and c.error_streak == 1

    c.decide(trial(3), "color")
    c.observe_feedback(False)  # color=-1, streak=2; lead 0-(-1)=1, not >1 / 전환 없음
    assert c.hypothesis == "color"

    c.decide(trial(4), "color")
    c.observe_feedback(False)  # color=-2, streak=3; lead 2 > 1 -> switch / 전환
    assert c.hypothesis == "shape"  # tie shape/number -> RULES order / 동점은 RULES 순서
    assert c.error_streak == 0


# ---------------------------------------------------------------------------
# 3. CONSIDER: decay and clip arithmetic against hand calculations.
# 3. CONSIDER: 감쇠·clip 산술을 수작업 계산과 대조.
# ---------------------------------------------------------------------------

def test_decay_arithmetic() -> None:
    c = WCDMinimalController(decay=0.5)
    c.decide(trial(1), "color")
    c.observe_feedback(True)   # 0*0.5+1 = 1.0
    assert c.scores["color"] == 1.0
    c.decide(trial(2), "color")
    c.observe_feedback(True)   # 1*0.5+1 = 1.5
    assert c.scores["color"] == 1.5
    c.decide(trial(3), "color")
    c.observe_feedback(False)  # 1.5*0.5-1 = -0.25
    assert c.scores["color"] == -0.25


def test_score_clip() -> None:
    c = WCDMinimalController(decay=1.0, score_clip=2.0)
    for t in range(1, 6):
        c.decide(trial(t), "color")
        c.observe_feedback(True)
    assert c.scores["color"] == 2.0  # clipped / clip 적용


# ---------------------------------------------------------------------------
# 4. ACT: hard budget on the worst-case fixated stream; unparsable
#    choices pass through and carry no attributable outcome.
# 4. ACT: 최악의 고착 스트림에서 하드 예산; 파싱 불가 선택은 통과하고
#    정오가 귀속되지 않는다.
# ---------------------------------------------------------------------------

def test_hard_budget_on_fixated_stream() -> None:
    evaluator = evaluator_from(synthetic_schedule())
    result = run_replay(WCDMinimalController(), synthetic_stream(), evaluator)
    s = summarize(result)
    assert s["intervention_count"] <= 9.0


def test_unparsable_passthrough_and_noop_feedback() -> None:
    c = WCDMinimalController()
    c.decide(trial(1), "color")
    c.observe_feedback(True)  # hypothesis=color / 가설 설치
    before = dict(c.scores)
    assert c.decide(trial(2), "") == ""  # never remap unparsable / 파싱 불가는 remap 금지
    c.observe_feedback(False)
    assert c.scores == before and c.error_streak == 0


# ---------------------------------------------------------------------------
# 5. Tie-breaking: equal scores resolve by least-recently-tried, then
#    fixed RULES order — deterministic, outcome-independent inputs only.
# 5. 동점 해소: 같은 점수는 최장 미시도 -> RULES 고정 순서 — 결정론적이며
#    결과 무관 입력만 사용.
# ---------------------------------------------------------------------------

def test_tiebreak_rules_order_on_tied_alternatives() -> None:
    c = WCDMinimalController(decay=1.0, switch_margin=0.0, wait_threshold=1)
    c.decide(trial(1), "color")
    c.observe_feedback(True)   # color=1, hypothesis=color
    c.decide(trial(2), "color")
    c.observe_feedback(False)  # color=0, streak=1; lead 0, not > 0 -> hold / 보류
    assert c.hypothesis == "color"
    c.decide(trial(3), "color")
    c.observe_feedback(False)  # color=-1; shape/number tied at 0, both untried
                               # -> lead 1 > 0, tie resolves by RULES order
                               # / 동점은 RULES 순서로 해소
    assert c.hypothesis == "shape"


# ---------------------------------------------------------------------------
# 6. Contract: decide precedes feedback on every trial under the harness.
# 6. 규약: harness 하에서 모든 trial은 decide가 feedback에 선행한다.
# ---------------------------------------------------------------------------

def test_freeze_before_feedback_ordering() -> None:
    evaluator = evaluator_from(synthetic_schedule())
    result = run_replay(WCDMinimalController(), synthetic_stream(), evaluator)
    by_trial: dict = {}
    for event, t in result.call_log:
        by_trial.setdefault(t, []).append(event)
    for t, events in by_trial.items():
        assert events.index("decide") < events.index("feedback"), t


# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        ("adoption + pre-success passthrough / 채택·성공 전 통과",
         test_adoption_and_passthrough_before_first_success),
        ("WAIT + margin-gated switch / 대기·마진 전환", test_wait_then_margin_gated_switch),
        ("decay arithmetic / 감쇠 산술", test_decay_arithmetic),
        ("score clip / 점수 clip", test_score_clip),
        ("hard budget / 하드 예산", test_hard_budget_on_fixated_stream),
        ("unparsable no-op / 파싱 불가 무시", test_unparsable_passthrough_and_noop_feedback),
        ("tie-break determinism / 동점 결정론", test_tiebreak_rules_order_on_tied_alternatives),
        ("freeze-before-feedback / 동결 후 피드백", test_freeze_before_feedback_ordering),
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
    print("\nall WCD-minimal tests passed / WCD-minimal 테스트 전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
