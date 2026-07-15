"""Condition 5 — YokedRandom placebo control.
조건 5 — YokedRandom 위약 대조.

Per ANALYSIS_PLAN.md, this control intervenes at EXACTLY the same trials
as a reference run of the Full controller on the same stream (yoking),
but replaces the chosen alternative with a seeded-random one. If the Full
condition's benefit came merely from interrupting the LLM at those
moments, YokedRandom will reproduce it; if the benefit requires choosing
a GOOD alternative, YokedRandom will fall short.

ANALYSIS_PLAN.md에 따라, 이 대조 조건은 같은 스트림에 대한 Full 컨트롤러
기준 실행과 '정확히 같은 trial'에서 개입하되(yoking), 선택되는 대안만
시드 고정 무작위로 바꾼다. Full 조건의 이득이 단지 그 시점에 LLM을
가로막는 데서 나온 것이라면 YokedRandom도 이를 재현할 것이고, 좋은 대안의
'선택'이 필요했던 것이라면 YokedRandom은 못 미칠 것이다.

The yoking schedule is derived from the Full run's intervention log —
i.e., from controller behaviour, which is public information.
yoking 일정은 Full 실행의 개입 기록에서 파생된다 — 즉 컨트롤러 행동에서
나온 것이므로 공개 정보다.
"""

from __future__ import annotations

import random
from typing import Set

from controller.base import RULES, PublicTrial, RuleBlindController


class YokedRandomController(RuleBlindController):
    """Intervenes on a fixed schedule with random alternatives.
    고정된 일정에 따라 무작위 대안으로 개입한다."""

    feedback_aware = False

    def __init__(self, intervention_trials: Set[int], seed: int) -> None:
        # Trial numbers at which the reference Full run intervened.
        # 기준 Full 실행이 개입했던 trial 번호들.
        self.intervention_trials = set(intervention_trials)

        # Explicit seed: replay must be exactly reproducible.
        # 명시적 시드: replay는 정확히 재현 가능해야 한다.
        self._rng = random.Random(seed)

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        if public_trial.trial_number in self.intervention_trials and raw_choice in RULES:
            # Same timing as Full, but the alternative is uniform random
            # over the other two dimensions.
            # Full과 같은 시점, 그러나 대안은 나머지 두 차원에 대한
            # 균등 무작위.
            alternatives = [r for r in RULES if r != raw_choice]
            return self._rng.choice(alternatives)
        return raw_choice
