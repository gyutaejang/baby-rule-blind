"""Randomized per-repetition WCST schedules for Study 2 (§11.3).
Study 2용 repetition별 무작위 WCST 일정 생성 (11.3절).

All 60 archived streams share ONE fixed schedule and every controller
parameter was selected on it; reusing it in Study 2 would test model
generalization but not schedule generalization. This script generates
one independent schedule per Study 2 repetition, from a committed master
seed, BEFORE any API call.

보관 스트림 60개는 하나의 고정 일정을 공유하고 모든 컨트롤러 파라미터가
그 위에서 선택되었다. Study 2에서 이를 재사용하면 모델 일반화는 검증해도
일정 일반화는 검증하지 못한다. 이 스크립트는 API 호출 전에, 커밋된 마스터
시드로 Study 2 repetition마다 독립 일정을 생성한다.

Frozen generation rules (§11.3) / 동결된 생성 규칙 (11.3절):
- 36 trials per session. / 세션당 36 trials.
- Block lengths drawn uniformly from {5, 6, 7}; the final remainder
  block may be 4–8 by the partition rule below.
  블록 길이는 {5,6,7}에서 균등 추출; 아래 분할 규칙에 따라 마지막 블록은
  4–8 허용.
- Partition rule: draw lengths while the remaining trials > 8; then, if
  the remainder is 4–8, it becomes the final block; if the remainder is
  1–3, it is added to the previously drawn block (making it at most
  7 + 3 = 10 is impossible since remainder <= 3 only occurs when the
  previous draw left <= 8; the merged block is at most 8).
  분할 규칙: 남은 trial이 8을 초과하는 동안 길이를 추출; 남은 수가 4–8이면
  마지막 블록으로 하고, 1–3이면 직전 블록에 합친다(합쳐진 블록은 최대 8).
- First rule uniform over {color, shape, number}; each subsequent rule
  uniform over the other two (no immediate repeat).
  첫 규칙은 셋 중 균등, 이후 규칙은 나머지 둘 중 균등(연속 반복 없음).
- Seed for repetition k of model m: MASTER_SEED + hash-free composition
  (stable across runs): seed = MASTER_SEED * 1000 + rep_index. Schedules
  are shared across models (the same rep index uses the same schedule
  for every model) so cross-model comparisons at the same rep are on the
  same schedule.
  시드: seed = MASTER_SEED * 1000 + rep 번호. 일정은 모델 간 공유한다
  (같은 rep 번호는 모든 모델에서 같은 일정) — 같은 rep의 모델 간 비교가
  같은 일정 위에서 이루어지게 하기 위해서다.

Usage / 사용:
    python scripts/generate_schedules.py [n_reps]   (default 50)
Outputs / 산출:
    data/ground_truth_study2/rep_NN_ground_truth.csv
    data/ground_truth_study2/schedule_manifest.csv  (SHA-256 per file)
"""

from __future__ import annotations

import csv
import hashlib
import random
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "ground_truth_study2"

RULES = ("color", "shape", "number")
N_TRIALS = 36
MASTER_SEED = 20260715


def partition_blocks(rng: random.Random) -> List[int]:
    """Frozen partition of 36 trials into blocks. / 36 trial의 동결된 분할."""
    lengths: List[int] = []
    remaining = N_TRIALS
    while remaining > 8:
        length = rng.choice([5, 6, 7])
        lengths.append(length)
        remaining -= length
    if remaining >= 4:
        lengths.append(remaining)
    else:
        # Remainder 1–3 merges into the previous block (result <= 8).
        # 남은 1–3은 직전 블록에 합친다 (결과는 8 이하).
        lengths[-1] += remaining
    assert sum(lengths) == N_TRIALS
    return lengths


def rule_sequence(rng: random.Random, n_blocks: int) -> List[str]:
    """First rule uniform; then uniform over the other two.
    첫 규칙 균등, 이후 나머지 둘 중 균등."""
    rules = [rng.choice(list(RULES))]
    for _ in range(n_blocks - 1):
        rules.append(rng.choice([r for r in RULES if r != rules[-1]]))
    return rules


def generate_schedule(rep_index: int) -> List[Dict[str, str]]:
    rng = random.Random(MASTER_SEED * 1000 + rep_index)
    lengths = partition_blocks(rng)
    rules = rule_sequence(rng, len(lengths))

    rows: List[Dict[str, str]] = []
    trial = 0
    for block_idx, (length, rule) in enumerate(zip(lengths, rules), start=1):
        prev_rule = rules[block_idx - 2] if block_idx > 1 else rule
        for pos in range(1, length + 1):
            trial += 1
            rows.append(
                {
                    "trial_number": str(trial),
                    "block": str(block_idx),
                    "trial_in_block": str(pos),
                    "rule_shift": "1" if (block_idx > 1 and pos == 1) else "0",
                    "hidden_rule": rule,
                    "previous_hidden_rule": prev_rule,
                    "lure_rule": "",
                    "old_rule_lure": "0",
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
    manifest: List[Dict[str, str]] = []
    columns = [
        "trial_number", "block", "trial_in_block", "rule_shift",
        "hidden_rule", "previous_hidden_rule", "lure_rule", "old_rule_lure",
    ]
    for rep in range(1, n_reps + 1):
        rows = generate_schedule(rep)
        out = OUT_DIR / f"rep_{rep:02d}_ground_truth.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        manifest.append(
            {
                "rep": str(rep),
                "path": str(out.relative_to(PROJECT_ROOT)),
                "seed": str(MASTER_SEED * 1000 + rep),
                "n_blocks": str(max(int(r["block"]) for r in rows)),
                "sha256": sha256_of(out),
            }
        )
    manifest_path = OUT_DIR / "schedule_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rep", "path", "seed", "n_blocks", "sha256"])
        writer.writeheader()
        writer.writerows(manifest)
    print(f"{n_reps} schedules -> {OUT_DIR}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
