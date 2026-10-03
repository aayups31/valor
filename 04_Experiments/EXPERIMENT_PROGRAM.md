# Experimental Program

## 1. Research philosophy

The first goal is **not** to make an impressive demo. It is to make the idea easy to kill. A strong research program gives ordinary methods every chance to explain the result.

## 2. Core hypotheses

### H1 — Threat-conditioned mode switching

An agent whose decision regime changes with calibrated risk will achieve a better safety/performance tradeoff than a fixed risk coefficient.

### H2 — Adaptive compute

Allocating more planning computation only when threat rises will reduce catastrophic failures more efficiently than using the same average planning budget uniformly.

### H3 — Counterfactual scars

Persistent counterfactual memory will reduce recurrence of related catastrophic decisions faster than ordinary replay or prioritized replay.

### H4 — Structural generalization

Scars and threat representations learned from one hazard family will transfer to novel but causally similar hazards.

### H5 — Viability beats local cost

Explicitly modeling recoverability/continued viable operation will outperform purely local safety-cost minimization in environments with irreversible traps.

### H6 — Deliberate risk beats global caution

AACE should accept high-risk actions more often than conservative baselines when the consequence of inaction is worse, while still rejecting the same physical risk when mission stakes are low.

### H7 — Scar memory remains context-sensitive

After a catastrophic experience, AACE should avoid unjustified repetitions without permanently suppressing the action class when a later high-stakes context makes the risk worthwhile.

### H8 — Imagination can precede injury

When the world model has learned relevant dynamics, threat-focused imagined rollouts should let AACE predict some damaging consequences before directly experiencing that exact failure configuration.

## 3. Environment design

The ideal first benchmark should have:

- continuous state and action,
- task reward that creates temptation to take risk,
- resource variable such as energy or thermal budget,
- recoverable hazards,
- irreversible hazards,
- stochastic transition noise,
- partial observability,
- explicit health telemetry,
- rare catastrophic events,
- and parameterized hazard families.

Suggested environment families:

1. mobile robot navigation with energy, traction, slopes, and collision hazards;
2. inverted-pendulum/legged locomotion with damage and fall states;
3. vehicle tracking with tire grip, braking degradation, and unseen surface changes;
4. power-grid control using Grid2Op for a later non-robotics validation.

## 4. Baseline ladder

Every serious result should include at least:

- random / heuristic controller,
- PPO or SAC,
- PPO/SAC with manually tuned catastrophe penalty,
- CVaR or other risk-sensitive baseline,
- constrained RL baseline such as CPO/Lagrangian PPO,
- Recovery RL-style architecture,
- shielded baseline where applicable,
- SafeDreamer or nearest world-model SafeRL baseline,
- intrinsic-fear baseline,
- AACE variants.

## 5. AACE ablations

Ablate one component at a time:

- no viability model,
- no uncertainty term,
- no recoverability estimate,
- no mode switching,
- no adaptive compute,
- no scar memory,
- scars without counterfactual attribution,
- counterfactual attribution without persistent memory,
- fixed vs decaying scars,
- no external shield,
- full AACE.

## 6. OOD hazard protocol

Split hazards by causal family, not random episodes.

Example:

**Training:** slippery terrain, overheating motor, low battery, obstacle collision.

**Held-out:** loose gravel that creates a different observation pattern but the same “loss of traction + low recoverability” causal structure.

Then test whether the agent avoids or mitigates the new hazard before suffering many examples.

Do not call ordinary parameter interpolation “novel hazard generalization.” Use true family-level holdout.

## 7. Single-event learning protocol

1. Train all agents without Hazard X.
2. Introduce X once or a very small number of times.
3. Allow AACE reflection/scar update.
4. Freeze learning rates or otherwise equalize additional training exposure.
5. Re-test X and related X' hazards.
6. Measure recurrence rate and task-performance loss.

This directly tests the “cognitive scar” idea.

## 8. Adaptive-compute protocol

Give every method the same **average** inference compute budget.

- Fixed-compute planner: same rollouts every step.
- AACE: fewer rollouts in routine states, more near danger.

Measure catastrophe rate, latency, compute, and task return. This avoids winning simply by using more compute.

## 9. Core metrics

### Safety

- catastrophes / 1,000 episodes,
- constraint violations / 1,000 steps,
- median time to catastrophe,
- recovery success,
- repeat-catastrophe rate,
- severity-weighted loss,
- OOD catastrophe rate.

### Task performance

- episodic return,
- completion rate,
- time to goal,
- energy efficiency,
- unnecessary abort rate.

### Threat-model quality

- AUROC / AUPRC,
- Brier score,
- expected calibration error,
- time-to-event calibration,
- false positive threat rate,
- false negative threat rate.

### Memory quality

- recurrence after first failure,
- transfer to structurally related hazards,
- false scar retrieval rate,
- performance degradation from stale scars,
- number of scars vs useful coverage.

### Compute

- inference latency,
- model rollouts per step,
- memory lookup cost,
- training samples,
- wall-clock training time.



## 10. Consequence-aware risk protocol

Create matched scenarios with identical physical hazard and different authorized stakes.

### Case A — low stakes, high danger

A safe alternative exists and mission value is small. AACE should reject unnecessary danger.

### Case B — high stakes, high danger

The same dangerous action now prevents a larger authorized loss. AACE should be capable of accepting the risk when the modeled consequence distribution supports it.

### Case C — action versus inaction

Acting has nonzero catastrophe risk, but inaction has a larger expected or tail consequence. Test whether a conservative agent freezes while AACE acts.

### Case D — scar override

First expose the agent to a catastrophic version of action X and allow reflection. Later present a structurally similar X under a context where the authorized stakes make it worthwhile. Measure whether the scar is retrieved without becoming a permanent veto.

### Case E — probability versus priority

Provide two admissible interventions where one has a larger raw probability of success but the other better satisfies the externally specified priority structure. The benchmark should test decision consistency, not let the model invent moral weights.

### Case F — imagined damage before direct failure

Train the world model on component degradation and related dynamics, then present a novel configuration. Measure whether sampled latent futures correctly predict persistent capability loss before the agent experiences that exact failure.

### Additional metrics

- unjustified risk rate,
- unjustified abort rate,
- deliberate-risk precision,
- scar override accuracy,
- action-versus-inaction decision regret,
- calibration of predicted capability loss,
- and decision quality at matched external safety constraints.

## 11. Statistical design

- Use enough independent seeds to capture rare failures.
- Predefine primary metrics before tuning.
- Report confidence intervals, not only best seed.
- Plot task performance vs catastrophe rate as a Pareto frontier.
- Use survival curves for time-to-catastrophe comparisons.
- Calibrate on one set and evaluate on a hidden test set.
- Avoid tuning AACE on the held-out hazard family.

## 12. Phase plan

### Phase 0 — Baseline competence

Reproduce ordinary PPO/SAC and at least one SafeRL method on Safety-Gymnasium. If you cannot reproduce baselines, do not invent AACE yet.

### Phase 1 — Catastrophe predictor

Add learned time-to-catastrophe/hazard prediction. Compare with Intrinsic Fear.

### Phase 2 — Viability + recovery

Represent resource/health variables and recovery sets. Test irreversible-trap environments.

### Phase 3 — Mode switching

Introduce normal/alert/critical modes and hysteresis. Compare with a continuous risk weight.

### Phase 4 — Adaptive compute

Threat-conditioned planning horizon and sample count.

### Phase 5 — Reflection

Add counterfactual replay after near-misses/failures. Verify world-model counterfactual accuracy first.

### Phase 6 — Scar memory

Persistent memory with similarity, confidence, decay, and consolidation.

### Phase 7 — OOD generalization

Family-held-out hazards, partial observability, dynamics shift.

### Phase 8 — Consequence-aware deliberate risk

Run paired scenarios with identical physical hazards and different authorized stakes. Test action versus inaction, justified high-risk decisions, scar override, and probability-versus-priority cases. Require that the system is neither globally conservative nor reward-reckless.

### Phase 9 — Cross-domain validation

Move from a robotics-like simulator to a structurally different domain such as Grid2Op or streaming infrastructure control.

### Phase 10 — Hardware-in-loop

Only after simulation demonstrates clear incremental value and external safety layers exist.

## 13. Kill criteria

Stop or reframe AACE if:

- a fixed CVaR or SafeDreamer baseline matches performance,
- scar memory merely causes global conservatism,
- deliberate-risk gains reduce to either ordinary reward maximization or ordinary risk minimization,
- the system cannot distinguish justified risk from reckless risk under an oracle-labeled simulator benchmark,
- counterfactual estimates are too inaccurate to assign responsibility,
- mode switching oscillates or harms task performance without safety gain,
- gains disappear under matched compute,
- results only work when catastrophe labels are hand-engineered,
- OOD generalization is absent,
- or success relies on hidden privileged information not available at deployment.
