# Survival AI / Affective Actor-Critic Engine (AACE)
## Master Research Blueprint — Start Here

**Working thesis:** Build autonomous agents that understand consequences rather than merely maximize reward or minimize danger. AACE gives an agent an explicit model of its own vulnerability, lets a world model imagine futures in which actions and inaction cause damage, and changes the agent's decision process as irreversible risk rises. The goal is not to make software literally feel fear, pain, guilt, or courage. The goal is to engineer measurable computational analogues: damage and viability, anticipatory threat prediction, deliberate risk taking, threat-conditioned cognition, counterfactual learning after failure, and persistent memory of harmful trajectories.

This archive is deliberately **research-first and no-code**. It contains the technical vision, mathematical foundations, prior-art map, experiment design, datasets and simulation environments, reading plan, learning curriculum, commercialization path, risk register, and falsification criteria needed before implementation.

## The core research question

> Can an artificial agent model its own vulnerability, imagine the consequences of action and inaction, remember harmful decisions, and distinguish worthwhile risk from recklessness while generalizing those lessons to novel hazards better than existing safe, risk-sensitive, and model-based RL baselines?

This is a harder and more defensible claim than “AI with fear.” Basic fear penalties, safe RL, CVaR objectives, shielding, and counterfactual replay already exist. AACE only becomes interesting if the **full architecture** produces behavior that cannot be explained by ordinary reward shaping or a standard constraint penalty.

## What AACE is

AACE separates task performance from consequence reasoning. A standard actor still pursues the task. A separate affective system estimates viability, future catastrophe risk, uncertainty, recoverability, consequences of inaction, and memory of similar harmful situations. Fear informs the decision but does not automatically win. Under authorized objectives, the agent may rationally accept substantial self-risk when the alternative is worse. That system can move the agent between operating regimes:

1. **Normal:** maximize task performance while respecting safety constraints.
2. **Alert:** increase pessimistic planning, reduce exploration, preserve resources, and favor recoverable actions.
3. **Critical:** prioritize survival and recovery by default, while permitting explicitly authorized deliberate risk when mission consequences justify it.
4. **Post-event reflection:** reconstruct the failure, simulate alternative actions, estimate which decision mattered, and store a calibrated “scar” for later retrieval.

The architecture therefore combines five core ideas:

- **Survival instinct:** preserve a viable operating envelope.
- **Fear:** prospective estimate of catastrophic risk.
- **Fear of consequences:** action selection based on long-horizon irreversible outcomes, not only local reward.
- **Deliberate risk / computational courage:** knowingly accepting modeled danger when an externally authorized objective justifies it.
- **Counterfactual guilt:** retrospective regret over actions that materially increased catastrophe probability, stored as persistent consequence memory.

## What AACE is not

AACE is **not** a claim that current AI has no memory, no safety methods, or only chases positive rewards. Modern RL already includes replay buffers, recurrent memory, world models, constrained objectives, robust policies, safety filters, and risk-sensitive optimization. The phrases “fear,” “guilt,” and “survival instinct” are biological metaphors for engineering mechanisms and must never substitute for measurable definitions.

AACE is also not a formal safety guarantee by itself. In safety-critical deployment, a learned survival layer should sit beside or beneath independent safeguards such as control barrier functions, runtime shields, model predictive safety filters, reachability analysis, watchdogs, and human override.

## The first falsifiable prototype

The recommended first research environment is a simulated continuous-control agent with:

- a task reward,
- internal resource limits,
- known hazards,
- rare catastrophic hazards,
- irreversible failure states,
- recoverable near-failure states,
- partial observability,
- controllable uncertainty,
- and a held-out hazard family that is never seen during training.

Compare:

- PPO or Dreamer-style baseline,
- reward-penalty baseline,
- risk-sensitive CVaR baseline,
- constrained RL / CPO-style baseline,
- Recovery RL or shielded baseline,
- SafeDreamer-style world-model baseline,
- intrinsic-fear baseline,
- AACE without scars,
- AACE without regime switching,
- full AACE.

The decisive result is **not** “AACE is more cautious.” AACE must sometimes take more risk than a conservative safe-RL baseline when the modeled consequence of inaction or mission failure justifies it. The decisive result would be something like:

> After limited exposure to one class of catastrophe, full AACE reduces repeat and structurally related unseen catastrophes, avoids unnecessary danger, and still accepts justified high-risk actions when the alternative is worse, outperforming the best matched safe-RL baseline at comparable compute and externally specified constraints.

## Go / no-go criteria

Continue investing only if AACE demonstrates at least one of the following reproducibly:

- lower catastrophic-event rate at matched task return,
- better OOD hazard survival at matched in-distribution performance,
- faster learning from one or a few catastrophic examples,
- fewer repeat catastrophes after reflection,
- better calibration of danger than standard cost critics,
- useful adaptive compute allocation under threat,
- or better recovery success without simply becoming globally conservative.

Kill or radically reframe the idea if a standard SafeDreamer, CPO, Recovery RL, shield, or CVaR agent matches AACE once hyperparameters and compute are controlled.

## Folder map

- `00_Vision/` — full vision, claim audit, scope, terminology.
- `01_Architecture/` — system components, data flow, operating modes, interfaces.
- `02_Mathematics/` — formal problem, risk, viability, world models, deliberate risk, action versus inaction, affective critic, counterfactual scars, losses, calibration.
- `03_Research_Literature/` — prior art, paper map, novelty boundary, search strategy.
- `04_Experiments/` — benchmark design, ablations, metrics, statistical plan, staged research roadmap.
- `05_Data_Environments/` — simulation environments and public datasets by domain.
- `06_Learning_Path/` — beginner-to-research curriculum and prerequisites.
- `07_Business/` — customer wedge, value proposition, commercialization, moat, competitive positioning.
- `08_Safety_Governance/` — deployment principles, human-subjects caution, misuse and failure modes.
- `09_Open_Questions/` — unresolved research questions and kill criteria.
- `References/` — curated paper list, BibTeX, web sources.

## Recommended reading order

Read these files in sequence:

1. `00_Vision/FULL_VISION.md`
2. `00_Vision/CLAIM_AUDIT_AND_NOVELTY.md`
3. `01_Architecture/AACE_ARCHITECTURE.md`
4. `02_Mathematics/MATHEMATICAL_SPEC.md`
5. `02_Mathematics/CONSEQUENCE_AWARE_DECISION_THEORY.md`
6. `03_Research_Literature/PRIOR_ART_MAP.md`
7. `03_Research_Literature/PAPER_READING_GUIDE.md`
8. `04_Experiments/EXPERIMENT_PROGRAM.md`
9. `06_Learning_Path/LEARNING_CURRICULUM.md`
10. `07_Business/COMPANY_AND_PRODUCT.md`

## Working one-line pitch

**Research:** “A consequence-aware survival architecture that models vulnerability, imagines action and inaction outcomes, changes how it reasons under threat, and learns when danger should be avoided or deliberately accepted.”

**Commercial:** “A survival runtime for autonomous systems operating where failure is expensive, recovery is difficult, and ordinary reward optimization is not enough.”

**Long-term:** “Machines that understand what can hurt them, what happens if they act or do nothing, and when a dangerous action is still worth taking.”
