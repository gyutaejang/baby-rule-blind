# Binary Outcome-Feedback Supervision of Memoryless LLM Outputs under a Budgeted Intervention Policy

Anonymous Author

## Highlights

- A small external supervisor makes memoryless LLM outputs adaptive in a WCST task
- One correctness bit per trial raised accuracy on all four held-out models
- Feedback-free trajectory reshaping changed outputs but not accuracy
- Simple win-stay/lose-shift beat an elaborate belief-and-veto supervisor
- Removing the protection stack eliminated the elaborate policy's error reversal

## Abstract

Can the outputs of a memoryless large language model be made adaptive by a small external supervisor that watches only its public choices? We tested this in a Wisconsin Card Sorting Test (WCST)-style task in which a hidden sorting rule changes without announcement and each LLM response is generated without any conversation history. Supervisors received binary outcome feedback — one correctness bit per trial — under a sparse intervention budget of at most nine of 36 trials. Three findings emerged. First, a feedback-free supervisor that only redistributed the model's repetitive output trajectory increased choice diversity but did not improve accuracy: output change alone was not adaptive change. Second, both supervisors with access to the correctness bit improved accuracy on all four held-out model generations, by roughly 12 to 17 percentage points (all Holm-adjusted p < .001). Third, the more elaborate supervisor did not beat the simple one: an information- and budget-matched win-stay/lose-shift policy was more accurate on every model, and the elaborate policy's predicted reduction in previous-rule-aligned errors reversed significantly on two models, so the proposed trade-off received the pre-registered label no transfer. A separately frozen follow-up (Study 2b), evaluated once on newly generated streams, found that removing the elaborate policy's protection mechanisms eliminated the reversal on all four models (all adjusted p < .001), implicating the protection stack rather than outcome tracking. Under the tested policies, improvement required access to correctness feedback, and a simple, auditable policy sufficed to harvest it; all designs and analyses were frozen before data contact.

Keywords: large language models; cognitive flexibility; rule shifting; outcome feedback; external supervision; Wisconsin Card Sorting Task; reproducibility

## 1. Introduction

An agent facing the Wisconsin Card Sorting Test (WCST) must discover which of several rules currently governs reward, using nothing but trial-by-trial correctness feedback, and must abandon that rule when it silently changes (Grant & Berg, 1948). The task has four properties that jointly make it a demanding test of adaptive control: the governing rule is never directly observable; it must be inferred from outcome feedback after each action; it changes during the run; and the previous rule remains available as a plausible — and now wrong — answer. Human work treats errors aligned with the previous rule as one observable consequence of impaired updating, while warning that no single WCST score uniquely identifies a mechanism (Milner, 1963; Kopp et al., 2021; Miles et al., 2021).

This study asks whether a system with none of the usual machinery for adaptation can nevertheless adapt. Each large language model (LLM) response in our design is generated independently, with no conversation history: the model itself cannot remember its last choice, let alone the outcome. Any adaptation must therefore come from outside — from a small external supervisor that observes the public response sequence and, in some conditions, receives a single additional bit after each final action: whether it was correct. The supervisor never sees the hidden rule, the card-to-rule mapping, or the future schedule, and it may intervene on at most nine of 36 trials. LLM behavior on cognitive tasks is sensitive to prompt form, sampling, memory, and parsing (Binz & Schulz, 2023; Sclar et al., 2024; Chatterjee et al., 2024), so we treat the resulting scores as properties of a specified system — model, prompt, parser, supervisor — rather than as measurements of a human-like faculty.

Three questions organize the confirmatory design:

1. Can performance be improved without any outcome information, by reshaping the model's repetitive output trajectory alone?
2. Does binary correctness feedback help, even under a sparse intervention budget?
3. Does an elaborate supervisor — one that accumulates evidence and protects its current hypothesis — outperform a simple policy given exactly the same information and the same budget?

The honest history of the project is part of its answer. The work began with a feedback-free trajectory controller, developed on two archived models and one fixed schedule, whose early results suggested large reductions in a broad "persistence" measure. That development design could not separate trajectory shaping from information supplied by correctness feedback, and its repeated fixed schedule invited overfitting. The present confirmatory study was therefore frozen in advance to put the original account at risk — and it failed: the feedback-free controller changed the output distribution without improving accuracy. What did improve accuracy, consistently and substantially, was access to binary outcome feedback. And within the feedback-using policies, the simple win-stay/lose-shift baseline beat the elaborate belief-and-veto supervisor on accuracy on every model, while the elaborate supervisor's predicted advantage on previous-rule-aligned errors reversed on two models. A separately frozen follow-up (Study 2b) then asked whether that reversal came from outcome-driven hypothesis tracking as such or from the added protection mechanisms: removing the protections eliminated the reversal, implicating the protection stack. This paper is thus not a proposal of a new supervisor; it is a stepwise dissection — with each step frozen before its data existed — of which ingredients of an adaptive LLM system do the work and which do not.

Throughout, rigor is preserved but repositioned. The main text presents each supervisor's purpose, visible information, action rule, expected effect, and observed result in plain language; exact parameters, freeze procedures, and audit machinery appear in the technical subsections, Section 7, and the repository.

## 2. Related Work

### 2.1 Card sorting and adaptive control

The WCST has long been used to study rule discovery, set shifting, and the balance between stability and flexibility (Grant & Berg, 1948; Milner, 1963). Contemporary methodological work emphasizes that reliability and interpretation depend on the scoring rule, task version, and target population (Kopp et al., 2021; Miles et al., 2021). Computational accounts model card sorting as sequential learning rather than as a single latent faculty, including sequential learning models (Bishara et al., 2010), Bayesian belief updating (D'Alessandro et al., 2020), and parallel model-based and model-free reinforcement learning (Steinke et al., 2020). These accounts motivate trial-level analysis but do not imply that the present heuristic supervisor implements a human mechanism.

Classic control tasks are not interchangeable, and this matters for scope. Stroop-type tasks measure conflict resolution under an explicitly stated rule — suppressing a dominant response in favor of an instructed one (Stroop, 1935). AX-CPT-type tasks measure the maintenance of contextual cues and distinguish proactive from reactive control (Braver, 2012). The WCST instead measures the discovery of a changing latent rule from outcome feedback and the decision to retain or abandon a current hypothesis. The present results are therefore evidence about the third process — latent-rule adaptation from binary outcome feedback — not about cognitive control in general (Section 5.3).

### 2.2 LLM behavioral evaluation and prompt sensitivity

LLMs can be probed with cognitive tasks, but the resulting behavior reflects the full evaluation interface: prompt wording, answer constraints, sampling settings, parser rules, and retained context. Prompt-format sensitivity has been quantified directly across model families (Sclar et al., 2024; Chatterjee et al., 2024). Studies of LLM cognitive flexibility and WCST performance similarly show that conclusions depend on model and modality (Kennedy & Nowak, 2024; Hao et al., 2025; Goto et al., 2025), and recent work finds that memory capacity and control performance can dissociate in LLMs (de Langis et al., 2026). We therefore describe observable response policies and refrain from treating them as direct evidence of human-like executive function.

### 2.3 Feedback-based correction of LLM outputs

A growing literature corrects LLM behavior at inference time using feedback expressed in natural language: self-generated critiques (Madaan et al., 2023), verbally stored episodic reflections across attempts (Shinn et al., 2023), and related agentic memory schemes. Intrinsic self-correction without external information, however, has proven unreliable for reasoning tasks (Huang et al., 2024).

A second strand delivers outcome or reward feedback into the model's context and asks whether the model itself can use it. The evidence is cautionary. LLMs fail to explore robustly in multi-armed bandits even with the full interaction history and rewards in the prompt, succeeding only when an external component summarized that history (Krishnamurthy et al., 2024); in-context agents update asymmetrically from positive and negative outcomes (Schubert et al., 2024) and encode rewards with human-like relative-value biases (Hayes et al., 2024); and on the WCST itself, models performed far below human accuracy even when the prompt spelled out a win-stay/lose-shift strategy verbatim (de Langis et al., 2026). The present approach draws the opposite design conclusion from the same signal: the correctness bit never enters the model's context at all. The corrective signal is a single externally supplied bit, the persistent state is a few numbers held outside the model, and the policy that converts signal into intervention is small enough to audit line by line — so knowing the policy and executing the policy are separated by construction. The question is not whether rich verbal feedback can help — it can — but how little information and machinery suffice, and where the processing has to live.

### 2.4 Limited supervision and strong baselines

Inference-time control can alter model outputs without modifying weights. The present supervisor chooses among three categorical actions under a hard intervention budget; the resource-rational perspective is relevant only as a design analogy — performance is evaluated under a fixed supervision allowance — not as an optimality claim (Lieder & Griffiths, 2020). Bayesian change-point models provide a conceptual language for belief revision under changing contingencies: online change-point detection formalizes when accumulating evidence should overturn a current belief (Adams & MacKay, 2007), hierarchical extensions learn the volatility of the environment itself (Behrens et al., 2007), and simple delta-rule updates have been shown to approximate full Bayesian inference closely in change-point environments (Nassar et al., 2010; Wilson, Nassar, & Gold, 2010). These accounts, together with the human set-shifting and inhibition literature (Monsell, 2003; Diamond, 2013), inspired the design of RuleBlindFull's mechanisms (Section 3.5). The claim is one of design lineage only: RuleBlindFull is a frozen heuristic, not an exact posterior computation (cf. D'Alessandro et al., 2020), and no mechanism equivalence or optimality is asserted. Finally, evaluation practice in adjacent fields shows that new policies are easily flattered by weak comparisons and must be tested against strong, information-matched baselines (Henderson et al., 2018). The co-primary design enforces exactly that requirement.

## 3. Method

### 3.1 Architecture and information isolation

For each trial, the generation layer gave the model a public card description and requested one dimension name. No system message or conversation history carried information across trials. The raw text was preserved and parsed by a frozen parser. A controller received only the public trial index and parsed choice; the evaluator, which alone had access to the hidden schedule, scored the controller's final choice. Only after the final choice was fixed did a feedback-aware controller receive the Boolean correctness outcome.

Ground truth was isolated from the controller package and request path: per-repetition public prompts and ground-truth schedules were stored separately, and automated gates verified that controller code contained no ground-truth tokens, that the generation path loaded no schedule files, and that the exact model × repetition × condition grid was complete before statistics ran (details in Section 7).

### 3.2 Task and randomized schedules

Each repetition contained 36 trials. Cards varied on color, shape, and number, and the hidden sorting rule changed across blocks. Study 2 schedules were generated before any API call from master seed 20260715. Block lengths were drawn from 5, 6, or 7 trials, with a frozen partition rule ensuring every realized block was between 4 and 8 trials. The first rule was uniform over the three dimensions; each subsequent rule was sampled uniformly from the other two. Models shared the schedule associated with a repetition index, and every condition replayed the same immutable raw response stream, so all contrasts are within-repetition comparisons of policies applied to identical model behavior.

### 3.3 Conditions overview

**Table 1.** Replay conditions, their information access, and their role in the design.

| Condition | Information and role |
|---|---|
| RawLLM | Parsed model choice without external intervention; baseline. |
| RuleBlindFull | Co-primary belief/veto/rescue supervisor; binary outcome feedback; maximum 9 interventions. |
| WSLSBudgeted | Co-primary win-stay/lose-shift supervisor; the same feedback and maximum 9 interventions. |
| NoVeto | RuleBlindFull ablation with the veto window removed. |
| TrajectoryOnly | Strictly feedback-free version testing whether the response trajectory alone is sufficient. |
| YokedRandom | Uses RuleBlindFull's intervention timing but selects random alternative actions. |
| WSLSUnlimited | Descriptive reference without an intervention budget; not a confirmatory target. |
| OracleFull | Oracle-assisted policy reference with explicit ground-truth access; not a performance ceiling. |

*Note.* Every condition replays the same immutable raw response stream per repetition, so all contrasts are within-repetition comparisons (Section 3.2).

The hard budget for budgeted supervisors was nine interventions, or 25% of trials. The three theory-bearing supervisors are described next in a common format — purpose, visible information, action rule, expected effect, and observed result — so that the design logic can be followed without reconstructing the algorithms; exact parameters follow in Section 3.6, and complete pseudocode with edge rules is in the supplement. (The fourth theory-bearing supervisor, WCDMinimal, belongs to Study 2b and is described in Section 3.10.)

### 3.4 The theory-bearing supervisors, in plain terms

**TrajectoryOnly.** *Purpose:* test whether performance can be improved with no correctness information at all, by adjusting only the repetitive shape of the output trajectory. *Visible information:* the model's past choices and their repetition pattern — never whether any choice was correct. *Action rule:* when one choice has been repeated excessively, redirect toward under-used alternatives. *Expected effect:* breaking fixation might incidentally increase choices that happen to match a new rule. *Observed result:* output diversity increased but accuracy did not (Section 4.3). Mere response change and increased exploration were not sufficient conditions for adaptive control.

**WSLSBudgeted.** *Purpose:* test whether the minimum possible outcome signal — one correctness bit — suffices to improve repetitive performance. *Visible information:* whether the most recent final choice was correct. *Action rule:* if correct, stay with the current dimension; if incorrect, try a different one (the least recently tried alternative), all within the nine-intervention budget. *Expected effect:* while a rule holds, successful choices repeat; when the rule changes, the resulting error is an immediate signal to move. *Observed result:* accuracy improved on every model, and this simple policy was consistently more accurate than the elaborate RuleBlindFull (Sections 4.1–4.2).

**RuleBlindFull.** *Purpose:* test whether a supervisor that accumulates evidence and protects its current hypothesis achieves a better accuracy versus previous-rule-error trade-off than immediate switching. *Visible information:* the same per-action correctness bit; never the hidden rule itself. *Action rule:* maintain a tentative rule hypothesis based on recent outcomes, and regulate when to switch using accumulated errors, a veto condition, a cooldown, and structural restrictions (Section 3.5). *Expected effect:* by not overreacting to a single stray error, it should commit fewer returns to the previous rule. *Observed result:* better than RawLLM but less accurate than WSLSBudgeted on every model; on both Claude models the protective machinery extended, rather than shortened, the life of the outdated rule (Section 4.2).

### 3.5 Protection mechanisms: what each one does, and at what cost

RuleBlindFull's distinguishing machinery consists of four mechanisms, named here with their function rather than only their parameters:

- **Veto window** — after a failure, the supervisor does not immediately abandon the current rule; it waits until failure evidence accumulates, treating a lone error as possibly transient. This is the heuristic counterpart of waiting for the change-point posterior to rise before overturning a belief (Adams & MacKay, 2007).
- **Cooldown** — after a switch, further switches are restricted for a short period, preventing continual oscillation — echoing the stabilization that follows a task switch in human performance (Monsell, 2003).
- **Structural protection** — returning immediately to a recently failed or already well-tested choice is restricted, a guard against perseverative returns analogous to inhibiting a prepotent response (Diamond, 2013).
- **Evidence accumulation** — each dimension's history of success and failure is preserved as a small external state and consulted at the next decision, a delta-rule-style update of the kind shown to approximate Bayesian belief revision (Nassar et al., 2010).

These correspondences are design inspiration, not implementation claims (Section 2.4). And the mechanisms should not be described only by their intended benefits. In environments where feedback is noisy or transient failures are common, they can prevent premature switching. But in an environment like the present one — where feedback is reliable and an error is a strong signal that the rule has changed — the same mechanisms can delay updates that are in fact necessary. Which regime obtains is an empirical question, and Sections 4.2 and 4.6 answer it for this task.

### 3.6 A worked example, then the frozen parameters

Suppose the model's card choices keep being sorted by *color* and keep coming back correct. WSLSBudgeted simply stays with color. When color suddenly returns an error, the outcome signal says the rule has changed, and WSLSBudgeted immediately tries another dimension. RuleBlindFull, facing the same error, may hold color a little longer to check whether the failure was transient, and its veto window and cooldown constrain which alternatives it may propose and when. That patience buys stability in a noisy world; in this WCST environment, where the error was almost always a true rule-change signal, it more often showed up as a cost — slower adaptation and longer retention of the old rule. The two policies differ, in short, in how they interpret a failure signal: WSLS reacts to it at once, RuleBlindFull interrogates it first, and here the interrogation was rarely worth the delay.

For completeness, the frozen RuleBlindFull parameters, selected only on Study 1, were: error streak to open = 1, veto window = 4, cumulative-unresolved rescue threshold = 2, rescue cooldown = 6, belief confirmation streak = 2. WSLSBudgeted retained the most recent correct final dimension, stayed while outcomes remained correct, and shifted to a least-recently-tried alternative after failure, subject to the same budget. Full update equations, tie handling, and exception rules are in the supplement.

### 3.7 Development and confirmatory data

Study 1 comprised 60 archived streams from Claude Sonnet 4.6 and GPT-4o (30 repetitions per model, April 2026) on a shared fixed schedule; it informed controller design, parameter search, and exploratory analyses, so any Study 1 interval or p-value is post-selection and non-confirmatory.

Study 2 was frozen before contact with the confirmatory streams. It included Claude Opus 4.8, Claude Sonnet 5, GPT-5.5 (2026-04-23), and GPT-5.4 mini (2026-03-17), with 130 repetitions per model. Three-repetition engineering pilots were excluded. The final confirmatory grid contained 4 models × 130 repetitions × 8 conditions × 36 trials = 149,760 condition-trial rows.

The answer-format prompt and parser were revised after the engineering pilot because the two Claude models frequently returned deliberative text that the earlier parser could not reliably reduce to one dimension. The parser-v3 rules and the added instruction, "Answer with just the dimension name," were then re-frozen before Study 2. This limits literal comparability to the archived generation but improves measurement validity within the confirmatory study.

### 3.8 Outcomes

The primary accuracy outcome was the proportion of correct final choices per repetition. A previous-rule-aligned error occurred when an incorrect final choice matched the preceding block's rule; the term is deliberately descriptive and replaces the older, broader label "persistence." Old-rule reentry required a previous-rule-aligned error after at least one correct response in the current block.

Safety outcomes distinguished corrective overrides (raw incorrect, final correct) from harmful overrides (raw correct, final incorrect); net correction was their difference. Choice entropy summarized the distribution over the three final dimensions among parseable choices. Recovery latency was the within-block position of the first correct response, censored at observed block length when no correct response occurred. "Productive rate" was removed as an inferential endpoint because later success can occur by chance; its narrow successor, subsequent-success rate, is descriptive only.

### 3.9 Statistical analysis and analysis environment

Analyses were performed separately for each model. Because every condition replayed the same raw stream and schedule, contrasts were paired at the repetition level (n = 130 pairs per model per contrast). Each primary comparison used a two-sided paired permutation test (Ernst, 2004), a paired-bootstrap 95% confidence interval (Efron & Tibshirani, 1993), and a matched-pairs rank-biserial effect size (Kerby, 2014), with Holm correction (Holm, 1979) over the four primary tests within each model.

The four directional primary tests were: RuleBlindFull > RawLLM accuracy; WSLSBudgeted > RawLLM accuracy; WSLSBudgeted > RuleBlindFull accuracy; and RuleBlindFull < WSLSBudgeted previous-rule-aligned errors. A test succeeded only when the Holm-adjusted p-value was below .05 and the observed direction matched the frozen prediction. All four tests had to succeed for the trade-off to replicate on a model. The pre-registered transfer label was broad for at least three successful models, partial for two, and no transfer for one or zero. The previous-rule error test required RawLLM headroom of at least three errors per repetition, which all models satisfied. Non-inferiority of each co-primary supervisor to RawLLM required the paired-bootstrap 95% lower bound of the accuracy difference to exceed −0.02. Equivalence of TrajectoryOnly and RawLLM required the paired-bootstrap 90% confidence interval to fall entirely within ±0.02 — the interval-inclusion form of two one-sided tests (Schuirmann, 1987; Lakens, 2017).

Because the exact implementation determines the numbers, the analysis stack is fixed and fully seeded. All replay, controller, and statistics code uses the Python standard library exclusively — no third-party numerical packages — verified under CPython 3.14; the permutation test is a two-sided sign-flip test of the mean paired difference (10,000 permutations, seed 20260715, add-one smoothing), confidence intervals are percentile bootstrap over 10,000 resamples with an independent seed, and Holm correction is applied to full-precision p-values within each model and pre-declared test family. Identical inputs reproduce identical outputs byte for byte. Tie-handling conventions, the treatment of zero differences, seed derivations, and package pins for stream generation are specified in the supplementary materials.

### 3.10 Parsing and intention-to-treat handling

The parser, frozen with the rest of the design, first searched the text after the last recognized final-answer marker; without a marker, exactly one dimension term was required, and zero or multiple dimensions produced an unparsable result. Unparsable responses were retained and scored incorrect. API failures were retried under a frozen policy and preserved in attempt logs. Study 2 contained no API errors or refusals. There were 24 unparsable public responses among 18,720 generated responses (0.128%), all from Claude Sonnet 5. Because each public stream was replayed across eight conditions, the same unparsable response appears in each condition-specific trial table and must not be counted as eight independent generation failures.

### 3.11 Study 2b: pre-registered minimal-supervisor follow-up

The Study 2 results (Section 4.2) left a question the original design could not answer: when RuleBlindFull increased previous-rule-aligned errors on both Claude models, was the cost produced by outcome-driven hypothesis tracking as such, or by the added protection mechanisms? Study 2b was designed to separate the two. Its hypothesis was explicitly formed after the Study 2 results were locked, so no analysis of the existing streams could confirm it; the follow-up therefore used a two-stage design with its own freeze tag.

**WCDMinimal.** *Purpose:* isolate whether RuleBlindFull's effects came from its core outcome tracking or from its protection stack. *Visible information:* only the per-choice correctness outcomes, accumulated as evidence scores. *Action rule:* keep the current choice while outcomes support it; when it fails, update toward the best-supported alternative — with the rejection window, cooldown, and related protections removed. *Expected effect:* if outcome-based hypothesis tracking itself carries an advantage over simple WSLS, it should survive the removal of the protections; if the protections caused the Claude-model reversal, the reversal should disappear. *Observed result:* under the frozen parameters it behaved identically to WSLSBudgeted on every confirmatory trial, and the reversal disappeared (Section 4.6). The core benefit in this environment is fast, simple outcome-driven updating, not an elaborate hypothesis apparatus.

Technically, WCDMinimal maintained a per-dimension evidence score updated after every attributable outcome (all scores multiplied by a decay factor, then ±1 to the chosen dimension, clipped to ±5), a single active hypothesis adopted at the first correct outcome and steered toward under the same nine-intervention budget, and a switch rule requiring both a minimum error streak and a strict evidence lead of the best alternative. Its three free parameters were selected by a codified rule (minimize pooled previous-rule-aligned errors subject to pooled accuracy at or above the raw baseline) on the archived Study 1 streams only, with the full 48-configuration grid published. The selected configuration lay at the most permissive corner of the grid (decay = 0.5, switch margin = 0.0, wait threshold = 1), meaning the calibration itself deactivated the waiting and margin gates; this boundary selection is disclosed rather than repaired, and the grid was not extended after inspection.

In the confirmatory stage, the specification, one primary hypothesis, one key secondary hypothesis, the non-inferiority margin, and the complete interpretation map were committed under an externally timestamped tag (study2b-freeze), together with the replay and statistics code, before any new stream was generated. Schedules and stimuli for 130 additional repetitions per model (indices 131–260) were generated from the same committed master-seed scheme without altering the original repetitions; the four models, generation configurations, prompt, and parser were unchanged. Generation produced no API errors and no refusals; 16 of 18,720 responses (0.085%, all Claude Sonnet 5) were unparsable and were retained under intention-to-treat scoring.

The primary hypothesis (P1) was that WCDMinimal would reduce previous-rule-aligned errors relative to RawLLM, tested per model with the same paired machinery and the same three-error headroom gate as Study 2. The key secondary hypothesis (S1) was non-inferiority of WCDMinimal to RuleBlindFull on the same endpoint, satisfied when the upper bound of the paired-bootstrap 95% confidence interval of the difference fell below a margin of 1.9917 errors per repetition, fixed in advance as half the pooled RawLLM-minus-RuleBlindFull difference on the calibration corpus (floored at 0.5). Four replayed conditions (RawLLM, WCDMinimal, RuleBlindFull, WSLSBudgeted) yielded 4 models × 130 repetitions × 4 conditions × 36 trials = 74,880 scored condition-trials. Accuracy contrasts, do-no-harm bounds (−0.02), and one labeled exploratory contrast (WCDMinimal versus RuleBlindFull on previous-rule-aligned errors) were specified in the same frozen document.

## 4. Results

Each subsection reports, in order: the verdict, the size of the effect, the statistical evidence, and the limits of interpretation.

### 4.1 Binary outcome feedback improved accuracy on every model

Verdict: both feedback-using supervisors improved accuracy over the raw model on all four held-out model generations, and both cleared the pre-specified do-no-harm bound.

RawLLM mean accuracy was tightly clustered across models, from .3271 to .3327. RuleBlindFull increased accuracy by .1160 to .1252, and WSLSBudgeted by .1585 to .1690 — roughly 12 and 16 percentage points, respectively, from a budget of at most nine interventions per 36 trials. Every supervisor-versus-Raw contrast passed the directional primary test with Holm-adjusted p < .001, and the lower bound of every 95% confidence interval lay well above the −.02 non-inferiority margin.

The third primary test was also decisive: WSLSBudgeted was more accurate than RuleBlindFull on all four models, by .0344 to .0530 (all adjusted p < .001; Table 2, Figure 1). The simple information-matched policy was consistently superior on the primary performance measure; the elaborate machinery bought no accuracy.

**Table 2.** Study 2 confirmatory accuracy by model and condition (n = 130 repetitions per model).

| Model | Raw accuracy | RuleBlindFull accuracy | WSLSBudgeted accuracy | Full − Raw, 95% CI | WSLS − Raw, 95% CI | WSLS − Full, 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | .3327 | .4568 | .4912 | .1241 [.1156, .1327] | .1585 [.1489, .1679] | .0344 [.0239, .0449] |
| Claude Sonnet 5 | .3306 | .4556 | .4917 | .1250 [.1165, .1335] | .1611 [.1517, .1705] | .0361 [.0254, .0470] |
| GPT-5.5 | .3306 | .4558 | .4919 | .1252 [.1167, .1338] | .1613 [.1530, .1694] | .0361 [.0250, .0470] |
| GPT-5.4 mini | .3271 | .4432 | .4962 | .1160 [.1066, .1252] | .1690 [.1615, .1765] | .0530 [.0423, .0637] |

*Note.* Accuracy is the mean proportion of correct final choices per repetition. Bracketed intervals are paired-bootstrap 95% confidence intervals of the difference; all three contrasts passed their directional primary tests at Holm-adjusted p < .001 on every model.

These results establish that, under the tested policies, the correctness bit was convertible into performance within a hard budget; they do not yet say which policy design best converts it, which is the subject of the next test.

### 4.2 The predicted trade-off did not transfer

Verdict: the predicted compensating advantage of RuleBlindFull — fewer previous-rule-aligned errors than WSLSBudgeted — held on one model, was inconclusive on one, and reversed significantly on two. Under the frozen transfer rule, the trade-off received the label no transfer.

The pattern appeared only for GPT-5.5: Full − WSLS = −0.4692 errors per repetition, 95% CI [−0.9077, −0.0308], Holm-adjusted p = .0369. GPT-5.4 mini showed a small difference in the predicted direction but an interval spanning zero: −0.1462 [−0.5385, 0.2231], adjusted p = .48515. Both Claude models showed significant effects in the opposite direction: Opus, +0.8308 [0.4231, 1.2385], adjusted p < .001; Sonnet, +0.5846 [0.1538, 1.0154], adjusted p = .0084. On those two models, the machinery intended to prevent returns to the outdated rule instead prolonged them (Table 3, Figure 2).

**Table 3.** Study 2 co-primary trade-off test: previous-rule-aligned errors under RuleBlindFull versus WSLSBudgeted.

| Model | Full previous-rule errors | WSLS previous-rule errors | Full − WSLS, 95% CI | Adjusted p | Frozen verdict |
|---|---:|---:|---:|---:|---|
| Claude Opus 4.8 | 6.0769 | 5.2462 | +0.8308 [0.4231, 1.2385] | < .001 | Opposite direction |
| Claude Sonnet 5 | 6.0231 | 5.4385 | +0.5846 [0.1538, 1.0154] | .0084 | Opposite direction |
| GPT-5.5 | 6.6385 | 7.1077 | −0.4692 [−0.9077, −0.0308] | .0369 | Pass |
| GPT-5.4 mini | 7.9308 | 8.0769 | −0.1462 [−0.5385, 0.2231] | .48515 | Inconclusive/fail |

*Note.* Values are mean previous-rule-aligned errors per repetition (36 trials). The pre-registered prediction was Full < WSLS; bracketed intervals are paired-bootstrap 95% confidence intervals, and p-values are Holm-adjusted within model.

Only one of four models satisfied all four primary tests. This label does not negate the replicated accuracy improvements; it rejects the stronger claim that RuleBlindFull reliably occupies a distinct, favorable trade-off point relative to WSLSBudgeted. What it could not yet determine — whether the reversal was caused by outcome tracking itself or by the protection stack — motivated Study 2b (Section 4.6).

### 4.3 Trajectory shaping alone was not sufficient

Verdict: the feedback-free TrajectoryOnly supervisor was accuracy-equivalent to doing nothing.

Its paired accuracy differences from RawLLM ranged from −.0064 to +.0017, and all four 90% confidence intervals fell within the pre-specified ±.02 equivalence bounds. This result matters because the project's original feedback-free account predicted benefit without outcome information; in the confirmatory design, redistributing the output trajectory changed what the model produced but not how often it was right. Output diversification without outcome information is not adaptive control.

Two secondary controls locate where the feedback-using supervisors' value comes from. RuleBlindFull outperformed YokedRandom in accuracy on every model despite matched intervention timing, and it outperformed the NoVeto ablation — so which action is chosen at an intervention matters, not merely that one occurs. These comparisons support the internal coherence of RuleBlindFull's design but do not rescue the failed co-primary trade-off, because WSLSBudgeted remained the stronger accuracy policy.

### 4.4 Safety and efficiency

Verdict: both co-primary supervisors helped more than they hurt, on every model.

Both produced positive mean net correction throughout. RuleBlindFull averaged 7.84 to 7.94 interventions per repetition and 4.18 to 4.51 net corrections; WSLSBudgeted averaged 8.26 to 9.00 interventions and 5.71 to 6.08 net corrections. Harmful overrides were nonzero for both and generally higher under WSLSBudgeted, but its larger number of corrective overrides yielded the stronger net result.

WSLSUnlimited reached mean accuracies from .6169 to .7216 but used 15.22 to 21.11 interventions per repetition; it is a descriptive high-intervention reference, not an information- or cost-matched competitor. OracleFull is likewise not a ceiling: it uses privileged rule information only within a frozen policy and reached .5244 to .6218 rather than the theoretical maximum of 1.0.

### 4.5 Exploratory information-processing analyses

Post hoc analyses separated output diversity from task alignment. TrajectoryOnly substantially increased choice entropy while leaving accuracy equivalent to RawLLM, confirming that a broader action distribution is not itself evidence of adaptive control. RuleBlindFull and WSLSBudgeted increased both diversity and accuracy, with WSLSBudgeted producing the larger task-aligned gain. Additional analyses of target-conditioned accuracy, mutual information, early recovery, and censored recovery time are descriptive because they were specified after confirmatory results were available; they are hypothesis-generating and do not redefine the primary outcome.

### 4.6 Study 2b: removing the protection stack removed the reversal

Verdict: on fresh confirmatory streams, the minimal supervisor reduced previous-rule-aligned errors on all four models, was non-inferior to RuleBlindFull everywhere, and eliminated the Claude-model reversal — and under its frozen parameters it behaved identically to win-stay/lose-shift.

RawLLM previous-rule-aligned errors on the newly generated repetitions exceeded the three-error headroom requirement on every model (10.04 to 10.96 per repetition), so the primary test ran confirmatorily on all four. P1 passed everywhere: WCDMinimal reduced previous-rule-aligned errors relative to RawLLM by 5.23 (Claude Opus 4.8; 95% CI [−5.48, −4.96]), 4.98 (Claude Sonnet 5; [−5.28, −4.65]), 3.73 (GPT-5.5; [−4.12, −3.32]), and 2.01 (GPT-5.4 mini; [−2.32, −1.68]) errors per repetition, all Holm-adjusted p < .001. S1 was satisfied on every model: the 95% upper bound of the WCDMinimal-minus-RuleBlindFull difference never exceeded 0.50 errors, well below the pre-registered 1.9917 margin. Under the frozen interpretation map, all four models received the same verdict: the minimal scaffold suffices, and the protection stack is unnecessary on this endpoint (Table 4, Figure 3).

**Table 4.** Study 2b confirmatory results: previous-rule-aligned errors on newly generated repetitions 131–260 (n = 130 per model).

| Model | Raw prev.-rule errors | WCDMinimal prev.-rule errors | RuleBlindFull prev.-rule errors | P1: WCD − Raw, 95% CI | S1: WCD − Full, 95% CI | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Claude Opus 4.8 | 10.96 | 5.73 | 6.52 | −5.23 [−5.48, −4.96] | −0.78 [−1.19, −0.39] | minimal sufficient |
| Claude Sonnet 5 | 10.96 | 5.98 | 6.52 | −4.98 [−5.28, −4.65] | −0.54 [−0.93, −0.13] | minimal sufficient |
| GPT-5.5 | 10.63 | 6.90 | 6.83 | −3.73 [−4.12, −3.32] | +0.07 [−0.36, 0.49] | minimal sufficient |
| GPT-5.4 mini | 10.04 | 8.03 | 7.93 | −2.01 [−2.32, −1.68] | +0.10 [−0.28, 0.48] | minimal sufficient |

*Note.* Values are mean previous-rule-aligned errors per repetition. P1 (primary) required WCDMinimal < RawLLM, all Holm-adjusted p < .001; S1 (key secondary) required the 95% upper bound of WCDMinimal − RuleBlindFull to fall below the pre-registered margin of 1.9917. Verdicts follow the frozen interpretation map.

The labeled exploratory contrast sharpened the localization: WCDMinimal produced significantly fewer previous-rule-aligned errors than RuleBlindFull on exactly the two models where the Study 2 reversal had appeared (Opus: −0.78, adjusted p < .001; Sonnet: −0.54, adjusted p = .013) and did not differ on either GPT model. WCDMinimal was also more accurate than RuleBlindFull on all four models (+0.021 to +0.047, all adjusted p ≤ .0014) and exceeded every do-no-harm bound.

One structural result constrains the interpretation and is reported as found: under the frozen corner parameters, WCDMinimal's final choices were identical to WSLSBudgeted's on all 74,880 confirmatory condition-trials (the paired difference was exactly zero on every repetition), while differing from RuleBlindFull on 4,904 of 18,720 stream-trials. The calibrated minimal evidence-accumulation policy therefore reduced, in practice, to win-stay/lose-shift on these streams. Study 2b consequently does not demonstrate that decayed evidence scores add anything beyond WSLS in this regime; what it demonstrates is that removing RuleBlindFull's protection stack removes the reversal, and that nothing beyond a WSLS-equivalent policy was needed to do so.

## 5. Discussion

### 5.1 What was found

The three organizing questions received clear answers. First, reshaping the output trajectory without outcome information did not improve accuracy: a supervisor can change what a model produces without making it more correct, and increased choice diversity is not adaptation. Second, binary outcome feedback improved accuracy substantially and with unusual cross-model consistency — roughly 12 percentage points under RuleBlindFull and 16 under WSLSBudgeted, on all four held-out generations, within a nine-intervention budget. Third, the elaborate supervisor earned no premium over the simple one: WSLSBudgeted used the same information and budget, was easier to describe, and was more accurate on every model, while RuleBlindFull's predicted advantage on previous-rule-aligned errors transferred to only one model and reversed on two. Study 2b then implicated the protection stack: a minimal supervisor without the veto window, rescue, and cooldown eliminated the excess errors on both Claude models and was non-inferior everywhere else.

Together these results support a specific definition of adaptation. A response stream is adaptive not when it varies, but when it changes in the direction the environment's outcome information indicates. In this design, the informative event was the delayed correctness bit; among the tested supervisors, everything that improved performance used it, and nothing that lacked it improved performance.

### 5.2 Why the WCST environment produced these results

The WCST combines four features: the latent rule is invisible; it must be inferred from post-action correctness feedback; it changes mid-run; and the previous rule persists as a plausible foil. This makes it a minimal testbed for separating the raw LLM choice, the information value of outcome feedback, the role of external state, and the complexity of the supervising policy — precisely the decomposition Sections 4.1–4.6 perform.

It also explains the direction of the complexity result. Adaptation need not be a property of persistent memory or learning inside the language model: a memoryless LLM plus a few externally held numbers and a simple feedback policy jointly constitute an adaptive system. But protective complexity is not automatically safety. In this environment, feedback is clean and an error is a strong, prompt signal of rule change, so a policy that waits for corroborating evidence pays for its caution in delayed updates and prolonged retention of the outdated rule. This is what the normative change-point literature predicts: waiting and evidence-margin policies are rational when individual outcomes are weakly informative, and simple update rules approach full Bayesian performance when environment statistics are clean (Nassar et al., 2010; Wilson et al., 2010). The protection stack lost not because caution is wrong in general but because this environment sits in the regime where caution buys nothing. In noisier environments the same mechanisms could earn their keep; here they did not (Section 5.4 marks that boundary).

The results also carry a methodological lesson: an untreated baseline is not enough. RuleBlindFull comfortably beat RawLLM — and had that been the only comparison, this paper would have reported a validated elaborate supervisor. Against a strong, information-matched, cost-matched simple baseline, it could not be the default recommendation. New supervision policies should be evaluated against the strongest simple policy that uses the same information and the same intervention budget (cf. Henderson et al., 2018). The comparison with in-context instruction points the same way: spelling out the win-stay/lose-shift strategy inside the prompt did not rescue WCST performance in prior work (de Langis et al., 2026), whereas enforcing the same policy outside the model did — what mattered was not whether the policy was available to the model but whether anything reliably executed it.

### 5.3 Scope: why only the WCST, and what is licensed

Earlier development phases of this project examined Stroop-type and AX-CPT-type tasks, but the three tasks do not measure the same control process. Stroop measures conflict resolution under an explicitly stated rule — suppressing a dominant response; AX-CPT measures cue maintenance and the division between proactive and reactive control; the WCST measures the discovery of a changing latent rule from outcome feedback and the decision to keep or abandon a hypothesis (Stroop, 1935; Braver, 2012). The present confirmatory evidence therefore supports claims about latent-rule adaptation from binary outcome feedback, not about cognitive control in general. Because the earlier Stroop and AX-CPT results were not produced under the present information-access conditions and pre-registered procedures, they are part of the project's development lineage and are not combined with the confirmatory evidence here. Whether the advantage of simple WSLS-type supervision is specific to WCST-like environments, or extends to tasks requiring conflict suppression or context maintenance, is an open question for follow-up work.

### 5.4 Where these results apply, and where they should not be generalized

The confirmed principle applies most directly to systems with the following properties: a small set of structured action alternatives; a reliable post-action success/failure signal; repeated similar choices; and a bounded intervention budget. Practical instances include tool or API selection, categorical routing of documents and queries, repeated workflow-step selection, structured outputs with automatic validation, and simple agentic actions that return success indicators. In such settings, a small external supervisor tracking recent outcomes can improve performance without retraining the model and without feeding the full interaction history back into context on every call.

The results should not be extrapolated to open-ended long-form generation, judgments without objective correctness criteria, environments with noisy or long-delayed feedback, or clinical, legal, and other high-stakes decisions where a single error is unacceptable. In those regimes, the balance may tip back toward evidence accumulation and conservative protection mechanisms of exactly the kind that lost here — the present study shows that their value is environment-dependent, not that it is nil.

### 5.5 How the initial account was revised

The project's original claim — feedback-free trajectory control improves rule-shift performance — was put at risk by a frozen, information-matched design and was refuted: TrajectoryOnly was accuracy-equivalent to doing nothing. The second-generation claim — an elaborate belief-and-veto supervisor buys a favorable accuracy/error trade-off — was likewise put at risk and failed to transfer, reversing on two of four models. The third step probed that reversal in new data: removing the protection stack eliminated it, implicating the protections rather than outcome tracking. Each revision was forced by evidence that the previous account could not accommodate, under procedures frozen before the evidence existed. Where the evidence could not distinguish two policies — WCDMinimal and WSLSBudgeted behaved identically on every confirmatory trial — we follow parsimony and report the simpler, auditable description as the sufficient mechanism. What survives is deliberately modest and correspondingly well-supported: under the tested policies, improvement required access to the correctness bit, and a simple, auditable policy sufficed to harvest it.

Bayesian and resource-rational language can organize future work, but only as analogy. RuleBlindFull maintains a compact belief-like state and reacts to unexpected outcomes; it does not compute a calibrated posterior or establish optimality. A natural next step is to compare the frozen heuristics against an explicit Bayesian change-point observer under a common information and intervention budget.

## 6. Limitations

The task has only three categorical actions and externally defined block changes. Results may not transfer to open-ended language generation, continuous control, partially observable environments, or tasks in which delayed outcomes are noisy (Section 5.4). Stateless single-turn generation improves isolation but is not representative of conversational deployment.

The public prompt added a direct answer-format instruction after the engineering pilot. That change was made and frozen before confirmatory data collection, but it limits exact comparison with archived model generations. Model APIs and provider defaults can also change; the study therefore records exact model identifiers, library versions, timestamps, and generation manifests.

The controller was developed on Study 1, including parameter search, so Study 1 estimates are exploratory and may be optimistic. Study 2 protects the main transfer test, but all additional information-processing analyses remain post hoc.

Study 2b has its own asymmetries. Its hypothesis was formed after the Study 2 results were observed, and its parameters were calibrated on the same archived corpus that shaped RuleBlindFull; its confirmatory status rests entirely on the newly generated streams and the externally timestamped freeze, not on any claimed independence of the hypothesis from prior results. The calibrated parameters sat at the boundary of the searched grid, and the resulting policy was behaviorally identical to WSLSBudgeted on every confirmatory trial. Study 2b therefore licenses a stack-level removal claim (removing the protection stack eliminated the reversal) and a sufficiency claim (a WSLS-equivalent policy suffices), but neither an attribution of the reversal to any individual protection mechanism nor the claim that evidence accumulation, waiting, or margin-based discrimination contribute anything measurable in this regime.

The conditions are information-matched only where explicitly stated. RuleBlindFull and WSLSBudgeted share feedback and budget; TrajectoryOnly lacks outcome feedback by design; WSLSUnlimited lacks a budget; OracleFull receives privileged information. Because TrajectoryOnly differs from the feedback-using policies in its action rule as well as its information access, the contrast bounds what the tested policies achieved rather than isolating an independent causal effect of the information itself. Comparisons involving those references answer different questions and should not be presented as a single leaderboard.

Finally, behavioral regularities do not identify internal cognitive mechanisms. Terms such as "belief," "control," and "recovery" name components or observable sequences in the external scaffold. They do not establish phenomenology, neural equivalence, or human-like executive function in the underlying LLM.

## 7. Reproducibility, Data Integrity, and Security

The repository preserves immutable public streams, separately generated ground-truth schedules, replay outputs, trial-level and repetition-level results, paired-statistics tables, and SHA-256 manifests. Automated checks enforce the complete trial grids for both studies, one-to-one repetition pairing, controller blindness, parser behavior, hard intervention budgets, and refusal to overwrite existing repetition files. All schedules regenerate deterministically from a single command (`python scripts/generate_schedules.py`), which derives the generator for repetition *k* as `random.Random(20260715 × 1000 + k)` (Matsumoto & Nishimura, 1998) and verifies its output against the committed manifest; because the analysis code is standard-library-only and fully seeded (Section 3.9), identical inputs reproduce identical outputs without an environment lock.

Study 2b extends the same discipline: the controller specification, calibration grid and selection rule, hypotheses, non-inferiority margin, interpretation map, and the complete replay and statistics code were committed under the externally timestamped study2b-freeze tag before any new stream existed, so no analyst degree of freedom remained once generation began; the schedule extension to repetitions 131–260 left all original files unchanged. Confirmatory statistics were re-run after a provenance and security hardening pass and were unchanged; the hardening measures (secret and path scanning, least-privilege continuous integration, attempts-log hashing, and related checks) are itemized in the supplementary materials. No API key, local environment value, personal path, or credential is included in this manuscript package.

## 8. Conclusion

External binary correctness feedback can improve the repetitive behavior of a memoryless LLM — robustly, across four current model generations, and within a sparse intervention budget — and no elaborate cognitive scaffold was required to harvest it. In this WCST-style environment the simple, auditable policy was the stronger one, outcome-free output diversification did not qualify as adaptive control, and removing the elaborate supervisor's protection machinery eliminated its characteristic failure — implicating that machinery, rather than outcome tracking, in the reversal. The paper's contribution is accordingly not a new supervisor but a dissection: a stepwise, pre-registered separation of the roles of information access, external state, update speed, and policy complexity in an adaptive LLM system — one that refuted its own initial feedback-free account, replaced an elaborate mechanism with a simpler sufficient one, and reports how far the surviving claims extend — a boundary drawn by pre-registered, operationalized criteria rather than by narrative judgment.

## Declaration of competing interest

The author declares that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Data availability

All public response streams, ground-truth schedules, controller and replay code, frozen analysis code and freeze tags, statistics tables, and SHA-256 manifests are available in the study repository; an anonymized link is provided for review, and a public archive will be linked upon acceptance.

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used large language model assistants: Claude (Anthropic) for language editing and drafting support, and GPT-5.6 sol (OpenAI) for auxiliary data review and cross-checking and for literature searching. After using these tools, the author reviewed, verified, and edited the content as needed and takes full responsibility for the content of the published article. (The LLMs evaluated as experimental subjects are described in Section 3.7 and are unrelated to this declaration; all confirmatory statistics were produced solely by the frozen analysis code described in Section 3.9.)

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

## References

Adams, R. P., & MacKay, D. J. C. (2007). Bayesian online changepoint detection. arXiv:0710.3742. https://doi.org/10.48550/arXiv.0710.3742

Behrens, T. E. J., Woolrich, M. W., Walton, M. E., & Rushworth, M. F. S. (2007). Learning the value of information in an uncertain world. Nature Neuroscience, 10(9), 1214–1221. https://doi.org/10.1038/nn1954

Binz, M., & Schulz, E. (2023). Using cognitive psychology to understand GPT-3. Proceedings of the National Academy of Sciences, 120(6), e2218523120. https://doi.org/10.1073/pnas.2218523120

Bishara, A. J., Kruschke, J. K., Stout, J. C., Bechara, A., McCabe, D. P., & Busemeyer, J. R. (2010). Sequential learning models for the Wisconsin Card Sort Task: Assessing processes in substance dependent individuals. Journal of Mathematical Psychology, 54(1), 5–13. https://doi.org/10.1016/j.jmp.2008.10.002

Braver, T. S. (2012). The variable nature of cognitive control: A dual mechanisms framework. Trends in Cognitive Sciences, 16(2), 106–113. https://doi.org/10.1016/j.tics.2011.12.010

Chatterjee, A., Renduchintala, H. S. V. N. S. K., Bhatia, S., & Chakraborty, T. (2024). POSIX: A prompt sensitivity index for large language models. Findings of ACL: EMNLP 2024, 14550–14565. https://doi.org/10.18653/v1/2024.findings-emnlp.852

D’Alessandro, M., Radev, S. T., Voss, A., & Lombardi, L. (2020). A Bayesian brain model of adaptive behavior: An application to the Wisconsin Card Sorting Task. PeerJ, 8, e10316. https://doi.org/10.7717/peerj.10316

de Langis, K., Park, J. I., Hu, B., Le, K. C., Schramm, A., Mensink, M. C., Elfenbein, A., & Kang, D. (2026). Strong memory, weak control: An empirical study of executive functioning in LLMs. Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers), 5971–5986. https://doi.org/10.18653/v1/2026.eacl-long.281

Diamond, A. (2013). Executive functions. Annual Review of Psychology, 64, 135–168. https://doi.org/10.1146/annurev-psych-113011-143750

Efron, B., & Tibshirani, R. J. (1993). An introduction to the bootstrap. Chapman & Hall.

Ernst, M. D. (2004). Permutation methods: A basis for exact inference. Statistical Science, 19(4), 676–685. https://doi.org/10.1214/088342304000000396

Goto, D., Idei, H., Shiozuka, Y., & Ogata, T. (2025). Performance of large language models and analysis of responses in the Wisconsin Card Sorting Task. 2025 IEEE International Conference on Development and Learning. https://doi.org/10.1109/ICDL63968.2025.11204408

Grant, D. A., & Berg, E. A. (1948). A behavioral analysis of degree of reinforcement and ease of shifting to new responses in a Weigl-type card-sorting problem. Journal of Experimental Psychology, 38, 404–411.

Hao, G., Alexandre, F., & Yu, S. (2025). Visual large language models exhibit human-level cognitive flexibility in the Wisconsin Card Sorting Test. arXiv:2505.22112. https://doi.org/10.48550/arXiv.2505.22112

Hayes, W. M., Yax, N., & Palminteri, S. (2024). Large language models are biased reinforcement learners. arXiv:2405.11422. https://doi.org/10.48550/arXiv.2405.11422

Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2018). Deep reinforcement learning that matters. Proceedings of the AAAI Conference on Artificial Intelligence, 32(1). https://doi.org/10.1609/aaai.v32i1.11694

Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65–70.

Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X., & Zhou, D. (2024). Large language models cannot self-correct reasoning yet. The Twelfth International Conference on Learning Representations. https://openreview.net/forum?id=IkmD3fKBPQ

Kennedy, S. M., & Nowak, R. D. (2024). Cognitive flexibility of large language models. ICML 2024 Workshop on LLMs and Cognition. https://openreview.net/forum?id=58yThpzlth

Kerby, D. S. (2014). The simple difference formula: An approach to teaching nonparametric correlation. Comprehensive Psychology, 3, Article 1. https://doi.org/10.2466/11.IT.3.1

Kopp, B., Lange, F., & Steinke, A. (2021). The reliability of the Wisconsin Card Sorting Test in clinical practice. Assessment, 28(1), 248–263. https://doi.org/10.1177/1073191119866257

Krishnamurthy, A., Harris, K., Foster, D. J., Zhang, C., & Slivkins, A. (2024). Can large language models explore in-context? Advances in Neural Information Processing Systems, 37. https://doi.org/10.48550/arXiv.2403.15371

Lakens, D. (2017). Equivalence tests: A practical primer for t tests, correlations, and meta-analyses. Social Psychological and Personality Science, 8(4), 355–362. https://doi.org/10.1177/1948550617697177

Lieder, F., & Griffiths, T. L. (2020). Resource-rational analysis: Understanding human cognition as the optimal use of limited computational resources. Behavioral and Brain Sciences, 43, e1. https://doi.org/10.1017/S0140525X1900061X

Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., Alon, U., Dziri, N., Prabhumoye, S., Yang, Y., Gupta, S., Majumder, B. P., Hermann, K., Welleck, S., Yazdanbakhsh, A., & Clark, P. (2023). Self-Refine: Iterative refinement with self-feedback. Advances in Neural Information Processing Systems, 36. https://doi.org/10.48550/arXiv.2303.17651

Matsumoto, M., & Nishimura, T. (1998). Mersenne twister: A 623-dimensionally equidistributed uniform pseudo-random number generator. ACM Transactions on Modeling and Computer Simulation, 8(1), 3–30. https://doi.org/10.1145/272991.272995

Miles, S., Howlett, C. A., Berryman, C., Nedeljkovic, M., Moseley, G. L., & Phillipou, A. (2021). Considerations for using the Wisconsin Card Sorting Test to assess cognitive flexibility. Behavior Research Methods, 53(5), 2083–2091. https://doi.org/10.3758/s13428-021-01551-3

Milner, B. (1963). Effects of different brain lesions on card sorting: The role of the frontal lobes. Archives of Neurology, 9, 100–110.

Monsell, S. (2003). Task switching. Trends in Cognitive Sciences, 7(3), 134–140. https://doi.org/10.1016/S1364-6613(03)00028-7

Nassar, M. R., Wilson, R. C., Heasly, B., & Gold, J. I. (2010). An approximately Bayesian delta-rule model explains the dynamics of belief updating in a changing environment. Journal of Neuroscience, 30(37), 12366–12378. https://doi.org/10.1523/JNEUROSCI.0822-10.2010

Schubert, J. A., Jagadish, A. K., Binz, M., & Schulz, E. (2024). In-context learning agents are asymmetric belief updaters. Proceedings of the 41st International Conference on Machine Learning, PMLR 235, 43928–43946.

Schuirmann, D. J. (1987). A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. Journal of Pharmacokinetics and Biopharmaceutics, 15(6), 657–680. https://doi.org/10.1007/BF01068419

Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2024). Quantifying language models’ sensitivity to spurious features in prompt design or: How I learned to start worrying about prompt formatting. The Twelfth International Conference on Learning Representations. https://openreview.net/forum?id=RIu5lyNXjT

Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., & Yao, S. (2023). Reflexion: Language agents with verbal reinforcement learning. Advances in Neural Information Processing Systems, 36. https://doi.org/10.48550/arXiv.2303.11366

Steinke, A., Lange, F., & Kopp, B. (2020). Parallel model-based and model-free reinforcement learning for card sorting performance. Scientific Reports, 10, 15464. https://doi.org/10.1038/s41598-020-72407-7

Stroop, J. R. (1935). Studies of interference in serial verbal reactions. Journal of Experimental Psychology, 18(6), 643–662. https://doi.org/10.1037/h0054651

Wilson, R. C., Nassar, M. R., & Gold, J. I. (2010). Bayesian online learning of the hazard rate in change-point problems. Neural Computation, 22(9), 2452–2476. https://doi.org/10.1162/NECO_a_00007

## Figure captions

**Figure 1.** Study 2 confirmatory accuracy across supervisor conditions. (A) Mean proportion of correct final choices per repetition (130 repetitions of 36 trials per model) for RawLLM, RuleBlindFull, and WSLSBudgeted. (B) Paired per-repetition accuracy differences for the three primary contrasts (Full − Raw, WSLS − Raw, WSLS − Full) with paired-bootstrap 95% confidence intervals; all twelve intervals exclude zero (all Holm-adjusted p < .001).

**Figure 2.** Study 2 co-primary trade-off test: RuleBlindFull minus WSLSBudgeted difference in previous-rule-aligned errors per repetition (36 trials), with paired-bootstrap 95% confidence intervals; the arrow marks the frozen predicted direction (fewer errors under RuleBlindFull). Only GPT-5.5 shows the predicted negative difference (−0.4692, 95% CI [−0.9077, −0.0308]); both Claude models differ significantly in the opposite direction, and GPT-5.4 mini shows no reliable difference, so the predicted trade-off received the pre-registered label no transfer.

**Figure 3.** Study 2b confirmatory results on previous-rule-aligned errors per repetition (36 trials), on newly generated repetitions 131–260. Filled circles show the primary contrast P1 (WCDMinimal − RawLLM) and open squares the key secondary contrast S1 (WCDMinimal − RuleBlindFull), each with paired-bootstrap 95% confidence intervals; the dashed line marks the pre-registered S1 non-inferiority margin (+1.9917). P1 is negative on all four models (−5.23 to −2.01, all Holm-adjusted p < .001) and every S1 upper confidence limit falls below the margin, supporting the frozen verdict that the minimal scaffold suffices.
