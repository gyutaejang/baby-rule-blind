"""Pre-registered power simulation for Study 2 sample size (plan §8).
Study 2 표본 크기를 위한 사전 등록 power simulation (계획 8절).

Question: with N repetitions per model, Holm correction over the four
primary tests, and effects ATTENUATED relative to Study 1 (new models,
new schedules), what is the power of each primary test?

질문: 모델당 N repetitions, 1차 4검정 Holm 보정, Study 1 대비 감쇠된
효과(새 모델·새 일정) 하에서 각 1차 검정의 검정력은 얼마인가?

Method (frozen) / 방법 (동결):
- Per-test effect inputs = mean and SD of the Study 1 paired differences,
  taken as the WORST CASE (smaller |mean|/SD ratio) across the two
  archived models.
  검정별 효과 입력 = Study 1 짝 차이의 평균·SD, 두 보관 모델 중 보수적
  (|평균|/SD가 작은) 쪽 채택.
- Attenuation scenarios: 100%, 50%, 33% of the Study 1 mean (SD kept).
  감쇠 시나리오: 평균의 100%/50%/33% (SD 유지).
- Differences simulated as Gaussian; test = sign-flip permutation
  (1,000 flips) as in the main analysis; Holm over the four tests;
  success = Holm p < .05 with the pre-registered direction.
  차이는 가우시안으로 모사; 검정은 본 분석과 같은 부호 반전
  permutation(1,000회); 4검정 Holm; 성공 = Holm p < .05 + 사전 방향.
- 400 simulated experiments per scenario; master seed 20260715.
  시나리오당 400회 모의실험; 마스터 시드 20260715.
- DECISION RULE (frozen): keep N = 30 iff every primary test has power
  >= .80 under 50% attenuation; otherwise increase N (in steps of 10)
  until the criterion holds, BEFORE pilot-freeze.
  판정 규칙(동결): 50% 감쇠에서 모든 1차 검정의 power >= .80이면 N = 30
  유지; 아니면 pilot-freeze 전에 N을 10 단위로 늘려 기준을 충족시킨다.

Usage / 사용:
    python -m analysis.power_simulation [N ...]   (default: 30)
Output / 산출: results/power_simulation.csv
"""

from __future__ import annotations

import csv
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.paired_stats import holm_correct, load_summary, paired_values  # noqa: E402

SEED = 20260715
N_SIMS = 400
N_PERMS = 1000
ATTENUATIONS = (1.0, 0.5, 1.0 / 3.0)

PRIMARY = [
    ("RuleBlindFull", "RawLLM", "total_accuracy", +1),
    ("WSLSBudgeted", "RawLLM", "total_accuracy", +1),
    ("WSLSBudgeted", "RuleBlindFull", "total_accuracy", +1),
    ("RuleBlindFull", "WSLSBudgeted", "prev_rule_error_count", -1),
]


def worst_case_effects(summary_path: Path) -> Dict[Tuple[str, str, str], Tuple[float, float]]:
    """(mean, sd) per primary test — the archived model with the smaller
    |mean|/sd. / 1차 검정별 (평균, SD) — |평균|/SD가 작은 모델 채택."""
    rows = load_summary(summary_path)
    models = sorted({r["model"] for r in rows})
    effects: Dict[Tuple[str, str, str], Tuple[float, float]] = {}
    for a, b, metric, _ in PRIMARY:
        candidates = []
        for model in models:
            diffs, _dropped = paired_values(rows, model, a, b, metric)
            if len(diffs) >= 2:
                mu = statistics.mean(diffs)
                sd = statistics.stdev(diffs)
                candidates.append((abs(mu) / sd if sd else math.inf, mu, sd))
        candidates.sort()
        _, mu, sd = candidates[0]
        effects[(a, b, metric)] = (mu, sd)
    return effects


def permutation_p(diffs: List[float], rng: random.Random) -> float:
    n = len(diffs)
    observed = abs(sum(diffs) / n)
    hits = 0
    for _ in range(N_PERMS):
        s = 0.0
        for d in diffs:
            s += d if rng.random() < 0.5 else -d
        if abs(s / n) >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (N_PERMS + 1)


def simulate(n_reps: int, effects, attenuation: float, rng: random.Random) -> Dict[str, float]:
    passes = {key: 0 for key in effects}
    for _ in range(N_SIMS):
        pvals, means = [], []
        for (a, b, metric), (mu, sd) in effects.items():
            diffs = [rng.gauss(mu * attenuation, sd) for _ in range(n_reps)]
            pvals.append(permutation_p(diffs, rng))
            means.append(sum(diffs) / n_reps)
        adjusted = holm_correct(pvals)
        for key, direction_spec, adj, mean in zip(
            effects.keys(), PRIMARY, adjusted, means
        ):
            direction = direction_spec[3]
            if adj < 0.05 and mean * direction > 0:
                passes[key] += 1
    return {f"{a}|{b}|{m}": passes[(a, b, m)] / N_SIMS for (a, b, m) in effects}


def main() -> None:
    n_values = [int(x) for x in sys.argv[1:]] or [30]
    summary_path = PROJECT_ROOT / "results" / "study1_summary.csv"
    effects = worst_case_effects(summary_path)
    rng = random.Random(SEED)

    out_rows: List[Dict[str, object]] = []
    for n in n_values:
        for att in ATTENUATIONS:
            power = simulate(n, effects, att, rng)
            for test, val in power.items():
                out_rows.append(
                    {"n_reps": n, "attenuation": round(att, 3), "test": test, "power": round(val, 3)}
                )
            worst = min(power.values())
            print(f"N={n} attenuation={att:.2f}: min power {worst:.3f} "
                  + " ".join(f"{k.split('|')[2][:4]}={v:.2f}" for k, v in power.items()))

    out_path = PROJECT_ROOT / "results" / "power_simulation.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["n_reps", "attenuation", "test", "power"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"written / 저장됨: {out_path}")

    # Frozen decision rule / 동결된 판정 규칙.
    for n in n_values:
        at_half = [r for r in out_rows if r["n_reps"] == n and r["attenuation"] == 0.5]
        ok = all(float(r["power"]) >= 0.80 for r in at_half)
        print(f"DECISION N={n}: {'KEEP (all primary power >= .80 at 50% attenuation)' if ok else 'INCREASE N'}")


if __name__ == "__main__":
    main()
