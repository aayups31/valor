# Adaptive repaired-body history probe v2

Frozen October 12, 2026 before the v2 pilot. V1 artifacts, recipe and negative result remain unchanged. This is a new development task, not a final test, autonomous survival policy, calibrated risk bound or subjective-feeling experiment.

## Question

Can anticipation adapt when cue danger changes? Compare learned recurrence against equally informed count summaries, forgetting, recent windows and change detection. V1 showed that plain cue counts beat its recurrent recipe; the next experiment strengthens controls and trains on changes rather than presenting them only as untrained shifts.

## Task and data

Keep v1's two cues, twelve encounters, six public features, damage magnitude 0.25, probabilities 0.05/0.65, controlled full repair/replenishment, recorded recovery costs and a final pre-action query. Query body variables are identical and contain no future event. Metadata, regime names, change times, seeds and reference probabilities are never predictor inputs.

Stable, extinction and reversal conditions are uniformly mixed in training and selection. Extinction switches both cues to low probability; reversal swaps dangerous cue roles. Change time is independently drawn from encounter indices 4 through 9. Fixed-condition development checks include stable/extinction/reversal and **recurrence**, which becomes safe at indices 4–6 and restores original cue danger at indices 9–11. Recurrence is absent from training/selection; it is a separate unseen transition pattern. All schedules are hidden. Random draws for cues/events are shared across check conditions for paired inspection.

Use new episode groups: train [3000, 9000), selection [11000, 12000), check [14000, 15000). The frozen pilot uses 3,000 / 500 / 500 episodes respectively, with four paired check conditions. These do not overlap v1's actually used groups. The repository's reserved test range [20000, 30000) remains untouched. Conditions/schedules are audit metadata only.

## Learned controls

Retain v1's stateless MLP, full-history linear head, full-history MLP and sixteen-unit GRU unchanged. Add a ten-feature **summary MLP**: query-cue exposure count and smoothed event rate, recent-four query-cue count/rate, other-cue whole/recent rates, whole-history harm rate, query cue and current body/resource fractions. All summaries are computed from the same observed sequence. Feature engineering is an explicit strong control, not privileged information.

Same data, minibatch order, output-prior initialization, optimizer rate 0.001, update opportunities and selection-epoch rule. Epoch zero remains eligible. Report different parameter counts and computation; matching updates does not match total work.

## Simple adaptive controls

Use the training query-event prevalence as the public training-only Beta prior mean. Choose each family's setting by **selection log loss only**, with no check access:

- Cue counts: prior strength 1, 2 or 4; three candidates.
- Forgetting counts: global encounter-age decay 0.5, 0.75, 0.9 or 1.0, crossed with prior strength 1, 2 or 4; twelve candidates.
- Recent-window counts: last 2, 4, 8 or 12 encounters, same three strengths; twelve candidates.
- Two-sided per-cue cumulative-residual detector: thresholds 0.75, 1.25 or 2.0, drift 0.05, prior strength 2. Reset only the encountered cue's counts and residuals after detection, retaining the triggering event; three candidates. Detector is a hand-specified control, not a statistical alarm guarantee.
- Public-history Markov/Bayes reference: three hidden regimes (cue A danger, cue B danger, both safe), uniform initial prior, known task probabilities. After each observed encounter, transition mass 0, 0.05, 0.15 or 0.3 to the other regimes; select among four settings. This reference knows the likelihood law but not actual schedules or hidden states. It is an informative known-law reference, not an equally uninformed learner or exact task oracle.

Record all candidate scores, settings, selection opportunities and measured control selection work. Learned heads have 26 checkpoint opportunities versus each simple family's stated grid; no claim of equal hyperparameter-search computation is made. Retain constant training prevalence and the privileged hidden-state probability scoring reference.

## Pilot and interpretation

Fitted seeds 42, 43, 44; maximum 25 epochs, batch size 128, two CPU threads, 120 seconds and 1,024 MiB sampled process memory per fit. Freeze these settings before measuring the checks. Record Brier, log loss, reliability bins, prediction error versus the hidden-state reference, paired episode intervals, fitted-seed variability and shuffled-history ablations for GRU/history/summary MLPs. Record batch-amortized inference work separately from training.

An improvement over v1 is not an apples-to-apples model comparison: training distribution, episode groups and controls have changed. A recurrent advantage requires outperforming these stronger history controls within v2; a good predictor alone is not a fear policy. Recurrence must be reported separately, including overreaction after safety and missed danger after return. Keep predictions experimental and outside action authority. Causal task completion/avoidance/damage comparisons and qualified counterfactual memory remain later work.
