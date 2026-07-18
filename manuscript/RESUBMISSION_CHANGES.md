# 재제출 원고 변경·오류 수정 기록

작성일: 2026-07-18  
이 문서는 철회된 Cognitive Systems Research 제출본과 현재 재제출 작업본 사이의 변경 사항을 편집자·공저자 검토용으로 정리한다. 과학적 결과의 근거는 현재 저장소의 동결 계획과 Study 2 결과이며, 이전 제출본은 문서 구조·배경 문헌·문제 발견 기록으로만 사용했다.

## 1. 원본과 재사용 범위

- 철회 제출본: `COGSYS-S-26-00464`
- Editorial Manager 표시 번호: `COGSYS-D-26-00370`
- 철회 요청 참조번호: `260715-008289`
- 직접적인 과거 과학 원고: `brain like/Cognitive Systems Research/최종구조/files/baby40_CSR_anonymous.tex`
- Word 편집 구조 기준: `brain like/TMLR/Baby40_anonymous.docx`
- 새 작업본: `manuscript/BabyRuleBlind_resubmission_working_draft.docx`

재사용한 것은 다음으로 제한했다.

1. US Letter, 1인치 여백, Times New Roman, 제목–초록–본문–레퍼런스의 Word 계층 구조
2. WCST 배경, LLM 행동평가, 외부 감독이라는 일반적 문제 설정
3. 현재 원고에서도 실제 인용하는 검증 가능한 레퍼런스
4. 익명 저자 표기

재사용하지 않은 것은 다음과 같다.

1. 이전 2모델·30회·고정 일정 수치와 그림
2. “feedback-free control”의 효과를 확정적으로 주장한 문장
3. “persistence”를 단일 기제처럼 해석한 문장
4. cross-model generalizability를 이미 입증했다고 쓴 문장
5. 생산적 개입률(productive rate)을 효율성의 확증 지표로 취급한 문장
6. 국소 파라미터 탐색을 최적성 증거로 표현한 문장
7. Gemini 예비 probe와 구형 모델 API 결과

## 2. 핵심 과학적 프레임 변경

| 항목 | 철회 원고 | 재제출 작업본 | 수정 이유 |
|---|---|---|---|
| 제목/주장 | feedback-free cognitive control, deterministic executive scaffold | sparse outcome-feedback supervision of memoryless LLM outputs | 현재 주요 조건은 정오 Boolean 피드백을 받으므로 “feedback-free”는 부정확 |
| 분석 단위 | 2개 구형 모델, 각 30회 | 4개 최신 모델, 각 130회 | 모델 외부 전이와 검정력 확보 |
| 일정 | 모든 반복에 같은 고정 순서 | 반복별 사전 생성 무작위 일정 | 일정 암기·과적합·특정 전환 위치 혼입 방지 |
| 주요 비교 | Independent vs Baby40 중심 | RuleBlindFull과 WSLSBudgeted 공동 주요 조건 | 같은 정보와 같은 개입 예산의 강한 기준선 필요 |
| 용어 | persistence error | previous-rule-aligned error | 관찰된 정렬만 기술하고 내부 지속 기제를 과잉 추론하지 않음 |
| 개입량 | 조건별 비교 가능성이 불명확 | 36 trial당 최대 9회(25%) 하드 예산 | 정책 성능과 개입량의 혼입 방지 |
| 전이 결론 | 두 모델에서 일반화 주장 | 1/4 모델만 전체 trade-off 통과 → no transfer | 사전 등록 판정 규칙을 그대로 적용 |
| Bayesian 표현 | 실행기제에 가까운 비유 가능 | 개념적 비유로만 제한, posterior/optimality 주장 금지 | 현재 감독자는 동결된 heuristic이며 Bayesian 계산을 구현하지 않음 |

## 3. 설계 오류와 보완

### 3.1 피드백 정보 비대칭

이전 원고는 외부 감독자의 실제 정보원을 명확히 분리하지 않아 trajectory 효과와 정오 피드백 효과가 섞일 수 있었다. 새 설계에서는 `RuleBlindFull`과 `WSLSBudgeted`가 동일한 Boolean 정오 피드백을 받고, 동일한 9회 예산을 사용한다. 엄격한 feedback-free 가설은 `TrajectoryOnly`로 분리했다.

결과적으로 `TrajectoryOnly`는 네 모델 모두 RawLLM과 ±.02 범위에서 정확도 동등이었다. 따라서 “trajectory shaping alone improves correctness”는 지지되지 않는다.

### 3.2 약한 기준선

이전 원고는 복잡한 감독자를 사실상 무통제 출력과 비교했다. 재제출 설계는 단순하지만 강한 정보일치 기준선인 `WSLSBudgeted`를 공동 주요 조건으로 승격했다.

새 결과에서는 WSLSBudgeted가 네 모델 모두에서 RuleBlindFull보다 정확도가 높았다(+.0344~+.0530, Holm p<.001). 복잡한 정책의 우월성을 주장하지 않고, 단순 정책이 현재 공학적 기본 선택이라는 결론으로 수정했다.

### 3.3 고정 일정 과적합

Study 1은 하나의 고정 일정과 카드 순서를 반복했다. 이는 특정 전환 위치나 카드 배열에 맞춘 파라미터 선택 위험이 있다. Study 2는 master seed 20260715로 API 호출 전에 반복별 일정을 만들고 커밋했다. 모든 블록 길이는 4~8이며, 같은 rep의 일정은 모델 간 공유하되 각 모델의 raw stream은 자기 일정에서 모든 조건으로 replay된다.

### 3.4 개발 자료와 확증 자료 혼합

이전 결과는 파라미터 탐색에 사용된 같은 자료의 효과크기를 중심으로 보고했다. 새 원고는 역할을 명시적으로 분리한다.

- Study 1: 60개 보관 stream, 개발·파라미터 탐색·탐색 분석 전용
- Study 2 pilot: 파서/프롬프트 공학 점검 전용, 모든 분석에서 제외
- Study 2 confirmatory: 동결 이후 최초 접촉, 파라미터 재조정 없음

### 3.5 파서와 응답 형식 오류

초기 Study 2 pilot에서 Claude 계열의 설명형 응답 때문에 parser v2의 unparsable 비율이 동결 허용치 10%를 넘었다. 계획의 re-freeze 절차에 따라:

1. 실제 최종답 표현을 포괄하는 parser-v3 marker regex를 추가했다.
2. 모든 모델·trial에 동일하게 “Answer with just the dimension name.” 한 줄을 추가했다.
3. stimuli를 같은 seed로 재생성했다. 카드와 일정은 변하지 않았다.
4. 기존 pilot은 실패 기록으로 보관하고 확증 자료에서 완전히 제외했다.

확증 생성 18,720건 중 unparsable은 24건(0.128%)이며 모두 Claude Sonnet 5였다. API error와 refusal은 0건이었다. 조건별 replay 표에서 같은 24건이 8번 나타나므로 192개의 독립 생성 실패로 잘못 세면 안 된다.

### 3.6 오류 처리와 선택 편향

전체 repetition을 제거하는 방식은 어려운 응답만 선택적으로 빠질 수 있다. 새 설계는 intention-to-treat를 사용한다. 재시도 후에도 파싱할 수 없는 trial은 빈 선택/오답으로 남기며, repetition 제외는 민감도 분석에서만 허용한다.

### 3.7 통계 family와 판정 규칙

모델별 주요 검정은 네 개이며 Holm 보정은 full-precision p-value에 적용한다.

1. RuleBlindFull > RawLLM 정확도
2. WSLSBudgeted > RawLLM 정확도
3. WSLSBudgeted > RuleBlindFull 정확도
4. RuleBlindFull < WSLSBudgeted previous-rule-aligned error

한 모델에서 네 검정이 모두 성공해야 trade-off 재현이다. 4개 모델 중 3개 이상 broad, 2개 partial, 1개 이하는 no transfer다. 결과는 GPT-5.5만 네 검정을 모두 통과했으므로 **no transfer**다.

### 3.8 지표 정의 오류

- `persistence`를 `previous-rule-aligned error`로 교체했다.
- old-rule reentry는 현재 블록에서 한 번 이상 정답 후 발생한 previous-rule-aligned error로 동결했다.
- recovery latency는 정답이 없는 블록을 관찰 길이에서 검열한다.
- productive rate는 이후 우연한 정답으로도 충족될 수 있어 주요 지표에서 제거했다.
- 직접 안전성 지표를 추가했다: corrective override, harmful override, net correction, intervention precision.
- TrajectoryOnly의 “효과 없음”은 유의하지 않음이 아니라 ±.02 SESOI의 90% CI 동등성으로 판정한다.
- 두 공동 주요 감독자의 do-no-harm은 −.02 비열등 마진으로 판정한다.

## 4. 결과 해석의 정정

### 유지되는 결론

- 희소 Boolean outcome feedback을 사용하는 외부 감독은 무기억 LLM 출력 정확도를 개선했다.
- RuleBlindFull의 정확도 개선은 네 모델에서 +.1160~+.1252였다.
- WSLSBudgeted의 정확도 개선은 네 모델에서 +.1585~+.1690였다.
- 두 감독자는 네 모델 모두 RawLLM 대비 비열등이었다.
- 동일 개입 시점의 YokedRandom 및 NoVeto와의 비교는 개입 선택·veto 논리가 중요함을 뒷받침한다.

### 철회하거나 약화한 결론

- feedback-free trajectory만으로 정답이 개선된다는 결론: 철회
- RuleBlindFull이 단순 정책보다 전반적으로 우월하다는 결론: 철회
- accuracy–previous-rule-error trade-off가 모델 세대를 넘어 일반화한다는 결론: 철회, frozen label은 no transfer
- 높은 entropy가 곧 유연성/적응성이라는 해석: 철회
- 모델 행동이 인간의 전두엽 또는 executive-control 기제와 동일하다는 해석: 사용 금지
- Bayesian 또는 resource-rational optimality를 입증했다는 표현: 사용 금지

## 5. 정확성·재현성 보완

- Study 2 exact grid: 4 models × 130 reps × 8 conditions × 36 trials = 149,760 rows
- public generation: 4 × 130 × 36 = 18,720 responses
- 모든 통계는 모델별 paired repetition 분석이며 모델을 pooling하지 않음
- paired permutation 10,000회, paired bootstrap 95% CI, matched-pairs rank-biserial
- duplicate/missing repetition 검증 후에만 pairing 허용
- 기존 repetition 덮어쓰기 금지
- prompt, ground truth, controller input 경로를 분리
- schedules, archived extraction, attempts logs에 SHA-256 manifest 적용
- 통계 재실행 후 `study2_paired_stats.csv`가 보완 전과 byte-identical임을 확인

## 6. 보안·개인정보 보완

- `.env`는 Git 추적 제외 상태를 확인했고 로컬 ACL을 현재 사용자, SYSTEM, Administrators로 제한했다.
- 공개 파일에서 개인 PC 절대경로를 제거했다.
- 비밀키 패턴, credential 포함 remote URL, private-key 파일, 로컬 경로 누출을 검사하는 자동 gate를 추가했다.
- GitHub Actions는 최소 권한, 전체 이력 검사, commit SHA 고정 action을 사용한다.
- Dependabot 주간 점검을 추가했다.
- 새 Word 파일의 core properties에서 작성자·마지막 편집자·조직·개인 경로를 제거한다.
- 새 원고와 변경 기록에는 API key, `.env` 값, 이메일, 계정 ID, 로컬 사용자 홈 경로를 넣지 않는다.

## 7. 재제출 시 편집자에게 요약할 문장

다음 취지로 cover letter 또는 response note에 사용할 수 있다.

> The withdrawn version relied on two development-era models, a repeated fixed schedule, and a weak uncontrolled comparison, which did not adequately separate trajectory effects from information supplied by outcome feedback. Before collecting the new confirmatory data, we froze an information-matched design with randomized schedules, a hard intervention budget, intention-to-treat parsing rules, and four held-out model generations. The revised manuscript reports the resulting null/negative evidence transparently: sparse outcome-feedback supervision improved accuracy across all four models, but the proposed accuracy–previous-rule-error trade-off transferred to only one model and therefore received the pre-registered label “no transfer.” A separately frozen follow-up (Study 2b) then evaluated a minimal supervisor on newly generated streams and localized the failure to the elaborate supervisor's protection machinery: the minimal policy — behaviorally identical to the win-stay/lose-shift baseline under its calibrated parameters — reduced previous-rule-aligned errors on all four models and was non-inferior to the elaborate supervisor everywhere, removing the reversal on both Claude models.

## 8. Study 2b 추가 (2026-07-18, 원고 통합)

Study 2 잠금 결과의 Claude 역전을 규명하기 위한 별도 동결 후속 확증을 원고에 통합했다.

- **설계 규율**: 가설은 Study 2 결과 관찰 '이후' 형성되었음을 원고에 명시.
  파라미터는 보관 Study 1 스트림에서만 calibration(공개 grid 48개, 코드화된
  선정 규칙, 경계값 선택 공개), `study2b-freeze` 태그(외부 타임스탬프)로
  가설·마진(Δ=1.9917)·해석 지도·재생/통계 코드까지 스트림 생성 전 커밋.
  신규 rep 131–260 (모델당 130, 기존 rep 바이트 동일성 검증).
- **결과**: P1(WCDMinimal < RawLLM, prev-rule error) 4/4 통과 (−5.23 ~
  −2.01, 전부 Holm p < .001); S1 비열등성 4/4 (CI 상한 최대 0.49 < 1.9917);
  판정 전 모델 "minimal sufficient". 탐색: 역전이 나타났던 두 Claude
  모델에서 정확히 WCDMinimal이 Full보다 우월 (Opus −0.78 p<.001, Sonnet
  −0.54 p=.013), GPT 모델은 null.
- **정직성 항목**: 동결 모서리 파라미터에서 WCDMinimal의 선택이 확증 trial
  전체에서 WSLSBudgeted와 정확히 동일 → 원고는 "제거 주장(보호 스택이
  역전의 원인)"과 "충분성 주장(WSLS 동등 정책으로 충분)"만 허용하고, 증거
  누적·대기·변별 기제의 기여 주장은 명시적으로 배제 (§4.6, §6).
- **원고 반영 위치**: Abstract 말미, §1 마지막 문단, §3.8(신설), §4.6(신설,
  표 포함), §5 새 문단, §6 새 문단, §7 확장, §8 결론 수정.

## 9. 편집 전 남은 체크리스트

- 목표 저널의 익명화·AI-assisted writing disclosure·data availability 형식에 맞춰 front/back matter 조정
- 저널 reference style에 맞춰 `manuscript/REFERENCES.bib` 또는 Word 참고문헌 변환
- 확증 표와 탐색 표를 명확히 분리하고 탐색 분석에 “post hoc/descriptive” 표시
- Figure는 현재 CSV에서 새로 생성하고, 이전 제출본 Figure 1–4/S1–S2를 재사용하지 않음
- model provider/version/date와 API 설정을 Methods 또는 supplement에 완전하게 기재
- cover letter에서 철회 번호 관계를 추정하지 말고 저널이 확인한 식별자만 역할별로 표기
