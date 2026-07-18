# Model-Authored State Carryover — Feasibility Design (Exploratory)
# 모델 작성 상태 이월 — 타당성 설계 (탐색)

**Status / 상태**: DESIGN DOCUMENT — no code exists yet; nothing here is
frozen. This extension is EXPLORATORY and feasibility-scoped: it may appear
in the paper only with feasibility claims (§6). The causal test of the state
(perturbation battery) belongs to a separately pre-registered Study 3 (§8).
**설계 문서 — 코드 없음, 미동결.** 이 확장은 탐색·타당성 한정이며, 논문에는
타당성 주장(6절)까지만 실을 수 있다. 상태의 인과 검증(조작 배터리)은 별도
사전등록 Study 3의 몫이다(8절).

## 1. Question / 질문

Study 2/2b place the WCD scaffold in an EXTERNAL supervisor. Can the same
functional structure be maintained by the MODEL ITSELF, using an externally
persisted, model-authored state as its only memory across single-turn calls?
Study 2·2b는 WCD 비계를 '외부 감독자'에 둔다. 같은 기능 구조를, 단일 턴
호출 사이의 유일한 기억인 '외부 보존·모델 작성 상태'로 '모델 스스로'
유지할 수 있는가?

## 2. Architecture: the neutral transport layer / 구조: 중립 통신 계층

Per trial, an interactive harness runs:
trial마다 인터랙티브 하네스가 다음을 수행한다:

1. build prompt = frozen template + trial stimulus + previous public
   feedback ("correct"/"incorrect"/null) + canonical prior state (or null);
2. one model call; freeze the parsed `choice`;
3. score the frozen choice (scoring module returns ONLY the boolean to the
   transport layer — the schedule never enters this process's readable
   paths, mirroring the two-stage blindness of the batch runner);
4. parse + schema-validate the model's `new_state`; canonicalize; store;
5. next trial receives the canonical state verbatim.

**Allowed transport operations / 허용 연산**: store previous choice, store
the environment boolean, store the model-authored state, validate against
the schema, drop non-schema fields and extra text, normalize key order and
number formatting.
**Forbidden / 금지**: computing belief scores; judging which candidate
leads; ordering or thresholding switches; supplying defaults for missing
fields; repairing values; adding ANY field the model did not output;
injecting schedule-derived information of any kind (shift timing, rewarded
dimension, old/new rule identity, oracle-derived recommendations).
If the harness computes state, the condition collapses into an external
controller (Study 2's A) and the design is void.
금지: belief 점수 계산, 우세 후보 판정, 전환 지시, 누락 필드 기본값 보충,
값 교정, 모델이 출력하지 않은 필드 추가, 일정 파생 정보 일체 주입. 하네스가
상태를 계산하는 순간 이 조건은 외부 컨트롤러(A)로 붕괴하며 설계는 무효다.

## 3. I/O schema / 입출력 스키마

Trial input (harness → model) / 시행 입력:

```json
{
  "trial_input": {"stimulus": "<card line>", "available_choices": ["color", "shape", "number"]},
  "previous_environment_feedback": "incorrect",
  "prior_model_state": {
    "belief_scores": {"color": -2, "shape": 1, "number": 0},
    "active_hypothesis": "color",
    "error_streak": 2
  }
}
```

Model output (model → harness) / 모델 출력:

```json
{
  "new_state": {
    "belief_scores": {"color": -3, "shape": 2, "number": 0},
    "active_hypothesis": "shape",
    "error_streak": 0,
    "decision": "switch",
    "evidence_margin": 2
  },
  "choice": "shape"
}
```

Plus one MANDATORY plain-text fallback line outside the JSON
(`Choice: <dimension>`) so behavioral choice survives JSON breakage —
lesson from the pilot parser-tolerance history.
JSON 밖에 평문 fallback 한 줄(`Choice: <dimension>`)을 의무화한다 — JSON이
깨져도 행동 선택이 살아남게 (파서 허용치 이력의 교훈).

Scaffold-to-variable mapping (no free-text rationales — observable state
only) / 비계-변수 대응 (자유 서술 없음, 관찰 가능한 상태만):

| Concept | Measured variable / 측정 변수 |
|---|---|
| WAIT | `decision` (maintain/switch), `error_streak` |
| CONSIDER | `belief_scores` per candidate |
| DISCRIMINATE | `evidence_margin`, `active_hypothesis` |
| ACT | `choice` |

## 4. Invalid-output rules (frozen before any run) / 무효 출력 규칙 (실행 전 동결)

- `choice` and `new_state` are parsed INDEPENDENTLY.
  `choice`와 `new_state`는 '독립적으로' 파싱한다.
- Valid choice + invalid state → trial KEPT in behavioral analyses, state
  recorded as missing for process analyses.
  선택 유효·상태 무효 → 행동 분석 유지, 과정 분석 결측.
- Invalid state → next trial receives `"prior_model_state": null` plus the
  fixed literal `"state_status": "previous_state_invalid"` — never a
  reconstructed or defaulted state.
  상태 무효 → 다음 시행은 `null` + 고정 리터럴 오류 표시만 받는다 —
  재구성·기본값 상태 금지.
- No manual repair; no semantic auto-repair; no numeric correction.
  수동 수정·의미 기반 자동 복구·수치 교정 금지.
- Feasibility MAIN analysis uses NO retries: failure is the measurement.
  A single format-only retry ("Return valid JSON matching the schema.",
  fixed verbatim) is logged as a SEPARATE descriptive arm, never merged.
  타당성 본 분석은 재시도 없음 — 실패 자체가 측정값이다. 형식 전용 1회
  재시도는 사전 고정 문구로 별도 기술 분석으로만 기록하며 병합 금지.

## 5. Feasibility conditions (small-N pilot) / 타당성 조건 (소규모)

| Condition | Carried across trials / 이월 정보 |
|---|---|
| Stateless | current stimulus only / 현재 자극만 |
| PublicHistory | prior choices + feedback list (no state) / 선택·피드백 이력 |
| WCDState | schema of §3 / 3절 스키마 |

Token-matched and shuffled-scaffold controls, plus NeutralState (same JSON
shape, semantically neutral field names), are DEFERRED to Study 3 — the
feasibility question does not require them, and running them underpowered
here would only burn their novelty.
Token-matched·shuffled·NeutralState 대조는 Study 3로 미룬다 — 타당성 질문에
불필요하며, 저검정력으로 소진하면 손해다.

Scale / 규모: 3–5 reps × 36 trials × 2 models (one Anthropic, one OpenAI,
the pinned confirmatory IDs) per condition. Sample size is set by the
precision of failure-rate estimates (95% CI half-width ≤ ~10pp at n=108–180
trials/model/condition), NOT by effect power — effects here are descriptive.
표본은 효과 검정력이 아니라 실패율 추정 정밀도로 정한다. 효과는 기술
전용이다.

## 6. Pre-specified feasibility metrics / 사전 지정 타당성 지표

Reported per model × condition; these, and only these, ground the paper's
feasibility claims / 모델×조건별 보고; 논문의 타당성 주장은 이것으로만
근거를 갖는다:

1. `choice` parse success rate (JSON and fallback line separately).
2. Full `new_state` schema validity rate.
3. Valid-choice-with-invalid-state rate.
4. State-stasis rate: trials where `belief_scores` are an exact copy of the
   prior state (a model that never updates is not maintaining memory).
   상태 정체율: 이전 상태의 단순 복사 비율 (갱신 없는 모델은 기억 유지가
   아니다).
5. Inter-trial state-change rate and direction consistency with feedback
   (score of the fed-back dimension moves the correct way).
6. `active_hypothesis`–`choice` agreement rate.
7. State size / token overhead per condition.
8. Post-invalid-state recovery rate (does the loop resume producing valid
   states after a null injection?).

Permitted abstract-level claim, fixed now / 지금 고정하는 초록 수준 주장:
"externally persisting model-authored structured state across single-turn
calls was technically feasible; states updated across trials and their use
was directionally consistent with improved behavior." FORBIDDEN until Study
3: causal control by the state, genuine internal memory, superiority of WCD
semantics over plain history or JSON formatting.
허용 주장: "기술적으로 실행 가능했고, 상태가 갱신되었으며 행동 개선과
방향이 일치했다"까지. 금지(Study 3 전): 상태의 인과 통제, 진정한 내부 기억,
단순 이력·JSON 형식 대비 WCD 의미 구조의 우월성.

## 7. Isolation tests (first commit of any Study 3 code) / 격리 테스트 (첫 커밋)

1. **Public-history invariance / 공개 이력 불변성**: identical stimuli,
   choices, and public feedback with a different underlying schedule must
   produce byte-identical prompts and canonical states.
2. **Transport-only / 운반 전용**: model-output state and next-trial
   delivered state are semantically identical (key order/format
   normalization allowed; value changes, field creation/deletion, defaults
   forbidden).
3. **Derived-information block / 파생 정보 차단**: banned-token scope
   extends to the transport layer; additionally scan for schedule-derived
   quantities (shift timing, rewarded dimension, old/new rule identity,
   oracle-derived correctness beyond the single boolean, recommendations
   computed from the schedule).
4. **Log completeness / 로그 완전성**: per trial — raw model output, parse
   result, parse errors, canonical state actually delivered, public
   feedback, commit hash, prompt version, generation config, model ID,
   run ID, seed. The run must be reconstructable from logs + manifest alone.

## 8. Deferred to pre-registered Study 3 / 사전등록 Study 3로 미루는 것

Full 6-condition design (Stateless / PublicHistory / NeutralState /
WCDState / ShuffledWCD / TokenMatched) with confirmatory tests, and the
state-perturbation battery: swap `active_hypothesis`, invert score ranks,
roll back one trial, ablate state vs history. Predictable behavioral shifts
under perturbation are the evidence that the state is functionally used
rather than post-hoc reported.
전체 6조건 확증 설계와 상태 조작 배터리(가설 교체·순위 반전·롤백·절제)는
Study 3로. 조작에 따른 예측 가능한 행동 변화가, 상태가 사후 보고가 아니라
기능적으로 사용된다는 증거다.
