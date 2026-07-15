"""Condition 4 — TrajectoryOnly-FeedbackFree (v0, exploratory).
조건 4 — TrajectoryOnly-FeedbackFree (v0, 탐색 단계).

The strict test of the original hypothesis: this controller sees neither
which dimension is rewarded nor whether any choice was correct. Its ONLY
input is the raw-choice trajectory itself. It can therefore detect
fixation (the same choice repeated many times) but can never know whether
that fixation is currently succeeding or failing.

원가설의 엄격한 검증: 이 컨트롤러는 어떤 차원이 보상되는지도, 어떤 선택이
정답이었는지도 보지 못한다. 유일한 입력은 원선택 궤적 자체다. 따라서
고착(같은 선택의 장기 반복)은 탐지할 수 있지만, 그 고착이 지금 성공 중인지
실패 중인지는 원리적으로 알 수 없다.

v0 policy (parameters are exploratory until the study2-freeze tag):
if the same raw choice has repeated `stuck_threshold` times in a row,
override this trial to the alternative dimension that was chosen least
recently, then require a cooldown before intervening again.

v0 정책 (파라미터는 study2-freeze 태그 전까지 탐색적으로 조정 가능):
같은 원선택이 연속 `stuck_threshold`회 반복되면 이번 trial을 가장 오랫동안
선택되지 않은 대안 차원으로 바꾸고, 다음 개입까지 쿨다운을 둔다.
"""

from __future__ import annotations

from controller.base import RULES, PublicTrial, RuleBlindController


class TrajectoryOnlyController(RuleBlindController):
    """Feedback-free fixation breaker. / 피드백 없는 고착 차단기."""

    feedback_aware = False

    def __init__(self, stuck_threshold: int = 6, cooldown: int = 4) -> None:
        # How many identical consecutive raw choices count as fixation.
        # Without outcome information this must be conservative: breaking
        # a streak that was actually correct is pure damage.
        # 몇 번의 동일 연속 원선택을 고착으로 볼지. 정오 정보가 없으므로
        # 보수적이어야 한다: 실제로는 정답이던 연속을 끊으면 순수한 손해다.
        self.stuck_threshold = stuck_threshold

        # Minimum number of trials between interventions, so one long
        # fixation cannot trigger a burst of overrides.
        # 개입과 개입 사이의 최소 trial 간격. 하나의 긴 고착이 연속 개입
        # 폭주로 이어지지 않게 한다.
        self.cooldown = cooldown

        # Consecutive-repeat counter for the current raw choice.
        # 현재 원선택의 연속 반복 카운터.
        self._streak_choice: str = ""
        self._streak_length: int = 0

        # Trials remaining before the next intervention is allowed.
        # 다음 개입이 허용되기까지 남은 trial 수.
        self._cooldown_remaining: int = 0

        # trial_number at which each dimension was last chosen (raw or
        # final), used to pick the least-recently-used alternative.
        # 각 차원이 마지막으로 선택된 trial 번호(원선택·최종선택 모두 반영).
        # 가장 오래 쓰이지 않은 대안을 고르는 데 사용한다.
        self._last_used = {rule: 0 for rule in RULES}

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        # Track the repeat streak of the raw trajectory.
        # 원선택 궤적의 반복 연속을 추적한다.
        if raw_choice and raw_choice == self._streak_choice:
            self._streak_length += 1
        else:
            self._streak_choice = raw_choice
            self._streak_length = 1 if raw_choice else 0

        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

        final_choice = raw_choice

        # Intervene only on a long fixation, outside the cooldown, and
        # only when the raw choice is a valid dimension.
        # 긴 고착일 때만, 쿨다운 밖에서만, 원선택이 유효한 차원일 때만
        # 개입한다.
        if (
            raw_choice in RULES
            and self._streak_length >= self.stuck_threshold
            and self._cooldown_remaining == 0
        ):
            alternatives = [r for r in RULES if r != raw_choice]
            # Least-recently-used alternative; ties break by the fixed
            # RULES order, which is public and outcome-independent.
            # 가장 오래 쓰이지 않은 대안 선택. 동점은 공개적이고 결과와
            # 무관한 RULES 고정 순서로 해소한다.
            final_choice = min(alternatives, key=lambda r: (self._last_used[r], RULES.index(r)))
            self._cooldown_remaining = self.cooldown
            # The forced switch resets the streak measurement.
            # 강제 전환은 연속 측정을 초기화한다.
            self._streak_choice = final_choice
            self._streak_length = 1

        if raw_choice in RULES:
            self._last_used[raw_choice] = public_trial.trial_number
        if final_choice in RULES:
            self._last_used[final_choice] = public_trial.trial_number

        return final_choice
