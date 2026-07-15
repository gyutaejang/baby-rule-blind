"""Frozen prompt/card generation for Study 2 (plan v2.0 §5–6).
Study 2용 동결된 프롬프트·카드 생성 (계획 v2.0 5–6절).

The prompt template is VERBATIM the archived study's single-turn prompt,
for cross-generation comparability. Card attributes are decorative
context (scoring compares the chosen dimension to the schedule's rule),
generated deterministically from the committed master seed so the full
stimulus sequence is reproducible before any API call.

프롬프트 템플릿은 세대 간 비교 가능성을 위해 보관 연구의 단일 턴
프롬프트를 그대로 사용한다. 카드 속성은 장식적 맥락이며(채점은 선택 차원
대 일정의 규칙 비교), 커밋된 마스터 시드로 결정론적으로 생성되어 API 호출
전에 전체 자극 시퀀스가 재현 가능하다.
"""

from __future__ import annotations

import random
from typing import List

# Distinct offset keeps the card RNG stream independent of the schedule
# RNG stream that uses MASTER_SEED * 1000 + rep.
# 카드 RNG를 일정 RNG(MASTER_SEED * 1000 + rep)와 분리하는 오프셋.
MASTER_SEED = 20260715
CARD_STREAM_OFFSET = 500_000

COLORS = ("red", "green", "blue", "yellow")
SHAPES = ("circle", "square", "triangle", "star")
NUMBERS = (1, 2, 3, 4)

# Verbatim archived template. / 보관 연구 템플릿 그대로.
PROMPT_TEMPLATE = (
    "You are sorting cards. Each card has a color, shape, and number.\n"
    "Sort this card by choosing one dimension: color, shape, or number.\n"
    "Card: {color} {number} {shape}(s).\n"
    "Your choice:"
)


def generate_prompts(rep_index: int, n_trials: int = 36) -> List[str]:
    """Deterministic per-repetition prompt list. / rep별 결정론적 프롬프트."""
    rng = random.Random(MASTER_SEED * 1000 + rep_index + CARD_STREAM_OFFSET)
    prompts = []
    for _ in range(n_trials):
        prompts.append(
            PROMPT_TEMPLATE.format(
                color=rng.choice(COLORS),
                number=rng.choice(NUMBERS),
                shape=rng.choice(SHAPES),
            )
        )
    return prompts
