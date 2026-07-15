"""Condition 1 — RawLLM / No Controller.
조건 1 — RawLLM / 컨트롤러 없음.

The baseline condition of ANALYSIS_PLAN.md: the raw LLM choice is passed
through unchanged. Kept as an explicit class (rather than skipping the
controller step) so that every condition flows through the identical
harness code path.
ANALYSIS_PLAN.md의 기준선 조건: LLM 원선택을 그대로 통과시킨다. 컨트롤러
단계를 건너뛰는 대신 명시적 클래스로 두는 이유는, 모든 조건이 완전히
동일한 harness 코드 경로를 지나가게 하기 위해서다.
"""

from __future__ import annotations

from controller.base import PublicTrial, RuleBlindController


class PassthroughController(RuleBlindController):
    """Returns the raw choice unchanged. / 원선택을 그대로 반환한다."""

    feedback_aware = False

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        # No intervention, ever. Unparsable responses ("") also pass
        # through unchanged so the baseline reflects the LLM as-is.
        # 어떤 개입도 하지 않는다. 파싱 불가 응답("")도 그대로 통과시켜
        # 기준선이 LLM의 원래 모습을 반영하게 한다.
        return raw_choice
