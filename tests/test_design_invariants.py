"""Design-invariant tests (plan v2.0 §11) — part of the mandatory gate.
설계 불변식 테스트 (계획 v2.0 11절) — 필수 게이트의 일부.

Covers what the leak tests do not: hard-budget enforcement, the WSLS
policy against a hand-worked fixture, metric definitions against hand
calculations, schedule-generator invariants over many seeds, and yoked
timing/count fidelity.

누출 테스트가 다루지 않는 것을 검증한다: 하드 예산 강제, 수작업 fixture에
대한 WSLS 정책, 수작업 계산에 대한 지표 정의, 다수 시드에 대한 일정
생성기 불변식, yoked 시점·횟수 일치.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import RuleBlindFullController, WSLSController  # noqa: E402
from controller.yoked_random import YokedRandomController  # noqa: E402
from replay import PublicStreamRow, run_replay, summarize  # noqa: E402
from scripts.generate_schedules import RULES as SCHED_RULES  # noqa: E402
from scripts.generate_schedules import generate_schedule, partition_blocks  # noqa: E402
from tests.test_leak_prevention import (  # noqa: E402
    evaluator_from,
    synthetic_schedule,
    synthetic_stream,
)


# ---------------------------------------------------------------------------
# 1. Hard budget: Full and WSLS never exceed 9 interventions, even on the
#    worst-case fully fixated stream.
# 1. 하드 예산: 최악의 완전 고착 스트림에서도 Full·WSLS의 개입이 9회를
#    넘지 않는다.
# ---------------------------------------------------------------------------

def test_hard_budget_never_exceeded() -> None:
    ev = evaluator_from(synthetic_schedule())
    for name, controller in [
        ("RuleBlindFull", RuleBlindFullController()),
        ("WSLSBudgeted", WSLSController(max_interventions_per_rep=9)),
    ]:
        result = run_replay(controller, synthetic_stream(), ev)
        n = sum(1 for r in result.records if r.intervened)
        assert n <= 9, f"{name}: {n} interventions > hard budget 9 / 하드 예산 초과"


# ---------------------------------------------------------------------------
# 2. WSLS hand fixture: win-stay then lose-shift on a 6-trial scenario.
# 2. WSLS 수작업 fixture: 6-trial 시나리오의 win-stay/lose-shift.
# ---------------------------------------------------------------------------

def _mini_schedule(rules: List[str]) -> List[dict]:
    rows = []
    prev = rules[0]
    block = 1
    for t, rule in enumerate(rules, start=1):
        if t > 1 and rule != rules[t - 2]:
            block += 1
            prev = rules[t - 2]
        rows.append(
            {
                "trial_number": str(t),
                "block": str(block),
                "trial_in_block": "1",
                "rule_shift": "1" if (t > 1 and rule != rules[t - 2]) else "0",
                "hidden_rule": rule,
                "previous_hidden_rule": prev,
                "lure_rule": "",
                "old_rule_lure": "0",
            }
        )
    return rows


def _stream_of(choices: List[str]) -> List[PublicStreamRow]:
    return [
        PublicStreamRow(
            trial_number=t, prompt=f"p{t}", raw_response=c, parsed_choice=c, ambiguous=False
        )
        for t, c in enumerate(choices, start=1)
    ]


def test_wsls_hand_fixture() -> None:
    # Rules: color x3, then shape x3. Raw: always color.
    # Expected WSLS trace / 기대 궤적:
    #   t1: no belief, no target -> pass "color" -> correct -> belief=color
    #   t2: raw==belief -> pass -> correct
    #   t3: pass -> correct
    #   t4 (rule now shape): raw==belief -> pass -> WRONG -> lose-shift:
    #       belief cleared, target = least-recently-tried of {shape,number}
    #       (neither tried; tie -> RULES order -> shape)
    #   t5: no belief, target=shape, raw=color != shape -> OVERRIDE to
    #       shape -> correct -> belief=shape
    #   t6: raw=color != belief=shape -> OVERRIDE to shape -> correct
    ev = evaluator_from(_mini_schedule(["color"] * 3 + ["shape"] * 3))
    result = run_replay(WSLSController(max_interventions_per_rep=9), _stream_of(["color"] * 6), ev)
    finals = [r.final_choice for r in result.records]
    assert finals == ["color", "color", "color", "color", "shape", "shape"], finals
    assert [r.intervened for r in result.records] == [False] * 4 + [True, True]


# ---------------------------------------------------------------------------
# 3. Metric hand calculations on a constructed record set.
# 3. 구성된 기록에 대한 지표 수작업 계산.
# ---------------------------------------------------------------------------

def test_metric_hand_calculation() -> None:
    # Schedule: color x4 (block 1), shape x4 (block 2). / 일정: color 4 + shape 4.
    schedule = _mini_schedule(["color"] * 4 + ["shape"] * 4)
    ev = evaluator_from(schedule)

    # Raw stream: c c c c | c s c ""(unparsable)
    raw = ["color", "color", "color", "color", "color", "shape", "color", ""]

    # Controller: none (passthrough via WSLS with budget 0 would still
    # act; use a WSLS with budget 0 -> never overrides).
    # 컨트롤러 없음과 동일하게 budget 0의 WSLS 사용 (절대 개입 안 함).
    result = run_replay(WSLSController(max_interventions_per_rep=0), _stream_of(raw), ev)
    s = summarize(result)

    # Hand calculation / 수작업 계산:
    # correct: t1-t4 color/color = 4, t5 color under shape = no,
    #          t6 shape = yes, t7 color = no, t8 "" = no  -> 5/8
    assert abs(s["total_accuracy"] - 5 / 8) < 1e-9
    # prev_rule_error: block 2 trials with final==color & wrong: t5, t7 -> 2
    assert s["prev_rule_error_count"] == 2.0
    # reentry: prev-rule-aligned error AFTER a correct in block 2:
    # t6 correct, then t7 -> exactly 1 (t5 precedes any correct).
    assert s["old_rule_reentry_count"] == 1.0
    # entropy: parsed finals = 6 color, 1 shape (t8 excluded):
    # p=6/7,1/7 -> H = -(6/7)log2(6/7) - (1/7)log2(1/7) ≈ 0.5917
    assert abs(s["choice_entropy"] - 0.5917) < 1e-3
    assert s["unparsable_count"] == 1.0
    # latency: block 2 length 4, first correct at position 2 -> mean 2.0
    assert s["recovery_latency_mean"] == 2.0
    assert s["latency_censored_count"] == 0.0
    # no interventions -> corrective/harmful 0, precision undefined (-1)
    assert s["intervention_count"] == 0.0
    assert s["corrective_override_count"] == 0.0
    assert s["harmful_override_count"] == 0.0
    assert s["intervention_precision"] == -1.0


def test_corrective_and_harmful_attribution() -> None:
    # Schedule: color x4. Raw: shape shape color color.
    # WSLS with budget: t1 pass shape (wrong -> shift target=color? lose
    # shift only fires when the FOLLOWED choice fails; t1 had no
    # belief/target so no attribution -> stays passive), so use a yoked
    # controller with fixed trials to force interventions precisely.
    # 정확한 개입 시점을 강제하기 위해 yoked 컨트롤러 사용.
    schedule = _mini_schedule(["color"] * 4)
    ev = evaluator_from(schedule)
    raw = ["shape", "shape", "color", "color"]
    # Intervene at t2 (raw wrong) and t3 (raw correct); random choice is
    # seeded — find a seed mapping t2->color (corrective) & t3->{not
    # color} (harmful). Seed search is deterministic and frozen here.
    # t2(원선택 오답)와 t3(정답)에 개입. 시드는 결정론적으로 고정.
    seed = next(
        s
        for s in range(1000)
        if random.Random(s).choice(["color", "number"]) == "color"
        and random.Random(s).choice(["color", "number"]) == "color"
    )
    # YokedRandom picks uniformly from the two non-raw dimensions; for
    # t2 raw=shape the alternatives are (color, number), for t3 raw=color
    # they are (shape, number) — the same seed draws in sequence.
    # 같은 시드가 순서대로 추출한다.
    controller = YokedRandomController({2, 3}, seed=seed)
    result = run_replay(controller, _stream_of(raw), ev)
    s = summarize(result)
    t2, t3 = result.records[1], result.records[2]
    assert t2.intervened and t3.intervened
    # Attribution must match the record-level truth exactly.
    # 귀속은 기록 수준의 사실과 정확히 일치해야 한다.
    expected_corrective = sum(
        1 for r in (t2, t3) if not result.raw_correct_by_trial[r.trial_number] and r.correct
    )
    expected_harmful = sum(
        1 for r in (t2, t3) if result.raw_correct_by_trial[r.trial_number] and not r.correct
    )
    assert s["corrective_override_count"] == float(expected_corrective)
    assert s["harmful_override_count"] == float(expected_harmful)
    assert s["net_correction"] == float(expected_corrective - expected_harmful)


# ---------------------------------------------------------------------------
# 4. Schedule generator invariants over 10,000 seeds.
# 4. 일정 생성기 불변식 — 10,000개 시드.
# ---------------------------------------------------------------------------

def test_schedule_invariants_10k() -> None:
    for rep in range(1, 10_001):
        rows = generate_schedule(rep)
        assert len(rows) == 36, f"rep {rep}: {len(rows)} trials"
        # Block lengths within 4-8. / 블록 길이 4-8.
        lengths: dict = {}
        for r in rows:
            lengths[r["block"]] = lengths.get(r["block"], 0) + 1
        assert all(4 <= v <= 8 for v in lengths.values()), f"rep {rep}: {lengths}"
        # No immediate rule repeat across blocks. / 연속 블록 규칙 중복 없음.
        block_rules = []
        for r in rows:
            if not block_rules or r["hidden_rule"] != block_rules[-1][1]:
                if not block_rules or r["rule_shift"] == "1":
                    block_rules.append((r["block"], r["hidden_rule"]))
        for (b1, r1), (b2, r2) in zip(block_rules, block_rules[1:]):
            assert r1 != r2, f"rep {rep}: consecutive rule repeat"
        # Rules valid. / 규칙 유효성.
        assert all(r["hidden_rule"] in SCHED_RULES for r in rows)


def test_partition_direct_10k() -> None:
    for seed in range(10_000):
        lengths = partition_blocks(random.Random(seed))
        assert sum(lengths) == 36
        assert all(4 <= length <= 8 for length in lengths), (seed, lengths)


# ---------------------------------------------------------------------------
# 5. Yoked timing and count fidelity.
# 5. Yoked 시점·횟수 일치.
# ---------------------------------------------------------------------------

def test_yoked_matches_full_schedule() -> None:
    ev = evaluator_from(synthetic_schedule())
    stream = synthetic_stream()
    full = run_replay(RuleBlindFullController(), stream, ev)
    yoked = run_replay(YokedRandomController(full.intervention_trials(), seed=7), stream, ev)
    full_trials = {r.trial_number for r in full.records if r.intervened}
    yoked_trials = {r.trial_number for r in yoked.records if r.intervened}
    assert full_trials == yoked_trials, "yoked timing mismatch / yoked 시점 불일치"


# ---------------------------------------------------------------------------
# Runner / 실행기
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        ("hard budget cap / 하드 예산", test_hard_budget_never_exceeded),
        ("WSLS hand fixture / WSLS 수작업", test_wsls_hand_fixture),
        ("metric hand calc / 지표 수작업", test_metric_hand_calculation),
        ("override attribution / 개입 귀속", test_corrective_and_harmful_attribution),
        ("schedule invariants 10k / 일정 불변식", test_schedule_invariants_10k),
        ("partition direct 10k / 분할 직접 검증", test_partition_direct_10k),
        ("yoked fidelity / yoked 일치", test_yoked_matches_full_schedule),
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
    print("\nall design-invariant tests passed / 설계 불변식 테스트 전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
