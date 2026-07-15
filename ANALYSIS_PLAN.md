# Rule-Blind Controller Study — Frozen Analysis Plan
# Rule-Blind 컨트롤러 연구 — 동결된 분석계획

**Version / 버전**: 1.0
**Date frozen / 동결일**: 2026-07-15
**Status / 상태**: FROZEN before any new controller code is written or executed.
새 컨트롤러 코드를 작성·실행하기 전에 동결됨.

> Any deviation from this plan after this commit MUST be recorded in
> `DEVIATIONS.md` with the date, the change, and the reason.
> 이 커밋 이후 계획에서 벗어나는 모든 변경은 날짜·내용·사유와 함께
> 반드시 `DEVIATIONS.md`에 기록해야 한다.

---

## 1. Background and purpose / 배경과 목적

This study is a corrected redesign of the withdrawn manuscript
COGSYS-S-26-00464 ("Baby40"). A post-submission audit found that the
original controller received the current and previous ground-truth task
rules (`hidden_rule`, `previous_hidden_rule`) **before** the final
response was determined. Rule-shift detection, intervention eligibility,
remap tie-breaking, and controller-state updates all depended on this
oracle information, so the original "feedback-free controller" claim was
not supported.

본 연구는 철회된 원고 COGSYS-S-26-00464("Baby40")의 교정 재설계이다.
제출 후 감사에서, 원래 컨트롤러가 최종 응답이 결정되기 **전에** 현재·이전
정답 규칙(`hidden_rule`, `previous_hidden_rule`)을 전달받았음이 확인되었다.
규칙 전환 감지, 개입 자격 판정, remap 동점 해소, 컨트롤러 상태 갱신이 모두
이 oracle 정보에 의존했으므로, 원래의 "feedback-free controller" 주장은
입증되지 않았다.

The purpose of this study is to test, with strict information isolation,
whether an external controller that observes only public trial
information and (in some conditions) outcome feedback can reduce
perseverative behaviour of a frozen LLM in a WCST-style rule-shift task.

본 연구의 목적은, 엄격한 정보 격리 하에서 — 공개된 trial 정보와 (일부
조건에서) 정오 피드백만 관찰하는 외부 컨트롤러가 — 고정된(frozen) LLM의
WCST형 규칙 전환 과제에서의 고착(perseveration) 행동을 줄일 수 있는지
검증하는 것이다.

---

## 2. Architecture and information isolation / 구조와 정보 격리

```
Immutable raw LLM stream (불변 원응답 스트림)
        │
        ▼
PublicTrial + raw_choice          ← 공개 정보만 / public info only
        │
        ▼
RuleBlindController ──→ final_choice FROZEN (최종 선택 동결)
        │
        ▼
Evaluator(hidden_rule) ──→ correct / metrics (채점·지표)
        │
        └─ only allowed feedback is passed back BEFORE the next trial
           다음 trial 전에 허용된 피드백만 컨트롤러로 전달
```

### 2.1 Physical data separation / 데이터의 물리적 분리

- `public_stream.csv` — prompt, stimulus attributes, raw LLM response,
  parsed choice, trial index.
  프롬프트, 자극 속성, LLM 원응답, 파싱된 선택, trial 번호.
- `ground_truth.csv` — trial ID, hidden rule, correct choice, shift flag.
  trial ID, 숨겨진 규칙, 정답 선택, 전환 여부.
- Controllers import **only** `public_stream.csv`.
  컨트롤러는 **오직** `public_stream.csv`만 읽는다.
- Only the Evaluator joins the two files.
  두 파일의 결합은 Evaluator만 수행한다.

### 2.2 Interface contract / 인터페이스 규약

```
final_choice = controller.decide(public_trial, raw_choice)   # 동결 / frozen
result       = evaluator.score(trial_id, final_choice)
controller.observe_feedback(result.correct)   # feedback-aware 조건에서만 / only in feedback-aware conditions
```

Controllers never receive a full CSV row, a trial dict containing
ground-truth keys, or any value derived from ground truth other than the
single boolean `correct` delivered **after** `final_choice` is frozen
(and only in feedback-aware conditions).

컨트롤러는 전체 CSV row, 정답 키가 포함된 trial dict, 또는 ground truth에서
파생된 어떤 값도 받지 않는다. 유일한 예외는 `final_choice` 동결 **이후**
전달되는 단일 boolean `correct`이며, 이것도 feedback-aware 조건에서만
허용된다.

### 2.3 Mandatory leak-prevention tests / 필수 누출 방지 테스트

All three tests must pass in CI before any result is reported.
아래 세 테스트를 통과하지 않은 결과는 보고하지 않는다.

1. **Ground-truth invariance / 정답 불변성**: changing the current
   trial's ground truth must not change the output of `decide()`.
   현재 trial의 ground truth를 바꿔도 `decide()`의 출력은 변하지 않아야 한다.
2. **Shuffle invariance (feedback-free) / 셔플 불변성**: in
   feedback-free conditions, shuffling the entire ground-truth file must
   leave every controller output identical.
   feedback-free 조건에서는 ground-truth 파일 전체를 섞어도 모든 컨트롤러
   출력이 동일해야 한다.
3. **Feedback ordering / 피드백 순서**: in feedback-aware conditions,
   past correctness may influence behaviour only from the next trial
   onward, never the trial in which the response is frozen.
   feedback-aware 조건에서 과거 정오 정보는 다음 trial부터만 영향을 줄 수
   있으며, 응답이 동결되는 해당 trial에는 절대 영향을 줄 수 없다.

**Banned tokens in the controller package / 컨트롤러 패키지 금지어**
(enforced by a CI grep / CI grep으로 강제):
`hidden_rule`, `previous_hidden_rule`, `correct_response`, `rule_shift`,
`is_AX`.

---

## 3. Conditions and their fixed roles / 조건과 사전 고정된 역할

The roles below are fixed **a priori**. The primary condition will not be
changed after seeing results.
아래 역할은 **사전에** 고정된다. 결과를 본 뒤 주 조건을 바꾸지 않는다.

| # | Condition / 조건 | Role / 역할 |
|---|---|---|
| 1 | `RawLLM` (no controller / 컨트롤러 없음) | Baseline / 기준선 |
| 2 | `RuleBlind-FeedbackAware Full` | **PRIMARY / 주 조건** |
| 3 | `RuleBlind-FeedbackAware NoVeto` | Ablation / 절제 조건 |
| 4 | `TrajectoryOnly-FeedbackFree` | Secondary: strict test of the original hypothesis / 보조: 원가설의 엄격한 검증 |
| 5 | `YokedRandom` | Placebo control: identical intervention timing and count as Full, random alternative choice / 위약 대조: Full과 개입 시점·횟수 동일, 대안만 무작위 |
| 6 | `Oracle-Full` (original Baby40) | Ceiling reference, appendix only / 상한선 참조, 부록 전용 |

Terminology / 용어:
- Condition 2–3 are described as **rule-blind, outcome-feedback**
  controllers (they never see the rule, but do see trial-level
  correctness after committing).
  조건 2–3은 **rule-blind, outcome-feedback** 컨트롤러로 기술한다
  (규칙은 절대 보지 않으며, 확정 이후의 trial 정오만 본다).
- Condition 4 is described as **trajectory-only, feedback-free** (it sees
  neither the rule nor correctness; only the raw-choice trajectory).
  조건 4는 **trajectory-only, feedback-free**로 기술한다 (규칙도 정오도
  보지 않고 원선택 궤적만 본다).
- The term "label-free" is NOT used anywhere: outcome feedback is itself
  a supervision signal derived from ground truth.
  "label-free"라는 표현은 어디에도 쓰지 않는다: 정오 피드백 자체가 ground
  truth에서 파생된 감독 신호이기 때문이다.

---

## 4. Two-study structure / 2-스터디 구조

### Study 1 — Archived-stream retrospective replay / 보관 스트림 회고 재생

- Input: the existing 30 GPT-4o and 30 Claude independent raw-response
  streams collected in April 2026 (single-turn prompts, no feedback to
  the LLM, prompts independent of controller state).
  입력: 2026년 4월에 수집된 기존 GPT-4o 30개·Claude 30개 independent
  원응답 스트림 (단일 턴 프롬프트, LLM에 피드백 없음, 프롬프트는 컨트롤러
  상태와 무관).
- Role: development, debugging, exploration, and a direct correction of
  the withdrawn manuscript. **Explicitly exploratory.** These streams
  have already been observed and used in prior parameter search, so they
  cannot serve as a confirmatory test set.
  역할: 개발·디버깅·탐색, 그리고 철회 원고에 대한 직접 교정.
  **명시적으로 탐색적 분석.** 이 스트림들은 이미 관찰되었고 과거 parameter
  search에 사용되었으므로 확증 검정 자료가 될 수 없다.
- Replay validity in WCST: prompts are per-trial independent, the LLM
  receives no history or feedback, the controller does not alter the
  next prompt, and the hidden-rule schedule does not depend on
  behaviour. Therefore one raw stream can be passed through every
  controller condition, yielding a true repetition-level paired design.
  WCST에서 replay가 타당한 이유: 프롬프트가 trial별 독립이고, LLM이 이력·
  피드백을 받지 않으며, 컨트롤러가 다음 프롬프트를 바꾸지 않고, 숨겨진
  규칙 일정이 행동에 의존하지 않는다. 따라서 하나의 원 스트림을 모든
  컨트롤러 조건에 통과시킬 수 있고, 이는 진짜 repetition 단위 paired
  design이 된다.
- NOTE: pairing exists only among conditions replayed from the **same**
  stream. The historical "Full" CSVs are never re-paired with historical
  "Independent" CSVs.
  주의: 짝(pairing)은 **동일한** 스트림에서 재생된 조건들 사이에서만
  성립한다. 과거의 "Full" CSV를 과거의 "Independent" CSV와 다시 짝짓는
  일은 하지 않는다.

### Study 2 — Confirmatory evaluation on current models / 현행 모델 확증 평가

1. All controller parameters and this analysis plan are frozen by Git
   commit **before** any Study 2 stream is generated.
   모든 컨트롤러 파라미터와 본 분석계획은 Study 2 스트림 생성 **전에**
   Git 커밋으로 동결한다.
2. Pilot: 3–5 repetitions per candidate model. Check raw-stream choice
   entropy and repeat rate. If the median within-stream maximum-choice
   repeat proportion is below 0.5 (i.e., the model rarely perseverates),
   task difficulty is revised (block length, dimensionality) and the
   revision is documented in `DEVIATIONS.md` **before** the confirmatory
   run.
   파일럿: 후보 모델당 3–5 반복. 원 스트림의 선택 엔트로피와 반복률을
   확인한다. 스트림 내 최다 선택 반복 비율의 중앙값이 0.5 미만이면(즉
   모델이 거의 고착하지 않으면) 과제 난이도를 수정하고(블록 길이, 차원 수),
   수정 내용을 확증 실행 **전에** `DEVIATIONS.md`에 기록한다.
3. Confirmatory run: newly generated raw streams (target: 30 repetitions
   per model) replayed through all six conditions.
   확증 실행: 새로 생성한 원 스트림(모델당 30 반복 목표)을 여섯 조건
   모두에 재생한다.
4. Model versions, temperature, and API parameters are pinned and
   recorded.
   모델 버전, temperature, API 파라미터는 고정하고 기록한다.

Absolute metric values are expected to differ across model generations.
The hypotheses concern **within-model condition contrasts**, which are
defined independently of model generation, because the LLM never receives
feedback and therefore cannot adapt in any condition by design.

지표의 절대값은 모델 세대에 따라 달라질 것으로 예상한다. 가설은 **모델 내
조건 대비**에 관한 것이며, 이는 모델 세대와 독립적으로 정의된다 — 설계상
LLM은 어떤 조건에서도 피드백을 받지 않으므로 원리적으로 적응할 수 없기
때문이다.

---

## 5. Task scope / 과제 범위

- **WCST (primary task / 주 과제)**: replay-eligible. / replay 가능.
- **AX-CPT, probabilistic reversal, Stroop**: replay-eligible (next
  stimulus independent of behaviour); reported as secondary tasks only
  with the same rule-blind interface and no task-specific answer
  correction.
  replay 가능(다음 자극이 행동과 무관). 동일한 rule-blind 인터페이스를
  사용하고 과제별 정답 교정 없이 보조 과제로만 보고한다.
- **Tower of Hanoi**: NOT replay-eligible (actions change the next state
  and prompt). Excluded from this study; requires a separate online
  experiment or a separate simulation-only study.
  replay 불가(행동이 다음 상태와 프롬프트를 바꿈). 본 연구에서 제외하며,
  별도의 온라인 실험 또는 시뮬레이션 전용 연구가 필요하다.

---

## 6. Metrics / 지표

Computed per repetition (one stream = one repetition = one sample).
repetition 단위로 계산한다(스트림 1개 = repetition 1개 = 표본 1개).

### Primary metrics / 1차 지표

1. **Total accuracy / 전체 정확도**: mean correctness of final choices
   over the 36 trials. / 36 trials에서 최종 선택의 평균 정오.
2. **Persistence error count / 고착 오류 횟수**: number of trials where
   the final choice equals the previous block's rule and is incorrect.
   최종 선택이 이전 블록 규칙과 같으면서 오답인 trial의 수.

### Secondary metrics / 2차 지표

3. Old-rule reentry count / old-rule reentry 횟수.
4. Choice entropy of final choices / 최종 선택의 엔트로피.
5. Productive intervention rate / 생산적 개입 비율 (definition below /
   정의는 아래).
6. Post-shift recovery latency: trials from each shift until the first
   correct final choice. / 전환 후 첫 정답까지의 trial 수.

### Single fixed definition of a productive intervention
### 생산적 개입의 단일 고정 정의

An intervention (override) is **productive** iff at least one of the next
two final choices is correct. This is the only definition used in the
main text. The streak-based definition (persistence streak ≥ 2 at
override) is reported once, in the supplement, as a sensitivity analysis.

개입(override)은 이후 두 trial의 최종 선택 중 하나 이상이 정답일 때에만
**생산적**으로 정의한다. 본문에서는 이 정의만 사용한다. streak 기반 정의
(override 시점 persistence streak ≥ 2)는 민감도 분석으로 보충자료에 한 번만
보고한다.

Repetitions with zero interventions are **excluded** from
productive-rate analyses (not coded as 0), and the number of excluded
repetitions is reported. A supplementary binomial analysis uses raw
productive / total intervention counts.

개입이 0회인 repetition은 productive-rate 분석에서 0으로 넣지 않고
**제외**하며, 제외된 repetition 수를 보고한다. 보충 분석으로 생산적 개입
횟수/총 개입 횟수를 사용한 binomial 분석을 수행한다.

---

## 7. Statistical analysis / 통계 분석

All analyses are run separately per model (no pooling across models;
model differences are described, not formally pooled).
모든 분석은 모델별로 별도 수행한다(모델 간 pooling 없음; 모델 차이는
기술적으로만 서술).

### Primary comparisons (confirmatory, Study 2) / 1차 비교 (확증, Study 2)

- H1: `RuleBlind-FeedbackAware Full` vs `RawLLM` — accuracy ↑,
  persistence errors ↓.
- H2: `RuleBlind-FeedbackAware Full` vs `YokedRandom` — accuracy ↑
  (the effect is not explained by intervention timing alone /
  효과가 개입 시점만으로 설명되지 않음을 검증).

### Tests / 검정

- Primary: **paired permutation test** (two-sided, 10,000 permutations)
  on repetition-level values, paired within stream.
  1차: repetition 값에 대한 **paired permutation test**(양측, 10,000회),
  같은 스트림 내에서 짝지음.
- Uncertainty: paired bootstrap 95% CI (10,000 resamples) of the mean
  within-pair difference.
  불확실성: 짝 내 차이 평균의 paired bootstrap 95% CI(10,000회).
- Effect size: mean paired difference and matched-pairs rank-biserial
  correlation.
  효과크기: 짝 차이 평균과 matched-pairs rank-biserial correlation.
- Multiplicity: H1 and H2 on the two primary metrics are tested at
  α = .05 with Holm correction within each model (4 tests per model).
  All secondary metrics and all other condition contrasts are Holm-
  corrected within their family and labelled secondary.
  다중성: H1·H2 × 1차 지표 2개는 모델별 Holm 보정(모델당 4개 검정),
  α = .05. 2차 지표와 나머지 조건 대비는 family 내 Holm 보정 후 2차로
  표기한다.
- Study 1 results are reported with the same machinery but labelled
  **exploratory**; no confirmatory claims are made from Study 1.
  Study 1 결과는 같은 방법으로 보고하되 **탐색적**으로 표기하며, Study 1로
  확증 주장을 하지 않는다.

### Sample size / 표본 크기

30 repetitions per model per study (paired across conditions). No
interim analysis; no optional stopping.
스터디당 모델당 30 repetitions(조건 간 짝지음). 중간 분석 없음, 조기 종료
없음.

---

## 8. Provenance and freezing / 출처 관리와 동결

- Every raw stream file is content-hashed (SHA-256) at creation; hashes
  are committed alongside the data manifest.
  모든 원 스트림 파일은 생성 시 SHA-256 해시를 기록하고, 해시는 데이터
  manifest와 함께 커밋한다.
- The commit freezing controller parameters is tagged
  `study2-freeze` before Study 2 stream generation.
  컨트롤러 파라미터를 동결하는 커밋에는 Study 2 스트림 생성 전에
  `study2-freeze` 태그를 부여한다.
- The withdrawn manuscript, its audit, and this plan are cross-referenced
  in the eventual paper's transparency statement.
  철회 원고, 감사 내용, 본 계획은 최종 논문의 투명성 진술에서 상호
  참조한다.

---

## 9. Out of scope / 범위 외

- No claim that the controller improves the LLM itself (the LLM is
  frozen and memoryless by design).
  컨트롤러가 LLM 자체를 개선한다는 주장은 하지 않는다(LLM은 설계상 고정·
  무기억이다).
- No cross-task generalisation claim beyond tasks run with the identical
  rule-blind interface under this plan.
  본 계획의 동일한 rule-blind 인터페이스로 수행되지 않은 과제에 대한
  일반화 주장은 하지 않는다.
- Oracle-Full appears only as a ceiling reference in the appendix and is
  never used as evidence for the main hypotheses.
  Oracle-Full은 부록의 상한선 참조로만 제시하며 주 가설의 근거로 사용하지
  않는다.
