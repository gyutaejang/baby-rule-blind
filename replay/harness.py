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
    prev_rule_error: bool  # previous-rule-aligned error (Amendment B) / 이전 규칙 정렬 오류
    block: int
    rule_shift: bool


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

    # Analysis-side side channel: correctness of the RAW choice per
    # trial, for the direct intervention safety metrics (§11.4).
    # Computed AFTER the final choice is frozen; never exposed to
    # controllers.
    # 분석 전용 사이드 채널: 직접 개입 안전성 지표(11.4절)를 위한
    # trial별 원선택 정오. 최종 선택 동결 이후 계산되며 컨트롤러에는
    # 절대 노출되지 않는다.
    raw_correct_by_trial: Dict[int, bool] = field(default_factory=dict)

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

        # Analysis-side raw-choice scoring (after freezing; not logged,
        # never passed to any controller).
        # 분석 전용 원선택 채점 (동결 이후; 로그 없음, 어떤 컨트롤러에도
        # 전달되지 않음).
        result.raw_correct_by_trial[row.trial_number] = evaluator.score(
            row.trial_number, row.parsed_choice
        ).correct

        result.records.append(
            TrialRecord(
                trial_number=row.trial_number,
                raw_choice=row.parsed_choice,
                final_choice=final_choice,
                intervened=final_choice != row.parsed_choice,
                correct=score.correct,
                prev_rule_error=score.prev_rule_error,
                block=score.block,
                rule_shift=score.rule_shift,
            )
        )
    return result


def summarize(result: ReplayResult) -> Dict[str, float]:
    """Repetition-level metrics per ANALYSIS_PLAN.md §6 and Amendment B
    (§11.4). / ANALYSIS_PLAN.md 6절 및 수정안 B(11.4절)의 repetition 단위
    지표."""
    import math

    n = max(1, len(result.records))
    records = result.records
    interventions = [r for r in records if r.intervened]

    # --- Direct intervention safety metrics (§11.4) ---
    # --- 직접 개입 안전성 지표 (11.4절) ---
    # Attribution needs the raw choice's own correctness, which we can
    # infer analysis-side: an intervention changed raw -> final, so raw
    # was correct iff final is incorrect AND raw equals the rule... we
    # cannot see the rule here. Instead: raw correctness is derived from
    # the pair (intervened, correct) ONLY when it is decidable — for
    # non-intervened trials raw == final. For intervened trials the
    # evaluator's per-trial correctness of the RAW choice is needed, so
    # we recompute it from the invariant: raw was correct iff raw ==
    # final would have been correct — undecidable here. Therefore the
    # runner passes raw correctness through the evaluator (see
    # run_replay: raw_score below).
    # 이 함수는 아래 run_replay가 채워 주는 raw 채점 결과에 의존한다.
    corrective = sum(1 for r in interventions if (not _raw_correct(result, r)) and r.correct)
    harmful = sum(1 for r in interventions if _raw_correct(result, r) and not r.correct)
    precision_hits = sum(1 for r in interventions if not _raw_correct(result, r))

    # subsequent_success_rate (DEMOTED per §11.4; was "productive rate"):
    # satisfied iff at least one of the next two FINAL choices is
    # correct. Descriptive only — later luck can satisfy it.
    # subsequent_success_rate (11.4절에 따라 강등; 구 productive rate):
    # 이후 두 최종 선택 중 하나 이상이 정답이면 만족. 기술 지표 전용.
    subsequent = 0
    by_index = {r.trial_number: i for i, r in enumerate(records)}
    for r in interventions:
        i = by_index[r.trial_number]
        if any(x.correct for x in records[i + 1 : i + 3]):
            subsequent += 1

    # --- old_rule_reentry (§11.4): prev-rule-aligned error occurring
    # after at least one earlier correct trial in the same block ---
    # --- old_rule_reentry (11.4절): 같은 블록에서 앞선 정답 이후에
    # 나오는 이전 규칙 정렬 오류 ---
    reentry = 0
    seen_correct_in_block: Dict[int, bool] = {}
    for r in records:
        if r.block > 1 and r.prev_rule_error and seen_correct_in_block.get(r.block, False):
            reentry += 1
        if r.correct:
            seen_correct_in_block[r.block] = True

    # --- choice entropy (§11.4): log2, unparsable excluded ---
    # --- 선택 엔트로피 (11.4절): log2, 파싱 불가 제외 ---
    counts: Dict[str, int] = {}
    unparsable = 0
    for r in records:
        if r.final_choice:
            counts[r.final_choice] = counts.get(r.final_choice, 0) + 1
        else:
            unparsable += 1
    total_parsed = sum(counts.values())
    entropy = 0.0
    if total_parsed > 0:
        for c in counts.values():
            p = c / total_parsed
            entropy -= p * math.log2(p)

    # --- recovery latency (§11.4): per post-shift block, 1-based
    # position of the first correct final choice; censored at block
    # length if none ---
    # --- 회복 지연 (11.4절): 전환 후 블록별 첫 정답의 1-기반 위치,
    # 없으면 블록 길이에서 중도절단 ---
    block_positions: Dict[int, int] = {}
    first_correct_pos: Dict[int, int] = {}
    block_lengths: Dict[int, int] = {}
    for r in records:
        pos = block_positions.get(r.block, 0) + 1
        block_positions[r.block] = pos
        block_lengths[r.block] = pos
        if r.correct and r.block not in first_correct_pos:
            first_correct_pos[r.block] = pos
    latencies = []
    censored = 0
    for block, length in block_lengths.items():
        if block == 1:
            continue
        if block in first_correct_pos:
            latencies.append(first_correct_pos[block])
        else:
            latencies.append(length)
            censored += 1

    return {
        "n_trials": float(n),
        "total_accuracy": sum(r.correct for r in records) / n,
        "prev_rule_error_count": float(sum(r.prev_rule_error for r in records)),
        "old_rule_reentry_count": float(reentry),
        "choice_entropy": round(entropy, 4),
        "unparsable_count": float(unparsable),
        "recovery_latency_mean": round(sum(latencies) / len(latencies), 4) if latencies else -1.0,
        "latency_censored_count": float(censored),
        "intervention_count": float(len(interventions)),
        "intervention_coverage": round(len(interventions) / n, 4),
        "corrective_override_count": float(corrective),
        "harmful_override_count": float(harmful),
        "net_correction": float(corrective - harmful),
        # -1 = undefined (zero interventions), excluded from rate
        # analyses per plan §6 / -1 = 정의 불가(개입 0회), 계획 6절에
        # 따라 비율 분석에서 제외.
        "intervention_precision": (precision_hits / len(interventions)) if interventions else -1.0,
        "subsequent_success_rate": (subsequent / len(interventions)) if interventions else -1.0,
    }


def _raw_correct(result: ReplayResult, record: TrialRecord) -> bool:
    """Whether the RAW choice would have been correct on this trial.
    이 trial에서 원선택이 정답이었을지 여부.

    Filled by run_replay via the raw-score side channel (analysis-side
    only; controllers never see it).
    run_replay가 raw 채점 사이드 채널로 채운다 (분석 전용, 컨트롤러는
    보지 못한다)."""
    return result.raw_correct_by_trial.get(record.trial_number, False)
