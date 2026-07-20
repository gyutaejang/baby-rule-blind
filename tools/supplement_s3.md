## S3. Controller pseudocode and frozen parameters

This section transcribes, in plain algorithmic English, the four theory-bearing supervisor controllers exactly as implemented in the frozen controller modules (`controller/base.py`, `controller/wsls.py`, `controller/rule_blind_full.py`, `controller/trajectory_only.py`, `controller/wcd_minimal.py`), together with the calibration grid and codified selection rule for WCDMinimal (`analysis/calibrate_wcd_minimal.py`). The pseudocode is intended to be sufficient for exact reimplementation; where any doubt remains, the repository code is authoritative.

### S3.1 Common interface and intervention budget

All controllers implement a single decision contract. On each trial, a controller receives exactly two inputs: (1) the *public trial*, consisting of the 1-based trial index within the session and the verbatim prompt text shown to the LLM (block numbers, within-block positions, lure flags, and anything else derived from the task schedule are deliberately excluded, because they would encode when the sorting rule changes); and (2) the LLM's parsed raw choice, one of `color`, `shape`, or `number`, or the empty string if the LLM's output was unparsable. The controller returns a *final choice*, which is immediately frozen: nothing the controller learns afterwards can change it, and all scoring happens outside the controller package.

Feedback-aware controllers (WSLSBudgeted, RuleBlindFull, WCDMinimal) additionally receive, after the final choice for the trial has been frozen and scored, a single Boolean stating whether that frozen final choice was correct. They never observe which dimension is currently rewarded — only the outcome of their own frozen choices. Feedback-free controllers (TrajectoryOnly) declare themselves as such, and the harness never delivers outcomes to them; if a harness bug ever attempted to, the base class raises an error rather than allowing information to leak silently. A continuous-integration check additionally rejects any occurrence of ground-truth-related tokens anywhere in the controller package, including comments.

Shared conventions, as implemented:

- **Hard intervention budget.** The three feedback-aware supervisors carry a hard budget of **9 interventions per 36-trial repetition** (25% of trials). An intervention is counted whenever the frozen final choice differs from the raw choice. Once the budget is exhausted, every remaining trial in the repetition passes through untouched. The budget enforces the supervisor regime as a hard constraint rather than a mean tendency. TrajectoryOnly has no intervention budget; its intervention rate is limited instead by its cooldown rule (S3.4).
- **Unparsable raw choices.** An unparsable raw choice (empty string) is never overridden by any controller: every intervention condition requires the raw choice to be one of the three valid dimensions, so an unparsable choice passes through as the final choice. When an unparsable frozen choice later receives an outcome, that outcome is attributed to no dimension and produces no state update (with one controller-specific exception for RuleBlindFull's window clock, noted in S3.3).
- **Fixed dimension order.** The three sorting dimensions are ordered `color`, `shape`, `number` throughout. This fixed order is public information (the prompt itself instructs the LLM to choose among these) and serves as the final, outcome-independent tie-breaker in every selection rule below.
- **Least-recently-tried bookkeeping.** Each feedback-aware supervisor records, per dimension, the trial number at which that dimension was most recently the frozen *final* choice (initialized to 0 for all dimensions). This record is used for outcome-independent tie-breaking. TrajectoryOnly keeps the analogous record over both raw and final choices (S3.4).

### S3.2 WSLSBudgeted

**Frozen parameters:** intervention budget = 9 per repetition (the study drivers pass this explicitly; a budget of "unlimited" defines the separate WSLSUnlimited player-regime reference, which is never a hypothesis-test target).

**State:** a *belief* dimension (initially none); a *shift target* dimension (initially none); the per-dimension last-tried trial numbers (all 0); an interventions-made counter (0); the pending frozen choice.

**Decision procedure (per trial):**

1. Record the current trial number. Initialize the final choice to the raw choice.
2. The budget is available if fewer than 9 interventions have been made in this repetition.
3. Let the *target* be the belief if one exists, otherwise the shift target (possibly none).
4. If the budget is available, the raw choice is a valid dimension, a target exists, and the raw choice differs from the target, set the final choice to the target.
5. If the final choice differs from the raw choice, increment the interventions-made counter.
6. If the final choice is a valid dimension, record the current trial number as that dimension's last-tried trial.
7. Freeze and return the final choice; remember it as the pending choice for feedback attribution.

**Feedback procedure (after the frozen choice is scored):**

1. Take the pending frozen choice and clear it. If it is not a valid dimension (unparsable), do nothing.
2. If the outcome is correct (*win-stay*): set the belief to the frozen choice and clear the shift target.
3. If the outcome is incorrect, and the frozen choice equals the belief, or no belief exists and the frozen choice equals the shift target (*lose-shift*): clear the belief, and set the shift target to whichever of the two other dimensions has the smaller last-tried trial number (i.e., was least recently a final choice), breaking ties by the fixed dimension order (`color` before `shape` before `number`).
4. If the outcome is incorrect but the frozen choice matches neither the belief nor the shift target (possible only when an intervention was blocked by the exhausted budget and a raw choice passed through), no state changes.

Note that before any feedback has arrived, both the belief and the shift target are empty and every trial passes through. While a shift target exists, the controller steers every parsed raw choice toward it until that target either succeeds (becoming the belief) or fails as the frozen choice (triggering a further shift).

### S3.3 RuleBlindFull

**Frozen parameters:** error streak to open the veto window = 1; veto window length = 4 trials; belief confirmation streak = 2; value gain = 0.30; value loss = 0.30; rescue failure threshold = 2; rescue cooldown = 6 trials; intervention budget = 9 per repetition. The NoVeto ablation is the identical class with veto window length = 0 (all other parameters unchanged), which disables all window-based intervention while leaving the rescue path active.

**State:** per-dimension estimated values in [0, 1] (all 0.0); a *believed* dimension (initially none); a *discredited* dimension (initially none); a correct-streak counter with its associated dimension; an error-streak-on-believed counter; per-dimension unresolved-failure counters (all 0); the remaining length of the currently open veto window (0); the remaining rescue cooldown (0); the per-dimension last-tried trial numbers (all 0); an interventions-made counter (0); the pending frozen choice. All state is inferred from outcomes of the controller's own frozen choices; the identity of the rewarded dimension is never observed.

**Decision procedure (per trial):**

1. Record the current trial number. If the rescue cooldown is positive, decrement it by 1 (this happens on every trial, including trials with unparsable raw choices, before any intervention check).
2. Initialize the final choice to the raw choice. The budget is available if fewer than 9 interventions have been made in this repetition.
3. *Veto-window intervention:* if the budget is available, a veto window is open (remaining window length is positive), the raw choice is a valid dimension, and the raw choice equals the discredited dimension, set the final choice to the best alternative excluding the raw choice (selection rule below). Choices of other dimensions pass through: the controller has no basis to judge them.
4. *Stuckness rescue* (checked only if step 3 did not fire): if the budget is available, the rescue failure threshold is positive, the rescue cooldown is zero, the raw choice is a valid dimension, and the raw choice's unresolved-failure counter is at least the rescue failure threshold (2), set the final choice to the best alternative excluding the raw choice, and set the rescue cooldown to 6. With the decrement in step 1, this means the earliest a subsequent rescue can fire is 6 trials after the previous rescue.
5. If the final choice differs from the raw choice, increment the interventions-made counter.
6. If the final choice is a valid dimension, record the current trial number as that dimension's last-tried trial.
7. Freeze and return the final choice; remember it as the pending choice for feedback attribution.

**Best-alternative selection (used by steps 3 and 4):** the candidate set is all dimensions other than the excluded raw choice *and* other than the currently discredited dimension (the discredited dimension is excluded because its estimated value, carried over from its successful streak, remains high right after it stops being rewarded, and a purely value-ranked choice would tend to remap into it — the exact perseveration this controller exists to reduce). If this candidate set is empty, fall back to all dimensions other than the excluded raw choice. (With three dimensions the fallback is unreachable in practice — excluding at most two distinct dimensions always leaves at least one candidate — but it is part of the implementation.) Among the candidates, choose the one with the highest estimated value; break ties by the smaller last-tried trial number (least recently tried as a final choice); break remaining ties by the fixed dimension order (`color` before `shape` before `number`).

**Feedback procedure (after the frozen choice is scored):**

1. Take the pending frozen choice and clear it.
2. If a veto window is open, decrement its remaining length by 1. The window clock ticks once per completed trial — including trials whose frozen choice was unparsable.
3. If the frozen choice is not a valid dimension (unparsable), stop: its outcome carries no attributable information about any dimension (no value, streak, or failure-counter update).
4. If the outcome is **correct**:
   - Increase the chosen dimension's value by 0.30, capped at 1.0.
   - Reset the chosen dimension's unresolved-failure counter to 0.
   - If the chosen dimension matches the current correct-streak dimension, increment the correct streak by 1; otherwise set the correct-streak dimension to this dimension and the streak to 1.
   - If the correct streak has reached the belief confirmation streak (2): set the believed dimension to this dimension (if not already), clear the discredited dimension, close any open veto window (set its remaining length to 0), and reset the error-streak-on-believed counter to 0. The system is treated as re-stabilized.
5. If the outcome is **incorrect**:
   - Decrease the chosen dimension's value by 0.30, floored at 0.0.
   - Reset the correct streak (dimension cleared, count 0).
   - Increment the chosen dimension's unresolved-failure counter by 1. Unresolved failures are cumulative: they are reset only by that dimension's own next correct outcome, never by intervening trials on other dimensions.
   - If a believed dimension exists and the chosen dimension equals it, increment the error-streak-on-believed counter. If that counter has reached the error streak to open (1) and the veto window length parameter is positive: demote the believed dimension to discredited (believed becomes none), reset the error-streak-on-believed counter to 0, and open the veto window with remaining length 4.

### S3.4 TrajectoryOnly

**Frozen parameters:** stuck threshold = 6 consecutive identical raw choices; cooldown = 4 trials. No intervention budget and no outcome feedback of any kind: the controller's only input is the raw-choice trajectory itself, so it can detect fixation but can never know whether that fixation is currently succeeding or failing.

**State:** the current streak dimension and streak length (initially none / 0); the remaining cooldown (0); per-dimension last-used trial numbers over both raw and final choices (all 0).

**Decision procedure (per trial):**

1. Update the repeat streak of the raw trajectory: if the raw choice is non-empty and equals the current streak dimension, increment the streak length by 1; otherwise set the streak dimension to the raw choice and the streak length to 1 if the raw choice is non-empty, or 0 if it is unparsable (an unparsable choice always breaks the streak).
2. If the cooldown is positive, decrement it by 1.
3. Initialize the final choice to the raw choice.
4. If the raw choice is a valid dimension, the streak length is at least 6, and the cooldown is zero: set the final choice to whichever of the two alternative dimensions has the smaller last-used trial number (least recently used), breaking ties by the fixed dimension order (`color` before `shape` before `number`); set the cooldown to 4; and reset the streak measurement to the forced switch (streak dimension = the new final choice, streak length = 1). With the decrement in step 2, the earliest a subsequent intervention can fire is 4 trials after the previous one.
5. If the raw choice is a valid dimension, record the current trial number as its last-used trial; if the final choice is a valid dimension, record the current trial number as its last-used trial as well (both the raw and the remapped choice are recorded).
6. Return the final choice.

Note that because the forced switch seeds the streak with the remapped final choice, a fixated model that keeps emitting the old raw choice on the next trial restarts the raw streak at 1, so a full further run of 6 identical raw choices is required before the next intervention (the cooldown of 4 is therefore usually not the binding constraint after a genuine fixation break).

### S3.5 WCDMinimal

**Frozen parameters:** decay = 0.5; switch margin = 0.0; wait threshold = 1; evidence score clip = 5.0 (scores bounded to [-5, +5]); intervention budget = 9 per repetition. The decay, switch margin, and wait threshold were selected by the codified calibration rule in S3.6; the score clip and the budget were fixed a priori and never searched (the clip bounds scores without interacting with the margin scale, and the budget is matched by design to the co-primary supervisors).

**State:** per-dimension evidence scores (all 0.0); an *active hypothesis* dimension (initially none); an error-streak counter for the active hypothesis (0); the per-dimension last-tried trial numbers (all 0); an interventions-made counter (0); the pending frozen choice. The information channel is identical to RuleBlindFull and WSLSBudgeted: post-freeze Boolean outcomes only.

**Decision procedure — ACT (per trial):**

1. Record the current trial number. Initialize the final choice to the raw choice. The budget is available if fewer than 9 interventions have been made in this repetition.
2. If the budget is available, the raw choice is a valid dimension, an active hypothesis exists, and the raw choice differs from the hypothesis, set the final choice to the hypothesis. While no hypothesis exists, everything passes through (the controller has no basis to steer). Unparsable choices pass through as in every supervisor.
3. If the final choice differs from the raw choice, increment the interventions-made counter.
4. If the final choice is a valid dimension, record the current trial number as that dimension's last-tried trial.
5. Freeze and return the final choice; remember it as the pending choice for feedback attribution.

**Feedback procedure — WAIT / CONSIDER / DISCRIMINATE (after the frozen choice is scored):**

1. Take the pending frozen choice and clear it. If it is not a valid dimension (unparsable), stop: no score decay and no update occur on that trial.
2. *CONSIDER:* multiply all three evidence scores by the decay factor (0.5). Then add +1 to the chosen dimension's score if the outcome was correct, or -1 if incorrect, and clip that dimension's score to the range [-5, +5].
3. If the outcome is **correct**: if no hypothesis exists yet, adopt the chosen dimension as the active hypothesis (the first success adopts the hypothesis); if the chosen dimension equals the active hypothesis, reset the error streak to 0. Then stop. (A correct outcome on a non-hypothesis dimension while a hypothesis exists — possible only after the budget is exhausted and raw choices pass through — updates that dimension's score in step 2 but changes neither the hypothesis nor the error streak.)
4. If the outcome is **incorrect** and the chosen dimension differs from the active hypothesis, stop: errors off-hypothesis say nothing about the hypothesis. (This branch also covers the no-hypothesis case, where errors accumulate evidence in step 2 but trigger nothing.)
5. *WAIT:* increment the error streak. If the error streak is below the wait threshold (1), stop and hold the hypothesis. (With the frozen threshold of 1, every attributed error of the active hypothesis proceeds to step 6.)
6. *DISCRIMINATE:* identify the best alternative — the non-hypothesis dimension with the highest evidence score, ties broken by the smaller last-tried trial number (least recently tried as a final choice), then by the fixed dimension order (`color` before `shape` before `number`). If the best alternative's score exceeds the active hypothesis's score by *strictly more than* the switch margin (0.0), switch the active hypothesis to that alternative and reset the error streak to 0. Otherwise keep the hypothesis; the error streak is *not* reset by a failed margin test and continues to accumulate.

### S3.6 WCDMinimal calibration grid and selection rule

The three searched parameters (decay, switch margin, wait threshold) were calibrated by an exploratory grid search implemented in `analysis/calibrate_wcd_minimal.py`, run exclusively on the 60 archived Study 1 streams (30 repetitions x 2 models) and frozen before any Study 2b confirmatory stream was generated. The selection rule was codified in the script before it was first run for selection, as follows:

1. **Objective:** minimize the pooled mean previous-rule-aligned error count over all 60 archived streams.
2. **Constraint (do-no-harm on the calibration corpus):** pooled mean accuracy must be greater than or equal to the pooled RawLLM (passthrough) mean accuracy on the same corpus, both values rounded to 4 decimals before comparison.
3. **Tie-breaking (fixed and deterministic, applied in order):** higher pooled mean accuracy; then smaller wait threshold; then larger decay; then smaller switch margin.

The same script also fixes the non-inferiority margin anchor from its own output by a pre-registered rule: Delta = 0.5 x |pooled mean previous-rule-aligned errors of RawLLM minus that of Full v1| on the calibration corpus, floored at 0.5 errors per 36-trial repetition.

The full 48-configuration grid (4 decay values x 4 switch margins x 3 wait thresholds; score clip fixed at 5.0 and budget fixed at 9 throughout) is reproduced below, with pooled means over the 60 archived streams. Columns: mean accuracy, mean previous-rule-aligned errors per repetition, mean interventions per repetition, and maximum interventions in any single repetition.

| Decay | Margin | Wait | Accuracy | Prev.-rule errors | Mean interv. | Max interv. |
| --- | --- | --- | --- | --- | --- | --- |
| 0.5 | 0.0 | 1 | 0.5523 | 8.5667 | 9.0 | 9.0 |
| 0.5 | 0.0 | 2 | 0.5102 | 10.55 | 9.0 | 9.0 |
| 0.5 | 0.0 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.5 | 0.5 | 1 | 0.5106 | 10.55 | 9.0 | 9.0 |
| 0.5 | 0.5 | 2 | 0.5102 | 10.55 | 9.0 | 9.0 |
| 0.5 | 0.5 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.5 | 1.0 | 1 | 0.5102 | 10.55 | 9.0 | 9.0 |
| 0.5 | 1.0 | 2 | 0.5102 | 10.55 | 9.0 | 9.0 |
| 0.5 | 1.0 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.5 | 2.0 | 1 | 0.3356 | 12.0667 | 5.15 | 9.0 |
| 0.5 | 2.0 | 2 | 0.3356 | 12.0667 | 5.15 | 9.0 |
| 0.5 | 2.0 | 3 | 0.3356 | 12.0667 | 5.15 | 9.0 |
| 0.7 | 0.0 | 1 | 0.5106 | 10.55 | 9.0 | 9.0 |
| 0.7 | 0.0 | 2 | 0.5102 | 10.55 | 9.0 | 9.0 |
| 0.7 | 0.0 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.7 | 0.5 | 1 | 0.494 | 11.6167 | 9.0 | 9.0 |
| 0.7 | 0.5 | 2 | 0.4935 | 11.6167 | 9.0 | 9.0 |
| 0.7 | 0.5 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.7 | 1.0 | 1 | 0.4657 | 12.6167 | 9.0 | 9.0 |
| 0.7 | 1.0 | 2 | 0.4657 | 12.6167 | 9.0 | 9.0 |
| 0.7 | 1.0 | 3 | 0.4648 | 12.6333 | 9.0 | 9.0 |
| 0.7 | 2.0 | 1 | 0.3796 | 16.5167 | 9.0 | 9.0 |
| 0.7 | 2.0 | 2 | 0.3796 | 16.5167 | 9.0 | 9.0 |
| 0.7 | 2.0 | 3 | 0.3796 | 16.5167 | 9.0 | 9.0 |
| 0.9 | 0.0 | 1 | 0.4671 | 13.0 | 9.0 | 9.0 |
| 0.9 | 0.0 | 2 | 0.4667 | 13.0 | 9.0 | 9.0 |
| 0.9 | 0.0 | 3 | 0.4403 | 13.9667 | 9.0 | 9.0 |
| 0.9 | 0.5 | 1 | 0.4343 | 14.5 | 9.0 | 9.0 |
| 0.9 | 0.5 | 2 | 0.4338 | 14.5 | 9.0 | 9.0 |
| 0.9 | 0.5 | 3 | 0.4097 | 15.3667 | 9.0 | 9.0 |
| 0.9 | 1.0 | 1 | 0.4329 | 14.5833 | 9.0 | 9.0 |
| 0.9 | 1.0 | 2 | 0.4329 | 14.5833 | 9.0 | 9.0 |
| 0.9 | 1.0 | 3 | 0.4079 | 15.4833 | 9.0 | 9.0 |
| 0.9 | 2.0 | 1 | 0.3653 | 17.1 | 9.0 | 9.0 |
| 0.9 | 2.0 | 2 | 0.3653 | 17.1 | 9.0 | 9.0 |
| 0.9 | 2.0 | 3 | 0.3653 | 17.1 | 9.0 | 9.0 |
| 1.0 | 0.0 | 1 | 0.4185 | 15.2 | 9.0 | 9.0 |
| 1.0 | 0.0 | 2 | 0.3931 | 16.1 | 9.0 | 9.0 |
| 1.0 | 0.0 | 3 | 0.3653 | 17.1 | 9.0 | 9.0 |
| 1.0 | 0.5 | 1 | 0.4185 | 15.2 | 9.0 | 9.0 |
| 1.0 | 0.5 | 2 | 0.3931 | 16.1 | 9.0 | 9.0 |
| 1.0 | 0.5 | 3 | 0.3653 | 17.1 | 9.0 | 9.0 |
| 1.0 | 1.0 | 1 | 0.3444 | 17.0167 | 9.0 | 9.0 |
| 1.0 | 1.0 | 2 | 0.3444 | 17.0167 | 9.0 | 9.0 |
| 1.0 | 1.0 | 3 | 0.3194 | 17.9 | 9.0 | 9.0 |
| 1.0 | 2.0 | 1 | 0.2718 | 18.7 | 9.0 | 9.0 |
| 1.0 | 2.0 | 2 | 0.2718 | 18.7 | 9.0 | 9.0 |
| 1.0 | 2.0 | 3 | 0.2718 | 18.7 | 9.0 | 9.0 |

The selected configuration (decay = 0.5, switch margin = 0.0, wait threshold = 1) lies at the most permissive corner of the searched grid — the strongest forgetting, the smallest switching margin, and the shortest wait — a boundary-selection fact disclosed in the pre-registered Study 2b plan.
