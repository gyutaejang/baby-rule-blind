"""Freeze Study 2 stimuli: exact prompts, order, and card attributes.
Study 2 자극 동결: 프롬프트 원문·순서·카드 속성.

Plan v2.0 §5–6: the API-facing side must be fully fixed and committed
BEFORE any call, and the request path must NEVER load ground truth. This
script materializes the deterministic prompt streams of study2/prompts.py
into per-repetition CSVs that the runner reads INSTEAD of any schedule
file — the two-stage structure that keeps generation blind.

계획 v2.0 5–6절: API로 나가는 쪽은 호출 전에 완전히 고정·커밋되어야 하고,
요청 경로는 ground truth를 절대 읽지 않아야 한다. 이 스크립트는
study2/prompts.py의 결정론적 프롬프트 스트림을 repetition별 CSV로
구체화하며, 러너는 일정 파일 대신 '이 파일'만 읽는다 — 생성을 맹검으로
유지하는 2단계 구조다.

Recorded per trial / trial별 기록: trial_number, color, number, shape,
prompt (verbatim request text). No system message is used
(system_message = none, recorded in the manifest).
system message는 사용하지 않는다(manifest에 none으로 기록).

Usage / 사용:
    python scripts/generate_stimuli.py [n_reps]   (default 50)
Outputs / 산출:
    data/stimuli_study2/rep_NN_prompts.csv
    data/stimuli_study2/stimuli_manifest.csv (SHA-256, system_message)
"""

from __future__ import annotations

import csv
import hashlib
import random
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from study2.prompts import (  # noqa: E402
    CARD_STREAM_OFFSET,
    COLORS,
    MASTER_SEED,
    NUMBERS,
    PROMPT_TEMPLATE,
    SHAPES,
)

OUT_DIR = PROJECT_ROOT / "data" / "stimuli_study2"
N_TRIALS = 36


def generate_stimuli(rep_index: int) -> List[Dict[str, str]]:
    """Same RNG stream as study2/prompts.generate_prompts, with card
    attributes recorded explicitly.
    study2/prompts.generate_prompts와 동일한 RNG 스트림, 카드 속성을
    명시적으로 기록."""
    rng = random.Random(MASTER_SEED * 1000 + rep_index + CARD_STREAM_OFFSET)
    rows = []
    for trial in range(1, N_TRIALS + 1):
        color = rng.choice(COLORS)
        number = rng.choice(NUMBERS)
        shape = rng.choice(SHAPES)
        rows.append(
            {
                "trial_number": str(trial),
                "color": color,
                "number": str(number),
                "shape": shape,
                "prompt": PROMPT_TEMPLATE.format(color=color, number=number, shape=shape),
            }
        )
    return rows


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    n_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for rep in range(1, n_reps + 1):
        rows = generate_stimuli(rep)
        out = OUT_DIR / f"rep_{rep:02d}_prompts.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["trial_number", "color", "number", "shape", "prompt"]
            )
            writer.writeheader()
            writer.writerows(rows)
        manifest.append(
            {
                "rep": str(rep),
                "path": str(out.relative_to(PROJECT_ROOT)),
                "n_trials": str(len(rows)),
                "system_message": "none",
                "sha256": sha256_of(out),
            }
        )
    manifest_path = OUT_DIR / "stimuli_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["rep", "path", "n_trials", "system_message", "sha256"]
        )
        writer.writeheader()
        writer.writerows(manifest)
    print(f"{n_reps} stimulus files -> {OUT_DIR}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
