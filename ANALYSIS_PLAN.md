# Sparse Outcome-Feedback Supervision of Memoryless LLM Outputs — Frozen Analysis Plan
# 무기억 LLM 출력에 대한 희소 Outcome-Feedback 감독 — 동결된 분석계획

**Version / 버전**: 2.0 (consolidated single text; replaces v1.0 + Amendments A/B,
which are preserved in git history — commits a7f8241, 53b347f, a06272e)
**Date / 일자**: 2026-07-15
**Status / 상태**: pre-freeze working text. The freeze sequence is §10; no
confirmatory data exists yet.
동결 전 작업본. 동결 절차는 10절; 확증 데이터는 아직 없다.

> Changes after the `pilot-freeze` tag must be logged in `DEVIATIONS.md`
> with date, change, and reason.
> `pilot-freeze` 태그 이후의 변경은 날짜·내용·사유와 함께 `DEVIATIONS.md`에
> 기록해야 한다.

---

## 1. Background, claim, and terminology / 배경·주장·용어

This study is the corrected redesign of a withdrawn manuscript
(submission-PDF ID COGSYS-S-26-00464; EM display number COGSYS-D-26-00370
— see ARCHIVED_STREAMS.md). The original controller read the ground-truth
task rule before deciding, so its "feedback-free" claim was unsupported.

본 연구는 철회 원고(제출 PDF ID COGSYS-S-26-00464; EM 표시 번호
COGSYS-D-26-00370 — ARCHIVED_STREAMS.md 참조)의 교정 재설계다. 원래
컨트롤러는 결정 전에 정답 규칙을 읽었으므로 "feedback-free" 주장이
성립하지 않았다.

**Research question / 연구 질문**:

> Under an identical sparse intervention budget (25% of trials), two
> outcome-feedback supervisors of memoryless LLM outputs occupy different
> points of an accuracy vs previous-rule-aligned-error trade-off. Does
> this Pareto trade-off, with all policies frozen, transfer to newer
> model generations?
> 동일한 희소 개입 예산(trial의 25%) 하에서, 무기억 LLM 출력에 대한 두
> outcome-feedback 감독자는 정확도-이전규칙정렬오류 트레이드오프의 서로
> 다른 지점을 차지한다. 모든 정책을 동결했을 때 이 Pareto 트레이드오프가
> 최신 모델 세대로 전이되는가?

Terminology rules / 용어 규칙:

- The LLM is **memoryless** (single-turn prompts, no history, no
  feedback); its repeated choices reflect stable output preferences
  (79–89% "color" in the archived streams). Therefore the term is
  **previous-rule-aligned error** (code: `prev_rule_error`), never
  "perseveration"; no claim of cognitive perseveration is made. An
  online condition (LLM receives history/feedback) is explicitly
  deferred to a separately frozen experiment.
  LLM은 **무기억**이다(단일 턴, 이력·피드백 없음). 반복 선택은 안정적
  출력 선호(보관 스트림에서 color 79–89%)를 반영하므로 용어는
  **previous-rule-aligned error**(코드 `prev_rule_error`)로 하며 "고착"
  이라 부르지 않고 인지적 고착 주장을 하지 않는다. 온라인 조건은 별도
  동결 실험으로 미룬다.
- The headline claim is NOT raw accuracy (an unlimited feedback policy
  trivially reaches ~.86) but **efficiency and safety under a hard
  intervention budget**.
  핵심 주장은 원 정확도가 아니라(무제한 피드백 정책은 ~.86에 도달)
  **하드 개입 예산 하의 효율과 안전성**이다.

## 2. Architecture and information isolation / 구조와 정보 격리

```
Immutable raw LLM stream (불변 원응답 스트림)
        │  PublicTrial(trial_number, prompt) + raw_choice
        ▼
Supervisor (controller/) ──→ final_choice FROZEN (동결)
        │
        ▼
Evaluator (evaluator/) ──→ correct / metrics (채점·지표)
        │
        └─ single boolean `correct` back to feedback-aware supervisors,
           strictly AFTER freezing / 동결 이후에만 boolean 정오 전달
```

- Ground truth is readable by exactly two components: the evaluator and
  the `oracle/` package (the oracle-assisted policy reference, an
  explicit exemption). `controller/` can read neither; a CI grep bans
  ground-truth tokens there, comments included.
  ground truth는 정확히 두 곳만 읽는다: 평가기와 (명시적 예외인)
  `oracle/` 패키지. `controller/`는 어느 쪽도 읽을 수 없으며 금지어
  CI가 주석까지 검사한다.
- Data separation: `public_stream.csv` (prompt, raw response, parsed
  choice) vs per-repetition ground-truth CSVs. Controllers load only the
  public side.
  데이터 분리: 공개 스트림과 repetition별 ground truth CSV. 컨트롤러는
  공개 측만 읽는다.
- Interface contract / 인터페이스 규약:
  `final = controller.decide(public_trial, raw_choice)` → freeze →
  `evaluator.score(trial, final)` → `controller.observe_feedback(correct)`
  (feedback-aware only / feedback-aware 조건만).

## 3. Conditions and fixed roles / 조건과 사전 고정된 역할

All supervisors with a budget share the same HARD cap: **9 interventions
per 36-trial repetition (25%)**, enforced in code and gate-tested.
예산이 있는 모든 감독자는 같은 하드 상한을 공유한다: **repetition당 9회
(25%)**, 코드로 강제되고 게이트로 검증된다.

| # | Condition | Role / 역할 |
|---|---|---|
| 1 | `RawLLM` | Baseline / 기준선 |
| 2 | `RuleBlindFull` | **CO-PRIMARY** supervisor (belief/veto-window/rescue; budget 9) / **공동 주 조건** |
| 3 | `WSLSBudgeted` | **CO-PRIMARY** supervisor (win-stay/lose-shift; same budget 9; information-matched) / **공동 주 조건**, 정보량 동일 |
| 4 | `NoVeto` | Ablation of Full (veto_window=0) / Full의 절제 |
| 5 | `TrajectoryOnly` | Feedback-free strict test of the original hypothesis / 원가설의 엄격 검증 |
| 6 | `YokedRandom` | Mechanism control: Full's intervention timing, random alternatives / 기제 대조 |
| 7 | `WSLSUnlimited` | Player-regime descriptive reference (no budget; never a test target) / 선수 체제 기술 참조 |
| 8 | `OracleFull` | **Oracle-assisted policy reference** — NOT a ceiling (theoretical ceiling = 1.0); appendix only / 상한선 아님, 부록 전용 |

WSLS policy (frozen): belief = dimension of the most recent correct
final choice; while belief exists override raw ≠ belief; on failure of
the followed dimension, clear belief and shift to the least-recently-
tried other dimension; overrides stop at the budget.
WSLS 정책(동결): belief = 가장 최근 정답 최종 선택의 차원; belief 존재 시
raw ≠ belief면 override; 따르던 차원 실패 시 belief를 지우고 최장 미시도
차원으로 이동; 예산 소진 시 중지.

RuleBlindFull parameters (frozen from the documented constrained search,
selected row printed by `analysis/param_search.py`): error_streak_to_open
1, veto_window 4, rescue_failure_threshold 2 (cumulative-unresolved
semantics: reset only by that dimension's next correct outcome),
rescue_cooldown 6, belief_confirm_streak 2, budget 9.
RuleBlindFull 파라미터(공개된 제약 탐색으로 동결): 위와 같음. rescue는
누적 미해결 의미론(해당 차원의 다음 정답으로만 초기화).

## 4. Studies and data roles / 스터디와 데이터 역할

- **Study 1 — controller development (exploratory)**: the 60 archived
  streams (claude-sonnet-4-6 / gpt-4o, temperature 1.0, single-turn,
  collected 2026-04; one shared fixed schedule — see
  ARCHIVED_STREAMS.md). Used for design, parameter search, and all
  exploratory analyses. All Study 1 CIs/p-values are post-search and
  never confirmatory.
  **Study 1 — 컨트롤러 개발(탐색적)**: 보관 스트림 60개. 설계·파라미터
  탐색·탐색 분석 전용. Study 1의 모든 CI·p값은 탐색 이후 값이며 확증이
  아니다.
- **Study 2 — frozen out-of-model validation (confirmatory)**: newly
  generated streams from current model generations, first touched only
  after the freeze sequence of §10. Nothing is retuned after seeing
  Study 2 data.
  **Study 2 — 동결된 모델 외부 검증(확증)**: 최신 세대 모델의 신규
  스트림. 10절의 동결 절차 이후에만 최초 접촉하며, 이후 재조정 금지.

Development-contact ledger (reported in the paper) / 개발 접촉 이력표:

| Data | Role | Touched parameter selection? |
|---|---|---|
| Archived Claude 30 + GPT-4o 30 streams (2026-04) | development / 개발 | YES |
| Study 2 pilot streams (§10) | engineering check / 공학 점검 | NO — excluded from confirmatory data / 확증 자료에서 제외 |
| Study 2 confirmatory streams | held-out / 확증 | NO — first contact after study2-freeze |

## 5. Study 2 models and generation config / Study 2 모델·생성 설정

Two families × capability tiers (generation axis + capability axis;
Haiku-tier excluded by decision of 2026-07-15):

| Family | Tier | Model (exact ID pinned at pilot-freeze) |
|---|---|---|
| Anthropic | Frontier | Claude Fable 5 (`claude-fable-5`) |
| Anthropic | Flagship | Claude Opus 4.8 (`claude-opus-4-8`) |
| Anthropic | Mid | Claude Sonnet 5 (`claude-sonnet-5`) |
| OpenAI | Flagship | current flagship at generation time / 생성 시점 플래그십 |
| OpenAI | Mid | current mid tier / 생성 시점 중위 티어 |

Per-model generation config / 모델별 생성 설정:

- Opus 4.8: omit `thinking` (off by default); no sampling params.
- Sonnet 5: explicit `thinking: {type: "disabled"}`; no non-default
  sampling params.
- Fable 5: thinking CANNOT be disabled — omit `thinking`, set
  `output_config.effort: "low"`, `max_tokens` headroom (~2000).
  Documented asymmetry: internal reasoning cannot reveal rule shifts
  (no feedback in the prompt); whether it changes raw-stream character
  (entropy, repeat rate) is itself a reported descriptive result.
  Fable 5: 추론 비활성 불가 — `thinking` 생략, effort low, max_tokens
  여유. 비대칭은 명시: 프롬프트에 피드백이 없어 추론으로도 규칙 전환은
  알 수 없으며, 원 스트림 특성 변화 여부 자체가 보고 대상이다.
- OpenAI: lowest available reasoning setting if a reasoning model;
  provider-default sampling, recorded.
- Model IDs, API/library versions (`anthropic`, `openai`,
  `python-dotenv` pinned with `==`), timestamps, and configs are
  recorded in the generation manifest.
  모델 ID·라이브러리 버전(== 고정)·시각·설정은 생성 manifest에 기록.

**Refusal / error handling (ITT principle)** / refusal·오류 처리(ITT 원칙):

- API errors: ≤3 retries with exponential backoff; still failing → the
  trial records "" with an `api_error` flag.
- Fable 5 refusals: retry once; if refused again the TRIAL is recorded
  as "" (unparsable/incorrect) and kept — **intention-to-treat is the
  primary analysis**. Whole-repetition exclusion is a sensitivity
  analysis only. All failure logs and attempt IDs are preserved; any
  replacement repetitions keep the original failure record.
  Fable 5 refusal: 1회 재시도, 재차 refusal이면 해당 TRIAL을 ""(파싱
  불가·오답)로 기록하고 유지한다 — **ITT가 1차 분석**이다. repetition
  전체 제외는 민감도 분석 전용. 실패 로그·attempt ID는 모두 보존하고,
  대체 repetition을 만들더라도 원 실패 기록을 남긴다.

**Parsing (frozen)** / 파싱(동결): case-insensitive word-boundary match
of dimension synonyms (color/colour/hue; shape/form; number/count/
quantity/numerosity/amount — the archived study's table verbatim);
earliest-position unique dimension wins; ties or no match → "" with
`ambiguous_response = 1`; "" always passes through supervisors.
대소문자 무시 단어 경계 일치(보관 연구의 동의어 표 그대로); 최초 위치
유일 차원 채택; 동률·불일치는 ""(ambiguous)로 기록; ""는 항상 통과.

## 6. Schedules / 일정

Study 1 keeps the archived fixed schedule (development data). Study 2
uses per-repetition randomized schedules generated by
`scripts/generate_schedules.py` from master seed 20260715 BEFORE any API
call, committed with SHA-256 manifest:

- 36 trials; block lengths drawn from {5,6,7}; remainder handled by the
  frozen partition rule such that **every block is 4–8 trials**
  (gate-tested over 10,000 seeds);
- first rule uniform; subsequent rules uniform over the other two (no
  immediate repeat);
- one ground-truth CSV per repetition; schedules shared across models at
  the same rep index; each raw stream replays through all conditions on
  its own schedule (paired structure preserved).

Study 2는 마스터 시드 20260715로 API 호출 전에 생성·커밋되는 repetition별
무작위 일정을 사용한다: 36 trials, 블록 길이 {5,6,7} 추출(동결된 분할
규칙으로 **모든 블록 4–8 보장**, 1만 시드 게이트 검증), 첫 규칙 균등·이후
연속 반복 없음, rep별 ground truth CSV, 같은 rep 번호는 모델 간 동일
일정, 각 스트림은 자기 일정 위에서 전 조건 재생(paired 유지).

## 7. Metrics (frozen definitions) / 지표(동결된 정의)

Per repetition, on final choices / repetition 단위, 최종 선택 기준:

- **total_accuracy**.
- **prev_rule_error**: final == previous block's rule, incorrect,
  block > 1.
- **old_rule_reentry**: a prev_rule_error occurring after ≥1 earlier
  correct final choice in the same block.
- **choice_entropy**: Shannon (log2) over final choices in {color,
  shape, number}; unparsable excluded, `unparsable_count` reported.
- **recovery_latency**: per block (>1), 1-based position of first
  correct final choice; censored at block length if none
  (`latency_censored_count` reported); repetition value = mean.
- **Direct safety metrics / 직접 안전성 지표**: corrective_override
  (raw incorrect → final correct), harmful_override (raw correct →
  final incorrect), intervention_precision (= interventions with raw
  incorrect / interventions; undefined (−1) at zero interventions and
  excluded from rate analyses), net_correction (corrective − harmful),
  intervention_coverage (interventions / trials).
- **subsequent_success_rate** (descriptive only; demoted — an
  intervention can satisfy it by later luck): at least one of the next
  two final choices correct.

All metric implementations are verified against hand calculations in the
gate (`tests/test_design_invariants.py`).
모든 지표 구현은 게이트의 수작업 계산 fixture로 검증된다.

## 8. Hypotheses and statistics / 가설과 통계

All analyses per model; no pooling across models. Same-stream replay
gives repetition-level pairing.
모든 분석은 모델별. 같은 스트림 재생으로 repetition 단위 paired.

**Primary family — FOUR tests per model (co-primary supervisors)**:

1. Full vs RawLLM — total accuracy
2. WSLSBudgeted vs RawLLM — total accuracy
3. WSLSBudgeted vs Full — total accuracy
4. Full vs WSLSBudgeted — prev_rule_error

**1차 family — 모델당 4개 검정 (공동 주 조건)**: 위 4개. Study 1 탐색
결과(정확도는 WSLS 우위, prev_rule_error는 Full 우위)가 새 세대에서
전이되는지가 확증 대상이다.

**Secondary (mechanism) family / 2차(기제) family**: Full vs YokedRandom
(both metrics), Full vs NoVeto (both), Full & WSLS vs RawLLM on
prev_rule_error, TrajectoryOnly vs RawLLM (both). Holm within family.

**Tests / 검정**: paired permutation (two-sided, 10,000), paired
bootstrap 95% CI, matched-pairs rank-biserial; Holm on FULL-PRECISION
p-values within each family per model; permutation-floor values reported
as p < .001.
paired permutation(양측 10,000회), paired bootstrap 95% CI, rank-
biserial; 모델별·family별 원정밀도 p에 Holm; 해상도 하한은 p < .001로
보고.

**Headroom gates (split by endpoint)** / headroom 게이트(지표별 분리):

- Accuracy hypotheses (1–3): ALWAYS tested confirmatorily — correction
  headroom exists whenever RawLLM accuracy < 1.
  정확도 가설(1–3): 항상 확증 검정한다 — Raw 정확도가 1 미만이면 교정
  여지가 존재한다.
- prev_rule_error hypothesis (4) and all secondary prev_rule_error
  contrasts: tested confirmatorily for a model only if that model's
  RawLLM mean prev_rule_error ≥ 3.0; otherwise reported descriptively as
  "insufficient alignment-error headroom".
  prev_rule_error 가설(4)과 2차의 해당 대비: RawLLM 평균 prev_rule_error
  ≥ 3.0인 모델에서만 확증 검정; 미달 시 "정렬 오류 headroom 부족"으로
  기술 보고.
- Same task regardless of headroom; a harder-task variant is a separate,
  separately frozen secondary experiment.
  headroom과 무관하게 동일 과제; 난이도 변형은 별도 동결의 2차 실험.

**Equivalence and non-inferiority / 동등성·비열등성**:

- TrajectoryOnly "no effect" claims require SESOI ±0.02 accuracy:
  equivalent iff the paired-bootstrap 90% CI lies within ±0.02, else
  "inconclusive".
- Do-no-harm: each co-primary supervisor is non-inferior to RawLLM on a
  model iff the 95% CI lower bound of the paired accuracy difference
  > −0.02.

**N / 표본**: 30 repetitions per model (confirmatory), paired across
conditions; no interim analysis, no optional stopping. Pilot reps (§10)
are excluded.

## 9. Provenance and secrets / 출처 관리·비밀 정보

- SHA-256 manifests for archived extractions, Study 2 schedules, and
  generated streams; git-committed before use.
- API keys live only in `.env` (ignored; `.env.example` tracked);
  key-pattern scans of tracked files are part of release hygiene; no
  keys in code, logs, CSVs, or manifests.
  API 키는 `.env`에만 두며(무시됨), 코드·로그·CSV·manifest에 금지.

## 10. Freeze sequence / 동결 절차

1. **Now / 지금**: this v2.0 plan and all Study 1 exploratory results.
2. **`pilot-freeze` tag**: Study 2 runner + parser + schedules + model
   candidates + pilot rules + pinned library versions + the end-to-end
   dry-run gate. / runner·파서·일정·모델 후보·파일럿 규칙·라이브러리
   버전 고정·dry-run 게이트까지 동결.
3. **Engineering pilot**: 3–5 reps/model, cost & parser verification
   only; EXCLUDED from confirmatory data. / 공학 파일럿(확증 제외).
4. Final choices (exact model IDs, N, API settings) fixed.
5. **`study2-freeze` tag**, externally timestamped (public repository
   push or OSF hash registration) BEFORE confirmatory generation.
   외부 타임스탬프 후에만 확증 생성.
6. Confirmatory generation and locked analysis. / 확증 생성·고정 분석.

## 11. Verification gates / 검증 게이트

`scripts/run_all_checks.py` must pass before any result is reported:
banned tokens; leak tests (ground-truth invariance, shuffle invariance,
feedback ordering); design invariants (hard budget cap, WSLS hand
fixture, metric hand calculations, override attribution, schedule
invariants over 10,000 seeds, yoked fidelity); plus, from pilot-freeze,
a Study 2 end-to-end dry run against a mock API.
게이트 통과 없이 어떤 결과도 보고하지 않는다: 금지어; 누출 3종; 설계
불변식(하드 예산, WSLS fixture, 지표 수작업 계산, 개입 귀속, 일정 1만
시드, yoked 일치); pilot-freeze부터는 mock API 대상 end-to-end dry run.

## 12. Independent external review / 독립 외부 검토

Before resubmission, the frozen code and manuscript undergo independent
review by people other than the author and the AI assistant that wrote
the code. Scope is FIXED in advance to keep cost bounded.
재제출 전, 동결된 코드와 원고는 저자 및 코드를 작성한 AI 어시스턴트가
아닌 사람의 독립 검토를 받는다. 비용을 제한하기 위해 범위를 사전에
고정한다.

- **Engagement title / 의뢰 명칭**: "Independent reproducibility and
  statistical review of a small computational study" (not "code audit",
  which invites enterprise-security-scale quotes).
  ("code audit"라 부르지 않는다 — 기업 보안감사 규모의 견적을 부른다.)
- **Code reviewer** (CS background / 컴퓨터공학): clean-environment
  execution; verification that no ground-truth information reaches
  `controller/`; end-to-end reproduction from raw data to every number
  in the manuscript. Entry route: CODECHECK (free, certificate with
  DOI) first; paid fixed-scope reviewer if unavailable.
  코드 검토자: 깨끗한 환경 실행, 정답 정보 비유입 확인, 원자료→논문
  수치 전체 재현. 경로: CODECHECK(무료, DOI 인증서) 우선, 불가 시 고정
  범위 유료 검토.
- **Statistics reviewer** (statistics/quant-methods graduate level or
  above / 통계·수리 석박사급): paired design validity, permutation/
  bootstrap implementation, multiplicity, metric definitions, and
  whether conclusions exceed the evidence. Entry route: university
  statistical consulting first (often free initial sessions).
  통계 검토자: paired 설계, permutation/bootstrap 구현, 다중성, 지표
  정의, 결론 강도. 경로: 대학 통계상담실 우선(초회 무료가 흔함).
- **Contract shape / 계약 형태**: fixed scope (≤ 8 hours per reviewer)
  + written findings report; fixes are implemented by us; reviewers
  provide findings and a final confirmation only. Target budget
  ~₩1.5–3M total; lower if CODECHECK and university consulting apply.
  고정 범위(검토자당 ≤ 8시간) + 서면 보고서. 수정 구현은 우리가 하고
  검토자는 발견사항과 최종 확인서만 제공. 목표 예산 총 150–300만 원,
  CODECHECK·대학 상담 적용 시 그 이하.
- **Timing / 시점**: reviewers engage only AFTER the manuscript-freeze
  commit, against a prepared review package (`REVIEWERS.md`: one-command
  reproduction script, environment spec, hash manifest, file map) — so
  paid hours go to verification, not orientation.
  검토는 원고 동결 커밋 이후, 준비된 검토 패키지(원클릭 재현 스크립트,
  환경 명세, 해시 manifest, 파일 지도)에 대해서만 진행한다 — 유료
  시간이 '정리'가 아니라 '검증'에만 쓰이게 한다.
- **Reporting / 보고**: reviewer names/roles (with consent), findings,
  and resolutions appear in the paper's transparency statement,
  alongside the withdrawal history and this plan's version trail.
  검토자 이름·역할(동의 시), 발견사항과 해결 내역을 철회 이력·계획
  버전 이력과 함께 논문 투명성 진술에 기재한다.
- English-language editing of the manuscript is budgeted separately by
  the author. / 영문 교정은 저자가 별도 예산으로 진행한다.

## 13. Out of scope / 범위 외

- No claim that the supervisor improves the LLM itself (memoryless by
  design). / 감독자가 LLM 자체를 개선한다는 주장 없음.
- No cognitive-perseveration claim (§1). / 인지적 고착 주장 없음.
- No cross-task generalization claim beyond tasks run under this exact
  interface and plan. / 본 인터페이스·계획 밖 과제로의 일반화 주장 없음.
- OracleFull is a policy reference, never evidence for the hypotheses.
  / OracleFull은 참조일 뿐 가설의 근거가 아니다.
