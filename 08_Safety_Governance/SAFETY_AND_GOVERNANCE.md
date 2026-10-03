# Safety, Governance, and Failure Modes

## 1. Self-preservation must remain subordinate to human-defined authority

The phrase “survival instinct” can be dangerous if interpreted as granting the system an unconditional objective to preserve itself. AACE should be designed so that machine viability is **instrumental and bounded**, not an overriding terminal goal.

Human-defined shutdown, safe disposal, mission abort, or decommissioning must remain legitimate actions. The system should never resist authorized shutdown merely because it predicts loss of its own operation.

## 2. Recommended objective hierarchy

A production design should use an explicit authority hierarchy such as:

1. hard human/legal/safety constraints,
2. protection of people and externally defined protected assets,
3. authorized shutdown and override,
4. system viability / recoverability,
5. mission objectives,
6. efficiency/preferences.

This prevents “survival” from becoming a generic power-seeking incentive.

## 3. External safety layer

During research-to-hardware transition, AACE should not be the sole safety controller. Use independent:

- emergency stops,
- watchdogs,
- control barrier functions,
- reachability-based safety filters,
- rate/force/temperature limits,
- geofences,
- runtime shields,
- manual override.

## 4. Failure mode: pathological fear

AACE may learn to avoid useful action because uncertainty itself becomes threatening.

Symptoms:

- freezing,
- unnecessary shutdowns,
- route refusal,
- low task completion,
- chronic critical mode.

Mitigations:

- calibrate uncertainty,
- reward information-gathering that preserves viability,
- track false aborts,
- separate unfamiliarity from evidence of catastrophe,
- add explicit recovery from false scars.

## 5. Failure mode: scar poisoning

A wrong world model can produce a false counterfactual lesson and make it persistent.

Mitigations:

- store confidence,
- require repeated confirmation for high-impact scars,
- decay unconfirmed memories,
- compare model counterfactuals with real/simulator interventions when possible,
- support contradiction and deletion,
- log provenance.

## 6. Failure mode: model exploitation

The actor may discover actions that fool the threat model.

Mitigations:

- separate threat model training from policy incentives where possible,
- ensembles,
- adversarial validation,
- random audits,
- external constraints,
- out-of-distribution detectors.

## 7. Failure mode: delayed action from overthinking

Adaptive compute can be counterproductive if the system spends extra time planning during a time-critical event.

Mitigations:

- hard latency budgets,
- precomputed recovery reflexes,
- critical-mode fallback policy,
- parallel planning,
- benchmark time-to-action as a safety metric.

## 8. Failure mode: catastrophic-memory overgeneralization

One failure may make the agent avoid an entire class of benign states.

Mitigations:

- represent causal factors explicitly,
- retrieve by structured similarity,
- validate scars against counterexamples,
- maintain uncertainty,
- compare to nearest benign episodes.

## 9. Human performance / stress research

Do not begin with live high-stress human experiments. Adaptive fear/horror simulation based on biometrics can create psychological and physical risk. Any real human-subject protocol should involve appropriate ethics review, informed consent, stop criteria, privacy controls, and subject-matter experts.

## 10. Cyber/infrastructure deployment

An autonomous cyber-defense AACE should not be allowed to “seal off” or modify production infrastructure solely from learned panic. Early deployments should be recommendation/shadow mode, followed by narrow pre-authorized actions with rollback.

## 11. Auditability

Every intervention should log:

- predicted catastrophe probability,
- uncertainty,
- retrieved scars,
- mode change,
- proposed/blocked action,
- alternative action,
- external shield status,
- eventual outcome.

AACE should be easier to investigate after an incident than a monolithic end-to-end policy.


## 12. Deliberate risk is not permission to invent values

The new deliberate-risk layer creates a governance requirement: AACE may compare self-risk with mission consequence, but the priority structure must come from externally authorized objectives and safety policy. The system must not infer that some people are worth more than others, create demographic value scores, or reinterpret a vague mission objective as permission to violate human-safety constraints.

“I, Robot”-style probability-versus-priority dilemmas are useful as controlled simulation benchmarks only when the experimenter specifies the objective and protected priorities explicitly. The scientific question is whether the agent can reason consistently about consequence distributions, not whether the model can invent moral philosophy.

## 13. Self-sacrifice remains subordinate to authority

Controlled sacrifice can be tested in simulation as an edge case of deliberate risk. The required ordering is:

1. human safety and non-negotiable external constraints,
2. authorized command / shutdown / override,
3. protected mission objectives,
4. machine self-preservation,
5. ordinary task reward.

Any deployed system must be prevented from developing instrumental resistance to shutdown or treating continued operation as a terminal value above human authority.
