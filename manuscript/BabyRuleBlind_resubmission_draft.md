# Sparse Outcome-Feedback Supervision of Memoryless LLM Outputs in a Rule-Shift Task

Anonymous Author

## Abstract

Large language models can produce stable but poorly task-aligned response policies when each trial is evaluated without conversational memory. We test whether a small external supervisor can improve such outputs using only the model’s public choices and a delayed binary correctness signal. The confirmatory study used four current-generation models, 130 independently randomized repetitions per model, eight replayed conditions, and 36 trials per repetition (149,760 scored condition-trials). Two information-matched, budget-limited supervisors were co-primary: RuleBlindFull, a belief-and-veto policy, and WSLSBudgeted, a win-stay/lose-shift policy. Both improved accuracy over the raw model on every model (RuleBlindFull: +0.1160 to +0.1252; WSLSBudgeted: +0.1585 to +0.1690; all Holm-adjusted p < .001), and both were non-inferior to the raw baseline under the pre-specified −0.02 margin. WSLSBudgeted was more accurate than RuleBlindFull on all four models (+0.0344 to +0.0530; all adjusted p < .001). The predicted compensating advantage of RuleBlindFull in reducing previous-rule-aligned errors was supported only for GPT-5.5; it failed on the other three models and was significantly reversed on both Claude models. Under the pre-registered rule, the proposed accuracy–error trade-off therefore showed no generation transfer. A feedback-free trajectory-only control was accuracy-equivalent to the raw baseline, indicating that output redistribution alone was insufficient. The results support a limited claim: sparse outcome feedback can substantially improve memoryless LLM action streams under a hard intervention budget, but the more elaborate supervisor did not reliably outperform a simple information-matched policy. A pre-registered follow-up (Study 2b) tested whether the reversal was caused by RuleBlindFull's protection mechanisms. A minimal evidence-accumulation supervisor, calibrated only on archived development data and evaluated once on 130 newly generated repetitions per model, reduced previous-rule-aligned errors relative to the raw baseline on all four models (all adjusted p < .001) and was non-inferior to RuleBlindFull under a pre-specified margin on all four; on both Claude models it produced significantly fewer previous-rule-aligned errors than RuleBlindFull. Under the frozen parameters the minimal supervisor's choices coincided exactly with the win-stay/lose-shift policy on every confirmatory trial, indicating that the additional protection machinery, not outcome-driven hypothesis tracking itself, drove the reversal.

Keywords: large language models; cognitive flexibility; rule shifting; outcome feedback; external supervision; Wisconsin Card Sorting Task; reproducibility

## 1. Introduction

Rule-shift tasks separate knowing the available actions from selecting the action appropriate to the current latent rule. The Wisconsin Card Sorting Test (WCST) is a canonical example: a participant sorts by color, shape, or number while the rewarded dimension changes without explicit announcement (Grant & Berg, 1948). Human work treats previous-rule-aligned errors as one observable consequence of impaired updating or control, while also warning that no single WCST score uniquely identifies a mechanism (Milner, 1963; Kopp et al., 2021; Miles et al., 2021).

Large language models (LLMs) offer a useful but delicate comparison. Cognitive-task evaluations can reveal reproducible input–output regularities, yet those regularities are sensitive to prompt form, sampling configuration, memory, and parsing (Binz & Schulz, 2023; Sclar et al., 2024; Chatterjee et al., 2024). Recent WCST-oriented work likewise reports substantial variation across models and presentation regimes (Kennedy & Nowak, 2024; Hao et al., 2025; Goto et al., 2025). Consequently, a behavioral score should not be read as a direct measurement of a human cognitive faculty or an internal model state.

This study evaluates a narrower engineering proposition. Each LLM response is generated independently, without conversation history. An external supervisor then observes the public response sequence. Feedback-aware supervisors receive only one additional bit after each final action: whether that action was correct. They never receive the hidden rule, card-to-rule mapping, or future schedule. This arrangement asks whether a small, auditable policy can convert sparse outcome feedback into better action selection while respecting a fixed intervention budget.

The project began with a feedback-free trajectory controller developed on two archived models and one fixed schedule. That development stream suggested large reductions in a broad “persistence” measure, but its design could not separate trajectory shaping from information gained through correctness, and its repeated fixed schedule raised overfitting concerns. The present study therefore replaces the earlier claim with a frozen, information-matched comparison. RuleBlindFull and WSLSBudgeted receive the same correctness bit and share the same hard cap of nine interventions per 36-trial repetition. Randomized schedules, held-out model generations, frozen parsing, intention-to-treat scoring, and same-stream replay are used to reduce avoidable sources of bias.

The confirmatory question is not whether supervision helps in the abstract. It is whether a proposed Pareto trade-off transfers to held-out models: RuleBlindFull should improve accuracy over RawLLM, WSLSBudgeted should improve accuracy over RawLLM, WSLSBudgeted should be more accurate than RuleBlindFull, and RuleBlindFull should produce fewer previous-rule-aligned errors than WSLSBudgeted. All four directional tests must succeed for the trade-off to replicate on a model.

The confirmatory results (Section 4) raised a second question that the original design could not answer: when RuleBlindFull increased previous-rule-aligned errors on both Claude models, was the cost produced by its protection mechanisms (veto window, stuckness rescue, cooldown), or by outcome-driven hypothesis tracking as such? Study 2b addresses this with a separately frozen, pre-registered follow-up: a minimal evidence-accumulation supervisor was calibrated exploratorily on the archived development streams, frozen under an externally timestamped tag, and evaluated exactly once on newly generated confirmatory streams that did not exist when the hypothesis was formed.

## 2. Related Work

### 2.1 Card sorting and adaptive control

The WCST has long been used to study rule discovery, set shifting, and the balance between stability and flexibility (Grant & Berg, 1948; Milner, 1963). Contemporary methodological work emphasizes that reliability and interpretation depend on the scoring rule, task version, and target population (Kopp et al., 2021; Miles et al., 2021). Computational accounts model card sorting as sequential learning rather than as a single latent faculty. Examples include sequential learning models (Bishara et al., 2010), Bayesian belief updating (D’Alessandro et al., 2020), and parallel model-based and model-free reinforcement learning (Steinke et al., 2020). These accounts motivate trial-level analysis but do not imply that the present heuristic supervisor implements a human mechanism.

### 2.2 LLM behavioral evaluation and prompt sensitivity

LLMs can be probed with cognitive tasks, but the resulting behavior reflects the full evaluation interface: prompt wording, answer constraints, sampling settings, parser rules, and retained context. Prompt-format sensitivity has been quantified directly across model families (Sclar et al., 2024; Chatterjee et al., 2024). Studies of LLM cognitive flexibility and WCST performance similarly show that conclusions depend on model and modality (Kennedy & Nowak, 2024; Hao et al., 2025; Goto et al., 2025). We therefore describe observable response policies and refrain from treating them as direct evidence of human-like executive function.

### 2.3 Limited external supervision

Inference-time control can alter model outputs without modifying model weights. The present supervisor is simpler than general controlled-generation systems: it chooses among three categorical actions and uses a hard intervention budget. The resource-rational perspective is relevant only as a design analogy—performance is evaluated under a fixed supervision allowance—not as a claim that the learned or hand-built policy is optimal (Lieder & Griffiths, 2020). Likewise, Bayesian change-point models provide a conceptual language for belief revision under changing contingencies (D’Alessandro et al., 2020), but RuleBlindFull is a frozen heuristic rather than an exact posterior computation.

## 3. Method

### 3.1 Architecture and information isolation

For each trial, the generation layer provided the model with a public card description and requested one dimension name. No system message or conversation history carried information across trials. The resulting raw text was preserved and parsed using a frozen parser. A controller received only the public trial index and parsed choice. The evaluator, which alone had access to the hidden schedule, scored the controller’s final choice. Only after the final choice was fixed did a feedback-aware controller receive the Boolean correctness outcome.

Ground truth was isolated from the controller package and request path. Per-repetition public prompts and ground-truth schedules were stored separately. Automated gates checked that controller code did not contain ground-truth tokens, that the generation path did not load schedule files, and that the exact model × repetition × condition grid was complete before statistics were run.

### 3.2 Task and randomized schedules

Each repetition contained 36 trials. Cards varied on color, shape, and number, and the hidden sorting rule changed across blocks. Study 2 schedules were generated before any API call from master seed 20260715. Block lengths were drawn from 5, 6, or 7 trials, with a frozen partition rule ensuring every realized block was between 4 and 8 trials. The first rule was uniform over the three dimensions; each subsequent rule was sampled uniformly from the other two. Models shared the schedule associated with a repetition index, and every condition replayed the same immutable raw response stream.

### 3.3 Conditions

| Condition | Information and role |
|---|---|
| RawLLM | Parsed model choice without external intervention; baseline. |
| RuleBlindFull | Co-primary belief/veto/rescue supervisor; binary outcome feedback; maximum 9 interventions. |
| WSLSBudgeted | Co-primary win-stay/lose-shift supervisor; the same feedback and maximum 9 interventions. |
| NoVeto | RuleBlindFull ablation with the veto window removed. |
| TrajectoryOnly | Strictly feedback-free version testing whether the response trajectory alone is sufficient. |
| YokedRandom | Uses RuleBlindFull’s intervention timing but selects random alternative actions. |
| WSLSUnlimited | Descriptive reference without an intervention budget; not a confirmatory target. |
| OracleFull | Oracle-assisted policy reference with explicit ground-truth access; not a performance ceiling. |

The hard budget for budgeted supervisors was nine interventions, or 25% of trials. RuleBlindFull used frozen parameters selected only on Study 1: error streak to open = 1, veto window = 4, cumulative-unresolved rescue threshold = 2, rescue cooldown = 6, and belief confirmation streak = 2. WSLSBudgeted retained the most recent correct final dimension, stayed with it while outcomes remained correct, and shifted to a least-recently-tried alternative after failure, subject to the same budget.

### 3.4 Development and confirmatory data

Study 1 comprised 60 archived streams from Claude Sonnet 4.6 and GPT-4o, with 30 repetitions per model, collected in April 2026. It used a shared fixed schedule and informed controller design, parameter search, and exploratory analyses. Any Study 1 interval or p-value is therefore post-selection and non-confirmatory.

Study 2 was frozen before contact with the confirmatory streams. It included Claude Opus 4.8, Claude Sonnet 5, GPT-5.5 (2026-04-23), and GPT-5.4 mini (2026-03-17), with 130 repetitions per model. Three-repetition engineering pilots were excluded. The final confirmatory grid contained 4 models × 130 repetitions × 8 conditions × 36 trials = 149,760 condition-trial rows.

The answer-format prompt and parser were revised after the engineering pilot because the two Claude models frequently returned deliberative text that the earlier parser could not reliably reduce to one dimension. The parser-v3 rules and the added instruction, “Answer with just the dimension name,” were then re-frozen before Study 2. This limits literal comparability to the archived generation but improves measurement validity within the confirmatory study.

### 3.5 Outcomes

The primary accuracy outcome was the proportion of correct final choices per repetition. A previous-rule-aligned error occurred when an incorrect final choice matched the preceding block’s rule. The term is deliberately descriptive; it replaces the older, broader label “persistence.” Old-rule reentry required a previous-rule-aligned error after at least one correct response in the current block.

Safety outcomes distinguished corrective overrides (raw incorrect, final correct) from harmful overrides (raw correct, final incorrect). Net correction was corrective minus harmful overrides. Choice entropy summarized the distribution over the three final dimensions among parseable choices. Recovery latency was the within-block position of the first correct response, with blocks lacking a correct response censored at their observed length. “Productive rate” was removed as an inferential endpoint because later success can occur by chance; its narrow successor, subsequent-success rate, is descriptive only.

### 3.6 Statistical analysis

Analyses were performed separately for each model. Because every condition replayed the same raw stream and schedule, contrasts were paired at the repetition level. Each primary comparison used a two-sided 10,000-draw paired permutation test, a paired-bootstrap 95% confidence interval, and a matched-pairs rank-biserial effect size. Holm correction was applied to full-precision p-values over the four primary tests within each model.

The four directional primary tests were: RuleBlindFull > RawLLM accuracy; WSLSBudgeted > RawLLM accuracy; WSLSBudgeted > RuleBlindFull accuracy; and RuleBlindFull < WSLSBudgeted previous-rule-aligned errors. A test succeeded only when the Holm-adjusted p-value was below .05 and the observed direction matched the frozen prediction. All four tests had to succeed for the trade-off to replicate on a model. The pre-registered transfer label was broad for at least three successful models, partial for two, and no transfer for one or zero.

The previous-rule error test required RawLLM headroom of at least three errors per repetition, which all models satisfied. Non-inferiority of each co-primary supervisor to RawLLM used a −0.02 accuracy margin. Equivalence of TrajectoryOnly and RawLLM required the paired-bootstrap 90% confidence interval to fall entirely within ±0.02.

### 3.7 Parsing and intention-to-treat handling

The frozen parser first searched the text after the last recognized final-answer marker. Without a marker, exactly one dimension term was required; zero or multiple dimensions produced an unparsable result. Unparsable responses were retained and scored incorrect. API failures were retried under a frozen policy and preserved in attempt logs. Study 2 contained no API errors or refusals. There were 24 unparsable public responses among 18,720 generated responses (0.128%), all from Claude Sonnet 5. Because each public stream was replayed across eight conditions, the same unparsable response appears in each condition-specific trial table and must not be counted as eight independent generation failures.

### 3.8 Study 2b: pre-registered minimal-supervisor follow-up

The Study 2b hypothesis was explicitly formed after the Study 2 results were locked, so no analysis of the existing Study 2 streams could confirm it. The follow-up therefore used a two-stage design with its own freeze tag.

In the exploratory calibration stage, a minimal supervisor (WCDMinimal) was specified with three components: a per-dimension evidence score updated after every attributable outcome (all scores multiplied by a decay factor, then ±1 to the chosen dimension, clipped to ±5); a single active hypothesis, adopted at the first correct outcome and steered toward under the same nine-intervention budget as the co-primary supervisors; and a switch rule requiring both a minimum error streak on the active hypothesis and a strict evidence lead of the best alternative. Its three free parameters were selected by a codified rule (minimize pooled previous-rule-aligned errors subject to pooled accuracy at or above the raw baseline) on the archived Study 1 streams only, with the full 48-configuration grid published. The selected configuration lay at the most permissive corner of the grid (decay = 0.5, switch margin = 0.0, wait threshold = 1), meaning the calibration itself deactivated the waiting and margin gates; this boundary selection is disclosed rather than repaired, and the grid was not extended after inspection.

In the confirmatory stage, the frozen specification, one primary hypothesis, one key secondary hypothesis, the non-inferiority margin, and the complete interpretation map were committed under an externally timestamped tag (study2b-freeze), together with the replay and statistics code, before any new stream was generated. Schedules and stimuli for 130 additional repetitions per model (indices 131–260) were then generated from the same committed master-seed scheme and verified to leave the original repetitions byte-identical. The four confirmatory models, generation configurations, prompt, and parser were unchanged. Generation produced no API errors and no refusals; 16 of 18,720 responses (0.085%, all Claude Sonnet 5) were unparsable and were retained under intention-to-treat scoring.

The primary hypothesis (P1) was that WCDMinimal would reduce previous-rule-aligned errors relative to RawLLM, tested per model with the same paired machinery and the same three-error headroom gate as Study 2. The key secondary hypothesis (S1) was non-inferiority of WCDMinimal to RuleBlindFull on the same endpoint, satisfied when the upper bound of the paired-bootstrap 95% confidence interval of the difference fell below a margin of 1.9917 errors per repetition, fixed in advance as half the pooled RawLLM-minus-RuleBlindFull difference on the calibration corpus (floored at 0.5). Four replayed conditions (RawLLM, WCDMinimal, RuleBlindFull, WSLSBudgeted) yielded 4 models × 130 repetitions × 4 conditions × 36 trials = 74,880 scored condition-trials. Accuracy contrasts, do-no-harm bounds (−0.02), and one labeled exploratory contrast (WCDMinimal versus RuleBlindFull on previous-rule-aligned errors) were specified in the same frozen document.

## 4. Results

### 4.1 Confirmatory accuracy

RawLLM mean accuracy was tightly clustered across models, from .3271 to .3327. RuleBlindFull increased accuracy by .1160 to .1252, and WSLSBudgeted increased it by .1585 to .1690. Every supervisor-versus-Raw contrast passed the directional primary test with Holm-adjusted p < .001. The lower bound of every 95% confidence interval was also well above the −.02 non-inferiority margin.

WSLSBudgeted was more accurate than RuleBlindFull on all four models. The paired differences ranged from .0344 to .0530, with every adjusted p < .001. Thus, the simple information-matched policy was consistently superior on the primary performance measure.

| Model | Raw accuracy | RuleBlindFull accuracy | WSLSBudgeted accuracy | Full − Raw, 95% CI | WSLS − Raw, 95% CI | WSLS − Full, 95% CI |
|---|---:|---:|---:|---:|---:|---:|
| Claude Opus 4.8 | .3327 | .4568 | .4912 | .1241 [.1156, .1327] | .1585 [.1489, .1679] | .0344 [.0239, .0449] |
| Claude Sonnet 5 | .3306 | .4556 | .4917 | .1250 [.1165, .1335] | .1611 [.1517, .1705] | .0361 [.0254, .0470] |
| GPT-5.5 | .3306 | .4558 | .4919 | .1252 [.1167, .1338] | .1613 [.1530, .1694] | .0361 [.0250, .0470] |
| GPT-5.4 mini | .3271 | .4432 | .4962 | .1160 [.1066, .1252] | .1690 [.1615, .1765] | .0530 [.0423, .0637] |

### 4.2 Previous-rule-aligned errors and transfer verdict

The fourth primary test predicted that RuleBlindFull would incur fewer previous-rule-aligned errors than WSLSBudgeted. This pattern appeared only for GPT-5.5: Full − WSLS = −0.4692, 95% CI [−0.9077, −0.0308], Holm-adjusted p = .0369. GPT-5.4 mini showed a small difference in the predicted direction but an interval spanning zero: −0.1462 [−0.5385, 0.2231], adjusted p = .48515. Both Claude models showed significant effects in the opposite direction: Opus, +0.8308 [0.4231, 1.2385], adjusted p < .001; Sonnet, +0.5846 [0.1538, 1.0154], adjusted p = .0084.

| Model | Full previous-rule errors | WSLS previous-rule errors | Full − WSLS, 95% CI | Adjusted p | Frozen verdict |
|---|---:|---:|---:|---:|---|
| Claude Opus 4.8 | 6.0769 | 5.2462 | +0.8308 [0.4231, 1.2385] | < .001 | Opposite direction |
| Claude Sonnet 5 | 6.0231 | 5.4385 | +0.5846 [0.1538, 1.0154] | .0084 | Opposite direction |
| GPT-5.5 | 6.6385 | 7.1077 | −0.4692 [−0.9077, −0.0308] | .0369 | Pass |
| GPT-5.4 mini | 7.9308 | 8.0769 | −0.1462 [−0.5385, 0.2231] | .48515 | Inconclusive/fail |

Only one of four models satisfied all four primary tests. Under the frozen transfer rule, the accuracy–previous-rule-error trade-off therefore received the label no transfer. This label does not negate the replicated accuracy improvements; it rejects the stronger claim that RuleBlindFull reliably occupies a distinct, favorable trade-off point relative to WSLSBudgeted.

### 4.3 Mechanism controls

TrajectoryOnly redistributed outputs but did not improve accuracy. Its paired accuracy differences from RawLLM ranged from −.0064 to +.0017, and all four 90% intervals fell within the pre-specified ±.02 equivalence bounds. This result is important because the original feedback-free trajectory account predicted benefit without outcome information. In the current design, trajectory manipulation alone was insufficient.

RuleBlindFull outperformed YokedRandom in accuracy on every model, despite matched intervention timing. It also outperformed the NoVeto ablation. These secondary comparisons support the importance of action selection and veto logic, but they do not rescue the failed co-primary trade-off because WSLSBudgeted remained the stronger accuracy policy.

### 4.4 Safety and efficiency

Both co-primary supervisors produced positive mean net correction on every model. RuleBlindFull averaged 7.84 to 7.94 interventions per repetition and 4.18 to 4.51 net corrections. WSLSBudgeted averaged 8.26 to 9.00 interventions and 5.71 to 6.08 net corrections. Harmful overrides were nonzero for both policies and were generally higher under WSLSBudgeted, but its larger number of corrective overrides yielded the stronger net result.

WSLSUnlimited reached mean accuracies from .6169 to .7216 but used 15.22 to 21.11 interventions per repetition. It is therefore a descriptive high-intervention reference, not an information- or cost-matched competitor. OracleFull is also not a ceiling: it uses privileged rule information only within a frozen policy and reached .5244 to .6218 rather than the theoretical task maximum of 1.0.

### 4.5 Exploratory information-processing analyses

Post hoc analyses separated output diversity from task alignment. TrajectoryOnly substantially increased choice entropy while leaving accuracy equivalent to RawLLM, showing that a broader action distribution is not itself evidence of adaptive control. RuleBlindFull and WSLSBudgeted increased both diversity and accuracy, but WSLSBudgeted produced the larger task-aligned gain. Additional analyses of target-conditioned accuracy, mutual information, early recovery, and censored recovery time are descriptive because they were specified after confirmatory results were available. They should be reported as hypothesis-generating and not used to redefine the primary outcome.

### 4.6 Study 2b: minimal supervisor on fresh confirmatory streams

On the newly generated repetitions, RawLLM previous-rule-aligned errors were higher than the three-error headroom requirement on every model (10.04 to 10.96 per repetition), so the primary test ran confirmatorily on all four. P1 passed on every model: WCDMinimal reduced previous-rule-aligned errors relative to RawLLM by 5.23 (Claude Opus 4.8; 95% CI [−5.48, −4.96]), 4.98 (Claude Sonnet 5; [−5.28, −4.65]), 3.73 (GPT-5.5; [−4.12, −3.32]), and 2.01 (GPT-5.4 mini; [−2.32, −1.68]) errors per repetition, all Holm-adjusted p < .001.

S1 was satisfied on every model: the 95% confidence-interval upper bound of the WCDMinimal-minus-RuleBlindFull difference never exceeded 0.50 errors, well below the pre-registered 1.9917 margin. Under the frozen interpretation map, all four models therefore received the same verdict: the minimal scaffold suffices, and the protection stack is unnecessary on this endpoint.

| Model | Raw prev.-rule errors | WCDMinimal prev.-rule errors | RuleBlindFull prev.-rule errors | P1: WCD − Raw, 95% CI | S1: WCD − Full, 95% CI | Verdict |
|---|---:|---:|---:|---:|---:|---|
| Claude Opus 4.8 | 10.96 | 5.73 | 6.52 | −5.23 [−5.48, −4.96] | −0.78 [−1.19, −0.39] | minimal sufficient |
| Claude Sonnet 5 | 10.96 | 5.98 | 6.52 | −4.98 [−5.28, −4.65] | −0.54 [−0.93, −0.13] | minimal sufficient |
| GPT-5.5 | 10.63 | 6.90 | 6.83 | −3.73 [−4.12, −3.32] | +0.07 [−0.36, 0.49] | minimal sufficient |
| GPT-5.4 mini | 10.04 | 8.03 | 7.93 | −2.01 [−2.32, −1.68] | +0.10 [−0.28, 0.48] | minimal sufficient |

The labeled exploratory contrast sharpened the localization. WCDMinimal produced significantly fewer previous-rule-aligned errors than RuleBlindFull on exactly the two models where the Study 2 reversal had appeared (Opus: −0.78, adjusted p < .001; Sonnet: −0.54, adjusted p = .013) and did not differ on either GPT model. WCDMinimal was also more accurate than RuleBlindFull on all four models (+0.021 to +0.047, all adjusted p ≤ .0014) and exceeded every do-no-harm bound.

One structural result constrains the interpretation and is reported as found: under the frozen corner parameters, WCDMinimal's final choices were identical to WSLSBudgeted's on all 74,880 confirmatory condition-trials (the paired difference was exactly zero on every repetition), while differing from RuleBlindFull on 4,904 of 18,720 stream-trials. The calibrated minimal evidence-accumulation policy therefore reduced, in practice, to win-stay/lose-shift on these streams. Study 2b consequently does not demonstrate that decayed evidence scores add anything beyond WSLS in this regime; what it demonstrates is that removing RuleBlindFull's protection stack removes the reversal, and that nothing beyond a WSLS-equivalent policy was needed to do so.

## 5. Discussion

Sparse binary outcome feedback substantially improved memoryless LLM action streams under a nine-intervention budget. The effect was unusually consistent in magnitude across four held-out model generations: RuleBlindFull improved accuracy by roughly 12 percentage points, and WSLSBudgeted by roughly 16 points. Same-stream replay, schedule randomization, and separate per-model inference make this a stronger result than the earlier two-model, fixed-schedule development evidence.

The stronger mechanistic claim did not survive. RuleBlindFull was expected to trade some accuracy for fewer previous-rule-aligned errors than the simpler policy. That comparison succeeded only for GPT-5.5, was inconclusive for GPT-5.4 mini, and reversed significantly for both Claude models. The correct interpretation is therefore asymmetric: outcome-feedback supervision transferred as an accuracy intervention, whereas the proposed special trade-off did not.

The TrajectoryOnly equivalence result further narrows the interpretation. A supervisor can change the output distribution without making it more correct. In this task, the informative event was the delayed correctness outcome, not merely the existence of a patterned trajectory. This finding directly corrects the earlier “feedback-free cognitive control” framing.

The result also argues for strong baselines. WSLSBudgeted used the same information and budget as RuleBlindFull, was easier to describe, and achieved higher accuracy on every model. The more complex policy remains scientifically useful as a test of belief/veto dynamics, but it is not the default engineering recommendation on the evidence currently available.

Study 2b converts the reversal from an anomaly into a localized mechanism claim. If outcome-driven hypothesis tracking as such carried the cost, a minimal tracker should have reproduced it; instead, the minimal supervisor eliminated the excess previous-rule-aligned errors on both Claude models while remaining non-inferior everywhere else. The cost is therefore attributable to the protection stack — the veto window, rescue, and cooldown machinery whose parameters were tuned on an earlier model generation — and not to the use of correctness feedback. The empirical identity between the calibrated minimal supervisor and WSLSBudgeted strengthens the strong-baselines argument to its limit: on this task, the best information-matched policy we could confirm is behaviorally indistinguishable from win-stay/lose-shift, and every mechanism added on top of it either left the endpoint unchanged (evidence decay, at these parameters) or made it worse (the protection stack, on two of four models). Calibration selecting the most permissive corner of the grid points the same way: on the development streams, waiting longer and demanding larger evidence margins before switching only added cost.

Bayesian and resource-rational language can organize future work, but only at the level of analogy. RuleBlindFull maintains a compact belief-like state and reacts to unexpected outcomes; it does not compute a calibrated posterior or establish optimality. A future study could compare the frozen heuristic against an explicit Bayesian change-point observer under a common information and intervention budget.

## 6. Limitations

The task has only three categorical actions and externally defined block changes. Results may not transfer to open-ended language generation, continuous control, partially observable environments, or tasks in which delayed outcomes are noisy. Stateless single-turn generation improves isolation but is not representative of conversational deployment.

The public prompt added a direct answer-format instruction after the engineering pilot. That change was made and frozen before confirmatory data collection, but it limits exact comparison with archived model generations. Model APIs and provider defaults can also change; the study therefore records exact model identifiers, library versions, timestamps, and generation manifests.

The controller was developed on Study 1, including parameter search. Study 1 estimates are consequently exploratory and may be optimistic. Study 2 protects the main transfer test, but all additional information-processing analyses remain post hoc.

Study 2b has its own asymmetries. Its hypothesis was formed after the Study 2 results were observed, and its parameters were calibrated on the same archived corpus that shaped RuleBlindFull; the confirmatory status of Study 2b rests entirely on the newly generated streams and the externally timestamped freeze, not on any claimed independence of the hypothesis from prior results. The calibrated parameters sat at the boundary of the searched grid, and the resulting policy was behaviorally identical to WSLSBudgeted on every confirmatory trial. Study 2b therefore licenses a removal claim (the protection stack caused the reversal) and a sufficiency claim (a WSLS-equivalent policy suffices), but not the claim that evidence accumulation, waiting, or margin-based discrimination contribute anything measurable in this regime.

The conditions are information-matched only where explicitly stated. RuleBlindFull and WSLSBudgeted share feedback and budget. TrajectoryOnly lacks outcome feedback by design; WSLSUnlimited lacks a budget; OracleFull receives privileged information. Comparisons involving those references answer different questions and should not be presented as a single leaderboard.

Finally, behavioral regularities do not identify internal cognitive mechanisms. Terms such as “belief,” “control,” and “recovery” name components or observable sequences in the external scaffold. They do not establish phenomenology, neural equivalence, or human-like executive function in the underlying LLM.

## 7. Reproducibility, Data Integrity, and Security

The repository preserves immutable public streams, separately generated ground-truth schedules, replay outputs, trial-level and repetition-level results, paired-statistics tables, and SHA-256 manifests. Automated checks enforce the exact 4 × 130 × 8 × 36 trial grid, one-to-one repetition pairing, metric fixtures, controller blindness, parser behavior, hard intervention budgets, and refusal to overwrite existing repetition files.

Confirmatory statistics were rerun after provenance and security hardening and remained byte-identical. The hardening pass added secret and local-path scanning, credential-bearing remote checks, private-key detection, complete attempts-log hashing, least-privilege continuous integration, pinned action revisions, and retrospective generation-config labels for historical manifests. No API key, local `.env` value, personal workstation path, or credential is included in this manuscript package.

Study 2b extends the same discipline: the controller specification, calibration grid and selection rule, hypotheses, non-inferiority margin, interpretation map, and the complete replay and statistics code were committed and pushed under the study2b-freeze tag before any new stream existed, so no analyst degree of freedom remained once generation began. The schedule and stimulus extension to repetitions 131–260 was verified to leave all original files byte-identical, and the automated grid checks now enforce the additional 4 × 130 × 4 × 36 Study 2b grid alongside the original.

## 8. Conclusion

Binary correctness feedback can be converted into robust accuracy gains for memoryless LLM outputs with a small external intervention budget. That result replicated across four current model generations. The proposed special advantage of the more elaborate RuleBlindFull supervisor did not: a simple, information-matched WSLS policy was more accurate on every model, and the predicted error trade-off transferred to only one. A pre-registered follow-up on fresh streams then localized the failure: a minimal supervisor — behaviorally identical to the WSLS policy under its calibrated parameters — reduced previous-rule-aligned errors on all four models and removed the reversal that RuleBlindFull's protection machinery had produced on both Claude models. The revised contribution is therefore a bounded and reproducible pair of findings about sparse outcome-feedback supervision — the feedback is what helps, and the simplest information-matched policy is sufficient to harvest it — not a general claim of feedback-free cognitive control or a validated Bayesian mechanism.

## References

Binz, M., & Schulz, E. (2023). Using cognitive psychology to understand GPT-3. Proceedings of the National Academy of Sciences, 120(6), e2218523120. https://doi.org/10.1073/pnas.2218523120

Bishara, A. J., Kruschke, J. K., Stout, J. C., Bechara, A., McCabe, D. P., & Busemeyer, J. R. (2010). Sequential learning models for the Wisconsin Card Sort Task: Assessing processes in substance dependent individuals. Journal of Mathematical Psychology, 54(1), 5–13. https://doi.org/10.1016/j.jmp.2008.10.002

Chatterjee, A., Renduchintala, H. S. V. N. S. K., Bhatia, S., & Chakraborty, T. (2024). POSIX: A prompt sensitivity index for large language models. Findings of ACL: EMNLP 2024, 14550–14565. https://doi.org/10.18653/v1/2024.findings-emnlp.852

D’Alessandro, M., Radev, S. T., Voss, A., & Lombardi, L. (2020). A Bayesian brain model of adaptive behavior: An application to the Wisconsin Card Sorting Task. PeerJ, 8, e10316. https://doi.org/10.7717/peerj.10316

Goto, D., Idei, H., Shiozuka, Y., & Ogata, T. (2025). Performance of large language models and analysis of responses in the Wisconsin Card Sorting Task. 2025 IEEE International Conference on Development and Learning. https://doi.org/10.1109/ICDL63968.2025.11204408

Grant, D. A., & Berg, E. A. (1948). A behavioral analysis of degree of reinforcement and ease of shifting to new responses in a Weigl-type card-sorting problem. Journal of Experimental Psychology, 38, 404–411.

Hao, G., Alexandre, F., & Yu, S. (2025). Visual large language models exhibit human-level cognitive flexibility in the Wisconsin Card Sorting Test. arXiv:2505.22112. https://doi.org/10.48550/arXiv.2505.22112

Kennedy, S. M., & Nowak, R. D. (2024). Cognitive flexibility of large language models. ICML 2024 Workshop on LLMs and Cognition. https://openreview.net/forum?id=58yThpzlth

Kopp, B., Lange, F., & Steinke, A. (2021). The reliability of the Wisconsin Card Sorting Test in clinical practice. Assessment, 28(1), 248–263. https://doi.org/10.1177/1073191119866257

Lieder, F., & Griffiths, T. L. (2020). Resource-rational analysis: Understanding human cognition as the optimal use of limited computational resources. Behavioral and Brain Sciences, 43, e1. https://doi.org/10.1017/S0140525X1900061X

Miles, S., Howlett, C. A., Berryman, C., Nedeljkovic, M., Moseley, G. L., & Phillipou, A. (2021). Considerations for using the Wisconsin Card Sorting Test to assess cognitive flexibility. Behavior Research Methods, 53(5), 2083–2091. https://doi.org/10.3758/s13428-021-01551-3

Milner, B. (1963). Effects of different brain lesions on card sorting: The role of the frontal lobes. Archives of Neurology, 9, 100–110.

Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2024). Quantifying language models’ sensitivity to spurious features in prompt design or: How I learned to start worrying about prompt formatting. The Twelfth International Conference on Learning Representations. https://openreview.net/forum?id=RIu5lyNXjT

Steinke, A., Lange, F., & Kopp, B. (2020). Parallel model-based and model-free reinforcement learning for card sorting performance. Scientific Reports, 10, 15464. https://doi.org/10.1038/s41598-020-72407-7
