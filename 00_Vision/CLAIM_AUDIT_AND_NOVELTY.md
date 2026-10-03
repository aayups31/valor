# Claim Audit, Prior Art Reality Check, and Novelty Boundary

This file separates the compelling story from claims that are already established or overstated.

## 1. Claims to avoid

### “Current AI only maximizes positive reward and forgets failures after reset.”

Too broad. Classical RL optimizes expected discounted return, but modern systems may use replay buffers, recurrent memory, world models, constraints, risk objectives, demonstrations, shields, uncertainty models, or persistent databases. A reset does not imply the algorithm forgets the transition.

### “A fear penalty is a new paradigm.”

False. Intrinsic-fear methods, fear-field safety methods, neuro-inspired fear RL, risk-sensitive RL, and constrained RL all predate AACE.

### “Counterfactual guilt is completely new.”

False as stated. Counterfactual regret, counterfactual credit assignment, counterfactual experience replay, hindsight replay, and actionable counterfactual failure analysis all exist. AACE can still propose a new *persistent memory mechanism* built from these ideas.

### “AACE gives formal safety guarantees.”

Not by default. Learned world models and critics can be wrong. Guarantees require assumptions and typically independent formal machinery such as reachability, barriers, shielding, or certified control.

### “The AI is literally afraid or guilty.”

Not a scientific claim. Use “fear” and “guilt” as memorable names for measurable computational variables.

## 2. Existing work that strongly overlaps

### Intrinsic Fear

Lipton et al., *Combating Reinforcement Learning's Sisyphean Curse with Intrinsic Fear* (2016/2018) learns a model of imminent catastrophe and uses it to penalize the agent before catastrophic states recur. This is one of the closest conceptual ancestors of the fear core.

### Fear Field Framework

A 2025 paper explicitly uses a “fear field” to adapt constraints and exploration under model mismatch. This means AACE cannot claim ownership of “fear as adaptive safety signal.”

### Fear-neuro-inspired safe driving

Work published in 2023 models amygdala-inspired defensive behavior for safe autonomous driving. This overlaps the biological framing.

### SafeDreamer

SafeDreamer combines Dreamer-style world models with explicit safety costs and planning. This is a critical baseline because AACE also relies on imagined futures and safety evaluation.

### Recovery RL

Recovery RL separates task policy and recovery policy, using a learned estimate of unsafe regions. AACE’s “critical mode” must do more than rediscover this split.

### Homeostatic RL

Keramati and Gutkin mathematically model behavior around maintenance of internal physiological variables. This is directly relevant to the viability concept.

### Survival Instinct in Offline RL

Li et al. show that pessimism plus biased offline data can produce an implicit “survival instinct.” The phrase itself is already established in RL literature.

### Future action-state occupancy

Recent work shows that maximizing future action-state path occupancy can implicitly avoid death/absorbing states. This provides another non-reward-shaping route to survival-like behavior.

### Counterfactual failure analysis

ACTER and counterfactual credit-assignment work already study alternative sequences/actions that would have prevented or explained bad outcomes.

## 3. Candidate novelty boundary for AACE

The strongest defensible research framing is:

> **AACE studies whether an explicit survival state machine that couples calibrated catastrophe forecasting, uncertainty-sensitive world-model planning, viability preservation, threat-conditioned compute allocation, and persistent counterfactual scar memory can generalize avoidance behavior to novel hazards better than existing safe-RL methods.**

This is a hypothesis, not a claim of novelty until a proper literature and patent search is complete.

## 4. What must be empirically different

AACE should demonstrate one or more behaviors not explained by a simple penalty:

- sudden but calibrated policy regime change as danger rises,
- selective increase in planning effort under threat,
- selective suppression of exploration near irreversible states,
- active preference for reversible/recoverable actions,
- strong memory after a single catastrophic experience without catastrophic global conservatism,
- transfer from one harmful trajectory to structurally related but visually different hazards,
- task abandonment only when viability genuinely falls below threshold,
- recovery from partial failures before a hard safety shield intervenes.

## 5. Novelty research tasks before publication or fundraising

1. Run exact-phrase and concept searches in Google Scholar, Semantic Scholar, arXiv, IEEE Xplore, ACM DL, Scopus/Web of Science if available.
2. Search patents for: affective reinforcement learning, fear reinforcement learning, survival autonomous agent, catastrophic memory, counterfactual safety memory, threat-conditioned policy switching, adaptive safe world model, viability reinforcement learning.
3. Search code repositories for existing implementations of intrinsic fear, SafeDreamer, Recovery RL, shielded RL, homeostatic RL, and counterfactual replay.
4. Build a claim chart: each proposed AACE mechanism versus prior work.
5. Do not use “first,” “novel,” “unprecedented,” or “new class of AI” until the claim chart survives expert review.

## 6. Name check

“Affective Actor-Critic Engine” and the acronym “AACE” should be treated as a working research name. Before public branding, perform trademark, company-name, package-name, and academic acronym searches. The technical contribution should not depend on the emotional branding.
