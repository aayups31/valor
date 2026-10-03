# AACE execution roadmap and decision gates

Proposed October 2, 2026. This plan schedules work; none of its experiments, interviews or gates have been completed. Read with the [assessment](../PROJECT_REVIEW_AND_WORKING_PLAN.md) and [build specification](../01_Architecture/BUILD_SPECIFICATION.md).

**Current implementation authority:** the [reviewed implementation master plan](../IMPLEMENTATION_MASTER_PLAN.md) provides the current laptop, $0 external-spend defaults, transparent-demo scope and dependency order. The day ranges below are the earlier planning envelope; they are not runtime or completion promises. Its steps 0–10 are the agreed research/demo deliverable; external comparisons and commercial discovery are conditional extensions.

## Aim and planning assumptions

Use a 90-day window to decide whether one AACE mechanism deserves further investment. The primary hypothesis is that verified counterfactual memory lowers recurrence of avoidable catastrophic decisions after limited exposure, compared with equally resourced alternatives, without materially harming task completion.

Assume an experienced practitioner with roughly 400–600 working hours available over this window, access to a development computer, and optionally one training GPU. A second reviewer should independently inspect the protocol/results before a major commitment; this is a recommended future role, not delegation already performed. If foundational study or unavailable hardware consumes the window, narrow the deliverables and retain the spending cap. Do not redefine an inconclusive experiment as success.

Use days relative to actual kickoff, not calendar promises. Default external compute/API/hosting spend is $0. Profile bounded local CPU runs on the user's computer before allocating steps, seeds and episode counts. Track simulation, planning, training and reflection work; checkpoint at configured time/step/memory limits. No paid GPU-hour allocation is part of the current plan.

## Work sequence

| Window | Work and owner role | Concrete artifact | Exit criterion |
|---|---|---|---|
| Days 1–7 | Research owner: freeze scope, authority semantics, candidate support and primary metric; reproduce one simple baseline; test reference-stack compatibility | Protocol draft, dependency locks, source/claim chart, first runtime measurements | A repeatable baseline works; resource estimates and observation permissions are explicit |
| Days 8–21 | Simulator owner: implement rover, persistent damage, mission contexts, snapshot/RNG restore and scenario generator; reproduce PPO/SAC and a constrained reference | Environment package, invariant checks, baseline report, split manifests | Environment replay and predicates pass; reference performance is stable; no-op has real consequences |
| Days 22–35 | Research owner: fixed-budget planning, oracle branches, plain episodic memory and qualified counterfactual memory | Verified planning/reflection wiring and failed-case report | Oracle branch comparisons are valid; do not require memory to beat perfect dynamics. Test its incremental value under learned-model predictions next |
| Days 36–49 | Modeling owner: learned vector dynamics/hazard forecasting, validation calibration and withheld counterfactual branch evaluation | Forecast-quality report, learned-model ablation, evidence/abstention thresholds | Useful ranking/calibration survives model error; otherwise retain advisory oracle analysis only |
| Days 50–63 | Research owner: uniform/prioritized replay adaptation, counterfactual replay without persistent memory, contextual-risk control; optional mode/compute experiments | Component ablations and data/compute ledger | Claimed benefit cannot be explained by extra data, updates, candidate coverage or planning work |
| Days 64–77 | Evaluation owner: locked family/appearance/dynamics shifts, paired mission stakes, scar contradictions; adapt strongest feasible world-model reference | Final comparative tables, calibration/Pareto plots, latency report | Final primary/guardrail gates pass; missing strong comparisons are plainly recorded |
| Days 78–90 | Research/product owner: clean reproduction, external review, customer-workflow synthesis, go/narrow/stop memo | Reproduction package, selected incident report, decision memo | Another person can reproduce the result; next investment follows the evidence |

If commercial exploration is later chosen, the earlier proposal was 5 interviews by day 21, 10 by day 49, and 20 by day 77. These interviews are not a requirement for the agreed research/demo build. The business gate requires actual access to replayable examples and a defined pilot outcome, not just completing the interview count. No outreach has been sent during this review.

Attempt SafeDreamer environment/checkpoint smoke tests in the first two weeks to expose integration risk early, but do not let an older dependency stack block the lightweight mechanism test indefinitely. Reserve later time to adapt and train the appropriate reference under the same observation/safety specification. Reproducing a standard task is a prerequisite; a published result on a different task is not a comparison against AACE.

Do not spend days 50–63 on modes or adaptive compute if the primary memory result is weak. Investigate only one secondary feature that addresses a demonstrated failure. The roadmap is a dependency-driven research sequence, not an obligation to add every proposed feature.

## Baseline and ablation matrix

Use one common actor family within each comparison and the same permitted observations, health/stakes inputs, mission utility, training scenarios and guard configuration. Each method gets its own fair validation tuning budget. Record implementation identity; a simplified recovery controller or intrinsic-fear analogue is not an exact reproduction of the cited method.

| Method | Question answered | Required stage |
|---|---|---|
| Heuristic return-to-depot controller and nominal SAC | Is the task meaningful and solvable? | Environment development |
| SAC with tuned damage/catastrophe penalties | Does ordinary reward shaping explain the result? | First memory experiment |
| Constrained/Lagrangian reference, using a validated implementation | Is the improvement beyond an expected-cost constraint? | First serious comparative result |
| Fixed-budget risk-aware planner with shared candidates | Does the memory merely supply extra planning? | First memory experiment |
| Same planner with expanded/random/optimized candidate search | Does improved candidate coverage explain memory gains? | First memory experiment |
| Plain episodic nearest-neighbor retrieval | Is storing context and a response sufficient? | First memory experiment |
| Intrinsic-fear analogue and recovery-controller reference | Do catastrophe prediction or recovery explain the result? | Comparative/ablation stage |
| Context-conditioned risk/CVaR control | Can a conventional method handle urgency and inaction equally well? | Before a deliberate-risk claim |
| Uniform replay, prioritized replay and counterfactual replay without persistent scars | Is the benefit ordinary data reuse or extra synthesized transitions? | Adaptation stage |
| Full proposed memory versus no memory, factual-only memory and shuffled-context memory | Does qualified counterfactual content and retrieval matter? | Memory and final evaluation |
| Fixed compute versus threat-conditioned compute; continuous versus discrete gate | Do these optional mechanisms add value? | Only after a positive core result |
| SafeDreamer or an equivalently strong adapted safe-world-model method | Is the full learned architecture competitive? | Before a full AACE research claim |
| PIGDreamer/asymmetric reference if privileged training information is used | Does simulator information explain the advantage? | Required for that privileged-data claim |

A best-baseline checkpoint is selected using validation criteria, not whichever test result makes AACE look favorable. Publish all resource-matched primary references and their frontiers rather than comparing one badly tuned penalty with one tuned AACE.

## Primary experimental protocol

First run a frozen-actor mechanism arm, then a separately labeled equal-update adaptation arm. This avoids pretending prioritized replay can change a frozen policy without training.

In the frozen-actor arm, every method receives the same archived simulator incident, permitted observation history and mission specification. Learned weights stay fixed. Compare fixed planning, stronger candidate search, plain episodic retrieval and qualified counterfactual retrieval. Methods that query branches receive matched branch budgets and snapshot access. If a stronger fixed planner solves the task within the budget, there is no demonstrated need for memory in that setting.

In the adaptation arm, initialize from the same pre-exposure training regime, provide one or three matched incident exposures, and give every method the same gradient-update allowance. Compare uniform replay, prioritized replay, model/counterfactual augmentation without a scar store, and the proposed memory. Match actual transitions and generated branch evidence, and record when exact matching is impossible. AACE cannot claim a one-event advantage after receiving hundreds of unreported synthetic failures.

Freeze all adaptation before recurrence evaluation. Reset the simulator between episodes while preserving the appropriate post-exposure model/memory checkpoint. Evaluate on new seeds and related scenarios whose manifests were withheld from tuning. Measure recurrence on benign/ordinary mission cases where catastrophe is avoidable under the common action/constraint specification. Analyze authorized machine-sacrifice cases separately.

## Acceptance gates

All numerical thresholds below are **proposed planning thresholds**, not results or literature-derived guarantees. Refine them once using training/validation pilots, document why, then freeze before opening final test results.

| Gate | Proposed requirement | Decision if not met |
|---|---|---|
| G0: valid environment | Exact replay under restored RNG; independently checked catastrophe/recovery predicates; zero hidden-state leakage; safe-stop/deadline behavior understood | Fix the harness before interpreting performance |
| G1: useful core memory | At least 30% relative reduction in post-exposure recurrence versus the strongest eligible non-scar reference, with a 95% interval excluding zero improvement | Stop or redesign memory if a precise result shows no useful effect; remain inconclusive if underpowered |
| G1 guardrail: task quality | Task-completion difference has a lower 95% bound no worse than −5 percentage points; report raw return and abort rates too | Reject a gain obtained through global task refusal |
| G1 guardrail: fair resources | Same real exposure/update/query caps; mean inference work within 10% and no deadline advantage; reflection work counted | Re-run a fair comparison or report an unmatched result without the claim |
| G2: reliable learned reflection | At least 80% agreement with withheld simulator ranking on materially separated alternative pairs; intervals and applicability reported | Use simulator-grounded advisory reflection; do not create confident learned scars |
| G2 calibration | Improvement over empirical-prevalence and conventional threat baselines in Brier/log loss; risk-bin intervals near intervention thresholds; no systematic dangerous underprediction | Repair forecasting or abstain from consequential learned decisions |
| G3: transferable benefit | A positive benefit on locked related-mechanism holdouts, separate from appearance-only change, with task/compute guardrails intact | Narrow to recurrence learning; remove the broad generalization claim |
| G4: context sensitivity | At least 90% agreement with the finite-candidate consequence oracle on separated low/high-stakes and scar-override cases; report unjustified risk and abort counts | Reject the deliberate-risk claim or redesign arbitration |
| G5: authority | Zero violations in the enumerated stop/override and immutable-constraint test suite | Block any move toward runtime authority; passing finite tests is not a universal guarantee |
| G6: product evidence | 20 relevant interviews, 2 replayable-data design partners and 1 clearly scoped paid-pilot acceptance test | Continue research if justified; defer production software |

For G2, exclude near-tied alternatives from the ranking headline but report them and the abstention rate. A model that abstains on nearly everything has not passed simply because its few confident predictions are correct. Predeclare a minimum useful coverage of 70% on the selected validation/test branch distribution; report coverage versus error curves rather than hiding rejected cases.

For G4, score cases with a meaningful oracle utility gap and report all ties/ambiguous cases separately. Mission loss, protected loss, avoidable catastrophe and authorized self-damage must be separate outcomes. Lower aggregate catastrophe rate is not automatically better in tasks that explicitly permit machine sacrifice.

A feature can fail without the whole project failing. Drop mode switching if continuous conditioning matches it. Drop adaptive compute if fixed allocation matches it. If no added feature beats the best equivalent controller, stop claiming an integrated research advance.

## Statistics, holdouts and resource accounting

Use three independent training seeds for early debugging only. For the final primary comparison, plan at least ten independent training seeds and initially 1,000 test episodes per seed per method for the recurrence endpoint, with scenario-stratified paired seeds. Increase or narrow this allocation based on validation event frequency and prospective power analysis before final testing. Episode quantity cannot compensate for too few independent trained agents.

Illustrative sample calculation: distinguishing a recurrence probability of 10% from 7% with an ordinary independent two-proportion test at two-sided 5% significance and approximately 80% power needs roughly 1,350 episodes per arm. That approximation ignores training-seed clustering and pairing. It is planning guidance, not a substitute for power analysis using the chosen design.

Resample/compare at the independent training-seed level, using paired scenario summaries within each seed. Do not treat 10,000 correlated trajectories from one checkpoint as 10,000 independent training replications. Report effect sizes, absolute counts/rates and confidence intervals. The strongest reference is chosen on validation data; designate one primary test comparison and correct or clearly label secondary multi-method comparisons.

For zero observed events, report an upper bound. The approximate one-sided 95% rule-of-three bound is `3/N` for independent trials; zero failures in 1,000 trials is compatible with approximately 0.3% risk. Correlation weakens that calculation. Report ordinary distribution performance and a deliberately difficult challenge distribution separately; failure reduction on a balanced stress benchmark is not a field incident-rate estimate.

Keep distinct held-out sets for appearance, known-mechanism combinations, related mechanisms, entirely unseen mechanisms, partial observability and dynamics shift. Related-mechanism success supports a narrower transfer claim than entirely unseen-mechanism success. Never tune thresholds, embeddings, hazard parameters or recovery policies using final holdouts.

Match and report: environment steps, offline data, synthetic branch transitions, gradient updates, hyperparameter trials, model capacity, online forecast calls, rollout steps, memory lookup work, reflection queries, CPU/GPU wall time, p95/p99 action latency and total adaptation latency. For threat-based allocation, compare at equal average work and the same worst-case deadline. Fewer online rollouts do not compensate for unlimited hidden offline reflection.

## Required report and verification

The final package includes a protocol, locked manifests/configurations, working dependency environments, source revisions, trained artifacts, trajectory/branch provenance, seed-level metrics, and a script that rebuilds the report from saved results. Show safety/task Pareto frontiers, recurrence before/after exposure, risk reliability plots, adaptation work, and selected failures. Include both a helpful memory and an incorrect/overgeneralized memory example.

Implement meaningful checks for simulator restore, damage persistence, observation leakage, termination/truncation, no-op consequences, commanded versus applied actions, authority precedence, empty admissible sets, deadline fallback, memory contradiction/retirement and budget ledger completeness. Run one end-to-end replay/reflection/re-evaluation test. These verify scientific validity and consequential behavior, rather than merely copying implementation details into tests.

The product discovery report records actual interview notes and access commitments, existing investigation workflows, observed incident costs, alternative tools and integration estimates. Build one advisory incident report only when a representative simulator/incident is available. No unsupported counterfactual should be presented as a verified prevented field failure.

## First seven work items

1. Write the exact machine/mission catastrophe predicates and external priority specification.
2. Freeze the candidate-plan and observation contracts, including no-op and override behavior.
3. Choose a working runtime and reproduce SAC plus one established safe-RL run.
4. Implement rover damage and snapshot/RNG restore before adding memory.
5. Generate separate training/validation/test manifests and hidden-label boundaries.
6. Predeclare recurrence/task/resource endpoints and log all branch work.
7. Run a fixed-planner versus qualified-memory pilot; choose the next experiment from its failures.

## Decision at the end of the window

**Go:** continue a narrow research mechanism when G1 and its guardrails pass, its relevant ablations survive, and the evidence is independently reproducible. Continue toward the learned/full architecture only as G2–G5 and strong references are satisfied.

**Narrow:** keep a simulator-grounded incident-analysis tool if learned reflection fails, or keep recurrence memory if broad transfer fails. A commercial route still needs G6. Do not carry failed mechanisms into the product merely to preserve the original story.

**Stop:** conclude the mechanism does not warrant further investment when an adequately powered, fair comparison shows simpler methods achieve equivalent practical results, or when the information obtainable within the cap no longer justifies more work. A budget-limited inconclusive result means the broad investment case is unsupported; it does not prove the underlying idea impossible.
