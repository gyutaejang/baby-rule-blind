"""Study 2b — WCD-minimal (Wait–Consider–Discriminate) supervisor.
Study 2b — WCD-minimal (Wait–Consider–Discriminate) 감독자.

MOTIVATION (from the LOCKED Study 2 results, 2026-07-15): RuleBlindFull
REVERSED (worsened) prev-rule-aligned errors on both Anthropic models
while replicating the trade-off only on gpt-5.5. The open question is
whether the reversal is caused by Full's protection stack (veto window,
rescue, cooldown) or by outcome-driven hypothesis tracking itself. This
controller strips the stack to the minimum: decayed evidence scores, one
active hypothesis, a WAIT threshold, and a DISCRIMINATE margin. If the
minimal form is non-inferior to Full, parsimony wins; if it is worse,
the protections earn their complexity.

동기 (2026-07-15 잠금된 Study 2 결과에서): RuleBlindFull은 두 Anthropic
모델에서 이전 규칙 정렬 오류를 오히려 '악화'시켰고 트레이드오프는
gpt-5.5에서만 재현되었다. 남은 질문은 그 역전이 Full의 보호 장치
스택(veto window, rescue, cooldown) 때문인지, 정오 기반 가설 추적 자체
때문인지다. 이 컨트롤러는 스택을 최소한으로 걷어낸다: 감쇠 증거 점수,
단일 활성 가설, WAIT 문턱, DISCRIMINATE 마진. 최소형이 Full에
비열등하면 절약 원리가 이기고, 열등하면 보호 장치의 복잡성이 정당화된다.

Scaffold mapping (fixed terminology: "WCD scaffold")
비계 대응 (고정 용어: "WCD scaffold"):

- WAIT:         no hypothesis switch before `wait_threshold` consecutive
                errors of the active hypothesis (as the frozen choice).
                활성 가설(동결 선택 기준)의 연속 오류가 `wait_threshold`
                미만이면 가설을 교체하지 않는다.
- CONSIDER:     every outcome updates a per-dimension evidence score
                with fixed decay: s <- decay * s, then ±1 to the chosen
                dimension, clipped to [-score_clip, +score_clip].
                모든 정오가 차원별 증거 점수를 갱신한다: s <- decay * s
                후 선택 차원에 ±1, [-score_clip, +score_clip]으로 clip.
- DISCRIMINATE: switch only when the best alternative's score exceeds
                the active hypothesis's score by more than
                `switch_margin`.
                최선 대안의 점수가 활성 가설보다 `switch_margin` 초과로
                우세할 때만 전환한다.
- ACT:          while a hypothesis is active, remap any other parsed raw
                choice to it (hard budget shared with the co-primary
                supervisors). No hypothesis -> pass through.
                가설이 활성인 동안 다른 파싱된 원선택을 가설로 remap
                (공동 주 감독자들과 동일한 하드 예산). 가설 없음 ->
                통과.

Everything this controller knows is outcome-derived or public; the
information channel is identical to RuleBlindFull and WSLSBudgeted
(post-freeze boolean outcomes only).
이 컨트롤러가 아는 모든 것은 정오 파생값 또는 공개 정보다. 정보 채널은
RuleBlindFull·WSLSBudgeted와 동일하다 (동결 후 boolean 정오만).

Parameters were calibrated by analysis/calibrate_wcd_minimal.py on the
archived Study 1 streams ONLY (never on any Study 2 or Study 2b data)
and are frozen at the study2b-freeze tag, before any fresh confirmatory
stream is generated (STUDY2B_PLAN.md, including the boundary-selection
disclosure).
파라미터는 analysis/calibrate_wcd_minimal.py가 '보관된 Study 1
스트림에서만' calibration했으며 (Study 2·2b 자료는 절대 사용 금지),
확증용 신규 스트림 생성 전 study2b-freeze 태그에서 동결된다
(STUDY2B_PLAN.md, 경계값 선택 공개 포함).
"""

from __future__ import annotations

from controller.base import RULES, FeedbackAwareController, PublicTrial


class WCDMinimalController(FeedbackAwareController):
    """Minimal evidence-accumulation supervisor. / 최소 증거 누적 감독자."""

    def __init__(
        self,
        decay: float = 0.5,
        switch_margin: float = 0.0,
        wait_threshold: int = 1,
        score_clip: float = 5.0,
        max_interventions_per_rep: int = 9,
    ) -> None:
        # Defaults are the A0-calibrated values selected by the codified
        # rule in analysis/calibrate_wcd_minimal.py on the archived
        # Study 1 streams (STUDY2B_PLAN.md §3, boundary selection
        # disclosed there). Same convention as RuleBlindFull's v1
        # defaults.
        # 기본값은 analysis/calibrate_wcd_minimal.py의 코드화된 규칙이
        # 보관 Study 1 스트림에서 선택한 A0 calibration 값이다
        # (STUDY2B_PLAN.md 3절, 경계값 선택 공개 포함). RuleBlindFull v1
        # 기본값과 같은 관행.
        # CONSIDER: forgetting factor applied to ALL scores before each
        # update. decay=1.0 disables forgetting.
        # CONSIDER: 매 갱신 전 모든 점수에 적용되는 망각 계수. 1.0이면
        # 망각 없음.
        self.decay = decay

        # DISCRIMINATE: required evidence lead of the best alternative
        # over the active hypothesis before a switch is allowed.
        # DISCRIMINATE: 전환 허용에 필요한, 최선 대안의 활성 가설 대비
        # 증거 우세 폭.
        self.switch_margin = switch_margin

        # WAIT: consecutive errors of the active hypothesis (as frozen
        # choice) required before a switch is even considered.
        # WAIT: 전환을 '검토'하기 위해 필요한 활성 가설(동결 선택)의
        # 연속 오류 수.
        self.wait_threshold = wait_threshold

        # Score bound; keeps early streaks from locking in forever.
        # 점수 한계; 초기 연속 성공이 영구 고착되는 것을 막는다.
        self.score_clip = score_clip

        # Hard per-repetition budget, matched to the co-primary
        # supervisors (RuleBlindFull / WSLSBudgeted use 9).
        # repetition당 하드 예산 — 공동 주 감독자들(9)과 일치.
        self.max_interventions_per_rep = max_interventions_per_rep
        self._interventions_made = 0

        # --- State (outcome-derived only) / 상태 (정오 파생만) ---

        # Per-dimension evidence scores. / 차원별 증거 점수.
        self.scores = {rule: 0.0 for rule in RULES}

        # Active hypothesis ("" = none yet: pass everything through).
        # 활성 가설 ("" = 아직 없음: 전부 통과).
        self.hypothesis: str = ""

        # Consecutive errors of the active hypothesis as frozen choice.
        # 동결 선택으로서의 활성 가설 연속 오류 수.
        self.error_streak: int = 0

        # Frozen choice awaiting its outcome. / 정오를 기다리는 동결 선택.
        self._pending_choice: str = ""

        # Last trial each dimension was the final choice — outcome-
        # independent tie-breaking, same convention as the other
        # supervisors.
        # 각 차원이 최종 선택이었던 마지막 trial — 결과 무관 동점 해소,
        # 다른 감독자들과 동일한 관행.
        self._last_tried = {rule: 0 for rule in RULES}
        self._trial_number: int = 0

    # ------------------------------------------------------------------
    # ACT / 행동
    # ------------------------------------------------------------------

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        self._trial_number = public_trial.trial_number
        final_choice = raw_choice

        budget_left = self._interventions_made < self.max_interventions_per_rep

        # While a hypothesis is active, steer parsed choices toward it.
        # Unparsable choices ("") pass through, as in every supervisor.
        # 가설이 활성인 동안 파싱된 선택을 가설로 유도한다. 파싱 불가("")
        # 는 다른 감독자들과 마찬가지로 통과시킨다.
        if (
            budget_left
            and raw_choice in RULES
            and self.hypothesis
            and raw_choice != self.hypothesis
        ):
            final_choice = self.hypothesis

        if final_choice != raw_choice:
            self._interventions_made += 1
        if final_choice in RULES:
            self._last_tried[final_choice] = self._trial_number

        # Freeze. / 동결.
        self._pending_choice = final_choice
        return final_choice

    # ------------------------------------------------------------------
    # WAIT -> CONSIDER -> DISCRIMINATE / 대기 -> 검토 -> 변별
    # ------------------------------------------------------------------

    def observe_feedback(self, correct: bool) -> None:
        choice = self._pending_choice
        self._pending_choice = ""
        if choice not in RULES:
            # Outcome of an unparsable frozen choice attributes to no
            # dimension. / 파싱 불가 동결 선택의 정오는 어떤 차원에도
            # 귀속되지 않는다.
            return

        # CONSIDER: decay all scores, then update the chosen dimension.
        # CONSIDER: 전 점수 감쇠 후 선택 차원 갱신.
        for rule in RULES:
            self.scores[rule] *= self.decay
        delta = 1.0 if correct else -1.0
        self.scores[choice] = max(
            -self.score_clip, min(self.score_clip, self.scores[choice] + delta)
        )

        if correct:
            if not self.hypothesis:
                # First success adopts the hypothesis (before that, the
                # controller has no basis to steer anything).
                # 첫 성공이 가설을 채택한다 (그 전에는 유도할 근거가 없다).
                self.hypothesis = choice
            if choice == self.hypothesis:
                self.error_streak = 0
            return

        if choice != self.hypothesis:
            # Errors off-hypothesis say nothing about the hypothesis.
            # 가설 밖 선택의 오류는 가설에 대해 아무것도 말하지 않는다.
            return

        self.error_streak += 1

        # WAIT: below threshold, hold. / WAIT: 문턱 미만이면 보류.
        if self.error_streak < self.wait_threshold:
            return

        # DISCRIMINATE: switch only on sufficient evidence lead.
        # DISCRIMINATE: 충분한 증거 우세가 있을 때만 전환.
        alternative = self._best_alternative()
        if self.scores[alternative] - self.scores[self.hypothesis] > self.switch_margin:
            self.hypothesis = alternative
            self.error_streak = 0

    def _best_alternative(self) -> str:
        """Highest-scoring non-hypothesis dimension; ties resolved by the
        least recently tried, then fixed RULES order — identical
        convention to the other supervisors, all inputs outcome-derived
        or public.
        가설이 아닌 차원 중 최고 점수; 동점은 가장 오래 시도되지 않은
        차원, 그다음 RULES 고정 순서 — 다른 감독자들과 동일한 관행이며
        모든 입력은 정오 파생값 또는 공개 정보다."""
        alternatives = [r for r in RULES if r != self.hypothesis]
        return max(
            alternatives,
            key=lambda r: (self.scores[r], -self._last_tried[r], -RULES.index(r)),
        )
