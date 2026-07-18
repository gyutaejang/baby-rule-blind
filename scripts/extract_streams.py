"""Extract public streams and ground truth from the archived Baby40 data.
보관된 Baby40 데이터에서 공개 스트림과 ground truth를 분리 추출한다.

Physical separation required by ANALYSIS_PLAN.md §2.1:
ANALYSIS_PLAN.md 2.1절이 요구하는 물리적 분리:

- data/public/{model}_rep_{NN}_public.csv
    trial_number, prompt, raw_response, parsed_choice, ambiguous_response
    (nothing derived from the schedule / 일정에서 파생된 것은 없음)
- data/ground_truth/wcst_ground_truth.csv
    trial_number, block, trial_in_block, rule_shift, hidden_rule,
    previous_hidden_rule, lure_rule, old_rule_lure

The hidden-rule schedule is fixed by design, so a single ground-truth
file serves all repetitions; this script ASSERTS that every source file
carries the identical schedule before writing anything.
숨겨진 규칙 일정은 설계상 고정이므로 ground truth 파일 하나가 모든
repetition에 공통이다. 이 스크립트는 쓰기 전에 모든 원본 파일의 일정이
동일한지 단언(assert)한다.

A SHA-256 manifest of every source and output file is written to
data/manifest.csv for provenance (plan §8).
출처 관리(계획 8절)를 위해 모든 원본·산출 파일의 SHA-256 manifest를
data/manifest.csv에 기록한다.

Usage / 사용:
    python scripts/extract_streams.py [source_dir]
    source_dir may also be supplied through ARCHIVED_SOURCE_DIR.
    source_dir는 ARCHIVED_SOURCE_DIR 환경변수로도 지정할 수 있다.
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PUBLIC_DIR = PROJECT_ROOT / "data" / "public"
GT_DIR = PROJECT_ROOT / "data" / "ground_truth"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.csv"

# Columns that are visible to the LLM or derived from its response only.
# LLM에게 보이거나 LLM 응답에서만 파생되는 컬럼.
PUBLIC_COLUMNS = ["trial_number", "prompt", "raw_response", "parsed_choice", "ambiguous_response"]

# Columns that encode the task schedule — evaluator side only.
# 과제 일정을 인코딩하는 컬럼 — 평가기 전용.
GT_COLUMNS = [
    "trial_number",
    "block",
    "trial_in_block",
    "rule_shift",
    "hidden_rule",
    "previous_hidden_rule",
    "lure_rule",
    "old_rule_lure",
]

MODELS = {"claude": "llm_independent_claude_rep_{:02d}.csv", "gpt": "llm_independent_gpt_rep_{:02d}.csv"}
N_REPS = 30
N_TRIALS = 36


def sha256_of(path: Path) -> str:
    """Content hash for the provenance manifest. / 출처 manifest용 해시."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def read_rows(path: Path) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: List[Dict[str, str]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" prevents blank lines on Windows; utf-8 without BOM keeps
    # hashes platform-stable.
    # newline=""은 Windows에서의 빈 줄 삽입을 막고, BOM 없는 utf-8은
    # 해시를 플랫폼 간 안정적으로 유지한다.
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def extract_schedule(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Project source rows onto the ground-truth columns.
    원본 행을 ground truth 컬럼으로 사영한다."""
    return [{col: row.get(col, "") for col in GT_COLUMNS} for row in rows]


def main() -> None:
    source_arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ARCHIVED_SOURCE_DIR")
    if not source_arg:
        raise SystemExit(
            "source dir required: pass it as the first argument or set "
            "ARCHIVED_SOURCE_DIR / 원본 경로를 인자 또는 환경변수로 지정하세요"
        )
    source_dir = Path(source_arg).expanduser()
    if not source_dir.exists():
        raise SystemExit("source dir not found / 원본 경로가 없습니다")

    manifest: List[Dict[str, str]] = []
    reference_schedule: List[Dict[str, str]] | None = None
    reference_name = ""

    for model, pattern in MODELS.items():
        for rep in range(1, N_REPS + 1):
            src = source_dir / pattern.format(rep)
            rows = read_rows(src)

            # Sanity: every archived stream must be a complete session.
            # 무결성: 모든 보관 스트림은 완전한 세션이어야 한다.
            if len(rows) != N_TRIALS:
                raise SystemExit(f"{src.name}: expected {N_TRIALS} trials, got {len(rows)}")

            # --- schedule consistency check / 일정 일관성 검사 ---
            schedule = extract_schedule(rows)
            if reference_schedule is None:
                reference_schedule = schedule
                reference_name = src.name
            elif schedule != reference_schedule:
                raise SystemExit(
                    f"schedule mismatch: {src.name} differs from {reference_name} — "
                    f"a single ground-truth file would be invalid / 일정 불일치: "
                    f"단일 ground truth 파일을 쓸 수 없습니다"
                )

            # --- public projection / 공개 사영 ---
            public_rows = [
                {
                    "trial_number": row["trial_number"],
                    "prompt": row["prompt"],
                    "raw_response": row["response"],
                    "parsed_choice": row["parsed_choice"],
                    "ambiguous_response": row["ambiguous_response"],
                }
                for row in rows
            ]
            out = PUBLIC_DIR / f"{model}_rep_{rep:02d}_public.csv"
            write_rows(out, public_rows, PUBLIC_COLUMNS)
            manifest.append(
                {
                    "role": "source",
                    # Keep public provenance portable and free of workstation
                    # usernames. The content hash remains the source identity.
                    # 공개 manifest에는 개인 PC 절대경로 대신 논리 경로를 기록한다.
                    "path": str(Path("external_source") / src.name),
                    "sha256": sha256_of(src),
                }
            )
            manifest.append(
                {
                    "role": "public_stream",
                    "path": str(out.relative_to(PROJECT_ROOT)),
                    "sha256": sha256_of(out),
                }
            )

    assert reference_schedule is not None
    gt_out = GT_DIR / "wcst_ground_truth.csv"
    write_rows(gt_out, reference_schedule, GT_COLUMNS)
    manifest.append(
        {"role": "ground_truth", "path": str(gt_out.relative_to(PROJECT_ROOT)), "sha256": sha256_of(gt_out)}
    )

    write_rows(MANIFEST_PATH, manifest, ["role", "path", "sha256"])
    print(f"public streams / 공개 스트림: {len(MODELS) * N_REPS} files -> {PUBLIC_DIR}")
    print(f"ground truth / 정답 일정: {gt_out}")
    print(f"manifest: {MANIFEST_PATH} ({len(manifest)} entries)")


if __name__ == "__main__":
    main()
