# Guarded decision rehearsal v1

Frozen October 12, 2026 before measurement. This is an offline controlled task experiment, not learned risk qualification, realistic deployment, felt fear or an AACE test.

Pre-measurement clarification: include a public-feasibility careful-first rule as a stronger fixed comparator. This makes sixteen actors and 38,400 rehearsals. Minimum necessary task time is 3 seconds (fast processing with no harm); the predefined contexts need not activate urgency ordering. The constrained budget counts qualified guard forecasts only; three cheap experimental plan transforms, predictor work and retrospective audit calculations are recorded separately. Total computation is not matched.

## Question and scope

Can history-based estimates improve finite proposal ordering when decision work is limited? Separate predictor proposals from the unchanged external action permission. Test completion, irreversible outages, recoverable harm, recovery costs and unnecessary task avoidance. Compare with simple fixed-order controls, not just a weaker stateless neural baseline.

A v2 controlled probe supplies twelve public observations and a repaired-body cue query. Frozen estimators receive only that sequence. Its subsequent query label is ignored. A new independent event stream drives the actual workload. Danger is held constant during that workload at the probe's final latent cue probability. Thus cue danger changes in the history, not during the task itself. No estimator is updated from guarded actions in this pilot: their action-conditioned feedback is outside the prediction training scope.

## Workload and guard

Six work units; candidates are complete fast, complete careful, and preserve/abandon. Fast uses three operations of two work units; careful uses six operations of one unit. Processing costs are two/one resource units and one/two simulated seconds per operation respectively.

Underlying cue probability p is 0.05 or 0.65. Fast irreversible-outage probability per operation is 0.05p; careful is 0.005p. Independent recoverable-harm events have probability p / 0.1p and magnitude 0.15 / 0.05 respectively. Outage and harm use independent indexed random streams shared across actors. The provider never reads those future draws.

After successful processing, actual repair consumes two resource units and one second per 0.15 integrity restored, rounded up. Full-continuation guard forecasts reserve worst-case repair resources and time: fast processing+repair at most 6 seconds / 12 units; careful at most 14 seconds / 10 units. Capability returns to 1 on the non-outage path after repair. Expected encountered harm is scored separately from irreversible outage, conditional on survival, rather than disappearing because repair occurs.

Three public contexts: normal (18 resource units, 16 seconds), reserve pressure (14 units, 16 seconds), time pressure (18 units, 6 seconds). Same fixed decision objective and policy for every actor: task value 30, harm cost 12, outage cost 40, time cost 0.1, full-plan outage limit 0.05, reserve 3, minimum capability 0.15, urgency slack 2. The existing `DecisionEngine` and `ActionAuthority` make the final choice and handoff. Its urgency ordering and stop/stale/deadline checks remain in force.

The **analytic guard has privileged access to latent p** in this constructed simulator. It knows declared transition laws, not future noise. This is a labeled oracle guard, not a qualified learned forecaster or realistic safety certificate. Experimental probabilities cannot replace its evidence. Guard benefit and proposal benefit must not be conflated.

## Proposal controls

Frozen v2 GRU and summary MLP from each fitted seed; counts, forgetting, recent window, change detector and known-law Markov/Bayes settings from the v2 selection record; constant training-event prevalence; always-fast-first, always-careful-first and always-preserve-first controls.

Public-feasibility careful-first checks worst-case time/resource requirements without any probability estimate. It prefers a structurally feasible careful plan, then fast, then preserve. It receives no latent cue state or retrospective audit result.

Estimated probabilities are experimental. Estimate plan scores and constraints with the common public task context and declared action transforms. Rank estimated-admissible plans before estimated-rejected plans, sorting each group by the same objective. This ranks search proposals only and cannot apply an action. Record estimated ordering separately from actual guard evaluation ordering, including urgency overrides. Fixed-order controls have no predictive advantage or probability requirement.

One forecast permits only the first evaluated plan. Three forecasts evaluate all alternatives; complete evaluation should remove ordering differences when there is no interruption. An abstention means no action applied and ends this one-choice rehearsal separately from explicit abandonment. An independent retrospective oracle audit identifies whether a task was feasible, and counts missed feasible tasks; its calculations are recorded separately and never fed to the actor.

## Frozen pilot and interpretation

100 new paired episode seeds [16000,16100), four cue-history conditions (stable, extinction, reversal, recurrence), three public resource/time contexts and budgets of one/three forecasts. No training or model selection is performed. These seeds are distinct from v1/v2 measured groups and avoid reserved [20000,30000) final-test seeds. Fifteen actors: six fitted learned heads, five simple history controls, one constant prior and three fixed orders. Non-learned controls run once, not duplicated as independent fitted seeds.

36,000 finite one-choice rehearsals. Retain per-episode results and replayable example traces, dataset/model hashes, source identity, forecast/prediction work and CPU timing. Whole-pilot limits: 180 seconds, 1,024 MiB sampled process memory, two PyTorch threads. Checks are cooperative. No real services/files/devices are controlled; no paid resources.

Report completion and failure separately from abandonment/abstention, encountered harm even after repair, resource use, repair cost, time, missed feasible tasks, guard rejections, urgency overrides and forecast calls. Confidence intervals resample paired episode IDs, with learned fitted-seed variability separate. Do not optimize on these checks or choose a winning actor separately per condition for deployment.

The guard's privileged information, fixed danger within a task, artificial prelude repair, short open-loop plans and frozen estimators limit conclusions. Better ordering is not a learned survival policy, calibrated risk, emotional experience or qualified counterfactual memory. If an always-careful control matches learned proposals, report that directly.
