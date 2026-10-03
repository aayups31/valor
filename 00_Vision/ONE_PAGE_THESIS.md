# One-Page Thesis

## Problem

Autonomous systems can optimize tasks while still behaving badly around rare, irreversible failures. The opposite failure is also possible: a system can become so conservative that it refuses a dangerous action even when the consequence of inaction is worse. A fixed reward penalty or safety constraint does not fully capture the fact that, as danger rises, both the *way of deciding* and the justification for accepting risk may change.

## Hypothesis

An autonomous agent will be more robust if it has a dedicated survival architecture that:

1. predicts future catastrophe and time-to-failure,
2. tracks internal viability and recoverability,
3. changes decision mode as threat rises,
4. spends more planning effort on consequential states,
5. reduces dangerous exploration without eliminating information gathering,
6. explicitly compares consequences of action with consequences of inaction,
7. enters recovery or retreat when the mission is no longer worth the risk,
8. deliberately accepts modeled danger when an externally authorized objective justifies it,
9. reconstructs harmful events counterfactually,
10. stores high-confidence harmful decision patterns as persistent scars,
11. retrieves those scars when structurally similar danger appears later without turning those scars into permanent prohibitions.

## Scientific challenge

All the pieces have precedents. The research contribution is not “fear in AI.” The contribution must be evidence that the **integrated consequence-aware survival architecture** produces one/few-shot consequence learning, OOD hazard generalization, and calibrated deliberate risk taking that strong SafeRL, risk-sensitive, recovery, and world-model baselines do not.

## First decisive experiment

Train agents in the same partially observed physics environment with irreversible hazards. Hold out one hazard family entirely. Give full AACE one or a few experiences with a related failure and allow reflection. Then test the unseen family.

Measure catastrophe rate, survival time, task return, false aborts, recovery success, threat calibration, recurrence, transfer, and compute.

## Success

AACE reduces unjustified catastrophic outcomes without collapsing into global caution. At matched compute and externally specified safety constraints, it avoids needless high-risk actions, accepts justified high-risk actions when inaction is worse, generalizes to held-out hazards, and shows that world-model imagination, mode switching, and counterfactual scars add value beyond fixed risk penalties and prioritized replay.

## Failure

If SafeDreamer/CPO/CVaR/Recovery RL matches the result, then the emotional framing has not created a distinct technical capability and the project should be narrowed or killed.

## Commercial translation

Sell reliability, not emotion: a survival runtime that sits around existing autonomy and predicts when the system should plan deeper, recover, retreat, or stop before expensive failure.
