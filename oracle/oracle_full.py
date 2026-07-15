"""Condition 8 — OracleFull: oracle-assisted policy reference (corrected).
조건 8 — OracleFull: oracle 보조 정책 참조 (교정판). 상한선이 아니다(이론적 상한 = 1.0).

This is a CLEAN REIMPLEMENTATION of the withdrawn Baby40 controller's
*intended* policy, with its known implementation bugs fixed. It is the
only component besides the Evaluator that may read ground truth, which is
why it lives OUTSIDE the controller/ package (whose CI gate bans
ground-truth tokens). Per ANALYSIS_PLAN.md §3 it appears only as a
oracle-assisted policy reference in the appendix (NOT a ceiling; theoretical ceiling = 1.0) and is never evidence for the main
hypotheses.

철회된 Baby40 컨트롤러가 '의도했던' 정책을, 알려진 구현 버그를 고쳐서
깨끗하게 재구현한 것이다. Evaluator 외에 ground truth를 읽을 수 있는
유일한 구성요소이며, 그래서 (금지어 CI가 걸린) controller/ 패키지 바깥에
둔다. ANALYSIS_PLAN.md 3절에 따라 부록의 oracle 보조 정책 참조로만 쓰이고(상한선 아님) 주 가설의
근거로는 절대 사용되지 않는다.

Fixes relative to the original Baby40 / 원본 Baby40 대비 수정 사항:

1. First-shift window dead code / first-shift window 죽은 코드:
   the original incremented its shift counter before computing the shift
   number, so the `shift_number == 1` branch never executed and the
   configured first-shift window (2 in Baby40, 4 in Baby42) was silently
   replaced by the default (3). Here the window length per shift is
   computed correctly and actually applied.
   원본은 shift 번호 계산 전에 카운터를 먼저 증가시켜 `shift_number == 1`
   분기가 절대 실행되지 않았고, 설정된 first-shift window(Baby40은 2,
   Baby42는 4)가 조용히 기본값 3으로 대체되었다. 여기서는 전환별 window
   길이를 올바르게 계산해 실제로 적용한다.

2. No spurious window on trial 1 / trial 1의 허위 window 제거:
   the original opened a veto window on the very first trial although no
   shift had occurred. Here windows open only on real shifts.
   원본은 전환이 없었던 첫 trial에도 veto window를 열었다. 여기서는 실제
   전환에서만 window가 열린다.

3. Single tie-break policy, stated openly / 동점 해소 정책 단일화·명시:
   the original broke remap ties toward the true current rule while the
   paper described the controller as feedback-free. The oracle version
   remaps DIRECTLY to the true rule — the defining oracle assist —
   and says so, instead of hiding the oracle inside a tie-break.
   원본은 논문에서 feedback-free라 기술하면서 remap 동점을 정답 규칙
   쪽으로 해소했다. oracle 판은 정답 규칙으로 '직접' remap한다 — 그것이
   oracle 보조의 정의다 — 그리고 그 사실을 동점 해소 속에 숨기지 않고 명시한다.

4. Productive-interruption bookkeeping removed / productive 계산 제거:
   the original computed it twice with different definitions. Here it is
   computed once, in the harness, from the plan §6 definition, for every
   condition identically.
   원본은 서로 다른 정의로 두 번 계산했다. 여기서는 harness가 계획 6절의
   정의로, 모든 조건에 동일하게, 한 번만 계산한다.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from controller.base import RULES, PublicTrial, RuleBlindController


class OracleFullController(RuleBlindController):
    """Ceiling supervisor with full ground-truth access.
    ground truth 전체에 접근하는 oracle 보조 정책 참조 감독자(상한선 아님)."""

    feedback_aware = False  # needs no feedback: it already knows everything
    #                         피드백이 필요 없다: 이미 모든 것을 알고 있다.

    def __init__(
        self,
        ground_truth_path: Path,
        veto_window: int = 3,
        first_shift_veto_window: int = 2,
        stuck_streak_to_rescue: int = 3,
    ) -> None:
        # The intended Baby40 parameters, now actually effective.
        # Baby40이 의도했던 파라미터 — 이제 실제로 효력을 가진다.
        self.veto_window = veto_window
        self.first_shift_veto_window = first_shift_veto_window

        # Outside any window, this many consecutive wrong raw choices of
        # the same dimension trigger a rescue remap (the corrected analog
        # of Baby40's stuckness override, using oracle knowledge).
        # window 밖에서 같은 차원의 오답 원선택이 이만큼 연속되면 rescue
        # remap을 발동한다 (Baby40 stuckness override의 교정판, oracle
        # 지식 사용).
        self.stuck_streak_to_rescue = stuck_streak_to_rescue

        # Load the schedule: trial_number -> (rule, previous rule, shift).
        # 일정 로드: trial 번호 -> (규칙, 이전 규칙, 전환 여부).
        self._rule: Dict[int, str] = {}
        self._prev_rule: Dict[int, str] = {}
        self._is_shift: Dict[int, bool] = {}
        with open(ground_truth_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = int(row["trial_number"])
                self._rule[t] = row["hidden_rule"]
                self._prev_rule[t] = row["previous_hidden_rule"]
                self._is_shift[t] = row["rule_shift"] == "1"

        # Number of shifts seen so far and the window countdown.
        # 지금까지 본 전환 수와 window 카운트다운.
        self._shift_count = 0
        self._window_remaining = 0

        # Consecutive identical wrong raw choices (for the rescue path).
        # 동일 오답 원선택의 연속 횟수 (rescue 경로용).
        self._wrong_streak_choice = ""
        self._wrong_streak = 0

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        t = public_trial.trial_number
        true_rule = self._rule[t]
        prev_rule = self._prev_rule[t]

        # FIX 1+2: open a window only on a real shift, and pick the
        # window length by the true shift ordinal computed BEFORE any
        # counter mutation.
        # 수정 1+2: 실제 전환에서만 window를 열고, 카운터 변경 '이전'에
        # 계산한 전환 순번으로 window 길이를 고른다.
        if self._is_shift[t]:
            self._shift_count += 1
            self._window_remaining = (
                self.first_shift_veto_window if self._shift_count == 1 else self.veto_window
            )

        final_choice = raw_choice
        intervene = False

        # Window intervention: veto true perseveration (the raw choice is
        # exactly the outdated rule) while the window is open.
        # window 개입: window가 열린 동안 원선택이 정확히 낡은 규칙인
        # 진짜 고착만 veto한다.
        if (
            self._window_remaining > 0
            and raw_choice in RULES
            and raw_choice == prev_rule
            and raw_choice != true_rule
        ):
            intervene = True

        # Rescue intervention outside windows: repeated identical wrong
        # choices (oracle sees correctness directly).
        # window 밖 rescue 개입: 동일 오답 선택의 반복 (oracle은 정오를
        # 직접 본다).
        if raw_choice in RULES and raw_choice != true_rule:
            if raw_choice == self._wrong_streak_choice:
                self._wrong_streak += 1
            else:
                self._wrong_streak_choice = raw_choice
                self._wrong_streak = 1
            if self._wrong_streak >= self.stuck_streak_to_rescue:
                intervene = True
        else:
            self._wrong_streak_choice = ""
            self._wrong_streak = 0

        if intervene:
            # FIX 3: the oracle-assisted reference remaps directly to the true rule and is
            # documented as doing so.
            # 수정 3: oracle 보조 참조는 정답 규칙으로 직접 remap하며, 그렇게 한다고
            # 명시한다.
            final_choice = true_rule
            self._wrong_streak_choice = ""
            self._wrong_streak = 0

        if self._window_remaining > 0:
            self._window_remaining -= 1

        return final_choice
