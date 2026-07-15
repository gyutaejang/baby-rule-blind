"""Study 2 stream-generation runner (plan v2.0 §5–6, §10).
Study 2 스트림 생성 러너 (계획 v2.0 5–6절, 10절).

Generates raw response streams from a live model, one repetition at a
time, against the committed randomized schedules. The runner itself is
pure with respect to the API: it takes an injected `call_fn`, so the
end-to-end dry-run gate exercises the full pipeline against a mock.

커밋된 무작위 일정에 대해 라이브 모델의 원응답 스트림을 repetition
단위로 생성한다. 러너는 API에 대해 순수하다: 주입된 `call_fn`을 받으므로
end-to-end dry-run 게이트가 mock으로 전체 파이프라인을 검증한다.

Frozen rules applied here (plan §5) / 여기서 적용되는 동결 규칙:
- API errors: up to 3 attempts (exponential backoff); still failing ->
  trial recorded as "" with api_error flag (ITT).
- Refusals: retry once; refused again -> trial recorded as "" with
  refusal flag (ITT). Repetition-level exclusion is sensitivity-only and
  happens at analysis time, never here.
- Every attempt is logged with an attempt ID; failures are preserved.
- No API keys or auth material ever reach any output file.

Usage (live) / 사용 (라이브):
    python -m study2.runner --provider anthropic --model claude-opus-4-8 \
        --reps 1-5 --pilot
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]

from study2.parser import parse_dimension_choice  # noqa: E402

# Two-stage blindness (plan v2.0 §5): the runner reads ONLY the committed
# stimulus files — never any ground-truth/schedule file. Scoring happens
# later, replay-side.
# 2단계 맹검 (계획 v2.0 5절): 러너는 커밋된 자극 파일만 읽는다 — ground
# truth·일정 파일은 절대 읽지 않는다. 채점은 이후 replay 측에서 한다.
STIMULI_DIR = PROJECT_ROOT / "data" / "stimuli_study2"

MAX_API_ATTEMPTS = 3   # frozen / 동결
MAX_REFUSAL_ATTEMPTS = 2  # initial + one retry / 최초 + 1회 재시도

CallFn = Callable[[str], Tuple[str, str]]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_stimuli(rep_index: int, stimuli_dir: Path) -> List[str]:
    """Load the committed per-repetition prompt list (must exist BEFORE
    any API call). / 커밋된 rep별 프롬프트 목록 로드 (API 호출 전 필수)."""
    path = stimuli_dir / f"rep_{rep_index:02d}_prompts.csv"
    if not path.exists():
        raise SystemExit(
            f"stimuli missing: {path} — run scripts/generate_stimuli.py and "
            f"commit BEFORE generation / 자극 파일 없음: 생성·커밋 후 실행하세요"
        )
    with open(path, newline="", encoding="utf-8") as f:
        return [row["prompt"] for row in csv.DictReader(f)]


def generate_repetition(
    call_fn: CallFn,
    rep_index: int,
    stimuli_dir: Path = STIMULI_DIR,
    sleep_seconds: float = 0.0,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Generate one repetition. Returns (public_rows, attempt_log).
    repetition 하나를 생성한다. (공개 행, 시도 로그)를 반환."""
    prompts = load_stimuli(rep_index, stimuli_dir)

    public_rows: List[Dict[str, str]] = []
    attempts_log: List[Dict[str, str]] = []

    for trial_number, prompt in enumerate(prompts, start=1):
        text, final_status = "", "api_error"
        api_attempts = 0
        refusal_attempts = 0
        attempt_id = 0
        # Frozen retry loop (plan §5): api_error -> up to 3 attempts with
        # exponential backoff; refusal -> one retry; first "ok" wins.
        # 동결된 재시도 루프: api_error는 지수 백오프로 3회, refusal은
        # 1회 재시도, 첫 "ok"가 채택된다.
        while True:
            attempt_id += 1
            text, status = call_fn(prompt)
            attempts_log.append(
                {
                    "rep": str(rep_index),
                    "trial_number": str(trial_number),
                    "attempt_id": f"r{rep_index:02d}t{trial_number:02d}a{attempt_id}",
                    "status": status,
                }
            )
            if status == "ok":
                final_status = "ok"
                break
            if status == "refusal":
                refusal_attempts += 1
                if refusal_attempts >= MAX_REFUSAL_ATTEMPTS:
                    final_status = "refusal"
                    text = ""
                    break
            else:  # api_error
                api_attempts += 1
                if api_attempts >= MAX_API_ATTEMPTS:
                    final_status = "api_error"
                    text = ""
                    break
                if sleep_seconds:
                    time.sleep(sleep_seconds * (2 ** (api_attempts - 1)))
        parsed, ambiguous = parse_dimension_choice(text) if final_status == "ok" else ("", 1)
        public_rows.append(
            {
                "trial_number": str(trial_number),
                "prompt": prompt,
                "raw_response": text,
                "parsed_choice": parsed,
                "ambiguous_response": str(ambiguous),
                # ITT flags (plan §5): kept in the public stream so the
                # analysis can run sensitivity checks; they carry no
                # schedule information.
                # ITT 플래그: 민감도 분석용으로 공개 스트림에 유지. 일정
                # 정보는 담지 않는다.
                "api_error": "1" if final_status == "api_error" else "0",
                "refusal": "1" if final_status == "refusal" else "0",
            }
        )
        if sleep_seconds:
            time.sleep(sleep_seconds)
    return public_rows, attempts_log


def write_repetition(
    model_label: str,
    rep_index: int,
    public_rows: List[Dict[str, str]],
    attempts_log: List[Dict[str, str]],
    out_root: Path,
    manifest_extra: Dict[str, str],
) -> Dict[str, str]:
    """Write outputs + per-rep manifest entry. / 산출물과 manifest 기록."""
    model_dir = out_root / model_label
    model_dir.mkdir(parents=True, exist_ok=True)

    public_path = model_dir / f"rep_{rep_index:02d}_public.csv"
    attempts_check = model_dir / f"rep_{rep_index:02d}_attempts.csv"
    # Never overwrite an existing repetition: the original failure record
    # must survive any retry/replacement (plan §5; review P1). Move the
    # old files to an archive directory first if a re-run is intended.
    # 기존 repetition은 절대 덮어쓰지 않는다: 재시도·대체 시에도 원 실패
    # 기록이 보존되어야 한다 (계획 5절; 검토 P1). 재실행하려면 기존
    # 파일을 먼저 보관 디렉터리로 옮겨라.
    if public_path.exists() or attempts_check.exists():
        raise SystemExit(
            f"refusing to overwrite existing repetition files for "
            f"{model_label} rep {rep_index:02d} ({public_path}) — archive "
            f"them first / 기존 rep 파일 덮어쓰기 거부 — 먼저 보관하세요"
        )
    with open(public_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trial_number", "prompt", "raw_response", "parsed_choice",
                "ambiguous_response", "api_error", "refusal",
            ],
        )
        writer.writeheader()
        writer.writerows(public_rows)

    attempts_path = model_dir / f"rep_{rep_index:02d}_attempts.csv"
    with open(attempts_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rep", "trial_number", "attempt_id", "status"])
        writer.writeheader()
        writer.writerows(attempts_log)

    def _portable(path: Path) -> str:
        # Project-relative when possible; absolute otherwise (e.g. the
        # dry-run gate writes to a temp directory).
        # 가능하면 프로젝트 상대 경로, 아니면 절대 경로(예: dry-run
        # 게이트의 임시 디렉터리).
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)

    entry = {
        "model": model_label,
        "rep": str(rep_index),
        "public_path": _portable(public_path),
        "public_sha256": sha256_of(public_path),
        "attempts_path": _portable(attempts_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    entry.update(manifest_extra)

    manifest_path = model_dir / "generation_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def library_versions() -> Dict[str, str]:
    """Record generation-library versions (pinned at pilot-freeze).
    생성 라이브러리 버전 기록 (pilot-freeze에서 고정)."""
    from importlib import metadata

    versions = {}
    for pkg in ("anthropic", "openai"):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = "not-installed"
    return versions


def parse_rep_range(spec: str) -> List[int]:
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(spec)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["anthropic", "openai"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reps", required=True, help="e.g. 1-5 or 7 / 예: 1-5 또는 7")
    parser.add_argument(
        "--pilot", action="store_true",
        help="write to the pilot directory (excluded from confirmatory data) / "
             "파일럿 디렉터리에 기록 (확증 자료에서 제외)",
    )
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument(
        "--reasoning-effort", default=None,
        help="OpenAI reasoning models only; pinned at pilot-freeze / "
             "OpenAI 추론 모델 전용; pilot-freeze에서 고정",
    )
    args = parser.parse_args()

    from study2.clients import (
        ANTHROPIC_CONFIGS,
        OPENAI_CONFIGS,
        build_anthropic_call,
        build_openai_call,
        load_env,
    )

    load_env()
    if args.provider == "anthropic":
        call_fn = build_anthropic_call(args.model)
        generation_config = ANTHROPIC_CONFIGS[args.model]
    else:
        call_fn = build_openai_call(args.model, args.reasoning_effort)
        generation_config = OPENAI_CONFIGS[args.model]

    out_root = PROJECT_ROOT / ("data/public_study2_pilot" if args.pilot else "data/public_study2")
    model_label = args.model.replace("/", "_")
    manifest_extra = {
        "provider": args.provider,
        "pilot": "1" if args.pilot else "0",
        "library_versions": json.dumps(library_versions(), sort_keys=True),
        # Actual frozen generation config used for every call in this
        # invocation — auditable from the manifest alone (review P1).
        # 이 실행의 모든 호출에 쓰인 동결 생성 설정 — manifest만으로 감사
        # 가능 (검토 P1 반영).
        "generation_config": json.dumps(generation_config, sort_keys=True),
    }

    # Pre-flight overwrite check BEFORE any API call, so a collision
    # costs nothing (the write-time guard remains as defense in depth).
    # API 호출 전 사전 충돌 검사 — 충돌 시 비용 지출 없이 중단 (write
    # 시점 가드는 이중 방어로 유지).
    reps = parse_rep_range(args.reps)
    model_dir = out_root / model_label
    for rep in reps:
        for name in (f"rep_{rep:02d}_public.csv", f"rep_{rep:02d}_attempts.csv"):
            if (model_dir / name).exists():
                raise SystemExit(
                    f"refusing to overwrite {model_dir / name} — archive "
                    f"existing repetition files first / 덮어쓰기 거부 — "
                    f"기존 rep 파일을 먼저 보관하세요"
                )

    for rep in reps:
        rows, log = generate_repetition(call_fn, rep, sleep_seconds=args.sleep)
        entry = write_repetition(model_label, rep, rows, log, out_root, manifest_extra)
        n_fail = sum(1 for r in rows if r["api_error"] == "1" or r["refusal"] == "1")
        print(f"rep {rep:02d}: {len(rows)} trials, {n_fail} ITT-flagged -> {entry['public_path']}")


if __name__ == "__main__":
    main()
