# Research Backlog

## P0 — Must answer before implementation

- Define catastrophe and viability precisely for the first environment.
- Select primary baseline stack.
- Decide whether first actor is PPO, SAC, or Dreamer-style.
- Decide if world model is necessary in Phase 1 or introduced later.
- Define train vs held-out hazard families.
- Define the external safety shield used during later physical experiments.
- Pre-register primary metrics and success threshold.

## P1 — Core architecture

- Threat predictor: horizon, severity, uncertainty.
- Mode controller: discrete vs continuous.
- Recovery set definition.
- Adaptive compute policy.
- Scar schema and retrieval.
- Counterfactual branch selection.
- Responsibility confidence.

## P2 — Scientific differentiation

- AACE vs Intrinsic Fear.
- AACE vs CVaR.
- AACE vs CPO/Lagrangian PPO.
- AACE vs Recovery RL.
- AACE vs SafeDreamer.
- scar memory vs prioritized replay.
- mode switching vs fixed risk weight.

## P3 — Generalization

- visual shift,
- dynamics shift,
- unseen hazard family,
- partial observability,
- sensor dropout,
- actuator degradation,
- cross-environment transfer.

## P4 — Product research

- autonomy teams with costly edge cases,
- simulator integration pain,
- incident replay workflows,
- current recovery-policy architecture,
- willingness to run a shadow survival layer,
- required evidence for action intervention.
