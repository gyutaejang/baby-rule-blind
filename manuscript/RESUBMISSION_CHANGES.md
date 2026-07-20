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

## 9. 서술 구조 개정 (2026-07-20, 공저자 피드백 반영)

엄밀성을 줄이지 않고 **엄밀성의 위치와 제시 순서를 재배치**하는 전면 서술
개정. 수치·판정·동결 절차는 단 하나도 변경하지 않았다.

- **Abstract**: 질문("무기억 LLM 출력을 외부 감독으로 적응시킬 수 있는가")
  → 3개 발견(궤적만으로 불충분 / 희소 피드백이 효과 / 단순 정책이 우월)
  → Study 2b 국소화 → 절차 요약 순으로 재구성.
- **§1 서론**: 조건 나열 대신 3개 질문 중심으로 재편. 개발사(피드백 없는
  궤적 가설 → 반증 → 단계적 분리)를 과학적 자기교정 서사로 명시.
- **§2.1 / §5.3**: Stroop(명시 규칙 하 갈등 해결) vs AX-CPT(단서 유지,
  proactive/reactive) vs WCST(결과 피드백 기반 잠재 규칙 발견)의 측정
  과정 구분을 추가하고, 확증 증거의 범위를 "희소 결과 피드백을 이용한
  잠재 규칙 적응"으로 한정. 이전 Stroop/AX-CPT 결과는 개발 계보로만 언급.
- **§2.3 신설**: 자연어 피드백 기반 LLM 교정(Self-Refine, Reflexion)과
  내재적 자기교정의 한계(Huang et al. 2024) 대비, 본 연구는 1비트 결과
  신호 + 감사 가능한 소형 외부 상태라는 위치 명시.
- **§2.4 / §5.2**: 강한 정보·비용 일치 기준선 필요성의 방법론 논거
  (Henderson et al. 2018) 추가.
- **§3.4 신설**: TrajectoryOnly / WSLSBudgeted / RuleBlindFull 각각을
  목적 → 볼 수 있는 정보 → 행동 규칙 → 기대 효과 → 실제 결과의 공통
  형식으로 평이하게 서술. WCDMinimal은 §3.11에서 같은 형식 적용.
- **§3.5 신설**: 거부 창·쿨다운·구조적 보호·증거 누적을 기능 한 문장씩
  정의하고, 기대 이득과 잠재 비용(명확한 피드백 환경에서 갱신 지연)을
  함께 제시.
- **§3.6 신설**: color 예시 작동 사례(WSLS 즉시 전환 vs RuleBlindFull의
  신중한 해석과 그 비용). 동결 파라미터는 사례 뒤 기술 단락으로 이동.
- **§3.9 확장(피드백 10절)**: 분석 환경을 본문에 명시 — 표준 라이브러리
  전용(CPython 3.14, Windows; NumPy/pandas/SciPy/statsmodels 미사용),
  생성 전용 패키지 anthropic 0.116.0 / openai 2.45.0, 부호반전 순열
  10,000회·시드 20260715·add-one 보정·0차이 유지, 백분위 부트스트랩
  10,000회·순열과 분리된 시드, rank-biserial의 0차이 제외(Wilcoxon
  관례)와 동률 평균순위, Holm은 모델별·family별 원정밀도 p값에 적용,
  비열등 −0.02(95% CI 하한)·동등성 ±0.02(90% CI) 판정 기준.
- **§4 결과**: 각 절을 핵심 판정 → 효과 크기 → 통계 근거 → 해석 제한
  순서로 통일. 절 제목을 판정문으로 변경(예: "The predicted trade-off
  did not transfer", "Removing the protection stack removed the
  reversal").
- **§5 논의**: 무엇을 발견했는가(5.1) / 왜 WCST 구조에서 나타났는가(5.2)
  / 범위와 WCST 한정 이유(5.3) / 적용 가능·불가 영역(5.4: 도구·API 선택,
  범주형 라우팅 등 vs 개방형 생성·고위험 의사결정) / 초기 가설의 수정
  경위(5.5) 구조로 재편. "출력 변화 ≠ 적응, 결과 정보 방향의 변화 = 적응"
  정의를 명시.
- **§8 결론**: "새 감독기 제안"이 아니라 "정보 접근권·외부 상태·갱신
  속도·정책 복잡성의 역할 분리(dissection)"로 기여 재규정.
- **참고문헌 6건 추가**: Stroop 1935; Braver 2012; Henderson et al. 2018;
  Huang et al. 2024; Madaan et al. 2023 (Self-Refine); Shinn et al. 2023
  (Reflexion). 또한 기검증 항목 de Langis et al. 2026을 §2.2에 인용.
  신규 6건의 서지정보는 기억 기반이므로 **제출 전 원문 대조 검증 필요**
  (REFERENCES.bib의 pending-verification 블록 참조).

## 10-1. 유저 검토 피드백 반영 + CSR 형식화 (2026-07-20, v3)

v2 검토 피드백 5건을 반영하고 CSR(Cognitive Systems Research) 투고 형식으로
정리했다. 수치·판정·동결 절차는 변경하지 않았다.

1. **"sparse feedback" 용어 분리**: 정오 피드백은 매 trial 제공(1비트)이고
   희소한 것은 개입 예산(36회 중 최대 9회)이므로, 전체 원고에서
   피드백 = "binary outcome feedback", 예산 = "sparse intervention budget"으로
   분리. 제목을 "Binary Outcome-Feedback Supervision of Memoryless LLM
   Outputs under a Budgeted Intervention Policy"로 변경. §4.1 절 제목도 수정.
2. **Study 2b 인과 표현 완화**: WCDMinimal이 확증 자료 전체에서
   WSLSBudgeted와 동일 행동이었으므로 "identified cause" 수준 표현을
   "removing the stack eliminated the reversal / implicating the protection
   stack"으로 하향(§1, §5.1, §5.5, §8, Abstract). §6에 "개별 보호 기제로의
   귀속은 불허" 명시.
3. **"correctness bit is what helps" 완화**: "under the tested policies,
   improvement required access to correctness feedback"로 교체(Abstract,
   §4.1, §5.1, §5.5). §6에 TrajectoryOnly는 정보뿐 아니라 행동 규칙도
   다르므로 정보의 독립 인과효과를 분리하지 못한다는 한계 문장 추가.
4. **분량·방어적 서술 감축**: §3.9 통계 구현 세부(동률 처리, 0차이 취급,
   시드 유도, 패키지 핀)와 §7 보안 hardening 목록을 보충자료 포인터로
   이관·압축. byte-identical 반복 제거, frozen 사용 밀도 완화.
5. **형식(CSR)**: Abstract 337→약 245단어(Study 2b 세부 통계는 1개 유지),
   Highlights 5개(각 85자 이내) 신설, 표 4개에 Table 1–4 번호·캡션·Note
   추가 및 본문 상호참조, Declaration of competing interest / Data
   availability / Generative AI 사용 선언 / Funding 절 신설(익명 호환).
6. **빌드**: `tools/build_english_manuscript_v3.py` 신설 — md 소스에서
   `BabyRuleBlind_resubmission_working_draft_v3.docx` 생성(US Letter, 1인치,
   Times New Roman, 바닥글 페이지 번호, 제목·캡션 keep-with-next로 고아
   제목 방지, 표 페이지 내 유지, core properties 익명화). Word 렌더 검증
   완료(22쪽, 초록 1쪽 내 완결, Table 1–4 분할 없음).
7. **주의**: 한영병기 docx 4종은 v2 기준이므로 v3 확정 후 재생성 필요.
8. **제출 패키지 생성 (2026-07-20)**: `manuscript/submission_package/`에
   CoverLetter / TitlePage / Manuscript_Anonymized / Highlights /
   DeclarationOfInterests / SupplementaryMaterials 6종 생성
   (`tools/build_submission_package.py`). 남은 placeholder와 업로드
   매핑은 폴더 내 README.md 참조 — 소속, 익명 저장소 링크, S3 의사코드,
   서지 검증, Figure 결정.
9. **제출 전 작업 완료 (2026-07-20 3차)**: ① 저자 정보 확정(무소속
   Independent Researcher; 상세는 비공개 submission_package의 Title
   Page에만 기재). ② 보충자료 S3 완성 — 컨트롤러 4종
   의사코드 전사(`tools/supplement_s3.md`), 코드-원고 파라미터 교차검증
   전부 일치, 48-구성 grid 전표 포함. ③ Figure 1–3 신규 생성 —
   `scripts/make_figures.py`(결정론적, locked CSV만 사용), 300dpi PNG +
   벡터 PDF, 값 대조 검증 완료; 본문 인용과 Figure captions 절 추가.
   ④ 서지 검증 — pending 21건 전부 원문 대조 일치(md 수정 0건); .bib
   결함 2건 수정(Kopp2021 죽은 DOI, Miles2021 타 논문 DOI·저자명).
   남은 것: 익명 저장소 링크, EM 번호(제출 후).
10. **선언문 갱신 (2026-07-20 2차)**: 단독 저자 표기("the author")로 수정;
   생성형 AI 선언에 GPT-5.6 sol(OpenAI) — 보조적 데이터 검토·교차확인,
   문헌 검색 — 추가. 확증 통계는 동결 분석 코드만 산출했음을 병기.
   CSR 이중 익명 규정상 제출 시 competing interest는 title page/별도
   파일로, highlights는 "highlights" 파일명의 별도 파일로 분리해야 함
   (현 작업본에는 검토 편의상 본문에 유지).

## 10. 편집 전 남은 체크리스트

- §7 재현성 절에 일정 재생성 한 문장 추가 (2026-07-20 합의 · 반영 완료 2026-07-20):
  단일 명령(`python scripts/generate_schedules.py`)으로 byte-identical
  재생성되며, repetition k의 생성기는 표준 라이브러리
  `random.Random(20260715 × 1000 + k)`로 유도됨 + SHA-256 manifest 검증.
  본문 §3.2에는 넣지 않는다(절차 상세는 후면 배치 원칙 유지).
- 기제의 설계 계보(design lineage) 추가 (2026-07-20 합의 · 반영 완료 2026-07-20).
  수위: "등가(equivalence)"가 아니라 "설계 영감/계보"로만 서술 —
  posterior/optimality 주장 금지 원칙(§2) 유지.
  - §3.5: 네 기제 각각에 반 문장씩 원리적 대응물 명시 — 거부 창 ↔
    change-point 추론의 증거 대기(Adams & MacKay 2007), 쿨다운 ↔ 전환 후
    안정화/전환 비용(Monsell 2003), 증거 누적 ↔ delta-rule 근사 베이지안
    갱신(Nassar et al. 2010), 구조적 보호 ↔ 보속 오류 방지·우세 반응
    억제(Diamond 2013).
  - §2.4: 베이지안 change-point 규범 프레임 2–3문장 (Adams & MacKay
    2007; Behrens et al. 2007; Wilson, Nassar & Gold 2010; Nassar et
    al. 2010) + "설계 영감이지 기제 등가가 아니다" 한정 문장.
  - §5.2: 보호 기제는 잡음 피드백 환경에서 합리적인 정책의 저비용
    근사였고, 이번 환경(깨끗한 피드백, 오답 = 강한 규칙 변화 신호)은 그
    전제가 성립하지 않는 지점이었다는 한 문장 — 실패를 환경 통계
    불일치로 해석하는 규범적 근거.
  - 레퍼런스 6건 추가 예정: 베이지안 4건(Adams & MacKay 2007, Behrens
    et al. 2007, Wilson et al. 2010, Nassar et al. 2010 — LITERATURE_MAP
    기검토) + 인지심리 2건(Monsell 2003 task switching TiCS, Diamond
    2013 Executive Functions Annu Rev Psychol — 신규, 서지 검증 필요).
- parsimony(오컴의 면도날) 한 문장 추가 (2026-07-20 합의 · 반영 완료 2026-07-20).
  적용 조건 엄수: WSLS가 '이긴' 곳이 아니라 Study 2b에서 WCDMinimal과
  WSLSBudgeted의 행동이 '구별 불가능'했던 곳에만. 위치는 §5.5 또는 결론.
  용어는 parsimony 사용(Occam's razor 직접 호명은 괄호 1회 이내). 문안:
  "Where the evidence could not distinguish two policies — WCDMinimal
  and WSLSBudgeted behaved identically on every confirmatory trial — we
  follow parsimony and report the simpler, auditable description as the
  sufficient mechanism."
- §8 결론 마지막 문장 보강 (2026-07-20 합의 · 반영 완료 2026-07-20). "reports
  exactly how far the surviving claims extend"의 'exactly'(수사)를
  검증 가능한 근거로 교체: "...and reports how far the surviving claims
  extend — a boundary drawn by pre-registered, operationalized criteria
  rather than by narrative judgment." 근거: 전이 판정 라벨, 비열등 마진
  −0.02, headroom 게이트, 동결 파서 + intention-to-treat 채점이 모두
  사전 조작적 정의임. '표준화'는 사용하지 않음(외부 표준 부재).
- de Langis et al. 2026 적극 활용 (2026-07-20 합의 · 반영 완료 2026-07-20). 전문
  확인 완료(ACL Anthology 공개). 핵심: 그들의 WCST 전략 힌트 프롬프트가
  문자 그대로 WSLS인데("correct면 같은 규칙, incorrect면 다른 규칙")
  in-context 언어 지시로는 실패 → 우리의 외부 집행 감독기는 +16%p.
  "정책을 아는 것 ≠ 정책이 집행되는 것" 대비.
  - §2.3 끝에 두 문장: in-context 언어 지시 실패 vs 외부 집행 성공.
  - §5.2 강한 기준선 문단에 한 문장.
  - 조건 차이 명시: 그들은 in-context 이력+피드백(102 trial 연속,
    오픈소스 소형 모델), 우리는 무기억+외부 피드백 → 정량 비교 불가,
    인접 증거로만. Re-TASK(Wang et al. 2025)는 검토 후 인용 제외 확정
    (프롬프팅 프레임워크, 피드백·적응·감독 루프 없음).
- 통계·재현성 방법 레퍼런스 7건 추가 (2026-07-20 합의 · 반영 완료 2026-07-20).
  위치는 §3.9와 §7, 각 판정 규칙의 출처 명시 목적(수 늘리기 아님).
  - Holm 1979 (Scand J Stat 6:65–70) — Holm 보정 원전, **필수**(현재 누락)
  - Efron & Tibshirani 1993 — 백분위 부트스트랩 CI
  - Ernst 2004 (Stat Sci 19:676–685) — 순열검정 정확 추론
  - Kerby 2014 (Compr Psychol 3) — matched-pairs rank-biserial 정의
  - Schuirmann 1987 (J Pharmacokinet Biopharm 15:657–680) — TOST 원전
  - Lakens 2017 (SPPS 8:355–362) — 동등성 검정 실무·SESOI
  - Matsumoto & Nishimura 1998 (ACM TOMACS 8:3–30) — Mersenne Twister
    (`random.Random`의 실제 PRNG; §7 시드 유도식 항목과 세트)
  - 전건 서지 검증 필요(기억 기반).
- 결과 피드백 in-context 계열 문헌 추가 (2026-07-20 합의 · 반영 완료 2026-07-20).
  §2.3에 "선행 연구는 결과/보상 피드백을 문맥 안에 넣었고 사용이
  불안정했다 → 우리는 같은 1비트를 문맥 밖으로 옮겼다(처리의 위치)"
  문단 구성.
  - Krishnamurthy et al. 2024 (NeurIPS 2024, arXiv:2403.15371) — MAB
    탐색 실패, 외부 요약 필요 → 외부화의 직접 선례. **필수**
  - Schubert et al. 2024 — bib 기검증, 본문 미인용 → 인용 추가. **필수**
  - Hayes, Yax & Palminteri 2024 (arXiv:2405.11422) — 상대가치 편향.
    arXiv 인용(저장소 관례상 허용; Hao/Li/Haznitrama와 동일 취급).
  - de Langis 2026과 함께 하나의 논변으로 통합(항목 5와 연결).

- 목표 저널의 익명화·AI-assisted writing disclosure·data availability 형식에 맞춰 front/back matter 조정
- 저널 reference style에 맞춰 `manuscript/REFERENCES.bib` 또는 Word 참고문헌 변환
- 확증 표와 탐색 표를 명확히 분리하고 탐색 분석에 “post hoc/descriptive” 표시
- Figure는 현재 CSV에서 새로 생성하고, 이전 제출본 Figure 1–4/S1–S2를 재사용하지 않음
- model provider/version/date와 API 설정을 Methods 또는 supplement에 완전하게 기재
- cover letter에서 철회 번호 관계를 추정하지 말고 저널이 확인한 식별자만 역할별로 표기
