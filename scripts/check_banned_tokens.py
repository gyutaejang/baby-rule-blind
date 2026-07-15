"""CI gate: ground-truth tokens are banned in the controller package.
CI 게이트: controller 패키지에서 ground truth 토큰 사용을 금지한다.

ANALYSIS_PLAN.md §2.3. The scan covers ALL text in controller/*.py —
code, strings, and comments alike — because a comment mentioning a
ground-truth field is usually the first symptom of a leak being coded in.

ANALYSIS_PLAN.md 2.3절. 검사는 controller/*.py의 모든 텍스트(코드, 문자열,
주석 전부)를 대상으로 한다 — ground truth 필드를 언급하는 주석은 대개
누출 코드가 들어오기 시작하는 첫 징후이기 때문이다.

Exit code 0 = clean, 1 = violation found.
종료 코드 0 = 통과, 1 = 위반 발견.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_DIR = PROJECT_ROOT / "controller"

# Banned exactly as listed in the frozen plan.
# 동결된 계획에 명시된 그대로 금지한다.
BANNED = [
    "hidden_rule",
    "previous_hidden_rule",
    "correct_response",
    "rule_shift",
    "is_AX",
]


def main() -> int:
    violations = []
    for path in sorted(CONTROLLER_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for token in BANNED:
                if token in line:
                    violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno}: {token}")

    if violations:
        print("BANNED TOKEN VIOLATIONS / 금지어 위반:")
        for v in violations:
            print("  " + v)
        return 1

    print(f"controller package clean / controller 패키지 통과 (banned tokens: {', '.join(BANNED)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
