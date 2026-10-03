# VALOR / AACE: project review and working plan

Reviewed: October 2, 2026. Status: assessment and proposed implementation plan; no experiments have been run.

**Current implementation authority:** the [reviewed implementation master plan](IMPLEMENTATION_MASTER_PLAN.md) incorporates the subsequently confirmed laptop, $0 preferred external spend and required transparent local demo. Its dependency order and resource limits supersede earlier estimates in this assessment. Read it first for the current build plan.

**Recommendation: build a bounded research prototype. Defer the broad autonomous survival platform until there is comparative evidence and a customer with a measurable problem.** The next investment should buy an answer to a specific research question, with a spending cap and a decision date.

This review covers all 11 existing folders and all 25 existing files: 23 Markdown documents, one reading-list CSV, and one BibTeX bibliography. All 22 standalone Markdown documents are included verbatim in `MASTER_BLUEPRINT.md`, after normalizing line endings. Reading those documents therefore also covers the master blueprint's substantive content. The archive contains 33 reading-list rows and 25 bibliography entries. These are documentation assets, not evidence of completed research.

Read this assessment first, then the [build specification](01_Architecture/BUILD_SPECIFICATION.md), the [execution roadmap](04_Experiments/EXECUTION_ROADMAP.md), and the [source checks](References/REVIEW_SOURCE_CHECKS.md). Original documents are preserved as the research background; these additions resolve proposed implementation choices without rewriting the original thesis.

## What the project aims to achieve

VALOR is the workspace name. The technical program in the documents is Survival AI / the Affective Actor-Critic Engine, or AACE. No separate VALOR product specification exists.

The aim is an autonomous controller that can predict the consequences of losing capability, change its planning when danger matters, and use verified lessons from previous failures. It should distinguish an unnecessary dangerous shortcut from a dangerous action justified by the externally specified mission. Staying still, delaying, and retreating all have consequences that must be modeled.

For example, a simulated inspection rover takes a slippery shortcut, damages a motor, and becomes unable to return to its dock. The system reconstructs the decision, compares feasible alternatives, and stores a qualified lesson. Later it recognizes a related traction-and-return-energy problem on a different surface. It avoids the shortcut for an ordinary task, but can reconsider it for a higher-priority authorized task. The decision must use current evidence and the same hard constraints.

The intended technical contributions are:

1. Predict persistent damage and loss of recoverability separately from ordinary task reward.
2. Allocate planning effort to consequential decisions while respecting action deadlines.
3. Turn failures into confidence-weighted, retrievable counterfactual lessons.
4. Reconsider those lessons when mission context or dynamics change.
5. Improve on strong safety methods at comparable data, compute, and task performance.

The first measurable objective should be narrower: **does verified counterfactual memory reduce repeat catastrophic decisions after one or a few failures, beyond equally resourced replay and planning, without increasing unjustified aborts?** Structural transfer and learned-model reflection are subsequent tests. Literal emotion, consciousness, a universal survival instinct, and cross-domain intelligence are not demonstrated outcomes in this archive.

## Complete folder assessment

| Location and files | What is already present | What the build needs next |
|---|---|---|
| Root: `START_HERE.md`, `MASTER_BLUEPRINT.md`, `VERSION_NOTES.md` | Navigation, complete collected blueprint, and September 23 consequence-aware revision | One execution source of truth; treat the master as an aggregate, not a second independently edited specification |
| `00_Vision`: `ONE_PAGE_THESIS.md`, `FULL_VISION.md`, `CLAIM_AUDIT_AND_NOVELTY.md` | Clear motivation, operational emotional metaphors, novelty boundaries, long-term ladder | Narrow the first claim to recurrence reduction; make the reference-method comparison explicit |
| `01_Architecture`: `AACE_ARCHITECTURE.md`, `TERMINOLOGY.md` | Actor, world model, viability, threat prediction, modes, arbitration, recovery, reflection, memory, shield | Typed interfaces, action deadlines, component ownership, observation permissions, and concrete failure behavior |
| `02_Mathematics`: `MATHEMATICAL_SPEC.md`, `CONSEQUENCE_AWARE_DECISION_THEORY.md` | POMDP/CMDP foundation, time-to-event risk, CVaR, proposed scores, deliberate risk | Resolve objective priorities, probability versus score, continuation-policy dependence, tail sampling, and counterfactual uncertainty |
| `03_Research_Literature`: `PRIOR_ART_MAP.md`, `PAPER_READING_GUIDE.md` | Substantial map of safe RL, fear, recovery, world models, memory and counterfactuals | Add closer counterfactual-harm work; compare precise mechanisms rather than names |
| `04_Experiments`: `EXPERIMENT_PROGRAM.md`, `RESEARCH_QUESTIONS.md` | Eight hypotheses, ablations, OOD and one-event protocols, 50 research questions | Choose one primary endpoint, freeze splits, define resource accounting and statistically meaningful gates |
| `05_Data_Environments`: `DATASETS_AND_ENVIRONMENTS.md` | Appropriate simulation-first strategy and supporting datasets | Build one snapshot-capable environment; public anomaly/degradation data cannot prove action-dependent control benefits |
| `06_Learning_Path`: `LEARNING_CURRICULUM.md`, `MATH_CHECKLIST.md` | Extensive prerequisites and a 12-week study sequence | Use competency checkpoints; the study timetable and implementation timetable are separate |
| `07_Business`: `COMPANY_AND_PRODUCT.md`, `USE_CASES.md` | Simulation advisory → runtime → fleet-memory progression; several candidate domains | Choose one buyer workflow, verify access to replayable incidents, quantify integration effort and willingness to pay |
| `08_Safety_Governance`: `SAFETY_AND_GOVERNANCE.md` | Human authority, independent safeguards, model-error risks, audit requirements | One executable authority ordering; make shutdown bypass learned arbitration; test stale memory and late decisions |
| `09_Open_Questions`: `RESEARCH_BACKLOG.md`, `KILL_CRITERIA_AND_DECISIONS.md` | Priority backlog and 11 falsification gates | Assign owners, deliverables, numerical thresholds and deadlines to the immediate gates |
| `References`: `WEB_SOURCES.md`, `papers_to_read.csv`, `bibliography.bib` | Source links and curated reading/bibliography lists | Maintain checked metadata and a claim chart; lists are partial mirrors rather than a single reference registry |

There is no application code, dependency manifest, simulator implementation, training pipeline, model checkpoint, experiment output, test suite, CI configuration, or customer evidence in the supplied folder. The existing conceptual architecture is detailed; implementation and empirical validation have not begun.

## What is convincing, and what remains unsupported

The strongest choices are simulation first, explicit comparisons against established methods, persistent damage rather than a one-time penalty, context-sensitive memory, and the separation of learned predictions from external safeguards. The documents already acknowledge that the individual ingredients have precedents.

The weakest part is the size of the proposed first architecture. Requiring an actor, world model, threat critic, viability model, mode gate, recovery policy, deliberate-risk rule, reflection engine, memory and benchmark before obtaining a useful result makes diagnosis expensive. The first experiment can isolate memory with simulator-grounded branches and a fixed planner. A positive result supports that mechanism; it does not establish the entire AACE thesis.

Research novelty remains unproven. Learned catastrophe penalties already appear in [Intrinsic Fear](https://arxiv.org/abs/1611.01211). Task/recovery separation is central to [Recovery RL](https://arxiv.org/abs/2010.15920), and safety-aware world-model planning is central to [SafeDreamer](https://arxiv.org/abs/2307.07176). These mechanisms must be credited and compared directly.

The existing reading map also misses [Do no harm: A counterfactual approach to safe reinforcement learning](https://proceedings.mlr.press/v242/vaskov24a.html), which formulates harm relative to an alternate policy, and [Counterfactually Safe Reinforcement Learning](https://arxiv.org/abs/2605.25114), a 2026 preprint that also evaluates individual harm against a baseline alternative. These overlap consequence comparison, although neither abstract establishes that AACE's proposed persistent memory mechanism is already solved. This is a targeted source review, not an exhaustive novelty or patent search.

Deliberate risk alone is weak differentiation. A conventional constrained controller given mission urgency, damage costs and no-op consequences can also choose justified danger. All reference agents must receive those inputs and objectives. The potential distinction is faster, more selective adaptation from verified failures, especially under changed observations and uncertain dynamics.

## Design corrections required before coding

| Issue in the current documents | Consequence | Proposed resolution |
|---|---|---|
| Governance section 2 ranks viability above mission, while section 13 puts protected mission objectives above viability | The same emergency can imply incompatible actions | Immutable external constraints and authorized override first; an explicit mission policy defines allowable machine-risk tradeoffs |
| Earlier critical-mode equations maximize survival; later equations allow deliberate risk | Critical mode may suppress exactly the behavior the update intends | Modes change compute and recovery readiness; they do not silently replace the authorized objective |
| Composite fear mixes probability, severity, uncertainty, recovery and memory | A bounded score can be mistaken for a calibrated probability | Keep a calibrated catastrophe forecast separate from a scheduling score and the consequence vector |
| Risk is written as a state/action quantity but depends on horizon and continuation policy | Changing the policy or horizon invalidates labels and calibration | Include horizon, continuation-policy version and operating regime in forecast metadata |
| One-step membership in the safe set is used as a viable-action proxy | The next state can be safe yet inevitably fail later | Use explicit finite-horizon recovery tests; do not call the proxy a certified viability kernel |
| Symmetric health/setpoint margins are offered generically | High battery or high actuator health can be penalized despite being beneficial | Define each variable's domain-specific one-sided or interval constraints |
| Tail branches are intentionally oversampled | Raw frequency overstates catastrophe probability and distorts CVaR | Separate adversarial stress search from probability estimation; use a defined proposal and importance weights when appropriate |
| Counterfactual regret is sometimes described as causal responsibility | A different future under a model does not prove real-world causation | Start with paired simulator interventions; store evidence type and confidence; abstain on uncertain learned branches |
| Scar retrieval is based on similarity | Latent similarity does not establish transfer of a causal mechanism | Start with observable structured features; test causal-family, appearance and dynamics shifts separately |
| Several loss terms price related damage | Double counting can create arbitrary conservatism | Define units and one explicit consequence accounting model before tuning weights |

The build specification turns these corrections into concrete interfaces and decision rules.

## Scope and delivery strategy

The research MVP is a reproducible command-line experiment package with one rover environment, reference controllers, paired replay, memory ablations and a generated comparison report. It should let another person recreate both successful and failed experiments.

Use four successive evidence levels:

| Level | Capability being tested | Interpretation |
|---|---|---|
| 1: simulator-grounded mechanism | Fixed planning plus counterfactual memory, with equal simulator-query budgets | Tests whether the memory concept adds value under accurate dynamics |
| 2: learned prediction | Small probabilistic dynamics/risk models replace online simulator access | Tests whether the value survives model error and realistic observation restrictions |
| 3: full comparative research | Strong safe-RL and safe-world-model references, held-out scenarios and compute controls | Supports a narrow research contribution if reproducible |
| 4: customer evaluation | One existing controller and one customer simulator, initially advisory | Tests usefulness and integration economics; no production-control claim |

Build only the components needed for the next level. Modes and adaptive compute are separate optional experiments. Add them if they improve results, and remove them if fixed planning or continuous risk conditioning performs equally well.

Defer pixels, photorealism, LLM reasoning, new optimizers, multi-agent coordination, fleet scar transfer, cloud infrastructure control, Grid2Op, space/subsea deployment, human stress training and a foundation model. Each introduces a separate validation problem. Evolution and Immune are mentioned in the business vision but have no specifications here and are outside this implementation plan.

## Commercial direction

The recommended initial buyer hypothesis is a field/inspection robotics engineering team with an existing simulator, expensive repeat incidents, and a controller they want to keep. The proposed deliverable is an **incident replay and consequence analysis tool**: identify a damaging decision, compare feasible alternatives, and demonstrate whether a verified lesson improves future simulated runs.

This is an inference from the project, not validated demand. Broader robotics data collection and debugging are already offered by [Foxglove](https://foxglove.dev/), while [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/latest/index.html) supplies robot simulation and validation workflows. AACE should integrate with such infrastructure. Its proposed value must come from tested action-to-consequence analysis and recurrence reduction.

The advisory product needs less evidence than a controller, but still needs reliable replay. Logged telemetry alone generally cannot establish what an unexecuted action would have caused. Require a trusted simulator/digital twin, or explicitly label alternatives as uncertain model predictions. A customer without either may be a poor first design partner.

Conduct 20 interviews before committing to production software, as the existing gate recommends. Seek at least two teams willing to share representative replayable incidents and one willing to define a paid-pilot acceptance test. These are proposed commercial gates, not customers already secured. Record incident frequency, investigation hours, recovery cost, existing tools, procurement owner and integration restrictions. Repeated praise without data access or a pilot commitment is weak evidence.

Use a customer-specific value equation:

`annual value = verified investigation hours saved × loaded hourly cost + attributable reduction in incident losses − integration and operating costs`

Keep observed engineering-time savings separate from simulated avoided losses. Do not assume a simulator improvement translates directly into fewer field failures. Set a pilot price only after learning delivery cost and the customer's measured value; the archive does not support revenue forecasts or a market-size estimate.

## Effort, resources and uncertainty

The [roadmap](04_Experiments/EXECUTION_ROADMAP.md) proposes a 90-day decision window for a practitioner already comfortable with Python, RL experiments and basic probability. It is a planning envelope, not a promise that all research comparisons fit in that period. Allow roughly 400–600 practitioner hours, including analysis and reproduction setbacks. These are estimates, not benchmark measurements.

A lightweight vector-state simulator will start on the user's Core Ultra 185H / Intel Arc / 32 GB RAM computer. Default external spend is $0; no paid GPU-hour allocation is part of the current plan. Use one bounded CPU process and measure runtime/memory before sizing later batches. Intel GPU acceleration is optional after CPU correctness and profiling. Compute may be insufficient for a full SafeDreamer/PIGDreamer reproduction; missing strong comparisons limit the claim rather than authorize extra spending. See the master plan for the current limits.

Core custom work can be Windows-compatible. The upstream OmniSafe README says Windows is not officially supported, so plan a separate Linux/WSL2 environment for that reference stack. SafeDreamer's reproduction instructions use an older JAX/CUDA stack; isolate it instead of forcing every method into one environment. See [source checks](References/REVIEW_SOURCE_CHECKS.md) for the checked support statements. No software has been installed as part of this review.

For a beginner, first complete the learning curriculum's practical checkpoints: reproduce an RL run, explain constrained objectives, build and calibrate a risk predictor, and restore simulator state correctly. The archive's 12-week curriculum is a study proposal; starting from limited ML experience can materially extend the schedule. Part-time execution extends the calendar in proportion to available hours.

## Is it worth building?

| Proposed investment | Decision now | Evidence that changes the decision |
|---|---|---|
| Small replayable benchmark and reference agents | **Yes** | They create a reusable way to falsify the idea |
| Counterfactual memory prototype | **Yes, with a cap** | Meaningful recurrence reduction without lost task performance or inflated compute |
| Learned-model reflection | **Conditional** | Simulator-grounded memory helps and learned branches rank alternatives reliably |
| Full mode-switching/adaptive-compute architecture | **Conditional** | Each added component beats its simpler equal-budget alternative |
| Customer advisory tool | **Conditional** | Replayable customer data, reliable reports and a pilot with measurable value |
| Broad autonomous survival platform or company-scale hiring | **Defer** | Independent reproduction, strong comparisons and customer evidence |
| Emotional/sentient AI claim or universal cross-domain system | **Unsupported** | The supplied materials offer no evidence for those claims |

Continue the research only if the primary experiment meets the predeclared performance gate and the gain survives its relevant controls. A positive toy-environment result justifies another experiment; it does not justify deployment or a broad intelligence claim. If equally resourced replay, context-conditioned risk control or safe planning matches AACE, drop the unsupported mechanism. If customers value the incident-analysis workflow but the algorithmic novelty fails, pursue a narrowly scoped tool on its own merits. If neither works, stop the program and retain the benchmark and findings.

The immediate aim is a credible decision in 90 days: a reproducible result supporting one useful mechanism, a narrower product opportunity, or evidence that this architecture does not merit further investment.
