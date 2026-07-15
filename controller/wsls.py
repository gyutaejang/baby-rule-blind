"""Information-matched baselines — win-stay/lose-shift supervisors.
정보량 동일 기준선 — win-stay/lose-shift 감독자.

Amendment B §11.2: the Full condition receives per-trial outcome
information that RawLLM does not, so Full − RawLLM confounds algorithm
quality with information quantity. These baselines receive EXACTLY the
same information (post-freeze outcome of each final choice) and apply
the classic win-stay/lose-shift heuristic.

수정안 B 11.2절: Full 조건은 RawLLM이 받지 못하는 trial별 정오 정보를
받으므로, Full − RawLLM은 알고리즘 품질과 정보량 효과를 혼동한다. 이
기준선들은 '정확히 같은 정보'(동결 후 각 최종 선택의 정오)를 받아 고전적
win-stay/lose-shift 휴리스틱을 적용한다.

Frozen policy (§11.2) / 동결된 정책 (11.2절):
- belief = dimension of the most recent CORRECT final choice.
  belief = 가장 최근 정답을 낸 최종 선택의 차원.
- While a belief exists, override any raw choice != belief.
  belief가 있는 동안 raw != belief면 override.
- When the belief dimension produces an incorrect outcome, clear the
  belief and set the shift target to the least-recently-tried other
  dimension. While no belief exists, override toward the shift target.
  belief 차원이 오답을 내면 belief를 지우고 가장 오래 시도 안 된 다른
  차원을 shift 대상으로 설정. belief가 없는 동안 shift 대상으로 override.
- Budgeted variant: all overrides stop when the hard per-repetition
  budget is exhausted. Unlimited variant (budget = None) is the "player
  regime" descriptive reference and is never a hypothesis-test target.
  예산 변형: 하드 repetition 예산 소진 시 모든 override 중지. 무제한
  변형(budget = None)은 "선수 체제" 기술 참조이며 가설 검정 대상이
  아니다.
"""

from __future__ import annotations

from typing import Optional

from controller.base import RULES, FeedbackAwareController, PublicTrial

# NOTE: co-primary condition (plan v2.0 §3). / 공동 주 조건 (계획 3절).


class WSLSController(FeedbackAwareController):
    """Win-stay/lose-shift supervisor. / win-stay/lose-shift 감독자."""

    def __init__(self, max_interventions_per_rep: Optional[int] = 9) -> None:
        # None = unlimited (player-regime reference); int = hard budget,
        # matched to RuleBlindFull's budget for the budgeted condition.
        # None = 무제한(선수 체제 참조); 정수 = 하드 예산 — 예산 조건에서는
        # RuleBlindFull의 예산과 일치시킨다.
        self.max_interventions_per_rep = max_interventions_per_rep
        self._interventions_made = 0

        # Current belief and, when belief is empty, the shift target.
        # 현재 belief와, belief가 없을 때의 shift 대상.
        self._belief: str = ""
        self._shift_target: str = ""

        # Last-tried trial number per dimension (final choices), for the
        # outcome-independent least-recently-tried shift rule.
        # 차원별 마지막 시도 trial 번호(최종 선택 기준) — 결과와 무관한
        # 최장 미시도 shift 규칙에 사용.
        self._last_tried = {rule: 0 for rule in RULES}

        self._pending_choice: str = ""
        self._trial_number: int = 0

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        self._trial_number = public_trial.trial_number
        final_choice = raw_choice

        budget_left = (
            self.max_interventions_per_rep is None
            or self._interventions_made < self.max_interventions_per_rep
        )

        # Target = belief if present, else the pending shift target.
        # 대상 = belief가 있으면 belief, 없으면 대기 중인 shift 대상.
        target = self._belief or self._shift_target
        if budget_left and raw_choice in RULES and target and raw_choice != target:
            final_choice = target

        if final_choice != raw_choice:
            self._interventions_made += 1
        if final_choice in RULES:
            self._last_tried[final_choice] = self._trial_number

        self._pending_choice = final_choice
        return final_choice

    def observe_feedback(self, correct: bool) -> None:
        choice = self._pending_choice
        self._pending_choice = ""
        if choice not in RULES:
            return
        if correct:
            # Win-stay: this dimension becomes (or stays) the belief.
            # win-stay: 이 차원이 belief가 된다(유지된다).
            self._belief = choice
            self._shift_target = ""
        elif choice == self._belief or (not self._belief and choice == self._shift_target):
            # Lose-shift: the followed dimension failed — shift to the
            # least-recently-tried other dimension.
            # lose-shift: 따르던 차원이 실패 — 가장 오래 시도 안 된 다른
            # 차원으로 이동.
            others = [r for r in RULES if r != choice]
            self._shift_target = min(others, key=lambda r: (self._last_tried[r], RULES.index(r)))
            self._belief = ""
