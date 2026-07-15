"""Evaluator — the ONLY component allowed to read ground truth.
평가기 — ground truth를 읽을 수 있는 '유일한' 구성요소.

The evaluator owns `ground_truth.csv` (hidden rule schedule) and scores
frozen final choices. It never exposes the schedule to controllers; the
only value that may cross back is the single boolean `correct`, and the
replay harness delivers it only after the final choice is frozen, and
only to feedback-aware controllers.

평가기는 `ground_truth.csv`(숨겨진 규칙 일정)를 보유하고 동결된 최종
선택을 채점한다. 일정은 컨트롤러에 절대 노출되지 않으며, 되돌아갈 수 있는
값은 단일 boolean `correct` 하나뿐이다. 그것도 replay harness가 최종 선택
동결 이후, feedback-aware 컨트롤러에만 전달한다.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class GroundTruthTrial:
    """One trial of the hidden schedule. / 숨겨진 일정의 한 trial."""

    trial_number: int
    block: int
    rule_shift: bool          # True on the first trial of a new rule / 새 규칙의 첫 trial에서 True
    hidden_rule: str          # currently rewarded dimension / 현재 보상되는 차원
    previous_hidden_rule: str # rule of the previous block / 이전 블록의 규칙


@dataclass(frozen=True)
class ScoreResult:
    """Outcome of scoring one frozen final choice.
    동결된 최종 선택 하나를 채점한 결과."""

    trial_number: int
    final_choice: str
    correct: bool

    # Final choice equals the previous block's rule while being wrong —
    # the perseveration signature this study targets.
    # 최종 선택이 이전 블록의 규칙과 같으면서 오답 — 본 연구가 겨냥하는
    # 고착의 흔적.
    persistence_error: bool


class Evaluator:
    """Scores final choices against the hidden schedule.
    숨겨진 일정에 대해 최종 선택을 채점한다."""

    def __init__(self, ground_truth_path: Path) -> None:
        self._trials: Dict[int, GroundTruthTrial] = {}
        with open(ground_truth_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                trial = GroundTruthTrial(
                    trial_number=int(row["trial_number"]),
                    block=int(row["block"]),
                    rule_shift=row["rule_shift"] == "1",
                    hidden_rule=row["hidden_rule"],
                    previous_hidden_rule=row["previous_hidden_rule"],
                )
                self._trials[trial.trial_number] = trial

    def __len__(self) -> int:
        return len(self._trials)

    def score(self, trial_number: int, final_choice: str) -> ScoreResult:
        """Score one frozen final choice. / 동결된 최종 선택 하나를 채점.

        This is the only crossing point between the public side and the
        ground-truth side. Note the input is (trial id, final choice)
        only — the evaluator never sees controller internals, and the
        controller never sees this object.
        여기가 공개 측과 ground truth 측이 만나는 유일한 지점이다. 입력은
        (trial 번호, 최종 선택)뿐이며, 평가기는 컨트롤러 내부를 보지 않고
        컨트롤러는 이 객체를 보지 않는다.
        """
        gt = self._trials[trial_number]
        correct = final_choice == gt.hidden_rule
        persistence_error = (
            not correct
            and gt.previous_hidden_rule != gt.hidden_rule
            and final_choice == gt.previous_hidden_rule
        )
        return ScoreResult(
            trial_number=trial_number,
            final_choice=final_choice,
            correct=correct,
            persistence_error=persistence_error,
        )
