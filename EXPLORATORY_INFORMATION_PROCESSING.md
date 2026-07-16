# Study 2 탐색 분석: 출력 엔트로피, 표적 민감성, 전환 적응

> 이 문서는 완료된 Study 2 replay를 사후적으로 다시 읽는 **탐색 분석**이다.
> 동결된 확증 분석, 가설, 검정 결과는 변경하지 않는다.

## 기술 요약

가장 강한 결론은 **출력 엔트로피와 과제 적응 능력은 같은 변수가 아니라는 것**이다.
RawLLM의 평균 정확도는 네 모델 모두 거의 우연 수준(0.3271–0.3327)이었지만,
반복별 선택 엔트로피는 0.0000–1.0711 bits로 크게 달랐다. 더 직접적인 대조인
TrajectoryOnly는 평균 엔트로피를 0.4265에서 0.9277 bits로 높였지만 정확도는
0.3302에서 0.3275로 개선되지 않았고, 숨은 표적과 선택의 상호정보량도 사실상
0이었다. 따라서 선택 다양성 자체는 유능성이나 표적 추적의 증거가 아니다.

RuleBlindFull의 핵심 효과는 전환을 미리 알아맞히는 능력이 아니라 **오류 결과를
받은 뒤 선택분포를 재배치하는 지연된 적응**이었다. 실제 전환 trial 정확도는
0.2632–0.3086으로 낮았지만, 전환 후 trial 2–3 정확도는 0.4652–0.5598로 올라
모델별 +0.2020–+0.2610의 초기 회복을 보였다. 이 조건의 정확도 이득은 Claude
Opus +0.1241, Claude Sonnet +0.1250, GPT-5.5 +0.1252로 거의 같았고,
GPT-5.4 mini는 +0.1160이었다. **GPT-5.5가 RuleBlindFull에서 특별히 더 큰
이득을 본 것은 아니다.**

반면 개입 예산을 제거한 WSLSUnlimited에서는 원래 선택 레퍼토리가 넓은 모델이
더 큰 이득을 얻었다. 정확도는 GPT-5.4 mini 0.7216, GPT-5.5 0.6776,
Sonnet 0.6214, Opus 0.6169 순이었다. 다만 평균 개입률이 0.4907이므로 이는
희소 감독기 비교가 아니라, **개입 용량을 크게 늘렸을 때의 정책 상호작용**으로
읽어야 한다.

후속 효율 분석에서도 같은 분리가 확인됐다. TrajectoryOnly는 개입당 엔트로피
증가가 가장 컸지만 추가 정답은 평균적으로 음수였고, RuleBlindFull은 동일한
개입률의 YokedRandom보다 개입당 추가 정답과 표적 MI가 높았다. 첫 오류 이후
Kaplan–Meier 회복분석에서는 RuleBlindFull의 2-trial 내 회복확률이
0.4485–0.6622, WSLSBudgeted는 0.5887–0.7046이었다.

## 주요 결과

### 1. Raw 엔트로피는 모델별 선택 레퍼토리를 구분하지만 정확도를 구분하지 않는다

`choice_entropy_bits`는 각 repetition의 세 선택지 분포 엔트로피를 구한 뒤
130회 평균한 값이다. `effective_choice_count = 2^H`는 같은 엔트로피를 갖는
균등 선택지 수로 환산한 기술통계다.

| Model | Raw 정확도 | Raw H (bits) | 유효 선택지 수 | 반복별 최대 선택 비중 | RuleBlindFull 정확도 이득 |
|---|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | 0.3327 | 0.0000 | 1.000 | 1.000 | +0.1241 |
| Claude Sonnet 5 | 0.3306 | 0.0377 | 1.026 | 0.994 | +0.1250 |
| GPT-5.5 | 0.3306 | 0.5973 | 1.513 | 0.868 | +0.1252 |
| GPT-5.4 mini | 0.3271 | 1.0711 | 2.101 | 0.574 | +0.1160 |

GPT-5.5는 Claude보다 분명히 넓은 Raw 선택분포를 가졌지만, 제한된
RuleBlindFull 예산에서 추가 정확도 이득은 거의 동일했다. 반복 내 Raw 엔트로피와
RuleBlindFull 정확도 이득의 상관도 작았다: Sonnet `r=0.048`, GPT-5.5
`r=0.093`, GPT-5.4 mini `r=-0.050`. Opus는 모든 repetition의 Raw 엔트로피가
0이어서 상관을 정의할 수 없다.

이 결과는 두 종류의 “여유”를 분리한다.

- **분포 여유:** 감독기가 기존의 단일 차원 편향을 얼마나 다양하게 바꿀 수 있는가.
- **정확도 여유:** 그 변화가 실제 숨은 표적 적중으로 얼마나 전환되는가.

Claude 계열은 분포 여유가 매우 컸지만, GPT-5.5와 정확도 이득은 같았다.
엔트로피 증가는 감독기의 작동 흔적일 수 있으나 그 자체가 이득은 아니다.

### 2. 표적 민감성은 단일 수치보다 표적별 비대칭과 함께 봐야 한다

표적 민감성은 최종 선택과 숨은 보상 차원 사이의 상호정보량
`I(final_choice; hidden_rule)`로 계산하고, 유한 표본의 양의 편향을 1차
보정했다. 이는 사후적 연관 지표이며 내부 표상이나 인과적 지식을 뜻하지 않는다.

| Model | RuleBlindFull 정확도 | 보정 표적 MI (bits) | 표적별 정확도 범위 | color | shape | number |
|---|---:|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | 0.4568 | 0.1203 | 0.8068 | 0.9820 | 0.2143 | 0.1752 |
| Claude Sonnet 5 | 0.4556 | 0.1179 | 0.7920 | 0.9711 | 0.2174 | 0.1791 |
| GPT-5.5 | 0.4558 | 0.0730 | 0.6089 | 0.8497 | 0.2408 | 0.2784 |
| GPT-5.4 mini | 0.4432 | 0.0510 | 0.3400 | 0.5954 | 0.2554 | 0.4822 |

Claude의 높은 MI는 모든 표적을 균형 있게 추적해서라기보다 color 표적에서 거의
완벽하고 다른 표적에서는 낮은 강한 비대칭의 영향을 받는다. GPT-5.4 mini는
MI가 가장 낮지만 표적별 범위는 가장 작고 number 적중률이 높다. 따라서 논문에는
MI와 함께 표적별 정확도 또는 `target_accuracy_range`를 같이 제시해야 한다.

### 3. 전환 민감성은 즉시 전환과 피드백 후 회복으로 분해된다

rule-blind 감독기는 전환 trial의 선택이 확정된 뒤에야 정오 피드백을 받는다.
그러므로 `switch_rate_on_shift`는 순수한 변화탐지 지표가 아니다. 실제로
RuleBlindFull의 전환 trial 선택변경률은 안정 trial보다 0.051–0.122 낮았다.
이전 블록에서 성공하던 선택이 첫 전환 trial에 남아 있기 때문이다.

더 적절한 지표는 오류 뒤 선택변경과 다음 trial들의 회복이다.

| Model | 오류 후−정답 후 선택변경 | 전환 trial 정확도 | 전환 후 trial 2–3 | 초기 회복 |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | +0.2237 | 0.3086 | 0.5598 | +0.2511 |
| Claude Sonnet 5 | +0.2291 | 0.3056 | 0.5507 | +0.2451 |
| GPT-5.5 | +0.2494 | 0.2693 | 0.5303 | +0.2610 |
| GPT-5.4 mini | +0.2410 | 0.2632 | 0.4652 | +0.2020 |

즉 RuleBlindFull의 특징은 “전환 순간 민감성”보다 **오류 조건부 재배치**에
가깝다. WSLSUnlimited에서는 초기 회복이 +0.5431–+0.7209까지 커졌지만,
이는 높은 개입률과 결합된 결과다.

### 4. 조건 비교는 엔트로피 증가와 정보성 증가를 분리한다

아래 값은 모델 네 개의 동일가중 기술 평균이다.

| Condition | 정확도 | H (bits) | 보정 표적 MI | 오류 조건부 변경 차이 | 개입률 | 개입당 순교정 |
|---|---:|---:|---:|---:|---:|---:|
| RawLLM | 0.3302 | 0.4265 | 0.0002 | 0.0052 | 0.0000 | — |
| TrajectoryOnly | 0.3275 | 0.9277 | 0.0003 | 0.0120 | 0.1067 | -0.0186 |
| NoVeto | 0.3715 | 0.8622 | 0.0442 | 0.1932 | 0.1230 | 0.3334 |
| YokedRandom | 0.4208 | 1.1281 | 0.0735 | 0.2194 | 0.2197 | 0.4120 |
| RuleBlindFull | 0.4528 | 1.1107 | 0.0906 | 0.2358 | 0.2197 | 0.5581 |
| WSLSBudgeted | 0.4927 | 1.1041 | 0.1349 | 0.2467 | 0.2390 | 0.6803 |
| WSLSUnlimited | 0.6593 | 1.3769 | 0.3665 | 0.5908 | 0.4907 | 0.6708 |
| OracleFull | 0.5858 | 1.2068 | 0.3586 | 0.0602 | 0.2556 | 1.0000 |

TrajectoryOnly가 가장 명확한 음성 대조다. 출력은 다양해졌지만 표적 정보와
정확도는 늘지 않았다. RuleBlindFull은 YokedRandom과 평균 개입률이 같으면서
정확도, 표적 MI, 개입당 순교정이 모두 높았다. 따라서 중요한 것은 개입량만이
아니라 **오류 이력과 개입 선택의 결합**이다.

OracleFull은 이론적 상한이 아니다. 정해진 window와 rescue 조건에서만 숨은
규칙을 이용하는 oracle-assisted 정책 참조다. 단일 차원 Raw 편향과 oracle의
발동 조건이 상호작용하므로 모델 순위 비교를 일반적 능력 순위로 읽으면 안 된다.

### 5. 가시 카드 속성은 Raw 선택 다양성의 작은 일부만 설명한다

Raw 선택과 카드의 color/shape/number 값 사이의 보정 상호정보량을 따로 계산했다.
GPT-5.5는 속성별 0.0100–0.0147 bits, GPT-5.4 mini는 0.0066–0.0385 bits였다.
따라서 두 GPT 모델의 높은 Raw 엔트로피가 특정 가시 속성 하나에 대한 단순 반응으로
대부분 설명되지는 않는다. 다만 세 카드 속성은 함께 제시되므로 각 MI는 서로
가산할 수 없고, 인과적 주의 배분 지표도 아니다.

Claude Sonnet에는 4,680개 Raw trial 중 24개의 unparsable 출력이 있어
parseable rate가 0.9949였다. 다른 세 모델은 1.0이었다. 엔트로피와 MI는
parseable 선택만 사용하고, 정확도는 전체 trial을 분모로 사용했다.

### 6. 개입 정규화 효율은 “다양성 생성”과 “유용한 교정”을 분리한다

정확도 효율은 같은 repetition의 RawLLM과 비교한 추가 정답 수를 실제 개입
수로 나눴다. 엔트로피와 MI는 가산적 사건 수가 아니므로, repetition별 또는
pooled 분포 이득을 평균 개입 수로 나눈 **정책 수준의 기술적 정규화 비율**이다.
개별 개입 한 번의 인과효과로 해석하지 않는다.

아래는 네 모델의 동일가중 기술 평균이다. OracleFull은 숨은 규칙을 사용하는
정책 참조이므로 효율 경계에서 제외한다.

| Condition | 개입률 | 개입당 추가 정답 | 개입당 H 증가 (bits) | 개입당 표적 MI 증가 (bits) |
|---|---:|---:|---:|---:|
| TrajectoryOnly | 0.1067 | -0.0186 | 0.1278 | -0.0004 |
| NoVeto | 0.1230 | 0.3334 | 0.1019 | 0.0104 |
| YokedRandom | 0.2197 | 0.4120 | 0.0886 | 0.0092 |
| RuleBlindFull | 0.2197 | 0.5581 | 0.0864 | 0.0114 |
| WSLSBudgeted | 0.2390 | 0.6803 | 0.0800 | 0.0158 |
| WSLSUnlimited | 0.4907 | 0.6708 | 0.0574 | 0.0207 |
| OracleFull | 0.2556 | 1.0000 | 0.0810 | 0.0376 |

세 가지 결론이 나온다.

1. **엔트로피를 만드는 효율과 정답을 만드는 효율은 반대일 수 있다.**
   TrajectoryOnly는 가장 큰 개입당 엔트로피 증가를 만들었지만 정확도와 표적
   MI에는 이득이 없었다.
2. **개입 선택성이 개입량보다 중요하다.** RuleBlindFull과 YokedRandom의
   개입률은 모델별로 동일하지만 RuleBlindFull의 개입당 추가 정답은
   0.533–0.569, YokedRandom은 0.332–0.452였다. 엔트로피 효율은 거의 같거나
   RuleBlindFull이 약간 낮아서, 차이는 단순 다양성 증가가 아니라 유용한 방향의
   재배치다.
3. **희소 비-oracle 정확도 경계의 상단은 WSLSBudgeted였다.** 개입당 추가
   정답은 0.658–0.696, 표적 MI 정규화 이득은 0.0117–0.0189 bits였다.
   WSLSUnlimited는 개입률을 두 배가량 높였지만 개입당 추가 정답은
   0.667–0.673으로 유지됐다. 현재 관측 범위에서는 정확도 수익의 뚜렷한
   포화보다, 추가 개입이 표적 정렬을 계속 강화하는 패턴이다. 반면 개입당
   엔트로피 증가는 0.0574 bits로 감소해 선택 레퍼토리 확장에는 한계가 보인다.

25% 이하 개입률의 비-oracle 조건에서 RawLLM, NoVeto, RuleBlindFull,
WSLSBudgeted가 일반적으로 정확도 Pareto 경계를 구성했다. GPT-5.5의
TrajectoryOnly도 점추정상 매우 낮은 비용의 경계점이지만 개입당 추가 정답의
95% bootstrap 구간이 `[-0.0495, 0.0871]`로 0을 포함하므로 강건한 경계점으로
보지 않는다.

### 7. 첫 오류→첫 회복 생존분석은 회복 속도와 오류 진입을 함께 보여준다

각 post-shift block에서 첫 오답이 나온 trial을 시간 0으로 정하고, 이후 첫
정답을 회복 사건으로 정의했다. 블록 종료까지 정답이 없으면 우측 검열했다.
오류가 한 번도 없는 블록은 오류 상태에 진입하지 않았으므로 생존곡선에서
제외하고 `no_error_block_rate`로 별도 보고했다. 전체 표본은 모델×조건별
661개, 총 21,152개 post-shift block이다.

| Condition | 오류 없는 블록 | 2 trial 내 KM 회복 | 4-trial 미회복 RMST | 우측 검열률 |
|---|---:|---:|---:|---:|
| RawLLM | 0.2016 | 0.2046 | 3.4151 | 0.7409 |
| TrajectoryOnly | 0.0185 | 0.3893 | 2.8543 | 0.4569 |
| NoVeto | 0.2001 | 0.3790 | 3.0352 | 0.5161 |
| YokedRandom | 0.1774 | 0.5413 | 2.4515 | 0.2762 |
| RuleBlindFull | 0.1781 | 0.5454 | 2.4749 | 0.3263 |
| WSLSBudgeted | 0.1660 | 0.6321 | 2.3846 | 0.3332 |
| WSLSUnlimited | 0.0893 | 0.9089 | 1.7282 | 0.0866 |
| OracleFull | 0.2228 | 0.9382 | 1.8173 | 0.1972 |

RuleBlindFull의 모델별 2-trial 회복확률은 Opus 0.4485, Sonnet 0.4614,
GPT-5.5 0.6094, GPT-5.4 mini 0.6622였다. 중앙 회복 지연은 각각
4, 3, 2, 2 trials였다. WSLSBudgeted는 네 모델 모두 중앙값 2 trials였고,
WSLSUnlimited는 Opus/Sonnet/GPT-5.5가 2, GPT-5.4 mini가 1 trial이었다.

TrajectoryOnly는 중요한 반례다. Claude Opus에서 RawLLM의 2-trial 조건부
회복은 0이지만 TrajectoryOnly는 0.3051이었다. 그러나 오류가 전혀 없는
블록 비율은 0.3374에서 0.0257로 붕괴했고 전체 정확도도 개선되지 않았다.
즉 **오류 상태에 들어간 뒤 빨리 우연히 정답을 한 번 내는 것**과 **처음부터
안정적으로 맞거나 정답을 유지하는 것**은 다르다.

YokedRandom과 RuleBlindFull의 첫 정답 생존곡선도 평균적으로 매우 비슷했지만,
RuleBlindFull의 전체 정확도와 개입당 추가 정답은 더 높았다. 첫 회복 시점은
정답의 지속성이나 이후 오류 재진입을 측정하지 않으므로 단독 성능지표로 쓰면
안 된다. 논문에서는 전체 정확도, 오류 없는 블록 비율, 생존곡선을 함께 제시하는
것이 적절하다.

우측 검열이 많은 Raw 조건에서는 독립 검열 가정이 완전히 보장되지 않는다.
이를 점검하기 위해 각 horizon의 상태를 실제로 관찰할 수 있었던 episode만으로
complete-case 회복률도 계산했다. 2-trial 값은 조건 평균에서 Kaplan–Meier
추정치와 비-oracle 조건에서 0.0016 이내로 가까웠지만, 이 일치는 검열 가정
자체를 증명하지는 않는다.

## 분석 범위와 지표 정의

- 자료: `results/study2_trials.csv`, 149,760 trial rows.
- 설계: 4 models × 130 repetitions × 8 conditions × 36 trials.
- 표적 결합: `data/ground_truth_study2/rep_XX_ground_truth.csv`.
- 가시 자극 결합: `data/stimuli_study2/rep_XX_prompts.csv`.
- 선택 엔트로피: `H(C) = -Σ p(c) log2 p(c)`, repetition별 계산 후 평균.
- 표적 민감성: `I(C; T)`, 선택 `C`와 숨은 표적 `T`의 pooled 상호정보량.
- 표적 비대칭: 세 표적별 정확도의 최댓값−최솟값.
- 피드백 민감성: `P(change | previous error) - P(change | previous correct)`.
- 초기 전환 회복: 전환 블록 trial 2–3 정확도−전환 trial 정확도.
- 개입 효율: `(corrective overrides - harmful overrides) / interventions`.
- 분포 이동: Raw와 각 조건의 최종 선택분포 사이 Jensen–Shannon divergence.
- 정확도 개입효율: `Σ(correct_condition - correct_raw) / Σ interventions`.
- 엔트로피 개입효율: `Σ(H_condition - H_raw) / Σ interventions`.
- 표적 MI 개입효율: pooled 표적 MI 이득을 repetition당 평균 개입 수로 나눈 값.
- 오류 후 회복 생존시간: 첫 오류 다음 trial부터 첫 정답까지의 지연;
  블록 끝까지 정답이 없으면 우측 검열.
- `RMST_unrecovered(4)`: 오류 뒤 4-trial 범위에서 Kaplan–Meier 미회복
  생존확률의 이산 합. 낮을수록 빠른 회복.

정확도와 기존 `choice_entropy`는 동결된 `results/study2_summary.csv`와
재대조했다. 동결 요약은 repetition별 엔트로피를 소수 넷째 자리로 저장하므로
그 반올림 범위만 허용했다. RuleBlindFull 정확도 이득의 95% bootstrap 구간은
repetition 쌍을 5,000회 재표집해 계산했다.

## 해석상 한계와 강건성

1. 이 분석은 사후적이다. 새 지표의 p-value를 확증 결과처럼 제시하지 않는다.
2. 엔트로피는 관측된 세 선택지 분포의 다양성이지 내부 추론량이 아니다.
3. 표적 MI는 행동과 표적의 연관이며, 숨은 규칙의 내부 표상을 직접 측정하지 않는다.
4. 전환 후 위치별 비교는 블록 길이와 스케줄 분포의 영향을 받을 수 있다.
   그래서 전환이 없는 첫 블록은 전환 profile에서 제외했다.
5. WSLSUnlimited의 높은 성능은 희소 감독기 제약 밖에서 얻은 참고 결과다.
6. 모델명, 프롬프트, 디코딩 설정, replay 정책에 조건화된 결과이며 다른 설정으로
   일반화하려면 새 실행이 필요하다.
7. MI와 엔트로피의 개입 정규화 비율은 분포 수준 기술통계이며 개별 개입의
   가산적·인과적 효과가 아니다.
8. 첫 오류 생존분석은 오류 상태에 진입한 블록에 조건화된다. 오류 없는 블록
   비율과 전체 정확도를 함께 보지 않으면 선택 편향이 생긴다.
9. 블록 종료 검열은 첫 오류 위치와 정책에 의존할 수 있다. Kaplan–Meier와
   horizon별 complete-case 결과를 함께 제공하지만 인과적 hazard 비교는 아니다.

## 논문에 추가하기 좋은 탐색 질문

- **레퍼토리 가용성:** Raw 엔트로피가 아니라 오류 뒤 도달 가능한 대안의 수가
  무제한 감독기 이득을 예측하는가?
- **표적 균형성:** 평균 정확도가 같을 때 표적별 정확도 범위가 이후 전환 회복을
  예측하는가?
- **지속 회복:** 첫 정답 대신 2회 연속 정답 또는 이후 블록 잔여 정확도를
  사건으로 두면 YokedRandom의 일시적 적중과 안정적 회복이 분리되는가?
- **인과적 한계효과:** 특정 개입을 제거한 counterfactual replay를 실행하면
  정책 수준 비율이 아니라 개별 개입의 실제 한계효과를 추정할 수 있는가?
- **경로 의존성:** 같은 개입 횟수라도 어느 오류 연쇄에서 개입했는지가 성과를
  설명하는가?

## 재현 파일

- 분석 코드: `analysis/exploratory_information_processing.py`
- 전체 조건 요약: `results/exploratory_information_processing_summary.csv`
- 표적별 선택분포: `results/exploratory_target_sensitivity.csv`
- 전환 블록 위치별 profile: `results/exploratory_transition_profile.csv`
- 가시 속성 민감성: `results/exploratory_stimulus_sensitivity.csv`
- Raw 엔트로피와 감독기 이득: `results/exploratory_entropy_headroom.csv`
- 개입 정규화 효율과 Pareto 표시:
  `results/exploratory_intervention_efficiency.csv`
- 첫 오류 회복 생존 요약:
  `results/exploratory_recovery_survival_summary.csv`
- Kaplan–Meier 곡선 자료:
  `results/exploratory_recovery_survival_curve.csv`

재실행:

```powershell
python -m analysis.exploratory_information_processing
python -m analysis.exploratory_efficiency_survival
```
