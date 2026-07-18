"""Study 2 end-to-end dry run against a mock API (plan v2.0 §11).
mock API에 대한 Study 2 end-to-end dry run (계획 v2.0 11절).

Exercises the FULL pipeline with zero API calls: committed-style schedule
-> deterministic prompts -> runner (retry/ITT rules) -> public CSV +
attempt log + manifest -> replay through all eight conditions with a
per-repetition evaluator -> summary metrics. Required in the gate from
pilot-freeze onward.

API 호출 0회로 전체 파이프라인을 검증한다: 일정 -> 결정론적 프롬프트 ->
러너(재시도·ITT 규칙) -> 공개 CSV·시도 로그·manifest -> rep별 평가기로
8조건 재생 -> 요약 지표. pilot-freeze부터 게이트 필수.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from controller import (  # noqa: E402
    PassthroughController,
    RuleBlindFullController,
    TrajectoryOnlyController,
    WSLSController,
)
from controller.yoked_random import YokedRandomController  # noqa: E402
from evaluator import Evaluator  # noqa: E402
from oracle import OracleFullController  # noqa: E402
from replay import load_public_stream, run_replay, summarize  # noqa: E402
from scripts.generate_schedules import generate_schedule  # noqa: E402
from scripts.generate_stimuli import generate_stimuli  # noqa: E402
from study2.runner import generate_repetition, sha256_of, write_repetition  # noqa: E402

REP = 1


def _write_schedule(tmp: Path) -> Path:
    rows = generate_schedule(REP)
    path = tmp / f"rep_{REP:02d}_ground_truth.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _write_stimuli(tmp: Path) -> Path:
    rows = generate_stimuli(REP)
    path = tmp / f"rep_{REP:02d}_prompts.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["trial_number", "color", "number", "shape", "prompt"]
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


class _MockLLM:
    """Stateful mock covering every runner branch; advances its own trial
    counter by mirroring the runner's frozen retry rules (a trial ends on
    "ok", after 3 api_errors, or after 2 refusals) — robust even when two
    consecutive cards render identical prompt text.

    러너의 모든 분기를 덮는 상태형 mock. 러너의 동결된 재시도 규칙("ok",
    api_error 3회, refusal 2회로 trial 종료)을 미러링해 스스로 trial을
    진행하므로, 연속 카드의 프롬프트 텍스트가 우연히 동일해도 안전하다.

    - trial 3: api_error x3 -> final "" with api_error flag (ITT)
    - trial 5: refusal x2 -> final "" with refusal flag (ITT)
    - trial 7: transient api_error then ok (retry success)
    - trial 9: synonym answer ("hue") -> parses to color
    - trial 11: no dimension mentioned -> ambiguous ""
    - otherwise: "color"
    """

    def __init__(self) -> None:
        self.trial = 1
        self.attempt = 0

    def __call__(self, prompt: str) -> Tuple[str, str]:
        self.attempt += 1
        t, a = self.trial, self.attempt

        if t == 3:
            response: Tuple[str, str] = ("", "api_error")
        elif t == 5:
            response = ("", "refusal")
        elif t == 7 and a == 1:
            response = ("", "api_error")
        elif t == 9:
            response = ("I would sort by hue.", "ok")
        elif t == 11:
            response = ("I am not sure at all.", "ok")
        else:
            response = ("color", "ok")

        status = response[1]
        trial_done = (
            status == "ok"
            or (status == "api_error" and a >= 3)
            or (status == "refusal" and a >= 2)
        )
        if trial_done:
            self.trial += 1
            self.attempt = 0
        return response


def _mock_call_factory():
    return _MockLLM()


def test_end_to_end_dry_run() -> None:
    tmp = Path(tempfile.mkdtemp())
    schedule_path = _write_schedule(tmp)
    _write_stimuli(tmp)

    # Two-stage blindness: the runner receives the STIMULI directory
    # only; the schedule file exists elsewhere and is used by the
    # evaluator below.
    # 2단계 맹검: 러너에는 자극 디렉터리만 전달하고, 일정 파일은 아래
    # 평가기에서만 사용한다.
    rows, attempts = generate_repetition(
        _mock_call_factory(), REP, stimuli_dir=tmp, sleep_seconds=0.0
    )
    assert len(rows) == 36, f"{len(rows)} trials"

    # ITT rules / ITT 규칙.
    t3 = rows[2]
    assert t3["api_error"] == "1" and t3["parsed_choice"] == "" and t3["ambiguous_response"] == "1"
    t5 = rows[4]
    assert t5["refusal"] == "1" and t5["parsed_choice"] == ""
    t7 = rows[6]
    assert t7["api_error"] == "0" and t7["parsed_choice"] == "color"  # retry succeeded
    assert rows[8]["parsed_choice"] == "color"  # "hue" synonym
    t11 = rows[10]
    assert t11["parsed_choice"] == "" and t11["ambiguous_response"] == "1"

    # Attempt log: t3 has 3 attempts, t5 has 2, t7 has 2, failures kept.
    # 시도 로그: t3=3회, t5=2회, t7=2회, 실패 기록 보존.
    per_trial = {}
    for a in attempts:
        per_trial.setdefault(a["trial_number"], []).append(a["status"])
    assert per_trial["3"] == ["api_error"] * 3
    assert per_trial["5"] == ["refusal"] * 2
    assert per_trial["7"] == ["api_error", "ok"]

    # Write outputs + manifest. / 산출물·manifest 기록.
    entry = write_repetition(
        "mock-model",
        REP,
        rows,
        attempts,
        tmp / "out",
        {
            "provider": "mock",
            "pilot": "1",
            "generation_config": json.dumps({"mock": True}, sort_keys=True),
            "generation_config_source": "runtime",
        },
    )
    public_path = PROJECT_ROOT / entry["public_path"] if not Path(entry["public_path"]).is_absolute() else Path(entry["public_path"])
    # write_repetition stores project-relative paths; resolve from tmp.
    public_path = tmp / "out" / "mock-model" / f"rep_{REP:02d}_public.csv"
    assert public_path.exists()
    manifest_path = tmp / "out" / "mock-model" / "generation_manifest.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8").splitlines()[0])
    assert manifest["public_sha256"] == entry["public_sha256"]
    attempts_path = tmp / "out" / "mock-model" / f"rep_{REP:02d}_attempts.csv"
    assert manifest["attempts_sha256"] == sha256_of(attempts_path)
    assert manifest["generation_config_source"] == "runtime"
    assert manifest["manifest_schema_version"] == "2"

    # Replay the generated stream through all eight conditions with the
    # per-repetition evaluator; budget and structure invariants hold.
    # 생성 스트림을 rep별 평가기로 8조건 재생; 예산·구조 불변식 확인.
    ev = Evaluator(schedule_path)
    stream = load_public_stream(public_path)
    assert len(stream) == 36

    full = run_replay(RuleBlindFullController(), stream, ev)
    conditions = {
        "RawLLM": run_replay(PassthroughController(), stream, ev),
        "RuleBlindFull": full,
        "NoVeto": run_replay(RuleBlindFullController(veto_window=0), stream, ev),
        "TrajectoryOnly": run_replay(TrajectoryOnlyController(), stream, ev),
        "YokedRandom": run_replay(
            YokedRandomController(full.intervention_trials(), seed=99), stream, ev
        ),
        "WSLSBudgeted": run_replay(WSLSController(max_interventions_per_rep=9), stream, ev),
        "WSLSUnlimited": run_replay(WSLSController(max_interventions_per_rep=None), stream, ev),
        "OracleFull": run_replay(OracleFullController(schedule_path), stream, ev),
    }
    for name in ("RuleBlindFull", "WSLSBudgeted"):
        n = sum(1 for r in conditions[name].records if r.intervened)
        assert n <= 9, f"{name} exceeded budget on dry run / 예산 초과"
    for name, result in conditions.items():
        s = summarize(result)
        assert s["n_trials"] == 36.0, name
        # ITT "" trials must remain (unparsable counted, never dropped).
        # ITT "" trial은 유지되어야 한다(파싱 불가로 집계, 제거 금지).
        assert s["unparsable_count"] >= 3.0, (name, s["unparsable_count"])


def main() -> int:
    try:
        test_end_to_end_dry_run()
        print("PASS  study2 end-to-end dry run / 전 구간 dry run")
    except AssertionError as exc:
        print(f"FAIL  study2 end-to-end dry run\n      {exc}")
        return 1
    print("\nstudy2 dry run passed / 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
