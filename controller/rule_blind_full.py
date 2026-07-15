"""Conditions 2 & 3 — RuleBlind-FeedbackAware (v0, exploratory).
조건 2·3 — RuleBlind-FeedbackAware (v0, 탐색 단계).

The primary condition of ANALYSIS_PLAN.md. The controller behaves like a
human WCST participant's supervisor: it never sees which dimension is
rewarded, but it does see — after each final choice is frozen — whether
that choice turned out correct. Everything it knows about the task state
is inferred from that outcome sequence.

ANALYSIS_PLAN.md의 주 조건. 이 컨트롤러는 사람 WCST 참가자의 감독자처럼
동작한다: 어떤 차원이 보상되는지는 절대 보지 못하지만, 각 최종 선택이
동결된 '이후' 그 선택의 정오는 본다. 과제 상태에 대해 아는 모든 것은 이
정오 시퀀스로부터 추론된다.

Policy (parameters exploratory only until the PILOT-FREEZE tag — the
pilot never touches parameter selection; plan v2.0 §10)
정책 (파라미터는 PILOT-FREEZE 태그 전까지만 탐색 조정 가능 — 파일럿은
파라미터 선택에 관여하지 않는다; 계획 v2.0 10절):

1. Belief tracking / 신뢰 추적: a dimension that was recently rewarded
   repeatedly is the "believed" dimension.
   최근 반복적으로 보상된 차원을 "신뢰 차원"으로 둔다.
2. Change detection / 변화 감지: consecutive errors on the believed
   dimension open a veto window — the moment where the environment has
   probably changed but the LLM (which receives no outcome information
   by design) cannot know it.
   신뢰 차원에서의 연속 오류가 veto window를 연다 — 환경은 아마 바뀌었지만
   (설계상 정오 정보를 받지 못하는) LLM은 그것을 알 수 없는 시점이다.
3. Intervention / 개입: inside the window, if the raw choice equals the
   now-discredited dimension, remap to the most promising alternative.
   window 안에서 원선택이 신뢰를 잃은 그 차원이면 가장 유망한 대안으로
   바꾼다.
4. Stuckness rescue (v1) / 고착 구조 (v1): independent of any window, a
   dimension whose frozen choices keep failing accumulates a failure
   streak; when the raw choice is such a dimension, remap. This covers
   the v0 blind spot — fixation at session start, before any belief has
   formed — and makes the NoVeto ablation meaningful (it isolates the
   window's contribution while rescue stays active).
   window와 무관하게, 동결 선택이 계속 실패하는 차원에는 실패 연속이
   누적된다. 원선택이 그런 차원이면 remap한다. 이는 v0의 맹점 — 신뢰가
   형성되기 전 세션 초반의 고착 — 을 메우고, NoVeto 절제 조건에 의미를
   부여한다(rescue는 유지된 채 window의 기여만 분리).

Condition 3 (ablation) is this same class with veto_window=0.
조건 3(절제)은 같은 클래스에 veto_window=0을 준 것이다.
"""

from __future__ import annotations

from controller.base import RULES, FeedbackAwareController, PublicTrial


class RuleBlindFullController(FeedbackAwareController):
    """Outcome-feedback supervisor for a frozen LLM.
    고정된 LLM을 위한 정오 피드백 기반 감독자."""

    def __init__(
        self,
        error_streak_to_open: int = 1,
        veto_window: int = 4,
        belief_confirm_streak: int = 2,
        value_gain: float = 0.30,
        value_loss: float = 0.30,
        rescue_failure_threshold: int = 2,
        rescue_cooldown: int = 6,
        max_interventions_per_rep: int = 9,
    ) -> None:
        # v1 defaults were chosen by the documented exploratory search
        # (analysis/param_search.py, 288 configs on the archived streams)
        # under the stated constraint set: maximize pooled accuracy
        # subject to persistence <= 9 and intervention rate <= 25% of
        # trials (supervisor regime). EXPLORATORY until the study2-freeze
        # tag; Study 2 runs only after these are frozen.
        # v1 기본값은 공개된 탐색(analysis/param_search.py, 보관 스트림에
        # 대한 288개 설정)에서, 명시된 제약 — 고착 오류 9 이하, 개입률
        # 25% 이하(감독자 체제) 하에서 합산 정확도 최대화 — 로 선택했다.
        # study2-freeze 태그 전까지는 탐색적이며, Study 2는 동결 이후에만
        # 실행한다.
        # Consecutive errors on the believed dimension needed to open the
        # veto window (change detected from outcomes alone).
        # veto window를 열기 위해 필요한, 신뢰 차원에서의 연속 오류 수
        # (정오만으로 변화를 감지).
        self.error_streak_to_open = error_streak_to_open

        # Length of the veto window in trials. veto_window=0 disables all
        # window-based intervention and yields the NoVeto ablation.
        # veto window의 길이(trial 수). 0이면 window 기반 개입이 전부
        # 비활성화되어 NoVeto 절제 조건이 된다.
        self.veto_window = veto_window

        # Consecutive correct outcomes needed before a dimension becomes
        # the believed dimension.
        # 어떤 차원이 신뢰 차원이 되기 위해 필요한 연속 정답 수.
        self.belief_confirm_streak = belief_confirm_streak

        # Value update sizes for correct / incorrect outcomes of the
        # frozen final choices. Values live in [0, 1] per dimension.
        # 동결된 최종 선택의 정오에 따른 가치 갱신 폭. 각 차원의 가치는
        # [0, 1] 범위를 가진다.
        self.value_gain = value_gain
        self.value_loss = value_loss

        # Stuckness rescue: UNRESOLVED failures of a dimension (as the
        # frozen final choice) accumulate and are reset ONLY by that
        # dimension's next correct outcome — not by trials on other
        # dimensions. This cumulative semantics is the intended design
        # (Amendment B §11.6). Threshold 0 disables the rescue path.
        # 고착 구조: 어떤 차원의 (동결된 최종 선택으로서의) '미해결' 실패가
        # 누적되며, 그 차원의 다음 정답으로만 초기화된다 — 다른 차원의
        # trial로는 초기화되지 않는다. 이 누적 의미론이 의도된 설계다
        # (수정안 B 11.6절). 임계값 0이면 rescue 경로 비활성화.
        self.rescue_failure_threshold = rescue_failure_threshold

        # HARD per-repetition intervention budget (Amendment B §11.2):
        # once this many interventions have been made, the controller
        # passes everything through for the rest of the repetition. This
        # enforces the supervisor regime as a constraint rather than a
        # mean tendency.
        # repetition당 하드 개입 예산 (수정안 B 11.2절): 이 횟수만큼
        # 개입하면 남은 trial은 전부 통과시킨다. 감독자 체제를 평균
        # 경향이 아닌 강제 제약으로 만든다.
        self.max_interventions_per_rep = max_interventions_per_rep
        self._interventions_made = 0

        # Minimum trials between rescue interventions. Without this the
        # rescue fires on every raw repetition of a discredited dimension
        # (its failure streak can never reset while it is being remapped),
        # and the controller drifts from supervisor to de-facto player —
        # a regime the parameter search showed raises accuracy but WORSENS
        # perseveration.
        # rescue 개입 사이의 최소 trial 간격. 이것이 없으면 신뢰를 잃은
        # 차원의 원선택 반복마다 rescue가 발화하고(remap되는 동안 그
        # 차원의 실패 연속은 초기화될 수 없다), 컨트롤러가 감독자에서
        # 사실상 선수로 변질된다 — 파라미터 탐색에서 정확도는 오르지만
        # 고착이 '악화'되는 것으로 확인된 체제다.
        self.rescue_cooldown = rescue_cooldown
        self._rescue_cooldown_remaining = 0

        # --- Internal state, all inferred from outcomes only ---
        # --- 내부 상태: 전부 정오로부터만 추론된다 ---

        # Estimated value of each dimension. / 각 차원의 추정 가치.
        self.values = {rule: 0.0 for rule in RULES}

        # The dimension currently believed to be rewarded ("" = none).
        # 현재 보상된다고 신뢰하는 차원 ("" = 없음).
        self.believed: str = ""

        # The dimension that WAS believed until outcomes discredited it.
        # Intervention targets exactly this dimension inside the window.
        # 정오에 의해 신뢰를 잃기 전까지 신뢰되던 차원. window 안의 개입은
        # 정확히 이 차원을 겨냥한다.
        self.discredited: str = ""

        # Streak counters over frozen final choices. / 동결된 최종 선택에
        # 대한 연속 카운터.
        self._correct_streak_choice: str = ""
        self._correct_streak: int = 0
        self._error_streak_on_believed: int = 0

        # Per-dimension consecutive-failure counters over frozen final
        # choices (feeds the rescue path). Reset by a correct outcome of
        # that dimension.
        # 동결된 최종 선택 기준의 차원별 연속 실패 카운터 (rescue 경로에
        # 공급). 해당 차원의 정답으로 초기화된다.
        self._unresolved_failures = {rule: 0 for rule in RULES}

        # Remaining trials of the currently open veto window.
        # 현재 열린 veto window의 남은 trial 수.
        self._window_remaining: int = 0

        # The final choice frozen in the current trial, kept only so the
        # next observe_feedback() knows which choice the outcome is for.
        # 현재 trial에서 동결된 최종 선택. 다음 observe_feedback()이 어느
        # 선택에 대한 정오인지 알기 위해서만 보관한다.
        self._pending_choice: str = ""

        # trial_number each dimension was last tried as a final choice,
        # for outcome-independent tie-breaking.
        # 각 차원이 최종 선택으로 마지막 시도된 trial 번호. 결과와 무관한
        # 동점 해소에 사용한다.
        self._last_tried = {rule: 0 for rule in RULES}
        self._trial_number: int = 0

    # ------------------------------------------------------------------
    # Decision / 결정
    # ------------------------------------------------------------------

    def decide(self, public_trial: PublicTrial, raw_choice: str) -> str:
        self._trial_number = public_trial.trial_number
        if self._rescue_cooldown_remaining > 0:
            self._rescue_cooldown_remaining -= 1
        final_choice = raw_choice

        # Hard budget gate (Amendment B §11.2): once exhausted, every
        # remaining trial passes through untouched.
        # 하드 예산 게이트 (수정안 B 11.2절): 소진 후 남은 trial은 전부
        # 그대로 통과한다.
        budget_left = self._interventions_made < self.max_interventions_per_rep

        # Intervene only while a window is open, and only against the
        # specific dimension that outcomes have discredited. Choices of
        # other dimensions pass through: the controller has no basis to
        # judge them.
        # window가 열려 있는 동안, 정오가 신뢰를 박탈한 바로 그 차원에
        # 대해서만 개입한다. 다른 차원의 선택은 통과시킨다 — 컨트롤러에게
        # 그것을 판단할 근거가 없기 때문이다.
        if (
            budget_left
            and self._window_remaining > 0
            and raw_choice in RULES
            and raw_choice == self.discredited
        ):
            final_choice = self._best_alternative(excluding=raw_choice)
        elif (
            budget_left
            and self.rescue_failure_threshold > 0
            and self._rescue_cooldown_remaining == 0
            and raw_choice in RULES
            and self._unresolved_failures[raw_choice] >= self.rescue_failure_threshold
        ):
            # Stuckness rescue (v1): this dimension has failed repeatedly
            # as a frozen choice, yet the LLM (which by design never sees
            # outcomes) is still proposing it. Remap regardless of any
            # window.
            # 고착 구조 (v1): 이 차원은 동결 선택으로서 반복 실패했는데도
            # (설계상 정오를 못 보는) LLM이 계속 제안하고 있다. window와
            # 무관하게 remap한다.
            final_choice = self._best_alternative(excluding=raw_choice)
            self._rescue_cooldown_remaining = self.rescue_cooldown

        if final_choice != raw_choice:
            self._interventions_made += 1

        if final_choice in RULES:
            self._last_tried[final_choice] = self._trial_number

        # Freeze: remember what we committed to, so the upcoming feedback
        # can be attributed to it. Nothing below this line can change
        # final_choice.
        # 동결: 곧 도착할 정오를 귀속시키기 위해 확정한 선택을 기억한다.
        # 이 지점 이후 어떤 것도 final_choice를 바꿀 수 없다.
        self._pending_choice = final_choice
        return final_choice

    def _best_alternative(self, excluding: str) -> str:
        """Pick the most promising non-discredited alternative.
        신뢰를 잃지 않은 대안 중 가장 유망한 것을 고른다.

        v2: the currently discredited dimension is also excluded from the
        candidate set. Its estimated value is still high right after it
        stops being rewarded (value carried over from its successful
        streak), so a purely value-ranked choice tends to remap INTO it —
        the exact perseveration this controller exists to reduce. Study 1
        showed this as Full carrying MORE persistence errors than the
        yoked-random placebo. With three dimensions this exclusion leaves
        at least one candidate whenever the discredited dimension differs
        from the excluded raw choice; otherwise the value ranking applies
        to the remaining two.
        v2: 현재 신뢰를 잃은 차원도 후보에서 제외한다. 보상이 끝난 직후
        그 차원의 추정 가치는 (성공 연속에서 이월되어) 여전히 높아, 순수
        가치 순위 선택은 오히려 그 차원으로 remap하는 경향이 있다 — 이
        컨트롤러가 줄이려는 바로 그 고착이다. Study 1에서 이 편향은 Full이
        yoked-random 위약보다 고착 오류가 '많은' 것으로 나타났다. 차원이
        셋이므로, 신뢰 상실 차원이 제외 대상 원선택과 다르면 후보는 최소
        하나 남고, 같으면 나머지 둘에 가치 순위가 적용된다.

        Ranking: higher estimated value first; ties resolved by the least
        recently tried dimension, then by fixed RULES order. Every input
        to this ranking is outcome-derived or public — never the identity
        of the currently rewarded dimension.
        순위: 추정 가치가 높은 것 우선, 동점은 가장 오래 시도되지 않은
        차원, 그다음 RULES 고정 순서로 해소. 이 순위의 모든 입력은 정오
        파생값 또는 공개 정보이며, 현재 보상되는 차원의 정체는 절대
        사용되지 않는다.
        """
        alternatives = [r for r in RULES if r != excluding and r != self.discredited]
        if not alternatives:
            alternatives = [r for r in RULES if r != excluding]
        return max(
            alternatives,
            key=lambda r: (self.values[r], -self._last_tried[r], -RULES.index(r)),
        )

    # ------------------------------------------------------------------
    # Feedback / 피드백
    # ------------------------------------------------------------------

    def observe_feedback(self, correct: bool) -> None:
        choice = self._pending_choice
        self._pending_choice = ""

        # The window clock ticks once per completed trial.
        # window 시계는 trial이 하나 끝날 때마다 한 칸 줄어든다.
        if self._window_remaining > 0:
            self._window_remaining -= 1

        if choice not in RULES:
            # An unparsable frozen choice carries no attributable
            # information about any dimension.
            # 파싱 불가 선택의 정오는 어떤 차원에도 귀속시킬 수 없다.
            return

        if correct:
            self.values[choice] = min(1.0, self.values[choice] + self.value_gain)
            self._unresolved_failures[choice] = 0

            # Extend or start the correct streak for this dimension.
            # 이 차원의 연속 정답을 잇거나 새로 시작한다.
            if choice == self._correct_streak_choice:
                self._correct_streak += 1
            else:
                self._correct_streak_choice = choice
                self._correct_streak = 1

            # Enough consecutive successes → this dimension becomes (or
            # stays) the believed one, and any open window closes: the
            # system has re-stabilised.
            # 연속 성공이 충분하면 이 차원이 신뢰 차원이 되고(유지되고),
            # 열려 있던 window는 닫힌다: 시스템이 다시 안정된 것이다.
            if self._correct_streak >= self.belief_confirm_streak:
                if self.believed != choice:
                    self.believed = choice
                self.discredited = ""
                self._window_remaining = 0
                self._error_streak_on_believed = 0
        else:
            self.values[choice] = max(0.0, self.values[choice] - self.value_loss)
            self._correct_streak_choice = ""
            self._correct_streak = 0
            self._unresolved_failures[choice] += 1

            # Errors on the believed dimension are the change signal.
            # 신뢰 차원에서의 오류가 곧 변화 신호다.
            if self.believed and choice == self.believed:
                self._error_streak_on_believed += 1
                if (
                    self._error_streak_on_believed >= self.error_streak_to_open
                    and self.veto_window > 0
                ):
                    # Open the window: demote the believed dimension to
                    # discredited and start the countdown.
                    # window 개방: 신뢰 차원을 '신뢰 상실'로 강등하고
                    # 카운트다운을 시작한다.
                    self.discredited = self.believed
                    self.believed = ""
                    self._error_streak_on_believed = 0
                    self._window_remaining = self.veto_window
