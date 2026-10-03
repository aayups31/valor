# Planning report 03 — fear, survival, intuition and pressure

**Date:** October 3, 2026. **Scope:** research design and documentation only.  
**Design commit:** `2ed85dd645848a65afee207ca9ed75fdcd4aedd3`.  
**Outcome:** the requested concepts are integrated into a concrete, linked design and staged experiment plan. Their effectiveness remains untested.

## Work completed

Added the 2,560-word [fear, survival, intuition and pressure plan](../01_Architecture/FEAR_SURVIVAL_AND_PRESSURE_PLAN.md). It defines:

- Fear as a candidate-conditioned threat forecast, with calibration and explicit unknown risk.
- Survival as estimated energy, time and movement margins for completing or recovering from the externally specified mission.
- Gut intuition as a fast response proposal learned from experience, beginning with shared fixed recovery primitives.
- Pressure as a computation-allocation problem under task and action deadlines.
- Qualified incident memory as a source of tested recourse and assumptions to recheck.
- A common mission arbitrator and independent action guard, with proposed and applied actions recorded separately.

The plan includes architecture, online decision sequence, training-label considerations, CPU reuse, representative scenarios, UI explanation requirements, failure modes, comparison methods, metrics and dependency order. It is linked from the implementation master plan, architecture specification, experiment roadmap and README. The reading map now records the relevant primary sources and their overlap.

## Important design decisions

The simulated mission clock and wall-clock action budget remain distinct. The current demo does not continuously advance physics during planning, so it is not advertised as a real-time pressure benchmark. A future latency experiment must charge equivalent delay consequences to all methods and reject expired/superseded decisions before action commit. In-flight override handling still requires implementation and verification.

Urgency may change candidate order, computation allocation or response path under the existing mission authority. It does not silently increase permitted risk. Resource preservation serves that mission policy; human stop/shutdown remains authoritative.

Use one consequence-accounting model. Avoid counting the same damage repeatedly as reward loss, fear, memory penalty and urgency. Keep uncertain estimates distinct from precise probabilities and untested choices distinct from rejected ones.

Test both excessive caution and reckless urgency. An agent that preserves its battery by never attempting the mission does not pass. A misleading fast warning must be revisable when terrain or context changes. Braking is a contextual fallback, not a universally best response.

The primary E1–E4 AACE memory comparisons remain identifiable. E5 expands into threat assistance, resource awareness, fast versus slow response, adaptive compute, a targeted memory × hybrid comparison, deadline pressure and stale-warning tests. Compare against thresholds, fixed budgets, ordinary retrieval and existing risk-conditioned planning before retaining extra complexity.

## Verification and source review

Local links and Markdown fences passed checks across the six design/reference documents. Git whitespace checks passed. An additional read-only agent review found no actionable contradictions or unsupported biological/novelty/safety claims. This is a design critique, not independent scientific replication.

Primary-source identity and abstract-level scope checked:

- [Intrinsic Fear](https://arxiv.org/abs/1611.01211): learned imminent-catastrophe prediction and reward shaping.
- [Visceral Machines](https://arxiv.org/abs/1805.09975): physiological-signal-derived intrinsic rewards in simulated driving.
- [Time Limits in Reinforcement Learning](https://proceedings.mlr.press/v80/pardo18a.html): remaining-time awareness and task termination versus training cutoffs.
- [Static and Dynamic Values of Computation in MCTS](https://proceedings.mlr.press/v124/sezener20a.html): valuing computation by its effect on decisions.

These sources establish relevant prior work, not VALOR's advantage. No full-paper reproduction, exhaustive novelty search, biological claim or new benchmark result is asserted.

## Version control, resources and current implementation

The design was committed and pushed during work as `2ed85dd`. This full report and progress-index update are a separate final documentation commit. Final local/remote agreement and worktree cleanliness are verified at the end of the turn.

No executable source, model, dataset, dependency, launcher or UI behavior changed. No training/evaluation job was launched. Existing test results are historical; no new runtime-test result is claimed for this documentation change. External compute/API/hosting spend for this work is $0, excluding existing Codex usage and electricity. Local demo availability was not rechecked during this planning task.

The current rover still has battery, persistent damage, a simulated deadline, fixed rules and known-physics planning. Learned fear, learned gut responses, qualified incident memory, adaptive scheduling and preemptive computation deadlines remain planned.

## Next steps and user input

Research implementation remains paused while project discussion continues. Once resumed: finish baseline competence, validate learned dynamics/threat forecasts, isolate qualified memory benefits with the fixed planner, then implement and compare the pressure/fast-response extensions in phases. Rendered UI review remains pending from the previous build report.

No additional technical input is required to complete this design. If a concrete product domain is chosen later, its mission priorities, acceptable failure outcomes, observable signals and representative simulator/data will determine how these mechanisms transfer.
