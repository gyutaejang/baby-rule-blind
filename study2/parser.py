"""Frozen response parser for Study 2 (plan v2.0 §5).
Study 2용 동결된 응답 파서 (계획 v2.0 5절).

Rules (frozen) / 규칙 (동결):
- Case-insensitive word-boundary match of dimension synonyms — the
  archived study's variant table, reused verbatim.
  차원 동의어의 대소문자 무시 단어 경계 일치 — 보관 연구의 변형 표를
  그대로 재사용.
- The dimension whose synonym appears at the EARLIEST position wins; if
  two dimensions tie at the same earliest position, or nothing matches,
  the parse is "" and ambiguous_response = 1.
  동의어가 '가장 앞'에 나타난 차원을 채택; 최초 위치 동률이거나 일치가
  없으면 ""이며 ambiguous_response = 1.
- "" always passes through supervisors unchanged.
  ""는 항상 감독자를 그대로 통과한다.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple

# Verbatim from the archived study (llm_wcst_benchmark.py).
# 보관 연구(llm_wcst_benchmark.py)의 표를 그대로 사용.
DIMENSION_VARIANTS: Dict[str, Tuple[str, ...]] = {
    "color": ("color", "colour", "hue"),
    "shape": ("shape", "form"),
    "number": ("number", "count", "quantity", "numerosity", "amount"),
}


def parse_dimension_choice(response: str) -> Tuple[str, int]:
    """Return (parsed_choice, ambiguous_flag). / (파싱 결과, 모호 플래그)."""
    text = (response or "").strip().lower()
    if not text:
        return "", 1

    # Earliest match position per dimension. / 차원별 최초 일치 위치.
    earliest: Dict[str, int] = {}
    for dimension, variants in DIMENSION_VARIANTS.items():
        positions = []
        for term in variants:
            m = re.search(rf"\b{re.escape(term)}\b", text)
            if m:
                positions.append(m.start())
        if positions:
            earliest[dimension] = min(positions)

    if not earliest:
        return "", 1
    best = min(earliest.values())
    winners = [d for d, pos in earliest.items() if pos == best]
    if len(winners) != 1:
        return "", 1
    return winners[0], 0
