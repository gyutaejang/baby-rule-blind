"""Base interfaces for rule-blind controllers.
rule-blind 컨트롤러의 기본 인터페이스.

STRICT ISOLATION RULE / 엄격한 격리 규칙:
This package must never see ground-truth information. Controllers receive
only (1) the public trial (trial number + prompt text), (2) the raw LLM
choice, and — for feedback-aware controllers only — (3) a single boolean
outcome delivered AFTER the final choice for that trial has been frozen.

이 패키지는 ground truth 정보를 절대 볼 수 없다. 컨트롤러가 받는 것은
(1) 공개 trial 정보(trial 번호 + 프롬프트 텍스트), (2) LLM의 원선택,
그리고 feedback-aware 컨트롤러에 한해 (3) 해당 trial의 최종 선택이 동결된
"이후"에 전달되는 단일 boolean 정오뿐이다.

A CI check (scripts/check_banned_tokens.py) rejects any occurrence of
ground-truth-related tokens in this package, including in comments.
CI 검사(scripts/check_banned_tokens.py)가 이 패키지 안의 ground truth 관련
토큰 사용을 주석까지 포함해 전부 차단한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


# The three sorting dimensions of the WCST-style task. This is public
# knowledge: the prompt itself tells the LLM to choose one of these.
# WCST형 과제의 세 분류 차원. 프롬프트 자체가 이 중 하나를 고르라고
# 알려주므로 공개 정보이다.
RULES = ("color", "shape", "number")


@dataclass(frozen=True)
class PublicTrial:
    """The ONLY trial information a controller may observe.
    컨트롤러가 관찰할 수 있는 '유일한' trial 정보.

    Deliberately excluded / 의도적으로 제외된 것:
    block numbers, within-block positions, lure flags, and anything else
    derived from the task schedule — those encode when the sorting rule
    changes and therefore live on the evaluator side only.
    블록 번호, 블록 내 위치, lure 플래그 등 과제 일정에서 파생되는 모든
    정보 — 이것들은 분류 규칙이 언제 바뀌는지를 인코딩하므로 평가기
    쪽에만 둔다.
    """

    # 1-based position of this trial in the session (public: the
    # controller may know how far along the session is).
    # 세션 내 1부터 시작하는 trial 위치 (공개 정보: 컨트롤러는 세션이
    # 얼마나 진행됐는지 알 수 있다).
    trial_number: int

    # The exact prompt text shown to the LLM, including the card
    # description. Public by definition.
    # LLM에 제시된 프롬프트 원문(카드 설명 포함). 정의상 공개 정보.
    prompt: str


class RuleBlindController(ABC):
    """Abstract base for all controllers in this study.
    본 연구의 모든 컨트롤러가 상속하는 추상 기반 클래스.

    Contract / 규약:
        final_choice = controller.decide(public_trial, raw_choice)
    The returned value is FROZEN: nothing the controller learns afterwards
    can change it. Scoring happens outside this package.
    반환값은 '동결'된다: 이후에 컨트롤러가 무엇을 알게 되든 이 값은 바뀔
    수 없다. 채점은 이 패키지 바깥에서 이루어진다.
    """

    # Whether the replay harness is allowed to call observe_feedback()
    # on this controller. Feedback-free controllers keep this False.
    # replay harness가 이 컨트롤러에 observe_feedback()을 호출해도 되는지
    # 여부. feedback-free 컨트롤러는 False를 유지한다.
    feedback_aware: bool = False

    @abstractmethod
    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        """Return the final choice for this trial, given only public info.
        공개 정보만으로 이 trial의 최종 선택을 반환한다.

        Args / 인자:
            public_trial: the public view of the current trial.
                          현재 trial의 공개 정보.
            raw_choice:   the LLM's parsed raw choice ("color" / "shape" /
                          "number", or "" if unparsable).
                          LLM의 파싱된 원선택 ("color"/"shape"/"number",
                          파싱 불가면 "").

        Returns / 반환:
            The frozen final choice. / 동결되는 최종 선택.
        """

    def observe_feedback(self, correct: bool) -> None:
        """Receive the outcome of the ALREADY-FROZEN final choice.
        '이미 동결된' 최종 선택의 정오를 수신한다.

        Only called by the harness, only after scoring, and only when
        feedback_aware is True. The default implementation raises so that
        a harness bug (calling this on a feedback-free controller) fails
        loudly instead of leaking information silently.
        harness만 호출하며, 채점 이후에만, feedback_aware가 True일 때만
        호출된다. 기본 구현은 예외를 던진다 — harness 버그로 feedback-free
        컨트롤러에 호출될 경우 정보가 조용히 새는 대신 즉시 실패하도록.
        """
        raise RuntimeError(
            "observe_feedback() called on a feedback-free controller "
            "(harness bug). / feedback-free 컨트롤러에 observe_feedback()이 "
            "호출되었습니다 (harness 버그)."
        )


class FeedbackAwareController(RuleBlindController):
    """Base for controllers that may use post-decision outcome feedback.
    확정 이후의 정오 피드백을 사용할 수 있는 컨트롤러의 기반 클래스.

    Terminology fixed in ANALYSIS_PLAN.md: these are described as
    "rule-blind, outcome-feedback" controllers — they never observe which
    dimension is currently rewarded, only whether their own frozen
    choices turned out correct.
    ANALYSIS_PLAN.md에 고정된 용어: 이들은 "rule-blind, outcome-feedback"
    컨트롤러로 기술한다 — 현재 어떤 차원이 보상되는지는 절대 관찰하지
    못하고, 자신이 동결한 선택의 정오만 관찰한다.
    """

    feedback_aware: bool = True

    @abstractmethod
    def observe_feedback(self, correct: bool) -> None:
        """Consume the outcome of the most recently frozen final choice.
        가장 최근에 동결된 최종 선택의 정오를 소비한다."""
