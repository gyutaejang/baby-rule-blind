# LITERATURE_MAP.md — 논문 개념·문헌 지도

> 목적: baby-rule-blind 논문(희소 정오 피드백 감독자 + 무기억 LLM, WCST형
> 규칙 전환)을 쓰기 위한 개념 프레임과 추천 문헌.
> 고급 수리·통계 세부(모델 유도, 사전분포 선택, 검정 설계)는 별도 상의
> 예정 — 여기서는 개념 수준의 자리만 잡아둔다.
>
> 표기: ★ = 반드시 읽고 인용할 핵심, ○ = 서론/고찰 보강용.

---

## 0. 논문의 한 문장 프레임

**"정오(correct/incorrect)만 관측하는 rule-blind 감독자는 은닉 규칙에 대한
근사 베이지안 change-point 추론기이며, 우리는 이를 무기억 LLM 위에 얹어
그 기여를 분리 측정했다."**

- 지금 컨트롤러(`controller/rule_blind_full.py`)의 각 요소는 베이지안
  대응물을 갖는다:
  - `values` 증감 ↔ 각 차원이 보상 차원일 사후확률
  - `belief_confirm_streak` ↔ 사후확률 임계값 통과
  - veto window ↔ change-point 사후확률 급등 구간
  - rescue ↔ 사후확률 바닥 차원에 대한 반복 제안 차단
- 과제의 수학적 정체: **은닉 마르코프 모델(HMM)**. 은닉 상태 = 현재 보상
  차원, 전이 = hazard rate h의 규칙 전환, 관측 = trial별 정오.
  → forward 알고리즘이 곧 ideal observer. 휴리스틱 감독자 vs 베이지안
  ideal observer 비교가 논문의 자연스러운 확장축 (Study 3 후보).

---

## 1. 베이지안 change-point / volatility 추론 (계산 모델의 뼈대)

| | 문헌 | 왜 필요한가 |
|---|---|---|
| ★ | Adams & MacKay (2007). *Bayesian Online Changepoint Detection.* arXiv:0710.3742 | "환경이 방금 바뀌었는가"의 온라인 추론 표준 프레임워크. veto window의 원리적 버전. 방법론 절에서 우리 휴리스틱이 이것의 저비용 근사임을 명시할 때 인용. |
| ★ | Behrens, Woolrich, Walton & Rushworth (2007). *Learning the value of information in an uncertain world.* Nat. Neurosci. | hazard rate(환경 변동성) 자체를 학습하는 계층 베이지안 + 인간 행동/ACC 증거. "감독자의 파라미터가 환경 통계에 대응한다"는 논변의 근거. |
| ★ | Wilson, Nassar & Gold (2010). *Bayesian online learning of the hazard rate in change-point problems.* Neural Comput. | 전체 베이지안 추론의 **근사(reduced) 모델**들이 행동을 거의 동등하게 설명함을 보임 — "휴리스틱 감독자 ≈ 근사 베이지안" 주장의 직접 선례. |
| ○ | Nassar et al. (2010). *An approximately Bayesian delta-rule model...* J. Neurosci. | delta-rule(우리의 value ±0.30과 같은 형태)이 근사 베이지안 갱신임을 보인 논문. `value_gain/loss`를 학습률로 재해석할 때. |
| ○ | Mathys, Daunizeau, Friston & Stephan (2011). *A Bayesian foundation for individual learning under uncertainty.* Front. Hum. Neurosci. (HGF) | 계층적 가우시안 필터.

---

## 2. WCST 계산모델과 LLM 직접검사

| | 문헌 | 우리 논문에서의 역할 |
|---|---|---|
| ★ | D'Alessandro et al. (2020). *A Bayesian brain model of adaptive behavior: an application to the WCST.* PeerJ 8:e10316 | 인간 WCST의 trial별 베이지안 믿음 갱신. 우리 감독자와 가장 가까운 인간 계산모델이지만, 외부 감독자·무기억 LLM·하드 예산은 없다. |
| ★ | Bishara et al. (2010). *Sequential Learning Models for the Wisconsin Card Sort Task.* J. Math. Psych. 54:5–13 | 잠재 주의/학습 과정을 분리하는 고전 비교모델. |
| ★ | Steinke, Lange & Kopp (2020). *Parallel model-based and model-free reinforcement learning for card sorting performance.* Sci. Rep. 10:15464 | 범주 수준 MB-RL과 반응 수준 MF-RL의 병렬 학습. 베이지안 change-point 감독자의 강한 RL 비교군. |
| ★ | Kennedy & Nowak (2024). *Cognitive Flexibility of Large Language Models.* ICML LLMs and Cognition Workshop | 같은 context 안의 전환과 분리 context의 과제 성공을 구분한다. |
| ★ | de Langis et al. (2026). *Strong Memory, Weak Control.* EACL 2026 | LLM의 작업기억 용량과 통제/전환 성능이 분리될 수 있음을 보인다. |
| ○ | Li et al. (2025); Hao et al. (2025); Goto et al. (2025); Haznitrama et al. (2026, preprint) | 최신 LLM-WCST 직접검사군. 성능 결론이 과제 형식·모달리티·프롬프트에 따라 갈리므로 우리의 외부 감독자 설계와 명확히 구분한다. |

## 3. 출력 엔트로피와 프롬프트 민감성

| | 문헌 | 우리 논문에서의 역할 |
|---|---|---|
| ★ | Sclar et al. (2024). *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design.* ICLR | 동일 의미의 포맷 변화도 성능을 크게 바꿀 수 있다. 단일 프롬프트의 모델 순위를 고유 특성으로 일반화하지 않는 근거. |
| ★ | Chatterjee et al. (2024). *POSIX.* Findings of EMNLP | intent-preserving prompt 변형에 대한 민감도를 별도 지표로 측정하는 선례. |
| ★ | Schubert et al. (2024). *In-Context Learning Agents Are Asymmetric Belief Updaters.* ICML | 피드백이 있는 미래 온라인 조건에서 긍정/부정 결과의 비대칭 갱신을 검정할 근거. 현재 무기억 RawLLM 설명에는 사용하지 않는다. |

**핵심 해석:** `choice_entropy`와 단일 차원 선호는 현재 자료에서는
**동결된 모델×프롬프트×디코딩 조건의 행동 표현형**이다. 내부 불확실성이나
ADHD/ASD와 유사한 인지 특성으로 직접 해석하지 않는다. Study 2에서
GPT-5.5의 Raw 엔트로피는 Claude보다 높았지만 RuleBlindFull의 정확도 증가는
Opus(+0.1241), Sonnet(+0.1250), GPT-5.5(+0.1252)에서 거의 같았다. 따라서
“높은 엔트로피가 감독 이득을 만든다”는 단순 설명은 현재 기술통계와 맞지
않는다.

## 4. 제한된 감독자의 규범적 프레임

| | 문헌 | 우리 논문에서의 역할 |
|---|---|---|
| ★ | Lieder & Griffiths (2020). *Resource-rational analysis.* Behav. Brain Sci. 43:e1 | 하드 개입 예산 아래의 휴리스틱을 이상 관측자의 저비용 근사로 위치시킨다. 단, 계산/개입 비용함수 없이 “최적”이라고 주장하지 않는다. |

상세한 신규성 대조, 논문용 문장, 검증 상태는 `BAYESIAN_LIT_MAP.md`, 확인된
서지정보는 `REFERENCES.bib`를 따른다. 이 문헌 보강은 Study 2의 동결 설계나
확증 분석을 변경하지 않는다.
