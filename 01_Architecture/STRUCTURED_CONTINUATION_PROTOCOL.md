# Structured consequence pilot v2

Frozen October 12, 2026 before implementation and measurement. This repairs the representational flaw observed in report 11; it is not a new claim of felt fear, calibrated authority or AACE advantage.

## Question and scope

Can learned public-history mixture weights yield coherent whole-plan predictions with useful proper scores? Compare with physics-matched simple controls, not just the flawed eleven-output heads. Supplied transition equations and two possible danger levels are explicit prior knowledge, not discovered world dynamics.

Reuse v1's immutable 3,000 training and 500 selection subjects and their observed six context/action targets. Never use latent danger, schedules, IDs or future query labels as learning inputs or targets. Reuse the three frozen v1 black-box fits as labeled historical references, without retuning them. Evaluate every actor on **new 80,000–80,499 subjects**, paired across stable/extinction/reversal/recurrence and all six context/action interventions. This is 12,000 action records from 500 paired IDs. Old 60,000 checks informed this new recipe and are not confirmation data. Reserved [20,000,30,000) final-test seeds remain untouched.

## Structured representation

The domain supplies exact distributions/moments for each declared action/context at danger 0.05 and 0.65. Predict one mixture weight w in [0,1] from the public 13-by-6 history. Each forecast is (1-w) times the low-danger consequences plus w times the high-danger consequences. This mixes possible outcomes before computing expectations; applying physics only to an average danger estimate is a separate plug-in control and can differ because laws are nonlinear.

Completed/outage/deadline/resource probabilities, harm probability and six expected quantities must be derived from the same mixture. Known task support and linear moment bounds then hold by construction. This is coherent only within the declared fixture; it does not provide a per-query epistemic upper bound, discover unknown dynamics, represent arbitrary cascading harm, or cover resource exhaustion absent from these data.

## Frozen fits

Fitted seeds 42/43/44. Four heads: learned constant logit (1 parameter), ten-feature summary linear head (11), 14-hidden-unit summary MLP (169), and 16-unit GRU (1,169). All initialize w=0.5 with zero output weights/bias. Use the same ten public summaries as v1 for summary heads; GRU sees the same sequence. Registered decoder tensors are audited buffers, not learned parameters.

Adam 0.001, twenty epochs, subject batches 128, all six paired plans in each batch, 480 updates per model, epoch-zero eligibility. Composite loss is terminal cross entropy plus binary experienced-harm cross entropy plus mean normalized quantity MSE, with probabilities clipped at 1e-7 only for scoring. Select after complete epochs using selection only. Per fit: 120 seconds, 1,024 MiB sampled process memory, two CPU threads, cooperative checks; retain incomplete work as partial rather than silently changing the recipe.

## Comparisons

Include the learned constant with matched decoder/data/updates as the primary control. Include all-count and recent-four cue likelihood mixtures under fixed Beta-state prior 0.5: observed cue damage likelihood uses p=0.05 versus 0.65, with no hidden schedule access. These stationary-window likelihood references are not exact posteriors under changing danger. Include v1 known-law smoothed-count plug-in controls and context/action empirical table. Retain all nine frozen black-box heads. A latent-law reference remains privileged audit-only.

Match information where possible and disclose added declared physics. Record model parameters, decoder provenance, fitted updates, inference and reference work separately. Historical raw heads lack structural decoder knowledge, so their difference is not evidence that a neural mechanism became more intelligent or emotional.

## Evaluation and gates

Use existing terminal/outage/harm proper scores, quantities, per-condition/context/action reliability bins and public-law audits. All structured actors must have zero contradictions in tested contexts; failure blocks a completed pilot report. Compare subject-averaged composite losses against the corresponding fitted constant with paired bootstrap intervals preserving six contexts/actions per ID, separately by condition/fit. These exclude fitted-seed uncertainty. No check-dependent recipe retry or actor selection for deployment.

Checkpoint gates validate the decoder against canonical declared-law buffers, capacities, settings, data hashes and weights. All models/previews retain `decision_ready: false`, unknown per-query upper bounds and absent shift qualification. Existing action authority and main UI remain unchanged. Export a predicted branch example with consistency findings and a separately labeled observed outcome; no arbitrary trajectory or all-futures claim.

Preserve v1 data/weights/results. Engineering smoke uses v1's separate small fit cohort plus new 81,000-range checks; it is not the frozen research pilot. Offline CPU only, external spend $0, no real tools/services or deployment.
