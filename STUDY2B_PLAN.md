# Study 2b — WCD-Minimal Confirmatory Evaluation / WCD-minimal 확증 평가

**Status / 상태**: DRAFT — not frozen. This document becomes binding only at
the `study2b-freeze` tag (externally timestamped), with every `[TO-FREEZE]`
placeholder replaced by its calibrated numeric value. Until that tag, nothing
here licenses any confirmatory claim.
**DRAFT — 미동결.** 이 문서는 `study2b-freeze` 태그(외부 타임스탬프)에서
모든 `[TO-FREEZE]` 자리가 calibration 수치로 채워진 뒤에만 구속력을 가진다.
그 전에는 어떤 확증 주장도 허가하지 않는다.

Relationship to the frozen plan: ANALYSIS_PLAN.md v2.0 remains frozen and
untouched. Study 2b is a separately frozen EXTENSION with its own tag, data,
and hypothesis families. Nothing in this document reopens any locked Study 1
or Study 2 analysis.
동결 계획과의 관계: ANALYSIS_PLAN.md v2.0은 그대로 동결 유지된다. Study 2b는
자체 태그·자료·가설 family를 가진 '별도 동결' 확장이며, 이 문서의 어떤
내용도 잠긴 Study 1·2 분석을 재개방하지 않는다.

---

## 1. Motivation (from locked results) / 동기 (잠금 결과로부터)

The locked Study 2 primary family (2026-07-15) replicated the accuracy
effects on all four models but showed the perseveration trade-off only on
gpt-5.5; on claude-opus-4-8 (+0.83) and claude-sonnet-5 (+0.58) RuleBlindFull
significantly REVERSED (worsened) prev_rule_error relative to WSLSBudgeted.
Two explanations compete:

- (a) Full's protection stack (veto window, stuckness rescue, cooldown)
  interacts badly with current-generation choice statistics, or
- (b) outcome-driven hypothesis tracking itself carries the cost.

Study 2b discriminates (a) from (b) with a minimal controller — WCD-minimal —
that keeps only evidence accumulation (CONSIDER), a switch-delay threshold
(WAIT), and a margin-gated comparison (DISCRIMINATE), removing the stack.

잠긴 Study 2 1차 family(2026-07-15)는 정확도 효과를 4개 모델 전부에서
재현했지만 고착 트레이드오프는 gpt-5.5에서만 재현했고, claude-opus-4-8
(+0.83)과 claude-sonnet-5(+0.58)에서는 RuleBlindFull이 WSLSBudgeted 대비
prev_rule_error를 유의하게 '역전(악화)'시켰다. 경쟁하는 설명은 둘이다:
(a) Full의 보호 장치 스택(veto window, rescue, cooldown)이 현세대 선택
통계와 나쁘게 상호작용한다, 또는 (b) 정오 기반 가설 추적 자체가 비용을
가진다. Study 2b는 스택을 제거하고 증거 누적(CONSIDER)·전환 지연(WAIT)·
마진 비교(DISCRIMINATE)만 남긴 최소 컨트롤러 WCD-minimal로 (a)와 (b)를
변별한다.

**Honest disclosure / 정직한 공개**: the WCD-minimal HYPOTHESIS was formed
AFTER observing the locked Study 2 results. Therefore no analysis of the
existing Study 2 streams can confirm it. Confirmation uses only FRESH streams
(§4) that did not exist when the hypothesis was formed.
WCD-minimal '가설'은 잠긴 Study 2 결과를 관찰한 '이후' 형성되었다. 따라서
기존 Study 2 스트림에 대한 어떤 분석도 이를 확증할 수 없다. 확증은 가설
형성 시점에 존재하지 않았던 '신규' 스트림(4절)만 사용한다.

## 2. Two-stage structure / 2단계 구조

**A0 — Exploratory calibration / 탐색적 calibration.**
`analysis/calibrate_wcd_minimal.py` selects the free parameters on the
ARCHIVED STUDY 1 STREAMS ONLY (data/public, 60 streams, single archived
schedule). The full grid, the codified selection rule, and the reference
replays are stated in that script's docstring and published in
`results/calibration_wcd_minimal.csv`. The calibration corpus may never
include any Study 2, Study 2 pilot, or Study 2b file.
자유 파라미터는 '보관된 Study 1 스트림에서만' 선택한다 (data/public,
60개 스트림, 단일 보관 일정). 전체 grid·코드화된 선정 규칙·참조 재생은
해당 스크립트 docstring에 명시되고 결과 CSV로 공개된다. calibration
코퍼스는 Study 2·Study 2 파일럿·Study 2b 파일을 절대 포함할 수 없다.

**A1 — Confirmatory evaluation / 확증 평가.**
The frozen WCD-minimal is applied ONCE to fresh Study 2b streams (§4),
scored replay-side with the same harness, and tested per §5. Manuscript
wording, fixed now / 원고 문구, 지금 고정:

> "WCD-minimal was calibrated exploratorily on the archived Study 1 streams
> and subsequently evaluated confirmatorily on newly generated streams that
> did not exist when the hypothesis was formulated."

## 3. Controller specification / 컨트롤러 명세

Implementation: `controller/wcd_minimal.py` (`WCDMinimalController`), inside
the banned-token-gated package; information channel identical to the
co-primary supervisors (post-freeze boolean outcomes only).
구현은 controller/wcd_minimal.py — 금지어 게이트 패키지 내부, 정보 채널은
공동 주 감독자들과 동일 (동결 후 boolean 정오만).

State / 상태: per-dimension evidence scores; one active hypothesis
("" until the first correct outcome); error streak of the active hypothesis.
차원별 증거 점수; 단일 활성 가설(첫 정답 전 ""); 활성 가설의 오류 연속.

| Scaffold step | Frozen semantics / 동결 의미론 |
|---|---|
| WAIT | no switch while `error_streak < wait_threshold` |
| CONSIDER | on every attributable outcome: `s <- decay * s` for all dimensions, then chosen dimension `± 1`, clipped to `[-5, +5]` |
| DISCRIMINATE | switch iff `score(best alternative) - score(hypothesis) > switch_margin` (strict); ties: least-recently-tried, then fixed RULES order |
| ACT | while a hypothesis is active, remap any other parsed choice to it; unparsable ("") always passes through; hard budget 9 interventions/rep (matched to Full and WSLSBudgeted — not a free parameter) |

Initial state: all scores 0, no hypothesis (pass-through until first correct
outcome). Unparsable frozen choices attribute to no dimension. Exception
handling: none needed beyond the above — every path is total.
초기 상태: 점수 0, 가설 없음(첫 정답까지 통과). 파싱 불가 동결 선택은 어느
차원에도 귀속되지 않는다. 예외 처리: 위 규칙으로 전 경로가 완결된다.

Free parameters, chosen by A0 (codified rule, full grid published in
`results/calibration_wcd_minimal.csv`) and FROZEN / A0가 코드화된 규칙으로
선택(전체 grid는 결과 CSV로 공개)하여 동결된 자유 파라미터:

- `decay` = **0.5** (grid: 0.5, 0.7, 0.9, 1.0)
- `switch_margin` = **0.0** (grid: 0.0, 0.5, 1.0, 2.0)
- `wait_threshold` = **1** (grid: 1, 2, 3)

Fixed, not searched / 고정(탐색 제외): `score_clip = 5.0`,
`max_interventions_per_rep = 9`.

**Disclosure — boundary selection / 공개 — 경계값 선택**: the codified rule
selected the extreme corner of the grid. With `wait_threshold = 1` and
`switch_margin = 0.0`, the WAIT and DISCRIMINATE gates are at their most
permissive settings: a single error of the active hypothesis licenses an
immediate switch whenever any alternative holds a strictly higher decayed
evidence score. On the calibration corpus every stricter setting produced
WORSE pooled perseveration (visible in the published grid). This is
disclosed as a calibration finding, not repaired: the confirmatory question
(§5) is whether the minimal evidence-accumulation form is non-inferior to
Full's protection stack, not whether particular threshold values are
active. The grid was run once; it was not extended after inspection.
코드화된 규칙은 grid의 극단 모서리를 선택했다. wait=1, margin=0.0에서
WAIT·DISCRIMINATE 게이트는 가장 관대한 설정이 된다: 활성 가설의 단일
오류만으로, 감쇠 증거 점수가 엄격히 더 높은 대안이 있으면 즉시 전환이
허용된다. calibration 코퍼스에서는 더 엄격한 모든 설정이 더 '나쁜' 합산
고착을 보였다 (공개된 grid에서 확인 가능). 이는 수리하지 않고 calibration
발견으로 공개한다: 확증 질문(5절)은 최소 증거 누적 형태가 Full의 보호
스택에 비열등한가이지, 특정 문턱값의 활성 여부가 아니다. grid는 1회만
실행되었고 결과 확인 후 확장되지 않았다.

## 4. Data / 자료

- **Models / 모델**: the same four confirmatory models, pinned IDs and
  generation configs unchanged from the study2-freeze
  (claude-opus-4-8, claude-sonnet-5, gpt-5.5-2026-04-23 with
  reasoning_effort "none", gpt-5.4-mini-2026-03-17 with reasoning_effort
  "none"). Library versions as pinned. No new pilot: prompts, parser, and
  models are unchanged from the passed pilot v2; the frozen 10% parser
  tolerance applies as a monitoring bound (exceeding it triggers the
  documented deviation procedure, not silent repair).
  동결된 4개 모델·생성 설정 그대로. 신규 파일럿 없음: 프롬프트·파서·모델이
  통과된 파일럿 v2와 동일하다. 파서 허용치 10%는 감시 기준으로 유지되며
  초과 시 침묵 수리가 아니라 문서화된 deviation 절차를 밟는다.
- **Repetitions / 반복**: reps **131–260** (130 per model), same master-seed
  scheme (`MASTER_SEED * 1000 + rep` for schedules; card stream offset for
  stimuli) — rep indices 131+ have never been generated, so schedules,
  stimuli, and streams are all new. Schedules remain shared across models at
  the same rep index.
  rep 131–260 (모델당 130). 동일 마스터 시드 체계 — rep 131+는 생성된 적이
  없으므로 일정·자극·스트림 모두 신규다. 같은 rep 번호의 일정은 모델 간
  공유된다.
- **Order of operations / 작업 순서** (violations void confirmatory status):
  1. `study2b-freeze` tag with all `[TO-FREEZE]` values filled, pushed with
     external timestamp;
  2. generate + COMMIT schedules and stimuli for reps 131–260 (extend the
     generator range without touching reps 1–130; the no-overwrite guards
     stay in force);
  3. confirmatory generation (runner unchanged);
  4. replay + statistics.
  순서 위반은 확증 지위를 무효화한다: ① 태그(수치 완결, 외부 타임스탬프)
  → ② rep 131–260 일정·자극 생성·커밋 (rep 1–130 불변, 덮어쓰기 방지 유지)
  → ③ 확증 생성 → ④ 재생·통계.
- **N justification / 표본 근거**: N = 130/model reuses the frozen power
  simulation: the binding original test (#4, prev_rule_error, worst-case
  d ≈ 0.60 at full effect) reached power .92 at N = 130 under 50%
  attenuation; the Study 2b primary is the same endpoint and analysis unit
  with an expected larger raw-vs-supervisor contrast. No interim analysis,
  no optional stopping.
  N=130은 동결된 power simulation을 재사용한다 (결정적 검정 d≈0.60에서
  N=130 power .92). 중간 분석·임의 중단 없음.
- **ITT / 결측**: identical to plan §5 — api_error ≤3 attempts, refusal ≤1
  retry, failures recorded as "" with flags; repetition-level exclusion is
  sensitivity-only.

## 5. Hypotheses and statistics / 가설과 통계

All analyses per model; repetition-level pairing via same-stream replay; the
statistical machinery is unchanged (paired permutation two-sided 10,000;
paired bootstrap 95% CI; matched-pairs rank-biserial; Holm on full-precision
p within each family per model).
모든 분석은 모델별, 같은 스트림 재생으로 rep 단위 paired. 통계 기계는 기존과
동일.

Conditions replayed on the Study 2b streams / Study 2b 스트림에 재생되는
조건: RawLLM (passthrough), WCDMinimal, RuleBlindFull (v1 frozen params),
WSLSBudgeted. (Full and WSLS are re-run on the new streams so all
comparisons are within-dataset; their Study 2 results stay locked and are
not re-litigated.)
(Full·WSLS도 새 스트림에서 재생해 모든 비교를 동일 데이터셋 내로 한정한다.
이들의 Study 2 결과는 잠금 상태로 유지되며 재론되지 않는다.)

**Primary (one test per model) / 1차 (모델당 1검정)**:

- **P1**: WCDMinimal < RawLLM on prev_rule_error (superiority).
  Two-sided permutation; success iff Holm p < .05 AND observed direction
  negative. Headroom gate as in plan §8: tested confirmatorily only if the
  model's RawLLM mean prev_rule_error ≥ 3.0 on the Study 2b streams;
  otherwise reported descriptively as "insufficient alignment-error
  headroom".
  1차: WCDMinimal의 prev_rule_error가 RawLLM보다 낮다(우월성). headroom
  게이트(RawLLM 평균 ≥ 3.0)는 계획 8절과 동일하게 적용.

**Key secondary / 핵심 2차**:

- **S1 (non-inferiority)**: WCDMinimal is non-inferior to RuleBlindFull on
  prev_rule_error iff the upper bound of the paired-bootstrap 95% CI of
  (WCDMinimal − Full) is **< Δ**, where
  **Δ = 1.9917** errors per 36-trial repetition, fixed by the
  pre-registered anchor rule: Δ = max(0.5, 0.5 × |pooled mean
  prev_rule_error of RawLLM − of Full v1| on the A0 calibration corpus)
  = max(0.5, 0.5 × |11.5333 − 7.5500|), computed and printed by
  `analysis/calibrate_wcd_minimal.py`.
  Non-inferiority is DIRECTIONAL (one-sided by CI bound); superiority of
  WCDMinimal over Full is not required and its absence is not a failure.
  비열등성: (WCDMinimal − Full) 차이의 paired bootstrap 95% CI 상한 < Δ.
  Δ는 사전 등록된 앵커 규칙으로 A0 코퍼스에서 산출·동결. 단측(CI 경계)
  판정이며 Full 대비 우월성은 요구되지 않고 그 부재는 실패가 아니다.

**Secondary family (Holm within family, per model) / 2차 family**:

- S2: WCDMinimal vs RawLLM — accuracy (expected +; also do-no-harm:
  non-inferior iff paired accuracy-difference 95% CI lower bound > −0.02,
  same SESOI as the frozen plan).
- S3: WCDMinimal vs WSLSBudgeted — prev_rule_error (two-sided, no
  pre-registered direction; context for the locked reversal).
- S4: WCDMinimal vs Full — accuracy (two-sided; do-no-harm bound −0.02).
- S5: intervention_count and intervention_precision — descriptive supervisor-
  regime checks (budget compliance is structural).

**Exploratory (labeled as such, no confirmatory claims) / 탐색**:

- WCDMinimal vs Full superiority on prev_rule_error per model (is minimal
  BETTER where Full reversed?); recovery-latency survival; post-error
  dynamics; per-model heterogeneity.

**Interpretation map, fixed now / 해석 지도, 지금 고정**:

| P1 | S1 | Reading / 해석 |
|---|---|---|
| pass | pass | minimal scaffold suffices; stack unnecessary — parsimony / 최소 비계로 충분, 스택 불필요 |
| pass | fail | scaffold works but the stack adds protection — complexity earns its keep / 비계 유효하나 스택이 보호를 더함 |
| fail | pass | neither helps beyond noise on this endpoint — hypothesis-tracking cost is intrinsic / 기전 자체의 비용 시사 |
| fail | fail | minimal form is actively harmful — protections were load-bearing / 보호 장치가 하중 지지 부재였음 |

## 6. Verification gates / 검증 게이트

`python scripts/run_all_checks.py` must pass (now includes the WCD-minimal
policy suite `tests/test_wcd_minimal.py`) before any Study 2b result is
reported. Banned-token gate covers `controller/wcd_minimal.py` automatically.
게이트 전체 통과 없이는 어떤 Study 2b 결과도 보고 금지. 금지어 게이트는 새
컨트롤러를 자동 포함한다.

## 7. Audit focus / 감사 초점

For the independent review (plan §12), the Study 2b-specific items:
독립 검토(계획 12절)용 Study 2b 특이 항목:

1. Calibration corpus (Study 1 archived) and confirmatory corpus (reps
   131–260) are disjoint by construction — verify no Study 2/2b path is
   readable from the calibration script.
2. WCD-minimal reads nothing beyond public info + post-freeze booleans
   (banned tokens; leak tests; freeze-before-feedback ordering).
3. Analysis unit is the repetition; no trial-level pseudo-replication.
4. Non-inferiority direction and margin implemented exactly as §5-S1.
5. No degrees of freedom remain after the tag: every `[TO-FREEZE]` value is
   numeric, the interpretation map is fixed, and deviations follow the
   documented procedure (DEVIATIONS.md).
6. Reps 1–130 files are byte-identical before/after the range extension.

## 8. Relation to the feasibility extension / 타당성 확장과의 관계

The model-authored state-carryover extension (exploratory, feasibility-only)
is specified separately in STUDY3_FEASIBILITY_DESIGN.md and makes no
confirmatory claims in this paper. Its causal test (state perturbation) is
deferred to a separately pre-registered Study 3.
모델 작성 상태 이월 확장(탐색·타당성 한정)은 STUDY3_FEASIBILITY_DESIGN.md에
별도 명세하며 본 논문에서 확증 주장을 하지 않는다. 인과 검증(상태 조작)은
별도 사전등록 Study 3로 미룬다.
