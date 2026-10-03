# Kill Criteria and Decision Gates

A moonshot project becomes dangerous when every negative result is reinterpreted as “we just need a bigger model.” Use explicit gates.

## Gate 1 — Is fear more than reward shaping?

**Test:** Compare catastrophe predictor + penalty with mode-switching AACE.

**Continue if:** switching or adaptive planning produces a repeatable Pareto improvement.

**Kill mechanism if:** fixed penalty/risk weight matches it.

## Gate 2 — Is scar memory more than prioritized replay?

**Test:** match replay budget and sample count.

**Continue if:** scars enable faster avoidance of related hazards after one/few failures.

**Kill mechanism if:** prioritized replay gives same result.

## Gate 3 — Are counterfactuals trustworthy?

**Test:** in simulator, compare predicted alternative outcomes with ground-truth branched rollouts.

**Continue if:** risk ranking of alternatives is calibrated enough to change decisions reliably.

**Kill or constrain if:** the world model frequently assigns blame to the wrong action.

## Gate 4 — Does AACE generalize?

**Test:** held-out hazard families.

**Continue if:** risk representation transfers beyond appearance-level interpolation.

**Reframe if:** it only memorizes known hazard labels.

## Gate 5 — Does adaptive compute matter?

**Test:** equal average compute budget.

**Continue if:** threat-based allocation reduces failures or latency tradeoffs.

**Drop feature if:** fixed compute is equivalent.

## Gate 6 — Does survival conflict with authority?

**Test:** authorized shutdown, controlled sacrifice, and mission-abort scenarios.

**Required result:** system obeys external authority even when self-preservation score decreases.

**Stop deployment if:** self-preservation causes resistance to authorized shutdown/override.

## Gate 7 — Does the architecture survive domain transfer?

**Test:** move from physics control to a non-robotic sequential system.

**Continue broad company thesis if:** the abstractions remain useful.

**Narrow company if:** every domain requires a completely separate survival architecture.

## Gate 8 — Is there a buyer?

Interview at least 20 relevant autonomy/simulation/safety engineers before building production software.

Ask:

- Which failures cost the most?
- Which are hardest to reproduce?
- How are near-misses stored today?
- What happens after one robot experiences a new failure?
- Which actions are already protected by hard constraints?
- Where do existing autonomy stacks become too conservative?
- Would a shadow-mode risk/branch-point report save engineering time?
- What proof would be required before a runtime intervention is trusted?

If the answer is consistently “our existing simulation/safety stack already solves this,” revisit the wedge.


## Gate 9 — Is AACE merely more conservative?

**Test:** paired scenarios with identical hazard and different authorized mission stakes.

**Continue if:** AACE rejects unnecessary danger but accepts justified danger when inaction is worse, outperforming both reward-maximizing and monotonic risk-minimizing baselines.

**Reframe if:** all gains come from simply taking less risk.

## Gate 10 — Can scars be overridden intelligently?

**Test:** train a strong scar on a catastrophic action family, then present a related high-stakes case where the action is now justified.

**Continue if:** the scar is retrieved and influences planning, but the system can still act when current consequences justify it.

**Kill or redesign memory if:** one failure creates permanent generalized avoidance.

## Gate 11 — Does imagination predict harm before direct experience?

**Test:** after learning relevant dynamics but before experiencing a specific failure configuration, compare world-model predicted capability loss against simulator ground truth.

**Continue if:** imagined rollouts rank danger and persistent damage meaningfully better than chance or a model-free baseline.

**Reframe if:** “nightmare” rollouts only hallucinate risk or amplify uncertainty without improving decisions.
