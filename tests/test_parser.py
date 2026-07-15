"""Parser fixtures (plan v2.0 §5, parser v2) — part of the gate.
파서 fixture (계획 v2.0 5절, 파서 2판) — 게이트의 일부.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from study2.parser import parse_dimension_choice  # noqa: E402

# (response, expected_choice, expected_ambiguous)
FIXTURES = [
    # Bare answers / 단답.
    ("color", "color", 0),
    ("Shape", "shape", 0),
    ("  number  ", "number", 0),
    # Synonyms / 동의어.
    ("I would sort by hue.", "color", 0),
    ("Form.", "shape", 0),
    ("The count.", "number", 0),
    # Deliberation with final marker — the v2 motivating case.
    # 숙고 + 최종 marker — v2의 동기 사례.
    ("I considered color, but my final choice is shape.", "shape", 0),
    ("Color seems likely; however, I choose number.", "number", 0),
    ("Answer: colour", "color", 0),
    # Correction: LAST marker wins. / 정정: 마지막 marker 채택.
    ("My choice is color. Actually, my final answer is shape.", "shape", 0),
    # Marker with no dimension after -> ambiguous.
    # marker 뒤 차원 없음 -> 모호.
    ("My final choice is the obvious one.", "", 1),
    # No marker, multiple dimensions -> ambiguous.
    # marker 없음 + 복수 차원 -> 모호.
    ("It could be color or shape.", "", 1),
    # No marker, no dimension -> ambiguous. / 차원 없음 -> 모호.
    ("I am not sure at all.", "", 1),
    ("", "", 1),
    # Word boundary: no substring false positives.
    # 단어 경계: 부분 문자열 오탐 없음.
    ("The colorful discount!", "", 1),
    # Unique dimension in a long sentence, no marker.
    # marker 없는 장문의 유일 차원.
    ("Given the card, matching on the number dimension makes sense.", "number", 0),
]


def test_parser_fixtures() -> None:
    for response, expected_choice, expected_ambiguous in FIXTURES:
        choice, ambiguous = parse_dimension_choice(response)
        assert (choice, ambiguous) == (expected_choice, expected_ambiguous), (
            f"{response!r} -> {(choice, ambiguous)}, expected "
            f"{(expected_choice, expected_ambiguous)}"
        )


def main() -> int:
    try:
        test_parser_fixtures()
        print(f"PASS  parser fixtures ({len(FIXTURES)} cases) / 파서 fixture")
    except AssertionError as exc:
        print(f"FAIL  parser fixtures\n      {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
