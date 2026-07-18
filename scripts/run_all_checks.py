"""Single verification gate (§11.8): banned tokens + leak tests.
단일 검사 게이트 (11.8절): 금지어 + 누출 방지 테스트.

No result may be reported unless this exits 0.
이 스크립트가 0으로 종료하지 않으면 어떤 결과도 보고할 수 없다.

Usage / 사용:
    python scripts/run_all_checks.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    (
        "repository security / 저장소 보안",
        [sys.executable, "scripts/verify_repository_security.py"],
    ),
    ("banned tokens / 금지어", [sys.executable, "scripts/check_banned_tokens.py"]),
    ("leak prevention / 누출 방지", [sys.executable, "-m", "tests.test_leak_prevention"]),
    ("design invariants / 설계 불변식", [sys.executable, "-m", "tests.test_design_invariants"]),
    ("WCD-minimal policy / WCD-minimal 정책", [sys.executable, "-m", "tests.test_wcd_minimal"]),
    ("parser fixtures / 파서 fixture", [sys.executable, "-m", "tests.test_parser"]),
    ("study2 dry run / 전 구간 dry run", [sys.executable, "-m", "tests.test_study2_dryrun"]),
]


def main() -> int:
    failed = 0
    for name, cmd in CHECKS:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        status = "PASS" if result.returncode == 0 else "FAIL"
        if result.returncode != 0:
            failed += 1
        print(f"[{status}] {name}")
    if failed:
        print(f"\n{failed} gate(s) failed — results MUST NOT be reported / 게이트 실패 — 결과 보고 금지")
        return 1
    print("\nall gates passed / 전체 게이트 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
