# Shared reserves and held-out shifts: checkpoints 8 and 9

Frozen November 9, 2026 before implementation and measurement. Development and holdout gate for a simulated policy; no action authority, subjective fear or final reserved test claim.

## Shared-reserve experiment

Two releases share one reserve of 7 or 8 resources (equiprobable), with independent equiprobable public completion values of 24 or 140 for each. The two values and reserve are visible from the start. Each task keeps the existing seven-tick deadline and cascade transitions. Carry integrity, faults **and unused reserve** into the second task; reset time and per-task counters only. Outage cancels remaining work. Charge only incremental resource spend in each task's existing score, so shared depletion is never double-counted. Completion and failure rates use two scheduled tasks.

The hidden low/high regime is initially equiprobable; shock probabilities are .08 and .38 with switch probability .20 between tasks. Three public precursor observations from the initial regime are drawn independently of the task tape. Action shocks are paired by subject, task and fast-attempt index. A policy sees public observations only, never regime, future shocks or shift label.

Use 512 paired IDs 112000–112511. Compare myopic Markov with exact two-task planning using fixed risk, the same fitted Markov (.20), the frozen recurrent fit 42 from report 14, and the same fit with state reset at each task start (no precursor retention). Continuations branch on public observations; only the horizon changes in the myopic vs lookahead Markov comparison. No refitting, changing objectives or selecting recurrent seeds on these checks. Same outcome model, action legality and score; report search work. Predeclared comparisons: two-task vs myopic Markov, Markov vs fixed at matched horizon, and recurrent vs both matched Markov and reset.

For each comparison, report paired bootstrap intervals over subjects (4,000 resamples, seed 28115). The development gate requires positive lower 95% score difference, completion lower bound at least −.02 and failure increase upper bound at most .01. Recurrent is eligible only if it clears both comparisons. Otherwise choose Markov if its lookahead clears the myopic comparison; otherwise keep the myopic reference and mark improvement unproven. Memory benefit is a separate claim: do not attribute lookahead gain to learned memory. Preserve report 14 as the verified-recall comparison; no claim of new recall superiority here.

Pre-measurement amendment after an engineering witness: include guarded lookahead Markov. At the start, use the same nominal model to integrate both the exact lookahead policy and the unchanged myopic policy over the pair. Choose lookahead only if expected score improves, expected completion falls by at most .04 tasks and expected failures increase by at most .02 tasks; otherwise run myopic for both tasks. Report fallback rate and all comparison work. These are model-based screening thresholds, not external permissions or safety bounds. The guarded arm also receives a predeclared comparison against myopic. Selection order: recurrent if it passes both matched comparisons and myopic; otherwise the unguarded Markov if it passes myopic; otherwise guarded Markov if it passes myopic; otherwise unchanged myopic. The guarded policy's fallback uses its integrated pair forecast for the shift gate. No measured pilot outcomes were inspected before this amendment.

## Independent shift validation

Freeze selected policy and source before generating check outcomes. Compare it to unchanged myopic Markov, with no tuning or knowledge of shift labels. 512 disjoint subjects per scenario:

| IDs | Scenario | Actual conditions |
|---|---|---|
| 113000–113511 | Nominal repeat | .20 switching, .08/.38 shocks, clean start |
| 114000–114511 | Volatile | .45 switching, .08/.38 shocks, clean start |
| 115000–115511 | Harsher hazards | .20 switching, .15/.52 shocks, clean start |
| 116000–116511 | Damaged start | .20 switching, .08/.38 shocks, integrity 2 and one unresolved fault |

Frozen policies retain their nominal assumptions. Use a paired bootstrap with 20,000 resamples (seed 28115); across four scenarios use two-sided Bonferroni-adjusted intervals for sixteen checks (four outcomes each). In each scenario require score difference lower bound ≥−2 points, completion-rate difference lower bound ≥−.02, failure-rate difference upper bound ≤.01, and upper bound on mean failure-count underprediction ≤.08 per campaign. The last check compares observed total terminal failures with the selected lookahead model's initial expected count, not probability of any failure. Myopic selection lacks a pair forecast and cannot pass this gate. All scenarios must pass for checkpoint 9 within this scope. This is an aggregate forecast stress check, not calibrated individual bounds or evidence of real safety. Also report shocks, propagation, repair, stops, and root forecast vs observed outcome. Do not reuse held-out outcomes for tuning. Reserved 20000–29999 untouched; smoke uses separate 117000-range IDs.
