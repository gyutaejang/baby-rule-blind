# Bayesian Reframing — Literature & Concept Map
# 베이지안 재구성 — 문헌·개념 지도

**Purpose / 목적**: build the theoretical scaffolding to reframe the
outcome-feedback supervisor as an approximation to a **Bayesian ideal
observer under rule-blindness**, and to seat a future *RuleBlind-Bayes*
condition (Study 3 direction) in the right literatures across psychology,
cognitive science, computational neuroscience, RL, and LLM research.

무기억 LLM 출력에 대한 outcome-feedback 감독자를 **규칙 무관측(rule-blind)
조건에서의 베이지안 ideal observer의 근사**로 재구성하고, 향후
*RuleBlind-Bayes* 조건(Study 3 방향)을 심리·인지과학·계산신경과학·RL·LLM
문헌에 정확히 안착시키기 위한 이론 골격.

> **Status / 상태**: reading map only. NOT a design change. Study 2 stays
> frozen (see `ANALYSIS_PLAN.md` §10, `DEVIATIONS.md`). Anything
> confirmatory needs a pre-registered amendment BEFORE first analysis
> contact (see `[[followup-queue-idea]]`).
> 읽기 지도일 뿐 설계 변경이 아니다. Study 2는 동결 유지. 확증적 사용은
> 최초 분석 접촉 전에 사전 등록 개정이 필요하다.
> 2026-07-16에 검증한 서지정보는 `REFERENCES.bib`에도 모았다.

> **Citation convention / 인용 규약**: entries marked **[canonical]** are
> ones I'm confident of author+year; **[verify]** means locate and confirm
> the exact reference before putting it in the manuscript. Advanced /
> mathematical-statistics threads are marked **[→ discuss w/ Claude]** and
> deliberately left as stubs.
> **[canonical]** = 저자·연도 확신, **[verify]** = 원고 삽입 전 재확인
> 필요, **[→ discuss w/ Claude]** = 수리통계 상의 대상(의도적 미완).

---

## 0. The one-paragraph bridge / 한 문단 요약

The task is a hidden-state inference problem. The rewarded dimension is a
latent variable over `{color, shape, number}`; rule shifts are transitions
of that latent state (a change-point process with some hazard rate); the
only observation available to a rule-blind supervisor is the post-freeze
binary outcome `correct`. This is **exactly a hidden Markov model / a
discrete POMDP with a change-point transition kernel**, and the optimal
rule-blind policy is the posterior over the latent dimension updated by the
forward algorithm. The current `rule_blind_full.py` — belief tracking
(`values`, `belief_confirm_streak`), change detection (`error_streak_to_open`
+ veto window), and rescue — is a hand-built approximation of that posterior
update. Naming the exact ideal observer it approximates is the theoretical
contribution.

이 과제는 은닉 상태 추론 문제다. 보상 차원은 `{color, shape, number}` 위의
잠재변수이고, 규칙 전환은 그 잠재상태의 전이(어떤 hazard rate를 가진
change-point 과정)이며, rule-blind 감독자가 얻는 관측은 동결 이후의 이진
정오뿐이다. 이는 **change-point 전이 커널을 가진 HMM / 이산 POMDP** 그
자체이고, 최적 rule-blind 정책은 forward 알고리즘으로 갱신되는 잠재 차원
사후분포다. 현재 컨트롤러의 신뢰 추적·변화 감지·rescue는 그 사후 갱신의
수제 근사다. 그것이 근사하는 이상 관측자를 정확히 명명하는 것이 이론적
기여다.

---

## Prior-art / novelty check (2026-07-16 web scan) / 선행연구·신규성 점검

Verdict / 판정: **no located paper takes the specific contribution.** This is
a search-bounded statement, not proof of absolute priority. Close neighbors
exist on two separate axes (LLMs-on-WCST, and Bayesian-models-of-WCST), but
the papers located in this pass do not combine them the way this study does — a **rule-blind
outcome-feedback supervisor over a *memoryless* LLM stream, with strict
information isolation and a hard intervention budget**. Every LLM-WCST paper
located tests the LLM *directly*; none puts a budgeted supervisor on top of a
feedback-free stream.

두 축(LLM-WCST, WCST의 베이지안 모델)에 인접 연구가 있으나, **무기억 LLM
스트림 위에 정보 격리·하드 예산을 건 rule-blind outcome-feedback 감독자**를
얹는 구성은 없다. 발견된 LLM-WCST 논문은 전부 LLM에게 매 trial in-context
피드백을 직접 주며, 예산 감독자를 얹지 않는다.

**Neighbor A — LLMs tested directly on WCST / set-shifting**:

- **[canonical]** de Langis, Park, Hu, Le, Schramm, Mensink, Elfenbein,
  Kang (2026), *Strong Memory, Weak Control: An Empirical Study of
  Executive Functioning in LLMs*, EACL 2026, pp. 5971–5986, DOI
  10.18653/v1/2026.eacl-long.281 (earlier arXiv 2504.02789). LLMs on WCST,
  **multi-turn in-context feedback**, **measures
  perseverative errors**, finds LLMs fail set-shifting (below human, "failure
  to maintain set", perseverative > non-perseverative). No supervisor, no
  budget, no Bayesian observer. **This is our nearest neighbor and a
  double-edged one**: (1) it uses the word *perseveration* for
  feedback-carrying LLMs — cite it and draw the boundary (our memoryless
  design deliberately says `prev_rule_error`, not perseveration, plan §1/§13);
  (2) its "LLMs fail WCST" result *motivates* a supervisor.
- **[canonical]** Kennedy & Nowak (2024), *Cognitive Flexibility of Large
  Language Models*, ICML Workshop on LLMs and Cognition. Tests WCST and the
  Letter-Number Test; some models fail to switch within one context despite
  succeeding when the tasks are placed in separate contexts. This directly
  motivates separating context-carried adaptation from the external
  supervisor used here.
- **[canonical]** Li, Zhang, Holme, Hu, Wang (2025), *Large Language Models
  are Near-Optimal Decision-Makers with a Non-Human Learning Behavior*,
  arXiv 2506.16163. Uses the Iowa Gambling Task, Cambridge Gambling Task,
  and **WCST** for uncertainty, risk, and set-shifting, respectively;
  benchmarked against 360 human participants. LLMs are reported as
  near-optimal but with a **non-human underlying process**. Overlaps our
  "compare to an optimal observer" instinct — but on the LLM directly, not
  on a rule-blind supervisor.
- **[canonical]** Hao, Alexandre, Yu (2025), *Visual Large Language Models
  Exhibit Human-Level Cognitive Flexibility in the Wisconsin Card Sorting
  Test*, arXiv 2505.22112. Visual LLMs reach human-level set-shifting under
  chain-of-thought, but performance depends strongly on input modality and
  prompting strategy. Direct testing.
- **[canonical]** Goto, Idei, Shiozuka, Ogata (2025), *Performance of Large
  Language Models and Analysis of Responses in the Wisconsin Card Sorting
  Task*, IEEE ICDL 2025, DOI 10.1109/ICDL63968.2025.11204408. Reports
  model-dependent rule/response mismatches and differences in combining
  bottom-up card information with top-down rule reasoning. Direct testing.
- **[preprint]** Haznitrama, Ardi, Oh (2026), *A Neuropsychologically
  Grounded Evaluation of LLM Cognitive Abilities*, arXiv 2603.02540.
  NeuroCognition evaluates 156 models on Raven's matrices, spatial working
  memory, and WCST, and argues these probes measure abilities not reducible
  to a single general benchmark factor. Treat as current adjacent work, not
  settled evidence.

> **Live contradiction to exploit / 이용할 만한 상충**: 2504.02789 says LLMs
> *fail* WCST; 2506.16163 / 2505.22112 say *near-optimal / human-level*. The
> split tracks task setup (feedback framing, multi-turn length). Our design
> **sidesteps the debate**: memoryless LLM makes no learning claim; the
> question is whether an outcome-feedback *supervisor* can move the frozen
> stream on the accuracy vs prev-rule-error frontier. Position the paper in
> exactly this gap.

**Neighbor B — Bayesian / RL models of WCST (human, no LLM)**:

- **[canonical]** D'Alessandro, Radev, Voss, Lombardi (2020), *A Bayesian
  brain model of adaptive behavior: an application to the WCST*, PeerJ
  10316. Belief-updating over {color, shape, number} via Bayes' rule per
  feedback, with **flexibility λ** (disengagement on negative feedback) and
  **information-loss δ**, plus Bayesian surprise / Shannon surprise /
  entropy. **This resolves the [verify] Bayesian-WCST slot in §A** and is
  the closest existing formal Bayesian-WCST observer — but it models *human*
  adaptive behavior and is belief-updating, not explicitly framed as a
  change-point / HMM ideal observer. Our RuleBlind-Bayes = take this class
  of observer, run it **rule-blind as a supervisor over memoryless LLM
  output** — an unoccupied combination.
- **[canonical]** Steinke, Lange, Kopp (2020), *Parallel model-based and
  model-free reinforcement learning for card sorting performance*,
  Scientific Reports 10:15464, DOI 10.1038/s41598-020-72407-7. In 375
  participants, parallel category-level model-based and response-level
  model-free learning predicted performance better for most participants
  than purely model-based or attentional-updating comparators. This is a
  strong RL comparison class, not a Bayesian change-point observer.

### D'Alessandro et al. (2020) vs our change-point / HMM frame — precise diff

Read from the model equations (PMC7713598). The upshot: **their model is a
performance-contingent, parametric-approximate Bayesian observer of a
*human*; ours is (or would be) an exogenous-change-point *exact* observer
run rule-blind over a memoryless LLM.** The change-point framing is in fact
*more* natural for our design than for classic WCST.

| Dimension | D'Alessandro et al. (2020) | Our design / RuleBlind-Bayes |
|---|---|---|
| Rule-change trigger | **Endogenous**: rule flips after 10 consecutive correct (performance-contingent, classic WCST) | **Exogenous**: schedule-driven blocks of 4–8 trials (`generate_schedules.py`), flips regardless of performance |
| Transition model | Γ(t) = agent's internal belief about stability; **no explicit environmental hazard** | explicit **hazard rate** implied by the block-length distribution; a genuine change-point/HMM transition kernel |
| Belief update | **parametric-approximate**: activation ωₜ = fₜ ωₜ₋₁^δ mₜ + λ(1−fₜ) ωₜ₋₁^δ(1−mₜ) ωₜ₋₁, with flexibility λ & info-loss δ, then Bayes | the **exact forward-algorithm** posterior is the ideal observer; the heuristic controller is the approximation to it |
| Change detection | **implicit** — entropy rises when a converged belief is violated | **explicit** run-length / change-point posterior (Adams–MacKay) = the veto window done exactly |
| Action selection | **samples** from the predictive belief p(sₜ\|x₀:ₜ₋₁) — i.e. essentially **Thompson sampling** | `_best_alternative` = value-argmax today; Thompson sampling is the principled upgrade — **D'Alessandro corroborates this choice** |
| Subject modeled | **human** participant | **memoryless LLM** stream + an external supervisor |
| Feedback to modeled agent | **full** feedback every trial | supervisor sees **post-freeze binary outcome only**; the LLM sees none |

**Three things this diff buys the paper**:

1. **The exogenous-change advantage.** In classic WCST the rule change is
   *confounded with the participant's own success* (it only fires after 10
   correct). Our schedule-driven blocks change the rule **independently of
   behavior**, so the change-point / hazard-rate observer is cleanly
   identifiable — a methodological point *in our favor* over the
   human-WCST modeling tradition. Say this explicitly.
   고전 WCST의 규칙 전환은 참가자 성공에 종속(10연속 정답 후 발화)되지만,
   우리 일정은 행동과 **독립적으로** 규칙을 바꾸므로 change-point/hazard
   관측자가 깨끗하게 식별된다 — 인간 WCST 모델링 전통 대비 우리 쪽 이점.
2. **Even the existing "Bayesian" WCST model is an approximation** (λ, δ
   parametric activation, not exact Bayes). So the *exact change-point ideal
   observer* is genuinely unoccupied — that is the object RuleBlind-Bayes
   should instantiate, and the ladder heuristic → D'Alessandro-style
   approximate → exact observer is a ready-made model-comparison ablation
   (§G).
   기존 "베이지안" WCST 모델조차 근사(λ, δ)다. **정확한 change-point 이상
   관측자**는 비어 있으며, 그것이 RuleBlind-Bayes가 구현할 대상이다.
3. **Thompson sampling is not exotic here.** The canonical Bayesian-WCST
   model already selects actions by sampling from the posterior, so
   replacing `_best_alternative`'s argmax with posterior sampling is
   well-precedented, not a novelty we must defend from scratch.
   포스터리어 샘플링(Thompson)은 이 맥락에서 이미 전례가 있다.

**Novelty statement to reuse in the paper / 논문에 재사용할 신규성 문장**:
existing work either (i) tests LLMs *inside* WCST with feedback, or (ii)
builds Bayesian/RL observers of *human* WCST. In the literature located by
our 2026-07-16 search, no study places a **rule-blind, budget-limited
outcome-feedback supervisor** on a **memoryless** LLM stream under strict
information isolation, or (Study 3) names the **Bayesian ideal observer it
approximates** as an *inference ceiling* distinct from the `oracle/`
*information ceiling*. Use "to our knowledge" in the manuscript unless a
systematic-review protocol is added.

---

## A. WCST, set-shifting, cognitive control / WCST·전환·인지통제

Where it attaches: framing §1, terminology guardrails, the "supervisor vs
player" distinction. **Guardrail**: the plan forbids a cognitive-
perseveration claim for a *memoryless* LLM (`prev_rule_error`, not
"perseveration"). Use this literature for the *task* and the *supervisor*
analogy, not to attribute cognition to the model.

- **[canonical]** Grant & Berg (1948) — the original Wisconsin Card Sorting
  Test. The task ancestor.
- **[canonical]** Milner (1963); Nelson (1976) — WCST and frontal-lobe
  function; perseverative-error scoring (the human construct we are careful
  NOT to claim for the LLM).
- **[canonical]** Dehaene & Changeux (1991), *The Wisconsin Card Sorting
  Test: theoretical analysis and modeling in a neuronal network* — the
  canonical computational model of WCST; direct precedent for modeling the
  task mechanistically.
- **[canonical]** Miller & Cohen (2001), *An integrative theory of
  prefrontal cortex function* — top-down rule/task-set control. The
  "supervisor" metaphor's neuroscientific anchor.
- **[canonical]** Bishara, Kruschke, Stout, Bechara, McCabe, Busemeyer
  (2010), *Sequential Learning Models for the Wisconsin Card Sort Task:
  Assessing Processes in Substance Dependent Individuals*, J. Math. Psych.
  54(1):5–13, DOI 10.1016/j.jmp.2008.10.002 — sequential /
  attentional-learning models fit to WCST performance. Closest existing
  "trial-by-trial latent-attention" formal model; a natural comparison
  class for the Bayesian observer.
- **[canonical]** Steinke, Lange, Kopp (2020), Scientific Reports 10:15464
  — parallel model-based and model-free RL at category and response levels;
  a direct recent computational-WCST comparison class.
- **[canonical]** Gläscher, Daw, Dayan, O'Doherty (2010) — model-based vs
  model-free learning signals; supports framing the supervisor as
  model-based inference over task structure.

## B. Bayesian learning in changing / volatile environments / 변화·변동 환경의 베이지안 학습

This is the theoretical core — the ideal observer the controller
approximates. Attaches to: `values`/belief update, the veto window, hazard
rate, and any RuleBlind-Bayes formalization.

- **[canonical]** Adams & MacKay (2007), *Bayesian Online Changepoint
  Detection* (arXiv) — THE reference for online "did the regime just
  change?" inference. The principled form of the veto window /
  `error_streak_to_open`. Run-length posterior = the veto window done
  exactly.
- **[canonical]** Behrens, Woolrich, Walton, Rushworth (2007), *Learning
  the value of information in an uncertain world*, Nat. Neurosci. —
  hierarchical estimation of **volatility** (learning the hazard rate
  itself). Motivates a two-parameter (hazard, obs-noise) model and a
  volatility-learning extension.
- **[canonical]** Yu & Dayan (2005), *Uncertainty, neuromodulation, and
  attention*, Neuron — **expected vs unexpected uncertainty**. Maps cleanly
  onto "noise within a rule" vs "a rule shift"; a vocabulary for the two
  error types the controller must distinguish.
- **[canonical]** Nassar, Wilson, Heasly, Gold (2010), J. Neurosci. — an
  *approximately Bayesian* delta-rule with an adaptive learning rate for
  change-point environments. This is the bridge between the heuristic
  (`value_gain`/`value_loss` fixed step) and the ideal observer: a
  reduced/approximate observer with adaptive step size.
- **[canonical]** Courville, Daw, Touretzky (2006), *Bayesian theories of
  conditioning in a changing world*, TICS — associative learning as
  inference under structural change. Good conceptual framing prose.
- **[canonical]** Wilson, Nassar, Gold (2013), *A mixture of delta-rules
  approximation to Bayesian inference in change-point problems*, PLoS
  Comput. Biol. — explicit "how many delta-rules approximate the exact
  Bayesian observer" result. Directly justifies calling the heuristic an
  approximation. **[→ discuss w/ Claude: this is the formal approximation
  bound to lean on]**
- **[verify]** Gallistel and colleagues — evidence humans/animals do
  step-like change detection rather than gradual updating; useful for the
  "is the veto window psychologically real" discussion.

## C. Reinforcement learning & exploration / RL·탐색

Attaches to: `value_gain`/`value_loss` (Rescorla–Wagner/TD form),
`_best_alternative` (the exploration policy), and the rescue path.

- **[canonical]** Rescorla & Wagner (1972) — prediction-error learning; the
  fixed-step value update is a Rescorla–Wagner rule. Name it as such.
- **[canonical]** Sutton & Barto, *Reinforcement Learning: An Introduction*
  (2nd ed., 2018) — TD learning, non-stationarity, bandits. General anchor.
- **[canonical]** Daw, O'Doherty, Dayan, Seymour, Dolan (2006), *Cortical
  substrates for exploratory decisions in humans*, Nature —
  exploration/exploitation trade-off in humans; frames `_best_alternative`
  as an exploration policy rather than mere argmax.
- **[canonical]** Thompson (1933); Russo, Van Roy, Kazerouni, Osband, Wen
  (2018), *A Tutorial on Thompson Sampling* — posterior sampling as the
  principled replacement for the value-argmax remap. RuleBlind-Bayes could
  sample the alternative from the posterior instead of taking the max.
- **[canonical]** Collins & Frank (2013), *Cognitive control over learning:
  creating, clustering, and generalizing task-set structure*, Psych.
  Review — hierarchical RL over **task-sets**. The formal notion of a
  latent "rule/task-set" that the agent infers and switches between —
  precisely our latent dimension.
- **[canonical]** Gershman (2015), *A unifying probabilistic view of
  associative learning*, PLoS Comput. Biol. — ties RL and Bayesian
  inference; useful for the "heuristic ≈ approximate Bayes" argument.

## D. Rational analysis / Bayesian cognition foundations / 합리적 분석·베이지안 인지 기초

Attaches to: the meta-argument that "ideal observer under an information
constraint" is the right normative yardstick — parallel to how `oracle/`
is the information ceiling and Bayes is the *inference* ceiling.

- **[canonical]** Anderson (1990), *The Adaptive Character of Thought* —
  rational analysis: derive behavior from the optimal solution to the
  problem the environment poses. The methodological template.
- **[canonical]** Oaksford & Chater (2007), *Bayesian Rationality* —
  rational analysis applied broadly.
- **[canonical]** Griffiths, Kemp, Tenenbaum — Bayesian models of cognition
  (handbook chapter, ~2008); Tenenbaum, Kemp, Griffiths, Goodman (2011),
  *How to grow a mind*, Science — structured probabilistic inference in
  cognition.
- **[canonical]** Lieder & Griffiths (2020), *Resource-rational analysis:
  Understanding human cognition as the optimal use of limited computational
  resources*, Behavioral and Brain Sciences 43:e1, DOI
  10.1017/S0140525X1900061X. The most defensible frame for
  "the heuristic supervisor is a bounded approximation to the ideal
  observer." Guardrail: resource-rationality is a modeling program, not
  evidence that this particular heuristic is optimal. That stronger claim
  would require an explicit computation/intervention cost function and a
  comparison against the resulting optimum.

## E. LLMs as (implicit) Bayesian in-context learners / LLM = (암묵적) 베이지안 in-context 학습자

Attaches to: the LLM half of the system, and the *reason the Bayesian frame
is timely for an LLM venue*. **Caveat to preserve**: our LLM is
**memoryless / single-turn / no feedback** (§1). So in-context Bayesian
learning is NOT what the raw stream is doing here — it is the frame for a
*future online condition* (Study 3 cue variant) and for positioning. Be
explicit about this boundary or a reviewer will catch it.

- **[canonical]** Xie, Raghunathan, Liang, Ma (2021/2022), *An Explanation
  of In-Context Learning as Implicit Bayesian Inference* — THE paper
  linking ICL to Bayesian posterior inference over a latent concept.
  Central citation for the bridge.
- **[canonical]** Brown et al. (2020), GPT-3 — in-context learning as an
  emergent capability (background).
- **[canonical]** Binz & Schulz (2023), *Using cognitive psychology to
  understand GPT-3*, PNAS — machine-psychology methodology; testing LLMs
  with cognitive-science paradigms. Methodological precedent for our whole
  enterprise.
- **[canonical]** Ortega et al. (2019, DeepMind), *Meta-learning of
  sequential strategies*; Mikulik et al. (2020), *Meta-trained agents
  implement Bayes-optimal agents* — meta-learned sequence models converge
  to Bayes-optimal predictors. Direct theoretical warrant for "a
  transformer can be a Bayesian observer". **[verify exact titles]**
- **[canonical]** Schubert, Jagadish, Binz, Schulz (2024), *In-Context
  Learning Agents Are Asymmetric Belief Updaters*, ICML 2024, PMLR
  235:43928–43946. Across three instrumental-learning tasks, LLMs update more
  after better-than-expected than worse-than-expected outcomes; the pattern
  reverses for counterfactual feedback and disappears when agency framing is
  removed. This is a direct citation for a **future online-feedback
  condition**, not an explanation of the current memoryless RawLLM stream.
- **[verify]** Coda-Forno, Binz, Schulz et al. (2023–2024) — LLMs on
  multi-armed bandits / meta-in-context learning; exploration behavior of
  LLM agents.
- **[verify]** Akyürek et al. (2022) / von Oswald et al. (2023) — ICL as
  implicit gradient descent / learning-algorithm-in-weights. The
  *mechanistic* alternative to the Bayesian reading; cite for balance so
  the Bayesian frame is presented as one of two live interpretations.
- **[verify]** Hagendorff (2023), *Machine Psychology* — umbrella framing
  for LLM-as-subject studies.
- **[canonical]** Sclar, Choi, Tsvetkov, Suhr (2024), *Quantifying Language
  Models' Sensitivity to Spurious Features in Prompt Design*, ICLR 2024 —
  meaning-preserving prompt-format changes can cause large performance
  spreads, and the ranking of formats transfers only weakly across models.
- **[canonical]** Chatterjee, Renduchintala, Bhatia, Chakraborty (2024),
  *POSIX: A Prompt Sensitivity Index for Large Language Models*, Findings of
  EMNLP 2024, pp. 14550–14565, DOI
  10.18653/v1/2024.findings-emnlp.852 — formalizes sensitivity to
  intent-preserving prompt variants; model size or instruction tuning alone
  does not guarantee lower sensitivity.

### E.1. Output entropy as a model × prompt behavioral phenotype

The observed RawLLM distribution over {color, shape, number} is best called
an **output-choice distribution under the frozen prompt and decoding protocol**.
It is not a direct readout of internal uncertainty or a stable model-intrinsic
cognitive trait. Prompt-sensitivity work and the
modality/prompt effects in Hao et al. make the conditioning explicit:

`observed choice distribution = f(model, prompt, decoding, stimulus set)`.

Study 2 descriptives support a narrower and more interesting statement:

| Model | Raw entropy (mean bits) | Raw accuracy | RuleBlindFull accuracy | Full − Raw |
|---|---:|---:|---:|---:|
| Claude Opus 4.8 | 0.0000 | 0.3327 | 0.4568 | +0.1241 |
| Claude Sonnet 5 | 0.0377 | 0.3306 | 0.4556 | +0.1250 |
| GPT-5.5 | 0.5973 | 0.3306 | 0.4558 | +0.1252 |
| GPT-5.4 mini | 1.0711 | 0.3271 | 0.4432 | +0.1161 |

Thus GPT-5.5 does have a more diverse raw choice distribution than either
Claude model under this protocol, but it does **not** receive a uniquely
larger RuleBlindFull accuracy gain. The near-equal gains for Opus, Sonnet,
and GPT-5.5, plus the high-entropy-but-smaller gain for GPT-5.4 mini, argue
against a simple "more entropy → more supervisory benefit" account. The
external supervisor appears able to create useful switching even when the
base stream is nearly one-dimensional.

**Manuscript-ready cautious sentence**: “Model families expressed markedly
different baseline choice distributions under the frozen elicitation
protocol, yet the rule-blind supervisor produced similar accuracy gains
across the two low-entropy Claude streams and the more diverse GPT-5.5
stream. We therefore interpret entropy as a protocol-conditioned behavioral
descriptor rather than a latent cognitive trait or a monotonic source of
supervisory headroom.”

**Robustness follow-up (exploratory only)**: repeat the RawLLM arm across a
small, preregistered set of meaning-preserving prompt formats and decoding
seeds; report the within-model range and model × prompt interaction, using
FormatSpread/POSIX as design precedents. Do not retroactively alter the
frozen Study 2 prompt.

## F. Control-theoretic framing: POMDP / ideal observer / 제어 관점: POMDP·이상 관측자

Attaches to: the formal statement of the RuleBlind-Bayes condition and the
"inference ceiling vs information ceiling" contrast with `oracle/`.

- **[canonical]** Kaelbling, Littman, Cassandra (1998), *Planning and
  acting in partially observable stochastic domains*, Artif. Intell. — the
  POMDP formalism. The rule-blind supervisor acts on a belief state; this
  is its home formalism.
- **[canonical]** Rabiner (1989), *A tutorial on hidden Markov models* —
  the forward algorithm = the exact belief update for our discrete latent
  with change-point transitions. The concrete math the heuristic
  approximates.
- **[→ discuss w/ Claude]** The two-ceiling picture to formalize:
  `OracleFull` = information ceiling (sees ground truth); **Bayes ideal
  observer** = inference ceiling (rule-blind, optimal use of outcomes);
  heuristic supervisor = bounded approximation; RawLLM = no supervisor.
  Placing the heuristic's realized accuracy on that axis is a clean result
  shape.

---

## G. Statistics & formal modeling — STUBS for us to work through together

수리·고급 통계는 여기서 자리만 잡아둠. 모두 **[→ discuss w/ Claude]**.

- Deriving the exact forward-algorithm posterior for the 3-dimension,
  block-length-{4–8}, hazard-rate change-point kernel actually used by the
  Study 2 schedules (`scripts/generate_schedules.py`). Closed form + the
  hazard implied by block lengths.
- Model comparison: heuristic controller vs Bayes observer vs WSLS vs
  reduced/approximate observers (Wilson–Nassar–Gold mixture-of-delta-rules)
  as **nested approximations** — a principled ablation ladder, not ad hoc.
- Fitting hazard rate + observation noise to the *heuristic's* behavior
  (i.e., "what Bayesian observer is `rule_blind_full.py` closest to?") —
  parameter recovery, identifiability.
- Whether/how any Bayesian result could be confirmatory vs exploratory
  given the freeze: replay-side (zero API cost) on the SAME confirmatory
  streams needs a pre-registered amendment BEFORE first contact
  (`[[followup-queue-idea]]`); otherwise strictly exploratory.
- Keeping the existing frozen inferential machinery (paired permutation,
  paired bootstrap CI, rank-biserial, Holm) as the comparison layer so the
  Bayesian work bolts onto — not replaces — the locked stats.

---

## H. Concept → study-component map / 개념 → 구성요소 지도

| Controller element (`rule_blind_full.py`) | Bayesian / formal counterpart | Primary literature |
|---|---|---|
| `values` + `value_gain/loss` | posterior over rewarded dimension; Rescorla–Wagner ≈ approx. Bayes | B (Nassar; Wilson), C (Rescorla–Wagner) |
| `belief_confirm_streak` | posterior crossing a decision threshold | B, F (Rabiner) |
| `error_streak_to_open` + `veto_window` | change-point / run-length posterior spike | B (Adams & MacKay) |
| hazard of rule shift (implicit) | transition kernel; volatility to be learned | B (Behrens) |
| `_best_alternative` (value argmax) | Thompson sampling from the posterior | C (Russo et al.) |
| rescue / `_unresolved_failures` | low-posterior dimension still proposed by a blind actor | B, F |
| `OracleFull` | information ceiling | F |
| **(new) RuleBlind-Bayes** | inference ceiling = forward-algorithm observer | F (Kaelbling; Rabiner) |
| RawLLM stream (memoryless) | fixed output prior; NOT in-context Bayes here | E (with the memoryless caveat) |
| RawLLM `choice_entropy` | protocol-conditioned output-choice phenotype; NOT posterior entropy | E.1 (Sclar; Chatterjee; Hao) |

---

## I. Framing cautions / 프레이밍 주의

1. **Memoryless caveat is load-bearing.** The Bayesian-ICL literature (E)
   describes an LLM *learning in context*; our raw LLM does not (single-turn,
   no feedback). The Bayesian observer lives in the **supervisor**, not the
   LLM. State this explicitly; it is the most likely reviewer objection.
   무기억 단서가 핵심. 베이지안 관측자는 감독자에 있지 LLM에 있지 않다.
2. **No cognitive-perseveration claim** (plan §13). WCST literature (A) is
   for task + supervisor analogy, not for attributing cognition to the model.
3. **Two live interpretations of ICL** (Bayesian vs implicit-gradient-
   descent, E). Present the Bayesian frame as one interpretation, cite the
   mechanistic alternative, don't overclaim.
4. **Freeze discipline.** None of this touches Study 2. Confirmatory use of
   any Bayesian condition requires a pre-registered amendment first
   (`[[followup-queue-idea]]`, `ANALYSIS_PLAN.md` §10).
5. **Every [verify] entry** must have author+year+venue confirmed before it
   enters the manuscript. Do not copy a citation from this map verbatim
   into a submission without checking it.
6. **Prompt conditioning is load-bearing.** Model differences in entropy or
   single-dimension preference are properties of the frozen evaluation
   protocol. Generalizing them to the model family requires prompt/decoding
   robustness evidence.

---

## J. Suggested next actions / 다음 단계 제안

- Remaining **[verify]** entries are lower-priority balance citations
  (Gallistel; Coda-Forno; mechanistic ICL; Hagendorff). The high-value
  resource-rationality, LLM belief-updating, prompt-sensitivity, and recent
  computational-WCST slots were resolved in the 2026-07-16 pass.
- Draft the RuleBlind-Bayes formal spec (Section G item 1) — do this WITH
  Claude for the math, replay-side, zero API cost.
- Decide confirmatory vs exploratory status and, if confirmatory, write the
  pre-registered amendment before any analysis contact.
