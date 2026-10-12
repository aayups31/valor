# Public-history action-conditioned continuation pilot v1

Frozen October 12, 2026 before implementation and measurement. This is a development forecasting experiment, not a qualified safety model, subjective fear or AACE test.

## Question

Can a small learned model predict the observed consequences of a specific complete action from public history and context? Does history improve over a strong context/action empirical table and known-law public-history controls? Test catastrophic event forecasting separately from easy completion averages. Prediction quality is not permission to execute.

## Fixed task and information

Reuse guarded-work-rehearsal-v1 unchanged: repaired starting body, twelve adaptive public encounters plus query, fast/careful processing then repair, six work units, independent indexed outage/harm streams and normal/reserve/time contexts. Danger remains fixed during processing. Run both actions directly in the controlled data harness, including structurally unsuitable actions, to observe deadline endings. This is an offline simulator intervention, not worker authorization. Preserve has deterministic no-work consequences and is excluded from learning.

Each subject has six paired context/action records. Public model inputs: the 13-by-6 observed sequence; quota/18, deadline/16, and two action indicators. Latent probability, hidden schedule, episode identity, future query label, outcome and future draws are excluded. Outcome labels are supervised targets, never model inputs. Actual task noise is separate from history/query generation.

Output: a four-class distribution over completed, irreversible outage, deadline missed and resource exhausted; probability of any observed harm; expected progress/6, harm/0.45, recovery resources/6, total resource use/12, elapsed seconds/14 and final integrity. Actual early termination determines targets. These bounded predictions describe a whole finite continuation, not a stepwise general world model or a video generator.

New episode ranges: training 40,000–42,999 (3,000 subjects, mixed stable/extinction/reversal); selection 50,000–50,499 (500 mixed); check 60,000–60,499 (500 paired subjects per stable/extinction/reversal/recurrence condition). Thus 18,000 train, 3,000 selection and 12,000 check action records. Reserved final-test [20,000,30,000) stays untouched. Check subjects repeat across conditions and contexts; do not claim 12,000 independent check trials.

## Frozen learned controls and work

Three fitted seeds 42/43/44. Compare linear summary/context head; summary MLP with 24 hidden units; recurrent 16-unit GRU followed by a 24-unit context/action MLP. Summary features are the existing ten public-history features. Shared 11 outputs, Adam learning rate 0.001, 20 epochs, batches of 128 subject clusters. All six contexts/actions from each subject share a batch. Each model gets 480 update opportunities, identical subject order and epoch-zero eligibility. Neural representation, parameters and latency are not equalized.

Initialize output weights to zero and biases to global training terminal prevalence (clipped 1e-4), harm prevalence, and six continuous means. Loss is terminal cross entropy plus binary harm cross entropy plus mean squared error over six normalized quantities. Select each head by the same combined loss on selection only after complete epochs; no check-dependent retuning. Per-fit caps: 120 seconds, 1,024 MiB sampled process memory, two CPU threads, cooperative checks. Fail/retain partial work rather than calling an incomplete recipe a completed frozen fit.

## Strong references

Training-only context/action empirical means and outcome frequencies are the primary stateless comparator (six public cells). Public-history known-law controls use all cue-matched counts or recent-four counts, each with Beta(1,1) smoothing, and exact integration of declared processing/repair equations. A latent-probability known-law reference is privileged and used only for auditing/scoring. No control settings are tuned on checks. Count predictor inference, exact-law work and fitted updates separately.

## Evaluation and qualification

Report terminal Brier/log loss, outage Brier/log loss, any-harm Brier/log loss, normalized continuous RMSE and per-quantity errors, stratified by history condition and action/context. Keep forecast-versus-observed bias visible. Paired intervals compare subject-averaged model loss with the primary stateless control while retaining all six records together; fitted-seed variation remains separate.

Fixed outage reliability bins: [0,.01,.025,.05,.1,.25,.5,.75,1]. Assess bins separately per condition/context/action, where subjects are independent. Record event counts, mean predictions and Wilson 95% intervals on observed event frequency; fewer than 100 subjects is insufficient descriptive support. Intervals are population-bin descriptions, not per-query upper bounds, cross-domain calibration or protection against distribution shift.

Every checkpoint and exported preview remains `decision_ready: false`. Qualification report must identify absent per-query risk bounds, applicability/shift evidence and approved model registration. Forecast wrappers use experimental evidence and unknown failure upper bound; the existing core must refuse to authorize them. Do not replace the privileged guard this turn regardless of scores. Previews identify the action, public context, model/data provenance, expected outcomes, scope and unavailable uncertainty; observed examples are separate.

Store immutable hashed public/target arrays and separate audit metadata, frozen settings, source identity, retained weights, prediction arrays, per-subject metrics and resource ledger. Run one recipe, publish unsuccessful results, no paid API/cloud resources. The main premium UI remains unchanged until these predictions earn a clearly labeled integration.
