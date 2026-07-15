"""API clients for Study 2 stream generation (plan v2.0 §5).
Study 2 스트림 생성용 API 클라이언트 (계획 v2.0 5절).

Design rules / 설계 규칙:
- Lazy imports: the replay/analysis side stays standard-library-only;
  `anthropic` / `openai` are imported only when a live client is built.
  지연 임포트: replay·분석 측은 표준 라이브러리 전용을 유지하고,
  `anthropic`/`openai`는 실제 클라이언트 생성 시에만 임포트한다.
- Keys come from `.env` via a stdlib loader and are NEVER printed,
  logged, or written to any output file.
  키는 표준 라이브러리 로더로 `.env`에서 읽으며 어떤 출력에도 남기지
  않는다.
- Each call returns (text, status) where status is "ok", "refusal", or
  "api_error"; the runner applies the frozen retry/ITT rules.
  각 호출은 (text, status)를 반환하며 status는 ok/refusal/api_error.
  재시도·ITT 규칙은 runner가 적용한다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Dict, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Per-model generation config, frozen in plan v2.0 §5. OpenAI entries are
# added (and IDs pinned) at pilot-freeze.
# 모델별 생성 설정 (계획 v2.0 5절에서 동결). OpenAI 항목은 pilot-freeze
# 시점에 추가·고정한다.
# Pinned OpenAI generation config (pilot-freeze-v2, 2026-07-15): exact
# confirmatory IDs and the lowest accepted reasoning setting. The runner
# refuses any other value so the frozen setting is ENFORCED, not advisory
# (external review P1, 2026-07-15).
# 고정된 OpenAI 생성 설정 (pilot-freeze-v2): 확증 모델 ID와 최저 추론
# 설정. 러너는 다른 값을 거부한다 — 동결 설정은 권고가 아니라 강제다
# (외부 검토 P1 반영).
OPENAI_CONFIGS: Dict[str, Dict] = {
    "gpt-5.5-2026-04-23": {"reasoning_effort": "none"},
    "gpt-5.4-mini-2026-03-17": {"reasoning_effort": "none"},
}

ANTHROPIC_CONFIGS: Dict[str, Dict] = {
    # Opus 4.8: thinking omitted -> runs without thinking (default).
    "claude-opus-4-8": {"max_tokens": 64, "thinking": None},
    # Sonnet 5: adaptive-by-default, so disable explicitly.
    "claude-sonnet-5": {"max_tokens": 64, "thinking": {"type": "disabled"}},
    # Fable 5: thinking cannot be disabled -> omit, minimize via effort,
    # give headroom because thinking tokens count toward max_tokens.
    "claude-fable-5": {
        "max_tokens": 2000,
        "thinking": None,
        "output_config": {"effort": "low"},
    },
}


def load_env(path: Path = PROJECT_ROOT / ".env") -> None:
    """Stdlib .env loader — values go into os.environ only.
    표준 라이브러리 .env 로더 — 값은 os.environ에만 들어간다."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


CallFn = Callable[[str], Tuple[str, str]]


def build_anthropic_call(model_id: str) -> CallFn:
    """Live Anthropic call function. / 실제 Anthropic 호출 함수."""
    import anthropic  # lazy / 지연

    if model_id not in ANTHROPIC_CONFIGS:
        raise SystemExit(f"no frozen config for model {model_id} / 동결된 설정 없음")
    config = ANTHROPIC_CONFIGS[model_id]
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    def call(prompt: str) -> Tuple[str, str]:
        kwargs: Dict = {
            "model": model_id,
            "max_tokens": config["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        }
        if config.get("thinking") is not None:
            kwargs["thinking"] = config["thinking"]
        if config.get("output_config") is not None:
            kwargs["output_config"] = config["output_config"]
        try:
            response = client.messages.create(**kwargs)
        except Exception:
            # Never include exception details that could echo headers.
            # 헤더를 되울릴 수 있는 예외 상세는 기록하지 않는다.
            return "", "api_error"
        if getattr(response, "stop_reason", None) == "refusal":
            return "", "refusal"
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return text, "ok"

    return call


def build_openai_call(model_id: str, reasoning_effort: str | None = None) -> CallFn:
    """Live OpenAI call function; exact model IDs and reasoning settings
    are pinned at pilot-freeze and ENFORCED here.
    실제 OpenAI 호출 함수; 모델 ID·추론 설정은 pilot-freeze에서 고정되며
    여기서 강제된다."""
    from openai import OpenAI  # lazy / 지연

    if model_id not in OPENAI_CONFIGS:
        raise SystemExit(f"no frozen config for model {model_id} / 동결된 설정 없음")
    pinned = OPENAI_CONFIGS[model_id]["reasoning_effort"]
    if reasoning_effort is not None and reasoning_effort != pinned:
        raise SystemExit(
            f"reasoning_effort {reasoning_effort!r} conflicts with the frozen "
            f"value {pinned!r} for {model_id} / 동결 값과 충돌"
        )
    reasoning_effort = pinned

    client = OpenAI()  # reads OPENAI_API_KEY from env

    def call(prompt: str) -> Tuple[str, str]:
        kwargs: Dict = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
        }
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort
        try:
            response = client.chat.completions.create(**kwargs)
        except Exception:
            return "", "api_error"
        text = response.choices[0].message.content or ""
        return text, "ok"

    return call
