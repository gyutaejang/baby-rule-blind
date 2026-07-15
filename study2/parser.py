"""Frozen response parser for Study 2 (plan v2.0 §5), version 2.
Study 2용 동결된 응답 파서 (계획 v2.0 5절), 2판.

v2 change (pre-pilot-freeze review): earliest-position-only parsing
misreads deliberative long answers ("I considered color, but my final
choice is shape" -> color). v2 gives priority to an explicit
final-answer marker.

v2 변경(파일럿 동결 전 검토 반영): 최초 위치 규칙만으로는 숙고형 장문
응답을 오분류한다("I considered color, but my final choice is shape" ->
color). v2는 명시적 최종 답변 표시를 우선한다.

Frozen rules / 동결 규칙:
1. Case-insensitive word-boundary matching of dimension synonyms (the
   archived study's variant table, verbatim).
   차원 동의어의 대소문자 무시 단어 경계 일치 (보관 연구 표 그대로).
2. If any final-answer MARKER occurs, parse ONLY the text after the LAST
   marker occurrence, taking the earliest-position dimension there; a
   marker with no dimension after it -> ambiguous "".
   최종 답변 MARKER가 있으면 '마지막' marker 이후 텍스트만 파싱하여 그
   구간의 최초 위치 차원을 채택; marker 뒤에 차원이 없으면 모호 "".
3. If no marker: exactly ONE distinct dimension mentioned anywhere ->
   that dimension; zero or two-plus distinct dimensions -> ambiguous "".
   marker가 없으면: 서로 다른 차원이 정확히 하나 언급되면 그 차원; 0개
   또는 2개 이상이면 모호 "".
4. "" always passes through supervisors unchanged.
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

# Final-answer markers, frozen. The LAST occurrence wins so that
# corrections ("...actually, my final answer is...") are honoured.
# 최종 답변 marker(동결). 정정 표현을 존중하기 위해 '마지막' 출현을
# 채택한다.
FINAL_ANSWER_MARKERS: Tuple[str, ...] = (
    "final choice",
    "final answer",
    "my choice is",
    "my answer is",
    "i choose",
    "i pick",
    "i select",
    "i would sort by",
    "i will sort by",
    "sort by",
    "answer:",
    "choice:",
)


def _dimension_positions(text: str) -> Dict[str, int]:
    """Earliest match position per dimension. / 차원별 최초 일치 위치."""
    earliest: Dict[str, int] = {}
    for dimension, variants in DIMENSION_VARIANTS.items():
        positions = []
        for term in variants:
            m = re.search(rf"\b{re.escape(term)}\b", text)
            if m:
                positions.append(m.start())
        if positions:
            earliest[dimension] = min(positions)
    return earliest


def parse_dimension_choice(response: str) -> Tuple[str, int]:
    """Return (parsed_choice, ambiguous_flag). / (파싱 결과, 모호 플래그)."""
    text = (response or "").strip().lower()
    if not text:
        return "", 1

    # Rule 2: last final-answer marker takes priority.
    # 규칙 2: 마지막 최종 답변 marker 우선.
    last_marker_end = -1
    for marker in FINAL_ANSWER_MARKERS:
        idx = text.rfind(marker)
        if idx >= 0:
            last_marker_end = max(last_marker_end, idx + len(marker))
    if last_marker_end >= 0:
        after = text[last_marker_end:]
        positions = _dimension_positions(after)
        if not positions:
            return "", 1
        best = min(positions.values())
        winners = [d for d, pos in positions.items() if pos == best]
        return (winners[0], 0) if len(winners) == 1 else ("", 1)

    # Rule 3: no marker — unique dimension anywhere, else ambiguous.
    # 규칙 3: marker 없음 — 유일 차원이면 채택, 아니면 모호.
    positions = _dimension_positions(text)
    if len(positions) == 1:
        return next(iter(positions)), 0
    return "", 1
