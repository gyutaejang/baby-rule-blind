"""Replay harness — enforces the interface contract of ANALYSIS_PLAN.md.
Replay harness — ANALYSIS_PLAN.md의 인터페이스 규약을 강제한다.

The harness is the only code that touches both sides. Per trial it runs:
harness는 양쪽을 모두 만지는 유일한 코드다. trial마다 다음 순서를 강제한다:

    final_choice = controller.decide(public_trial, raw_choice)   # freeze / 동결
    result       = evaluator.score(trial_number, final_choice)
    controller.observe_feedback(result.correct)                  # feedback-aware only / feedback-aware 조건만

It also records a call-order log so tests can prove that feedback never
precedes freezing (mandatory leak test 3).
또한 호출 순서 로그를 남겨, 피드백이 동결보다 먼저 일어나지 않았음을
테스트가 증명할 수 있게 한다 (필수 누출 테스트 3번).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from controller.base import PublicTrial, RuleBlindController
from evaluator import Evaluator


@dataclass(frozen=True)
class PublicStreamRow:
    """One row of public_stream.csv. / public_stream.csv의 한 행."""

    trial_number: int
    prompt: str
    raw_response: str    # the LLM's verbatim response / LLM 응답 원문
    parsed_choice: str   # parsed dimension or "" / 파싱된 차원 또는 ""
    ambiguous: bool


@dataclass
class TrialRecord:
    """Everything recorded about one replayed trial.
    재생된 trial 하나에 대해 기록되는 모든 것."""

    trial_number: int
    raw_choice: str
    final_choice: str
    intervened: bool     # final differs from raw / 최종이 원선택과 다름
    correct: bool
    persistence_error: bool


@dataclass
class ReplayResult:
    """Result of replaying one stream through one controller.
    스트림 하나를 컨트롤러 하나에 재생한 결과."""

    records: List[TrialRecord] = field(default_factory=list)

    # Flat call-order log: ("decide"|"score"|"feedback", trial_number).
    # Used by the leak-prevention tests to verify ordering.
    # 평면 호출 순서 로그: ("decide"|"score"|"feedback", trial 번호).
    # 누출 방지 테스트가 순서를 검증하는 데 사용한다.
    call_log: List[tuple] = field(default_factory=list)

    def intervention_trials(self) -> set:
        """Trial numbers where the controller intervened — the yoking
        schedule for the YokedRandom condition.
        컨트롤러가 개입한 trial 번호들 — YokedRandom 조건의 yoking 일정."""
        return {r.trial_number for r in self.records if r.intervened}


def load_public_stream(path: Path) -> List[PublicStreamRow]:
    """Load one public stream file. Controllers must receive data ONLY
    through this loader, which physically cannot expose schedule fields
    because the file does not contain them.
    공개 스트림 파일 하나를 읽는다. 컨트롤러는 반드시 이 로더를 통해서만
    데이터를 받아야 하며, 파일 자체에 일정 필드가 없으므로 물리적으로
    노출이 불가능하다.
    """
    rows: List[PublicStreamRow] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                PublicStreamRow(
                    trial_number=int(row["trial_number"]),
                    prompt=row["prompt"],
                    raw_response=row["raw_response"],
                    parsed_choice=row["parsed_choice"],
                    ambiguous=row["ambiguous_response"] == "1",
                )
            )
    rows.sort(key=lambda r: r.trial_number)
    return rows


def run_replay(
    controller: RuleBlindController,
    stream: List[PublicStreamRow],
    evaluator: Evaluator,
) -> ReplayResult:
    """Replay one stream through one controller instance.
    스트림 하나를 컨트롤러 인스턴스 하나에 재생한다.

    NOTE: a controller instance is stateful and must be fresh per stream.
    참고: 컨트롤러 인스턴스는 상태를 가지므로 스트림마다 새로 만들어야 한다.
    """
    result = ReplayResult()
    for row in stream:
        public_trial = PublicTrial(trial_number=row.trial_number, prompt=row.prompt)

        # (1) Decide, then freeze. / (1) 결정 후 동결.
        final_choice = controller.decide(public_trial, row.parsed_choice)
        result.call_log.append(("decide", row.trial_number))

        # (2) Score the frozen choice. / (2) 동결된 선택을 채점.
        score = evaluator.score(row.trial_number, final_choice)
        result.call_log.append(("score", row.trial_number))

        # (3) Outcome feedback strictly after freezing, and only for
        #     feedback-aware controllers.
        # (3) 정오 피드백은 동결 이후에만, feedback-aware 컨트롤러에만.
        if controller.feedback_aware:
            controller.observe_feedback(score.correct)
            result.call_log.append(("feedback", row.trial_number))

        result.records.append(
            TrialRecord(
                trial_number=row.trial_number,
                raw_choice=row.parsed_choice,
                final_choice=final_choice,
                intervened=final_choice != row.parsed_choice,
                correct=score.correct,
                persistence_error=score.persistence_error,
            )
        )
    return result


def summarize(result: ReplayResult) -> Dict[str, float]:
    """Repetition-level metrics as defined in ANALYSIS_PLAN.md §6.
    ANALYSIS_PLAN.md 6절에 정의된 repetition 단위 지표."""
    n = max(1, len(result.records))
    records = result.records

    interventions = [r for r in records if r.intervened]

    # Single fixed definition (plan §6): an intervention is productive
    # iff at least one of the next two FINAL choices is correct.
    # 단일 고정 정의(계획 6절): 개입은 이후 두 '최종' 선택 중 하나 이상이
    # 정답일 때에만 생산적이다.
    productive = 0
    by_index = {r.trial_number: i for i, r in enumerate(records)}
    for r in interventions:
        i = by_index[r.trial_number]
        nxt = records[i + 1 : i + 3]
        if any(x.correct for x in nxt):
            productive += 1

    return {
        "n_trials": float(n),
        "total_accuracy": sum(r.correct for r in records) / n,
        "persistence_error_count": float(sum(r.persistence_error for r in records)),
        "intervention_count": float(len(interventions)),
        # None-equivalent (-1) when undefined: plan §6 excludes zero-
        # intervention repetitions from rate analyses instead of coding 0.
        # 정의 불가 시 -1: 계획 6절에 따라 개입 0회 repetition은 비율
        # 분석에서 0이 아니라 제외 처리한다.
        "productive_rate": (productive / len(interventions)) if interventions else -1.0,
    }
