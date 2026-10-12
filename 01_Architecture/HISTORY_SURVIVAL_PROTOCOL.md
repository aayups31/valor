# Repaired-body history probe v1

Protocol frozen October 12, 2026 before its development pilot. This is a small predictive benchmark, not an autonomous survival policy, AACE comparison or test of subjective feeling.

## Question and scope

After complete repair, can learned recurrent state anticipate a repeated harmful encounter from public history? Does it outperform simpler controls with the same history? A repaired body removes current damage as a shortcut. This isolates predictive memory; task completion, courage, action coupling and counterfactual reflection are later tests.

Each episode has two visible cues. One is randomly assigned a 0.65 probability of damage; the other has probability 0.05. Assignment is hidden and randomized independently per episode. Twelve controlled encounters produce observed damage or no damage. Each encounter spends one resource unit; damage reduces integrity by 0.25 and costs two units to repair. The test harness performs repair and external replenishment before the next encounter. This intervention deliberately restores identical body/resource variables; it is not free recovery in a mission environment. Cumulative recovery cost remains in the audit record.

Thirteen public rows comprise twelve post-encounter observations and one pre-action query. Six features are cue A/B indicators, observed integrity loss, an exposure-completed flag, integrity and resource fraction. The query contains no future outcome: health and resources are 1, harm and exposure-completed are 0. The target is observed damage from a new query encounter. Episode seeds, latent cue assignment, labels and analytic reference probabilities are not inputs. No actual future noise is observed by the predictors.

## Conditions and splits

- Stable: cue assignment persists through history and query. This is the only training/selection condition.
- Extinction: the last four encounters and query use probability 0.05 for both cues. This is an unseen development shift, not learned extinction.
- Reversal: the last four encounters and query swap dangerous/safe cue roles. This is an unseen development shift.
- Episode seed intervals: train [0, 10000), selection [10000, 11000), separate development check [12000, 13000). Final-test episodes remain reserved. Each condition uses the same check seeds for paired shift inspection.

Data are bounded, deterministically reproducible and hashed. Check episodes cannot select checkpoints. Report per-episode scores, observed event counts and recovery costs. Shift conditions cannot be collected as training or selection under v1.

## Controls and budget

1. Stateless MLP: query row only.
2. History linear head: the exact flattened public sequence.
3. History MLP: the exact flattened sequence, fourteen hidden units.
4. GRU: six inputs, sixteen recurrent units, one event head. Recurrent state has 16 float32 values, 64 bytes; this excludes weights, runtime and other input storage.
5. Simple cue counts: Laplace-smoothed damage/exposure counts for the query cue, using the same observed history without training.
6. Public-history Bayes reference: knows v1's two cue probabilities and stable assignment law, but observes only the same history. It is a strong known-law reference, not a learned model with equal prior knowledge; under shifts its stable assumption is intentionally wrong.
7. Constant training event rate and privileged hidden-state probability reference. The hidden-state reference is a scoring upper-reference, not a fair learner.

Learned controls share data, minibatch order, update opportunities, optimizer rate 0.001 and checkpoint selection by selection log loss. All start with the same training-event prior at their output head; epoch zero is eligible. History MLP and GRU have similar parameter counts (1,121 / 1,169), but identical updates do not equalize total computation. Record all counts, wall time, sampled process memory and inference timing. CPU only, two threads by default, explicit cooperative wall/memory limits. No paid resources.

Frozen pilot: 3,000 training / 500 selection / 500 check episodes per condition; training seeds 42, 43, 44; 25 epochs maximum, batch size 128, at most 120 seconds and 1,024 MiB sampled process memory per training run. Do not change the recipe to improve check results in this pilot.

## Measurements and interpretation

Brier score, log loss, reliability bins, error relative to hidden-state probability and shuffled-history ablation. Bootstrap uncertainty resamples episode scores, with training-seed variability reported separately. The check is development evidence, not a final significance test. Predictions remain experimental and cannot authorize actions.

A GRU beating stateless prediction only shows that history helps in this constructed task. It must beat equally informed simple controls to support a recurrent-model advantage. A failure under extinction/reversal is a reported limitation. Neither outcome proves fear, improved survival behavior, calibrated individual risk or AACE's counterfactual-memory hypothesis.
