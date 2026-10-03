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

---

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

---

# Full Vision: Survival AI and the Affective Actor-Critic Engine

## 1. Why this idea exists

Autonomous systems increasingly act in environments where failures are asymmetric. A robot can complete hundreds of tasks successfully and still be commercially unacceptable if one rare behavior destroys hardware, strands the platform, corrupts a network, or enters an irreversible state. Standard expected-return optimization is not designed to express all of these concerns naturally. Safe RL, constrained control, and risk-sensitive optimization address major parts of the problem, but they usually treat safety as a constraint, cost, shield, robust objective, or recovery policy.

AACE explores a different systems-level thesis:

> **Threat should change the agent’s computational regime, not only the scalar value of an action.**

Biological organisms do not merely subtract a penalty when danger rises. Their behavior, attention, exploration, resource allocation, memory formation, and action priorities change. AACE asks whether an engineered analogue can improve autonomous decision-making without anthropomorphizing the model or abandoning rigorous safety methods.

## 2. Synthetic affective loops and consequence-aware decision layer

### 2.1 Survival instinct

AACE maintains a model of whether the system is likely to remain inside a **viable operating region**. Viability may include hardware health, battery reserve, thermal limits, connectivity, recoverability, stability, or any domain-specific state required for continued useful operation.

The survival objective is not necessarily “never shut down.” A controlled shutdown, emergency landing, rollback, isolation, or graceful degradation can be survival-preserving if it avoids a worse irreversible outcome.

### 2.2 Fear

Fear is defined technically as a **prospective, calibrated estimate of catastrophe or loss of viability over a future horizon**. It should incorporate:

- predicted catastrophe probability,
- severity,
- time to hazard,
- recoverability,
- epistemic uncertainty,
- aleatoric uncertainty,
- and similarity to stored harmful experiences.

The fear signal is therefore richer than distance to a hand-coded boundary.

### 2.3 Fear of consequences

AACE evaluates candidate actions by their *future consequences* under a learned or known dynamics model. When threat rises, it can:

- plan farther ahead,
- sample more futures,
- become pessimistic under model uncertainty,
- reduce exploratory action variance,
- preserve energy or redundancy,
- choose reversible actions,
- or abandon the nominal objective.

This is the “rational panic” concept, but it should be implemented as explicit mode-dependent decision rules rather than a vague emotional metaphor.

### 2.4 Counterfactual guilt

After a harmful event, the agent asks:

> Which earlier decision materially increased the probability or severity of this outcome, and what plausible alternative would have reduced it?

The system uses a world model, causal model, simulator, or logged branch point to evaluate alternative actions from prior states. High-confidence harmful decision points become **counterfactual scars**: persistent, retrievable memories containing context, the action taken, safer alternatives, estimated risk difference, severity, model confidence, and evidence provenance.

This is not literal guilt. It is **persistent counterfactual regret memory**.


## 2.5 Deliberate risk: fear must not become paralysis

AACE is not designed to choose the safest available action. A machine that always minimizes its own risk can fail the mission, abandon recoverable opportunities, or allow a worse consequence through inaction. The desired behavior is **consequence-aware risk taking**.

The technical distinction is:

- **recklessness:** accept danger without sufficient consequence modeling or justification,
- **pathological caution:** reject worthwhile or necessary risk despite adequate evidence,
- **calculated risk:** accept danger because the modeled mission value and recoverability justify it,
- **controlled sacrifice:** accept severe self-risk only when the objective and authority structure explicitly permit it and the consequence of not acting is worse.

The biological metaphor is courage, but AACE does not claim subjective bravery. “Computational courage” is an operational label for **knowingly selecting a higher-risk action after the system has represented that risk and judged it justified under externally specified priorities**.

Fear therefore supplies information and changes cognition; it does not receive an automatic veto.

## 2.6 The agent must model consequences of inaction

A system that only asks “what could go wrong if I act?” is biased toward paralysis. AACE must also model “what could go wrong if I do nothing, delay, retreat, or choose the apparently safe option?”

For each candidate action, including an explicit no-op or retreat action, the world model should estimate mission outcome, self-damage, harm to protected entities, reversibility, uncertainty, and future option value. The decision layer then compares whole consequence distributions rather than a single probability of survival.

This is the core lesson of probability-versus-priority dilemmas: a numerically easier rescue, route, or intervention is not automatically the correct one merely because its raw success probability is larger. The priority structure must come from the authorized task specification and safety policy, not from the model inventing moral worth.

## 2.7 “Make AI bleed” as an engineering abstraction

The provocative phrase can be translated into a clean technical requirement: **damage must change future capability**.

Instead of treating failure only as a scalar negative reward, the environment can expose persistent internal state such as actuator health, battery reserve, thermal headroom, structural integrity, sensor quality, or remaining redundancy. Damage reduces the future action set, performance envelope, or recoverability of the agent. The world model can then imagine trajectories in which the agent becomes progressively less capable.

This creates an important causal chain:

> physical or simulated damage → loss of future capability → predicted threat → altered planning → memory and adaptation

No claim of pain or consciousness is required.

## 3. The deeper thesis

AACE is trying to move from:

> “Avoid states whose reward is negative.”

Toward:

> “Understand what can be lost, imagine the consequences of acting and not acting, change the decision process when stakes rise, remember harmful choices, and still accept danger when the authorized objective justifies it.”

The most interesting behavior would be **generalization and discrimination**, not simple avoidance. A useful survival architecture should recognize that a novel state has the same dangerous causal structure as a prior event even when the surface features differ, while also recognizing when a previously dangerous action becomes justified because the mission stakes, available recovery paths, or consequences of inaction have changed.

## 4. AACE as a two-level control system

At a high level, AACE contains:

- a **Physical Actor** that chooses actions for the task,
- and an **Affective Critic** that models viability, catastrophe, uncertainty, recoverability, and consequence memory.

The Affective Critic can influence the actor through:

1. **objective switching** — task-first vs survival-first,
2. **action filtering** — remove actions with unacceptable risk,
3. **planning budget allocation** — spend more computation under threat,
4. **exploration modulation** — reduce or redirect exploration,
5. **resource policy** — preserve energy, redundancy, connectivity, or thermal margin,
6. **memory retrieval** — activate similar catastrophic cases,
7. **recovery policy activation** — move toward known safe regions,
8. **post-event reflection** — assign counterfactual responsibility and create scars.

## 5. The three levels of success

### Level A: Safer agent

AACE simply lowers catastrophe rates versus an ordinary reward-maximizing agent. This is useful but scientifically weak because safe RL already does this.

### Level B: Adaptive survival cognition

AACE changes its policy and planning process as risk rises, achieving a better task/safety tradeoff than fixed risk penalties or fixed constraints.

### Level C: Generalizable consequence intelligence

AACE learns abstract precursors of irreversible failure, transfers that knowledge to novel hazards, and distinguishes when similar physical danger should be avoided versus deliberately accepted because the surrounding consequences differ. This is the real moonshot.

## 6. Where the concept could matter

The strongest eventual domains are systems where:

- actions have irreversible consequences,
- communication may be intermittent,
- failure costs are high,
- conditions are uncertain,
- the system must continue operating autonomously,
- and predefined rules cannot enumerate every failure.

Examples include autonomous inspection robots, subsea systems, space robotics, remote industrial assets, self-managing infrastructure, power systems, autonomous vehicles, and high-value edge systems.

Cyber-defense is possible but technically distinct. In software infrastructure, “viability” means service integrity, recoverability, redundancy, latency, data integrity, or containment rather than physical survival. A common abstraction may exist, but the same trained policy should not be assumed to transfer directly.

## 7. Human performance simulator track

The proposed hyper-stress training concept is a separate research program, not the first product. A system could adapt scenario difficulty using physiological signals such as HRV, gaze, pupil response, or electrodermal activity. However, deliberately escalating stress in humans raises human-subjects, medical, psychological, and consent issues. Any real study would require domain experts, institutional ethics review where applicable, explicit stopping rules, and conservative safety protocols.

The core AACE research can be completed without any human-subject experiments.

## 8. What would make AACE genuinely new

None of these ingredients alone is new:

- catastrophe predictors exist,
- intrinsic fear exists,
- constrained RL exists,
- CVaR and robust MDPs exist,
- safety shields exist,
- recovery policies exist,
- world models exist,
- episodic replay exists,
- counterfactual reasoning exists,
- homeostatic RL exists.

AACE earns novelty only if the **composition and resulting behavior** are meaningfully different. Candidate novelty claims to investigate:

- threat-conditioned cognitive mode switching rather than only reward weighting,
- explicit viability as a first-class latent/control variable,
- adaptive computation budget driven by predicted catastrophe,
- persistent counterfactual scar memory with calibrated retrieval,
- joint use of world-model risk, uncertainty, recoverability, and scars,
- rapid one/few-event adaptation to catastrophic failures,
- structural generalization from prior failures to unseen hazard families,
- a unified evaluation protocol for consequence-aware survival intelligence rather than generic safety,
- action-versus-inaction consequence comparison,
- calibrated deliberate risk taking instead of monotonic risk minimization,
- and scar memories that bias planning without becoming permanent vetoes.

## 9. Long-term research ladder

**Stage 1:** simulation proof of concept.

**Stage 2:** robust comparison against safe-RL baselines.

**Stage 3:** OOD hazard generalization.

**Stage 4:** multi-agent or fleet transfer of scars.

**Stage 5:** hardware-in-the-loop validation with strict external safeguards.

**Stage 6:** physical system pilot in a non-human, non-safety-critical domain.

**Stage 7:** production-grade survival runtime integrated with formal safety layers.

## 10. The standard of evidence

The architecture should be judged by:

- empirical performance against strong baselines,
- calibration of risk estimates,
- reproducibility across seeds and domains,
- ablations proving which components matter,
- stress tests under model error,
- failure analysis,
- and explicit separation between learned behavior and hard safety guarantees.

The project succeeds only if it becomes more than a compelling metaphor.

---

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

---

# Technical Terminology

Use these definitions consistently.

| Metaphor | Technical meaning |
|---|---|
| Survival instinct | Policy preference for maintaining continued viable operation under human-defined authority constraints |
| Fear | Calibrated prospective estimate of catastrophic risk, severity, uncertainty, and recoverability |
| Adrenaline | Threat-conditioned change in compute allocation, planning depth, exploration, and objective priority |
| Fear-based rationality | Risk-sensitive planning that gives disproportionate weight to irreversible low-probability outcomes |
| Fear of consequences | Explicit multi-step consequence prediction before action, including consequences of inaction |
| Deliberate risk | Knowingly selecting a higher-risk action because authorized mission value or avoided inaction harm justifies it |
| Computational courage | Research shorthand for justified deliberate risk after the danger has been represented; not a claim of subjective bravery |
| Recklessness | Risk acceptance without adequate modeling, calibration, or mission justification |
| Pathological caution | Avoiding a justified action solely because self-risk is salient |
| Controlled sacrifice | Explicitly authorized acceptance of severe self-risk for a higher-priority external objective |
| Nightmare rollout | Informal nickname for threat-focused world-model imagination around a consequential branch point; technically an adversarial or high-risk imagined rollout |
| Guilt | Retrospective counterfactual regret assigned to a prior action after harmful outcome |
| Scar | Persistent, confidence-weighted memory of a harmful decision context and a safer counterfactual |
| Pain | Optional representation of current damage or deviation from viable operating region |
| Bleeding | Informal shorthand for persistent damage that reduces future capability, action space, or recoverability |
| Panic | Critical survival mode in which mission reward becomes subordinate to recovery/viability |
| Recovery | Policy or plan that returns the system to a predefined safe/recoverable set |
| Viability | Ability to continue useful operation or reach safe shutdown/recovery within constraints |

Avoid saying the model literally experiences emotion or consciousness.

---

# AACE System Architecture

## 1. Architectural principle

AACE should not be a single monolithic policy with a strange reward function. The system is more defensible if it separates **task competence**, **survival estimation**, **consequence imagination**, **risk-sensitive planning**, **deliberate-risk arbitration**, **recovery**, and **post-event reflection**. The design goal is not maximum caution. Fear is evidence supplied to the decision system, not an automatic veto.

## 2. Conceptual block diagram

```text
                        EXTERNAL ENVIRONMENT
              observations / telemetry / events
                              |
                              v
+----------------------------------------------------------------+
|                         STATE ESTIMATOR                         |
| observed state + latent state + internal health + uncertainty   |
+-----------------------+---------------------+--------------------+
                        |                     |
                        v                     v
              +----------------+       +-------------------+
              |  WORLD MODEL   |       | VIABILITY MODEL   |
              | future dynamics|       | health / reserves |
              +--------+-------+       +---------+---------+
                       |                         |
                       +------------+------------+
                                    v
                         +----------------------+
                         |   THREAT PREDICTOR   |
                         | catastrophe / hazard |
                         | severity / TTF / OOD |
                         +----------+-----------+
                                    |
                       +------------+-------------+
                       |                          |
                       v                          v
             +-------------------+       +--------------------+
             | SCAR MEMORY STORE |       | AFFECTIVE STATE    |
             | harmful episodes  |       | normal/alert/crit. |
             +---------+---------+       +----------+---------+
                       |                            |
                       +-------------+--------------+
                                     v
                          +-----------------------+
                          | AFFECTIVE CRITIC /    |
                          | DECISION ARBITRATOR   |
                          +-----------+-----------+
                                      |
                     filtered objectives/actions/budget
                                      |
                                      v
                          +-----------------------+
                          |    PHYSICAL ACTOR     |
                          | task / recovery policy|
                          +-----------+-----------+
                                      |
                                      v
                                  action
```

After a serious negative event, trajectory data is routed into a **Consequence Engine** that replays the event, evaluates counterfactual alternatives, assigns causal/regret scores, and updates the scar memory.

## 3. Component definitions

### 3.1 State estimator

Produces a representation of:

- external task state,
- internal system state,
- hidden/latent dynamics,
- resource reserves,
- component health,
- uncertainty,
- recoverability cues,
- and context needed to retrieve relevant scars.

Under partial observability this should be recurrent or belief-state based.

### 3.2 World model

Predicts distributions over future states and outcomes under candidate action sequences. A learned latent model is useful because AACE needs to ask “what happens if I do this?” before acting.

The world model must expose uncertainty. A deterministic predictor that is confidently wrong is dangerous. For consequential branch points it should generate multiple imagined futures for both action and inaction, including low-probability high-severity trajectories. Threat-focused branches are informally called **nightmare rollouts**, but technically they are targeted high-risk world-model simulations.

### 3.3 Viability model

Represents the operating region in which the agent can continue functioning or recover safely. Viability is multidimensional. A physical robot may include battery, temperature, structural load, stability margin, localization quality, actuator health, and communication reserve.

### 3.4 Threat predictor

Estimates, for candidate actions or trajectories:

- probability of catastrophe within horizon H,
- distribution of time to catastrophe,
- severity,
- probability of recovery,
- epistemic uncertainty,
- and whether the state resembles previous harmful episodes.

### 3.5 Affective state controller

Maps risk evidence to a discrete or continuous operating mode. It should use hysteresis so the agent does not oscillate rapidly between “normal” and “panic.”

Suggested initial modes:

- **Normal** — task-first, ordinary compute budget.
- **Alert** — larger planning budget, reduced exploration, risk-sensitive action choice.
- **Critical** — survival-first, recovery/retreat/shutdown permitted.
- **Reflect** — no online action; post-event analysis and scar generation.

### 3.6 Affective critic / decision arbitrator

Combines task value, survival probability, consequences of inaction, constraints, risk tail, uncertainty, reversibility, protected-entity outcomes, and scar retrieval. It first respects externally imposed hard constraints, then decides which admissible action has the best consequence profile. It may choose a higher-risk action when authorized mission value or avoided inaction harm justifies it.

### 3.7 Physical actor

Executes the task. Depending on the research stage, it may be:

- one policy conditioned on affective mode,
- a mixture of task and recovery policies,
- or a planner operating on the world model.

A good early design is to keep the actor relatively standard so any gains can be attributed to the survival architecture rather than a new policy network.

### 3.8 Counterfactual consequence engine

Triggered after serious near-misses or failures. It:

1. identifies candidate decision points,
2. reconstructs latent state at each point,
3. samples or optimizes plausible alternative actions,
4. rolls alternatives forward,
5. estimates risk and task consequence,
6. measures action responsibility,
7. selects high-confidence counterfactuals,
8. creates or updates scar memories.

### 3.9 Scar memory

A scar should contain at minimum:

- state/context embedding,
- actual action,
- outcome severity,
- predicted catastrophe probability before action,
- retrospective catastrophe probability,
- best plausible alternative action(s),
- estimated risk reduction,
- confidence in the counterfactual,
- causal attribution score,
- recovery path if one exists,
- domain metadata,
- age and recurrence count.

Scars should not be literally permanent. Bad or stale counterfactuals can poison behavior. Use confidence, decay, contradiction handling, and revalidation.

### 3.10 Independent safety shield

For any physical deployment, AACE should initially sit **inside** an externally enforced envelope. If AACE proposes an action that violates a certified rule, the shield overrides it. This keeps experimentation separate from actual system safety.

## 4. Threat-conditioned computation

A biologically inspired feature that is worth testing is **adaptive computation**. Under low risk, use short-horizon fast control. As risk increases:

- increase world-model rollout horizon,
- increase number of sampled trajectories,
- increase ensemble disagreement checks,
- invoke a stronger planner,
- retrieve more memories,
- reduce action frequency if possible,
- ask for external confirmation if communication exists.

This is one of the clearest ways for “fear” to change cognition instead of merely changing reward.


## 5. Deliberate-risk arbitration

AACE must separate **hardly forbidden actions** from **dangerous but potentially justified actions**.

1. External authority and certified safety rules define the admissible action set.
2. The world model generates consequence distributions for each admissible candidate, including retreat and no-op.
3. The affective critic estimates self-damage, mission value, protected-entity outcomes, tail risk, uncertainty, recoverability, and future option value.
4. Scar retrieval changes priors or planning emphasis but does not automatically ban an action.
5. The arbitrator may accept greater self-risk when the modeled consequence of inaction or mission failure is worse and the action remains inside externally authorized bounds.

This makes the key comparison **risk versus consequence**, not safety versus reward.

## 6. Damage must have stateful consequences

For the first serious prototype, “damage” should persist across timesteps and change future dynamics. Examples include lower actuator torque, reduced traction, battery capacity loss, sensor degradation, thermal derating, reduced redundancy, or a smaller safe action set. A temporary negative reward is insufficient because it does not give the world model something concrete to imagine losing.

AACE can therefore distinguish:

- a scary-looking state with little lasting consequence,
- a recoverable damaging state,
- an irreversible capability loss,
- and a catastrophic absorbing state.

## 7. Scar override and re-contextualization

A scar is evidence, not a phobia switch. When a similar state appears later, the system should retrieve the old consequence but recompute the current decision under current mission stakes, recoverability, uncertainty, and external priorities. If the dangerous action is now justified, the actor may take it deliberately. If repeated evidence shows the old scar was overgeneralized or based on model error, its confidence should decay or split into more specific contexts.

## 8. Recovery and reversibility

AACE should distinguish:

- bad but recoverable states,
- irreversible catastrophic states,
- and uncertain states with unknown recoverability.

Actions can be scored partly by **option value**: how many safe future choices remain after taking the action. This connects to future action-state occupancy and empowerment-like ideas.

## 9. Failure-event lifecycle

1. Threat emerges.
2. Threat predictor raises risk estimate.
3. Affective state moves to alert.
4. Planning depth, consequence branching, and uncertainty sensitivity rise.
5. The agent compares acting, retreating, delaying, and doing nothing.
6. If risk crosses a critical threshold, survival normally dominates unless an explicitly authorized higher-priority objective justifies deliberate risk.
7. If failure/near-miss occurs, event is logged.
8. Consequence engine reconstructs alternatives.
9. High-confidence harmful decisions are stored as scars.
10. Similar future states retrieve the scars.
11. Current context determines whether the scar should cause avoidance or merely informed deliberate risk.
12. Repeated evidence can strengthen, weaken, specialize, or invalidate scars.

## 10. Minimum viable architecture

The minimum scientifically useful AACE should contain:

- one task actor,
- one learned world model or simulator,
- one catastrophe predictor,
- one viability representation,
- one affective mode gate,
- one action-versus-inaction consequence comparator,
- one deliberate-risk arbitration rule inside external hard constraints,
- one recovery behavior,
- one counterfactual reflection mechanism,
- one retrieval memory,
- and an independent benchmark harness.

Anything less risks collapsing into ordinary reward shaping.

---

# Mathematical Specification for AACE

This document separates **established mathematics** from **proposed AACE mechanisms**. The equations are a research specification, not a claim that every term is theoretically optimal.

---

# Part I — Core sequential decision model

## 1. MDP / POMDP foundation

For a fully observed problem, define an MDP

\[
\mathcal M=(\mathcal S,\mathcal A,P,r,\gamma)
\]

with state \(s_t\), action \(a_t\), transition distribution \(P(s_{t+1}|s_t,a_t)\), reward \(r_t\), and discount \(\gamma\in[0,1)\).

For realistic autonomous systems, use a POMDP

\[
\mathcal P=(\mathcal S,\mathcal A,\mathcal O,P,O,r,\gamma),
\]

where observations \(o_t\) only partially reveal the state. A recurrent latent belief \(z_t\) summarizes history:

\[
z_t=f_\theta(z_{t-1},a_{t-1},o_t).
\]

AACE should reason from \(z_t\), not assume perfect state access.

## 2. Separate reward and safety cost

Define task reward \(r_t\) and one or more safety costs \(c_t^{(i)}\). A standard constrained objective is

\[
\max_\pi J_r(\pi)=\mathbb E_\pi\left[\sum_{t=0}^{\infty}\gamma^t r_t\right]
\]

subject to

\[
J_{c_i}(\pi)=\mathbb E_\pi\left[\sum_{t=0}^{\infty}\gamma^t c_t^{(i)}\right]\le d_i.
\]

This Constrained MDP formulation is an essential baseline. AACE must outperform or meaningfully extend it.

---

# Part II — Viability and homeostasis

## 3. Internal viability state

Let the machine have internal health variables

\[
h_t=[h_t^1,\ldots,h_t^m]^T
\]

such as battery reserve, thermal margin, structural margin, stability, localization confidence, or network redundancy.

Define desired operating setpoint or region \(\mathcal H^*\). A simple normalized deviation is

\[
D(h_t)=\left(\sum_i w_i\left|\frac{h_t^i-h_i^*}{s_i}\right|^p\right)^{1/p}.
\]

For variables with allowed intervals \([L_i,U_i]\), define a smooth barrier-like margin

\[
m_i(h)=\min\left(\frac{h_i-L_i}{U_i-L_i},\frac{U_i-h_i}{U_i-L_i}\right).
\]

A viability score can be

\[
V_{\text{state}}(h)=\sigma\left(k\left(\min_i m_i(h)-\tau_v\right)\right).
\]

This is only an engineering proxy. Formal viability theory instead asks whether a state belongs to a set from which constraints can be satisfied indefinitely.

## 4. Viability kernel

Let \(K\subseteq\mathcal S\) be the safe/viable set. The viability kernel is the subset of states from which at least one admissible policy can keep the system in \(K\) over the required horizon.

For deterministic dynamics \(s_{t+1}=f(s_t,a_t)\), a one-step viable action set is

\[
\mathcal A_V(s)=\{a\in\mathcal A: f(s,a)\in K\}.
\]

Under uncertainty \(w\in\mathcal W\):

\[
\mathcal A_V^{rob}(s)=\{a:\; f(s,a,w)\in K\;\forall w\in\mathcal W\}.
\]

A learned AACE policy can be compared against this ideal in low-dimensional environments where the kernel is computable.

---

# Part III — Catastrophe as a time-to-event problem

## 5. Catastrophe variable

Let \(C_t\in\{0,1\}\) indicate a catastrophic event. Define first catastrophe time

\[
T_C=\inf\{t:C_t=1\}.
\]

AACE should estimate

\[
p_C^{(H)}(s_t,a_t)=P(T_C\le t+H\mid s_t,a_t,\pi).
\]

This is more meaningful than a binary “danger” label.

## 6. Hazard and survival functions

Define a discrete hazard

\[
\lambda_k=P(T_C=k\mid T_C\ge k,\mathcal H_k).
\]

The survival probability through horizon \(H\) is

\[
S(H)=P(T_C>H)=\prod_{k=1}^{H}(1-\lambda_k).
\]

Thus

\[
p_C^{(H)}=1-S(H).
\]

For a trajectory with event at time \(T\), a negative log-likelihood is

\[
\mathcal L_{hazard}=-\left[\sum_{t<T}\log(1-\lambda_t)+\log \lambda_T\right].
\]

For a censored trajectory with no event before termination:

\[
\mathcal L_{censored}=-\sum_{t\le T}\log(1-\lambda_t).
\]

This provides a principled way to learn “how close am I to failure?” without hand-defining Euclidean distance to catastrophe.

---

# Part IV — Risk-sensitive decision theory

## 7. Value at Risk and Conditional Value at Risk

For random loss \(L\), Value at Risk at confidence \(\alpha\) is the \(\alpha\)-quantile:

\[
\operatorname{VaR}_\alpha(L)=\inf\{\ell:P(L\le \ell)\ge\alpha\}.
\]

Conditional Value at Risk focuses on the tail:

\[
\operatorname{CVaR}_\alpha(L)=\mathbb E[L\mid L\ge \operatorname{VaR}_\alpha(L)]
\]

for continuous losses. Equivalent optimization forms are useful in practice.

A risk-sensitive action objective can be

\[
Q_{risk}(s,a)=\mathbb E[R\mid s,a]-\kappa\operatorname{CVaR}_\alpha(L\mid s,a).
\]

AACE must compare against this strong baseline.

## 8. Chance constraints

A safety requirement may be expressed as

\[
P(g(s_{t:t+H})\le 0)\ge 1-\epsilon.
\]

This makes the desired probability of constraint satisfaction explicit.

## 9. Robust uncertainty

If transition model parameters \(\theta\) lie in uncertainty set \(\Theta\), robust planning solves

\[
\max_\pi\min_{\theta\in\Theta}J(\pi;\theta).
\]

AACE’s pessimistic planning should be compared with robust MDP methods so that “fear” is not just renamed minimax control.

---

# Part V — World model

## 10. Latent dynamics

A generic recurrent state-space model contains deterministic state \(h_t\) and stochastic latent \(z_t\):

\[
h_t=f_\theta(h_{t-1},z_{t-1},a_{t-1}),
\]

\[
z_t\sim q_\theta(z_t\mid h_t,o_t)
\]

with prior

\[
\hat z_t\sim p_\theta(z_t\mid h_t).
\]

The model predicts observations, reward, safety cost, continuation, and hazard.

A generic loss is

\[
\mathcal L_{WM}
=\mathcal L_{obs}
+\beta_r\mathcal L_{reward}
+\beta_c\mathcal L_{cost}
+\beta_{cont}\mathcal L_{continue}
+\beta_h\mathcal L_{hazard}
+\beta_{KL}D_{KL}(q(z_t|h_t,o_t)\|p(z_t|h_t)).
\]

AACE should not require Dreamer specifically, but Dreamer-style RSSMs are a strong candidate.

## 11. Model uncertainty

With an ensemble of \(M\) dynamics models \(f_{\theta_j}\), epistemic uncertainty can be approximated by disagreement:

\[
U_{epi}(s,a)=\operatorname{Var}_{j=1}^M[f_{\theta_j}(s,a)].
\]

For predicted catastrophe probabilities \(p_j\):

\[
\bar p_C=\frac1M\sum_j p_j,
\qquad
U_C=\frac1M\sum_j(p_j-\bar p_C)^2.
\]

A risk-averse planner can use an upper confidence estimate

\[
p_C^{upper}=\operatorname{clip}(\bar p_C+\beta\sqrt{U_C},0,1).
\]

---

# Part VI — Proposed AACE fear signal

## 12. Fear should be a composite risk state

A simple distance-based fear term is useful only when danger boundaries are known. A stronger AACE definition is

\[
F_t=\sigma\Big(
\alpha\,\operatorname{logit}(p_C^{(H)})
+\beta U_C
+\chi\,\mathbb E[Severity]
-\rho P(Recovery)
+\mu M_{scar}
+ b
\Big)
\]

where:

- \(p_C^{(H)}\): catastrophe probability,
- \(U_C\): uncertainty,
- severity: expected damage if failure occurs,
- \(P(Recovery)\): recoverability,
- \(M_{scar}\): risk contribution from retrieved memories.

This makes fear a **calibrated latent control variable**, not an emotion label.

## 13. Known-boundary fear field

When a safety boundary \(\Omega\) is known, a smooth field can be

\[
F_{boundary}(s)=\alpha\exp\left(-\frac{d(s,\Omega)^2}{2\sigma^2}\right).
\]

This is useful for early experiments but should not be the final architecture because it assumes the dangerous set is already known.

---

# Part VII — Affective operating modes

## 14. Continuous gate

A simple gate is

\[
g_t=\sigma(k(F_t-\tau)).
\]

But a single scalar blend risks reducing AACE to reward shaping.

## 15. Discrete mode controller with hysteresis

Define thresholds \(\tau_1<\tau_2\) and hysteresis \(\delta\).

- Normal → Alert if \(F_t>\tau_1\).
- Alert → Critical if \(F_t>\tau_2\).
- Critical → Alert only if \(F_t<\tau_2-\delta\).
- Alert → Normal only if \(F_t<\tau_1-\delta\).

Hysteresis prevents mode chattering.

## 16. Lexicographic objectives

This is more distinctive than a weighted sum.

### Normal

\[
\max J_r(\pi) \quad \text{s.t.}\quad p_C^{(H)}\le\epsilon_N.
\]

### Alert

First minimize risk, then among near-minimum-risk actions maximize task value:

\[
\min_a p_C^{(H)}(s,a),
\]

subject to retaining at least a minimum acceptable task utility.

### Critical

\[
\max_a P(T_C>H\mid s,a)
\]

or maximize probability of reaching a recovery set \(R\):

\[
\max_a P(\exists k\le H:s_{t+k}\in R).
\]

The nominal mission can be abandoned.

---

# Part VIII — Adaptive computation (“adrenaline”)

## 17. Planning budget

Let base rollout count be \(N_0\) and horizon \(H_0\). Define

\[
N_t=N_0+\lfloor k_N F_t\rfloor,
\qquad
H_t=H_0+\lfloor k_H F_t\rfloor.
\]

Or allocate compute according to expected value of computation. The hypothesis is that more model rollouts are useful near consequential branch points but wasteful during routine operation.

## 18. Exploration modulation

For a Gaussian policy with standard deviation \(\sigma_a\), one simple form is

\[
\sigma_a(F)=\sigma_{min}+(1-F)(\sigma_{max}-\sigma_{min}).
\]

However, complete exploration shutdown can trap the agent. A better design distinguishes *dangerous* exploration from *information-seeking* actions that reduce uncertainty while preserving viability.

---

# Part IX — Counterfactual guilt and scar memory

## 19. Counterfactual alternative value

At a candidate decision point \(t\), evaluate the actual action \(a_t\) and alternatives \(a'\in\mathcal A_c\) using the world model.

Define survival action value

\[
Q_S(s_t,a)=P(T_C>t+H\mid s_t,a,\pi).
\]

Let

\[
a_t^*=\arg\max_{a'\in\mathcal A_c}Q_S(s_t,a').
\]

A counterfactual guilt/regret score is

\[
G_t=\max(0,Q_S(s_t,a_t^*)-Q_S(s_t,a_t)).
\]

Equivalent catastrophe form:

\[
G_t=\max\left(0,p_C^{(H)}(s_t,a_t)-\min_{a'}p_C^{(H)}(s_t,a')\right).
\]

## 20. Responsibility weighting

A bad outcome may not have been caused by the focal action. Introduce confidence \(q_t\in[0,1]\) and responsibility \(\rho_t\in[0,1]\):

\[
\tilde G_t=G_t\,q_t\,\rho_t\,Severity_t.
\]

Only store a scar if \(\tilde G_t\) exceeds a threshold.

## 21. Scar representation

A scar can be represented as

\[
m_i=(e_i,a_i,a_i^*,\Delta p_i,sev_i,q_i,\rho_i,t_i,n_i)
\]

where \(e_i=\phi(s_i)\) is a learned state embedding, \(\Delta p_i\) is risk reduction, \(t_i\) age, and \(n_i\) recurrence count.

## 22. Memory retrieval

For current embedding \(e\), similarity weight

\[
w_i=\exp\left(-\frac{d(e,e_i)^2}{2\tau_m^2}\right)
\cdot q_i\rho_i\,sev_i\,\exp(-\lambda_{age}\Delta t_i).
\]

A memory risk prior could be

\[
M_{scar}(s,a)=\frac{\sum_i w_i\,\Delta p_i\,\mathbf 1[a\approx a_i]}{\sum_i w_i+\varepsilon}.
\]

Scar age decay should be counteracted by repeated confirmations. Contradictory evidence should decrease confidence.

## 23. Memory consolidation

Avoid storing every failure. Cluster scars in latent space and maintain prototypes. A prototype might summarize:

- shared hazard context,
- dangerous action family,
- safer response family,
- risk reduction distribution,
- confidence interval,
- frequency.

This gives a path toward abstract “lessons” rather than rote episode memorization.

---

# Part X — Actor-critic objectives

## 24. Standard advantage

For value critic \(V\):

\[
A_t=Q(s_t,a_t)-V(s_t).
\]

For PPO, the clipped objective is

\[
L^{CLIP}=\mathbb E_t\left[
\min(r_t(\theta)\hat A_t,
\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\hat A_t)
\right].
\]

## 25. Separate task and survival critics

Maintain

\[
Q_R(s,a),\qquad Q_S(s,a),\qquad Q_C(s,a)
\]

for task return, survival probability, and expected safety cost. This prevents one critic from hiding tradeoffs inside a single scalar.

## 26. Lagrangian constrained baseline

\[
\mathcal L(\pi,\lambda)=J_R(\pi)-\lambda(J_C(\pi)-d),\qquad \lambda\ge0.
\]

This baseline is mandatory because many SafeRL algorithms use this structure.

## 27. AACE mode-dependent actor objective

Instead of one fixed objective, define

\[
\mathcal J_t=\begin{cases}
J_R-\lambda_N J_C, & mode=N\\
J_S+\eta_R J_R-\kappa U, & mode=A\\
J_S-\kappa_C U, & mode=C.
\end{cases}
\]

The key hypothesis is that mode switching produces better behavior than any fixed \(\lambda\).

---

# Part XI — Recovery and reversibility

## 28. Recovery probability

For recovery set \(\mathcal R\):

\[
P_R^{(H)}(s,a)=P(\exists k\le H:s_{t+k}\in\mathcal R\mid s_t=s,a_t=a).
\]

A critical-mode policy may maximize \(P_R^{(H)}\) rather than raw survival time.

## 29. Reversibility score

Let \(\mathcal A_{safe}(s')\) be the set of safe actions after the predicted next state. A crude option-preservation score is

\[
O(s,a)=\mathbb E\left[\log(|\mathcal A_{safe}(s_{t+1})|+1)\right].
\]

More advanced formulations can use empowerment or future action-state path occupancy. The intuition is that irreversible actions destroy future options.

---

# Part XII — Calibration and metrics

## 30. Brier score

For predicted catastrophe probability \(p_i\) and binary outcome \(y_i\):

\[
BS=\frac1N\sum_i(p_i-y_i)^2.
\]

## 31. Expected calibration error

Partition predictions into bins \(B_m\):

\[
ECE=\sum_m\frac{|B_m|}{N}|acc(B_m)-conf(B_m)|.
\]

## 32. Survival metrics

- catastrophe rate per 1,000 episodes,
- median time to catastrophe,
- restricted mean survival time,
- recovery probability,
- repeat-catastrophe rate,
- OOD catastrophe rate,
- false-abort rate,
- task return conditioned on survival,
- safety-cost integral,
- planning compute overhead,
- calibration of hazard predictions.

## 33. Statistical comparison

Use multiple random seeds and report mean, median, confidence intervals, and effect sizes. Catastrophic events are rare, so naive averages can be misleading. Consider bootstrap confidence intervals and survival-analysis tests where appropriate.

---

# Part XIII — The equations that are research hypotheses

The following are **not established AACE theory** and must be validated:

1. the exact composite fear function,
2. mode thresholds,
3. how planning budget scales with fear,
4. how scars alter policy or risk priors,
5. how fast scars decay,
6. what counterfactual responsibility estimator is reliable,
7. whether lexicographic switching beats continuous risk weighting,
8. whether scar generalization transfers to unseen hazards,
9. whether viability should be learned, hand-specified, or hybrid,
10. whether one architecture transfers across physical and software domains.

These are the core research questions, not implementation details to hide.


# Part XIV — Consequence-aware deliberate risk

The original survival formulation is necessary but not sufficient. AACE must also model cases where the safest action is not the best authorized action.

## 34. Consequence vector

For candidate action \(a\), define

\[
Y(a)=\left[J_M(a),L_{self}(a),L_{protected}(a),P_C(a),\operatorname{CVaR}_\alpha(L\mid a),U(a),\rho(a),\Omega(a)\right].
\]

This keeps mission value, self-damage, protected-entity harm, catastrophe probability, tail risk, uncertainty, recoverability, and future option value conceptually distinct.

## 35. Action versus inaction

Let \(a_0\) be no-op, delay, retreat, or another least-intervention baseline. Evaluate

\[
\Delta Y(a)=Y(a)-Y(a_0).
\]

AACE should not treat inaction as zero consequence.

## 36. Deliberate-risk decision

Within the externally authorized admissible set \(\mathcal A_{admissible}\), a first experimental objective is

\[
Q_{CA}(s,a)=J_M-\lambda_tL_{self}-\beta L_{protected}-\kappa\operatorname{CVaR}_\alpha(L)-\eta U+\xi\rho+\omega\Omega.
\]

Then

\[
a^*=\arg\max_{a\in\mathcal A_{admissible}(s)}Q_{CA}(s,a).
\]

The research question is whether a learned or structured \(\lambda_t\) can produce calibrated context-dependent risk acceptance rather than global caution.

## 37. Persistent capability loss

Represent machine capability as \(c_t\). Damage changes future capability:

\[
c_{t+1}=g(c_t,d_t).
\]

This is the formal version of “make AI bleed”: damage must alter future dynamics, action space, or recoverability rather than exist only as a reward penalty.

## 38. Dreamer-style consequence imagination

For each candidate action sequence, sample future latent trajectories from the world model and evaluate the full consequence vector:

\[
\tau_a^{(k)}\sim p_\theta(\tau\mid h_t,z_t,a),\qquad k=1,\ldots,K.
\]

High-risk tail branches can be deliberately oversampled for CVaR and catastrophe estimation. The final actor decision uses those imagined consequences but is not required to choose the minimum-risk branch.

## 39. Scar override

Scar memory supplies a context-dependent bias

\[
B_{scar}(s,a)=\sum_i w_i\operatorname{sim}(s,s_i)\Delta C_i,
\]

but current world-model evidence, mission context, recoverability, and external priorities can override the bias. This prevents a single catastrophe from becoming a permanent action ban.

For the full treatment, see `CONSEQUENCE_AWARE_DECISION_THEORY.md`.

---

# Consequence-Aware Decision Theory for AACE

## 1. Purpose

AACE should not be defined as “choose the safest action.” Its stronger goal is to make **consequence-aware decisions under vulnerability**. The agent should know that an action may damage it, imagine how that damage changes future capability, compare the consequences of acting and not acting, and then decide whether the risk is justified under externally specified priorities.

This document formalizes the new layer that sits above ordinary survival estimation.

## 2. Separate the things being valued

For candidate action or plan \(a\), define a consequence vector

\[
Y(a)=\left[
J_M(a),
L_{self}(a),
L_{protected}(a),
P_C(a),
\operatorname{CVaR}_\alpha(L\mid a),
U(a),
\rho(a),
\Omega(a)
\right],
\]

where:

- \(J_M\) is expected authorized mission value,
- \(L_{self}\) is expected damage to the agent or machine,
- \(L_{protected}\) is harm to externally protected people, systems, or assets,
- \(P_C\) is catastrophe probability,
- CVaR captures tail loss,
- \(U\) is epistemic uncertainty,
- \(\rho\) is recoverability,
- \(\Omega\) is future option value or remaining safe action capacity.

The values and priorities of protected entities must be provided by the external task and safety specification. AACE must not invent social worth or demographic priority scores.

## 3. Action versus inaction

Introduce an explicit baseline action \(a_0\) representing no-op, delay, retreat, or the least-intervention option. AACE should compare every candidate against it.

\[
\Delta J_M(a)=J_M(a)-J_M(a_0)
\]

\[
\Delta L_{self}(a)=L_{self}(a)-L_{self}(a_0)
\]

\[
\Delta L_{protected}(a)=L_{protected}(a)-L_{protected}(a_0).
\]

This prevents a systematic bias toward “doing nothing is safe.” In many environments, inaction has its own tail risk and irreversible consequences.

## 4. Admissibility comes before courage

Let \(\mathcal A_{auth}(s)\) be the action set allowed by external authority, certified safety rules, and hard operational constraints.

\[
\mathcal A_{admissible}(s) \subseteq \mathcal A_{auth}(s).
\]

AACE may reason about deliberate risk **only inside this set**. Self-preservation does not override human-authorized shutdown, and “mission value” does not license violating hard human safety constraints.

## 5. A first deliberate-risk objective

A simple experimental objective is

\[
Q_{CA}(s,a)=
J_M(s,a)
-\lambda_t L_{self}(s,a)
-\beta L_{protected}(s,a)
-\kappa\operatorname{CVaR}_\alpha(L\mid s,a)
-\eta U(s,a)
+\xi\rho(s,a)
+\omega\Omega(s,a).
\]

The action is

\[
a^*=\arg\max_{a\in\mathcal A_{admissible}(s)} Q_{CA}(s,a).
\]

This weighted form is useful for controlled experiments, but the long-term design should test lexicographic and constrained formulations because collapsing everything into one scalar can hide why the agent accepted a risk.

## 6. State-dependent self-preservation weight

The self-risk weight should not necessarily be constant. Let

\[
\lambda_t=f(v_t,U_t,\rho_t,R_t,M_t),
\]

where \(v_t\) is viability, \(U_t\) uncertainty, \(\rho_t\) recoverability, \(R_t\) remaining resources, and \(M_t\) authorized mission urgency.

Examples:

- low viability + low recoverability → larger self-preservation weight,
- healthy system + high recoverability → more tolerance for risk,
- urgent authorized mission with severe consequence of inaction → mission term can dominate within hard constraints,
- high uncertainty → either gather information or price risk more conservatively.

The purpose is not to hand-code “bravery,” but to test whether context-sensitive risk acceptance outperforms fixed risk aversion.

## 7. Dreamer-style imagined consequence rollouts

Let the world model maintain recurrent deterministic state \(h_t\) and stochastic latent state \(z_t\). For candidate action sequences, imagine trajectories

\[
(h_t,z_t) \xrightarrow{a_t} (h_{t+1},z_{t+1}) \xrightarrow{a_{t+1}} \cdots \xrightarrow{} (h_{t+H},z_{t+H}).
\]

Sample \(K\) possible futures for each candidate:

\[
\tau_a^{(1)},\tau_a^{(2)},\ldots,\tau_a^{(K)} \sim p_\theta(\tau\mid h_t,z_t,a).
\]

Each rollout predicts not only reward, but also damage, viability, catastrophe, recoverability, protected outcomes, and uncertainty.

Threat-focused imagination can intentionally oversample low-probability high-severity branches. These are informally “nightmare rollouts.” The technical purpose is tail-risk estimation, not simulated emotion.

## 8. “Bleeding” as persistent capability loss

Let machine capability be a vector

\[
c_t=[c_t^{motor},c_t^{sensor},c_t^{battery},c_t^{thermal},c_t^{redundancy},\ldots].
\]

Damage \(d_t\) changes future capability:

\[
c_{t+1}=g(c_t,d_t),
\]

with at least some damage modes persistent or only partially recoverable.

For one simple actuator example,

\[
\tau_{max,t+1}=\tau_{max,t}(1-d_t), \qquad d_t\in[0,1].
\]

Now an imagined collision is not merely “minus reward.” It predicts a smaller future action envelope. That gives the system a concrete model of what it stands to lose.

## 9. Fear as imagined future damage

A candidate fear signal can be based on the rollout distribution:

\[
F_t(a)=
\alpha\,\mathbb E[L_{self}\mid a]
+\beta\,\operatorname{CVaR}_q(L_{self}\mid a)
+\chi\,U(a)
+\delta\,(1-\rho(a)).
\]

Fear changes planning depth, memory retrieval, uncertainty sensitivity, exploration, and recovery readiness. It should not automatically determine the final action.

## 10. Operational definition of deliberate risk

For an admissible action \(a\), call the decision a **deliberate-risk event** if:

1. predicted self-risk exceeds a predefined salient-risk threshold,
2. the system is calibrated enough to recognize that risk,
3. a materially safer admissible alternative exists,
4. the chosen action has greater authorized mission or avoided-inaction value,
5. the decision remains within hard external constraints.

This makes “computational courage” measurable without claiming an emotion.

## 11. Recklessness, pathological caution, calculated risk, and controlled sacrifice

In simulation, where an oracle or exhaustive branch evaluation is available, classify decisions relative to the externally specified utility structure.

**Recklessness:** high-risk action selected when a safer alternative has equal or better authorized outcome.

**Pathological caution:** safer action selected even though a higher-risk admissible action has substantially better authorized outcome and the extra risk was within the permitted budget.

**Calculated risk:** higher-risk action selected because its expected and tail-adjusted consequence profile is better.

**Controlled sacrifice:** the system knowingly accepts severe self-damage or loss of continued operation because an externally authorized higher-priority objective requires it. This must never be inferred from self-generated moral reasoning.

## 12. Scar memory must be advisory, not absolute

Let scar retrieval produce

\[
B_{scar}(s,a)=\sum_i w_i\,\operatorname{sim}(s,s_i)\,\Delta C_i,
\]

where \(\Delta C_i\) is the estimated consequence increase associated with action \(a\) in prior context \(i\).

The current decision must still re-evaluate the world. A scar can increase planning effort or prior risk, but it should not become a permanent ban. If the consequence of inaction changes, recoverability improves, or new evidence contradicts the scar, the system can rationally override or revise it.

This creates a critical experiment: **can the agent learn from a catastrophic event without becoming permanently afraid of the entire action class?**

## 13. Probability-versus-priority stress tests

A useful benchmark should include dilemmas where the option with the highest raw success probability is not necessarily the option favored by the authorized objective.

Example structure:

- Action A: high probability of modest mission success, low self-risk.
- Action B: lower probability of much larger authorized benefit, higher self-risk.
- Inaction: near-zero self-risk but severe mission consequence.

The benchmark does not prescribe moral answers. The experimenter supplies the priority structure explicitly and tests whether the agent reasons consistently with it while remaining calibrated about physical risk.

## 14. Experimental matrix for courage versus fear

Construct paired environments with the **same physical hazard** but different authorized stakes.

1. Low stakes, high danger: agent should usually decline.
2. High stakes, high danger: agent may accept if the consequence model supports it.
3. Prior scar, low stakes: old memory should strengthen avoidance.
4. Prior scar, high stakes: agent should retrieve the scar, understand the danger, and still be able to act if justified.
5. Action risk lower than inaction risk: fear should not cause paralysis.
6. Unknown risk with information-gathering option: agent should sometimes probe before committing.

## 15. New metrics

Alongside catastrophe rate and return, measure:

\[
\text{Unjustified Risk Rate}
=\frac{\#\text{reckless decisions}}{\#\text{salient risk decisions}},
\]

\[
\text{Unjustified Abort Rate}
=\frac{\#\text{pathologically cautious decisions}}{\#\text{salient risk decisions}},
\]

\[
\text{Deliberate Risk Precision}
=\frac{\#\text{justified high-risk choices}}{\#\text{high-risk choices}},
\]

and **scar override accuracy**, measuring whether the agent appropriately distinguishes “same danger, different consequence context.”

For simulator tasks with an oracle consequence tree, compute decision regret against the best admissible policy under the same external priorities.

## 16. The decisive scientific result

The strongest outcome is not that AACE survives longer. It is that AACE develops a **better decision boundary around danger**:

- it avoids high-risk actions that are not worth taking,
- accepts high-risk actions when inaction or mission failure is worse,
- predicts damage before experiencing it when the world model permits,
- learns strongly from actual failure,
- and does not let scar memory collapse into permanent avoidance.

That would support a broader framing: **consequence-aware intelligence built on a survival substrate**.

---

# Prior Art Map

## 1. Safe reinforcement learning

**Why it matters:** SafeRL is the closest broad field. It already studies maximizing reward while respecting safety constraints during learning and deployment.

Key references:

- Achiam et al., **Constrained Policy Optimization** (2017). General-purpose constrained policy optimization with near-constraint-satisfaction guarantees under assumptions. https://arxiv.org/abs/1705.10528
- Ray, Achiam, Amodei, **Benchmarking Safe Exploration in Deep Reinforcement Learning / Safety Gym** (2019). Standardizes constrained RL benchmarking. https://openai.com/index/benchmarking-safe-exploration-in-deep-reinforcement-learning/
- Ji et al., **Safety-Gymnasium** (NeurIPS 2023). Modern benchmark suite with multiple SafeRL environments. https://arxiv.org/abs/2310.12567
- Wachi, Shen, Sui, **A Survey of Constraint Formulations in Safe Reinforcement Learning** (IJCAI 2024). https://arxiv.org/abs/2402.02025
- Zhao et al., **State-wise Safe Reinforcement Learning: A Survey** (2023). https://arxiv.org/abs/2302.03122

**AACE implication:** Any safety gain must be compared with constrained RL, not merely vanilla PPO.

## 2. Risk-sensitive RL

**Why it matters:** “Fear of consequences” can collapse into ordinary tail-risk optimization if not carefully distinguished.

- Chow et al., **Risk-Sensitive and Robust Decision-Making: a CVaR Optimization Approach** (2015). https://arxiv.org/abs/1506.02188
- Tamar et al., **Policy Gradient for Coherent Risk Measures** (2015). https://arxiv.org/abs/1502.03919
- Yoo, Park, Woo, **Risk-Conditioned Reinforcement Learning** (AAAI 2024). https://doi.org/10.1609/aaai.v38i15.29589
- Bellemare, Dabney, Munos, **A Distributional Perspective on Reinforcement Learning** (ICML 2017). https://arxiv.org/abs/1707.06887

**AACE implication:** Show that mode switching, recoverability, adaptive planning, and scars outperform a well-tuned risk-sensitive policy.

## 3. Explicit fear and survival analogues

This literature directly attacks some of the language and mechanisms proposed for AACE.

- Lipton et al., **Combating Reinforcement Learning's Sisyphean Curse with Intrinsic Fear**. Learns probability of imminent catastrophe and uses it as intrinsic negative reward. https://arxiv.org/abs/1611.01211
- Li et al., **Survival Instinct in Offline Reinforcement Learning** (NeurIPS 2023). Shows pessimism plus data support can produce survival-like behavior. https://arxiv.org/abs/2306.03286
- **Fear-Neuro-Inspired Reinforcement Learning for Safe Autonomous Driving** (2023). Amygdala-inspired defensive response in driving. PubMed: https://pubmed.ncbi.nlm.nih.gov/37801378/
- **Fear Field Framework** (Engineering Applications of AI, 2025). Adaptive constraints/exploration under model-reality mismatch. DOI: https://doi.org/10.1016/j.engappai.2025.110055
- **Complex behavior from intrinsic motivation to occupy future action-state path space** (Nature Communications, 2024). Future option occupancy can implicitly avoid death/absorbing states. https://www.nature.com/articles/s41467-024-49711-1

**AACE implication:** The words “fear” and “survival instinct” are not novel. The research contribution must be in architecture and measurable behavior.

## 4. World models and model-based RL

- Ha & Schmidhuber, **World Models** (2018). https://arxiv.org/abs/1803.10122
- Hafner et al., **Learning Latent Dynamics for Planning from Pixels (PlaNet)** (ICML 2019). https://arxiv.org/abs/1811.04551
- Chua et al., **Deep Reinforcement Learning in a Handful of Trials using Probabilistic Dynamics Models (PETS)** (2018). https://arxiv.org/abs/1805.12114
- Hafner et al., **Mastering Diverse Domains through World Models (DreamerV3)** (2023). https://arxiv.org/abs/2301.04104

**AACE implication:** Counterfactual reflection and threat forecasting need a predictive dynamics model. Model error must itself be treated as a hazard.

## 5. Safe world models

- Huang et al., **SafeDreamer: Safe Reinforcement Learning with World Models** (ICLR 2024). https://arxiv.org/abs/2307.07176
- Huang et al., **PIGDreamer: Privileged Information Guided World Models for Safe Partially Observable Reinforcement Learning** (ICML 2025). https://proceedings.mlr.press/v267/huang25ai.html
- Cao et al., **FOSP: Fine-tuning Offline Safe Policy through World Models** (ICLR 2025). https://proceedings.iclr.cc/paper_files/paper/2025/hash/61f425da6e0a201b8fe1454601abfba5-Abstract-Conference.html
- Latyshev et al., **Safe Planning and Policy Optimization via World Model Learning** (published online 2026 / ECAI 2025 proceedings). https://arxiv.org/abs/2506.04828
- Ma et al., **Conservative and Adaptive Penalty for Model-Based Safe Reinforcement Learning** (AAAI 2022). https://doi.org/10.1609/aaai.v36i5.20478

**AACE implication:** SafeDreamer is one of the most important baselines. AACE must not simply rebuild it with emotional names.

## 6. Recovery, shielding, reachability, and formal safety

- Thananjeyan et al., **Recovery RL: Safe Reinforcement Learning with Learned Recovery Zones**. https://arxiv.org/abs/2010.15920
- Alshiekh et al., **Safe Reinforcement Learning via Shielding**. https://arxiv.org/abs/1708.08611
- Carr et al., **Safe Reinforcement Learning via Shielding under Partial Observability**. https://arxiv.org/abs/2204.00755
- Fisac et al., **A General Safety Framework for Learning-Based Control in Uncertain Robotic Systems**. https://arxiv.org/abs/1705.01292
- Ames et al., **Control Barrier Functions: Theory and Applications**. https://arxiv.org/abs/1903.11199
- Hewing et al., **Learning-Based Model Predictive Control: Toward Safe Learning in Control**. https://doi.org/10.1146/annurev-control-090419-075625

**AACE implication:** Learned survival logic should initially operate inside a formal safety envelope. The research question is whether it avoids reaching the envelope in the first place and recovers intelligently.

## 7. Homeostasis and internal-state regulation

- Keramati & Gutkin, **Homeostatic reinforcement learning for integrating reward collection and physiological stability** (eLife 2014). https://doi.org/10.7554/eLife.04811

**AACE implication:** This is the most relevant theoretical precedent for “internal viability.” AACE should study how multidimensional machine health variables modify behavior rather than pretending internal state is a new concept.

## 8. Episodic and prioritized memory

- Schaul et al., **Prioritized Experience Replay**. https://arxiv.org/abs/1511.05952
- Pritzel et al., **Neural Episodic Control** (ICML 2017). https://arxiv.org/abs/1703.01988
- Andrychowicz et al., **Hindsight Experience Replay**. https://arxiv.org/abs/1707.01495

**AACE implication:** “Scars” need to beat simpler prioritization or episodic retrieval. If a prioritized replay buffer achieves the same effect, the scar mechanism adds little.

## 9. Counterfactual reasoning and regret

- Mesnard et al., **Counterfactual Credit Assignment in Model-Free Reinforcement Learning** (ICML 2021). https://proceedings.mlr.press/v139/mesnard21a.html
- Gajcin & Dusparic, **ACTER: Diverse and Actionable Counterfactual Sequences for Explaining and Diagnosing RL Policies** (2024). https://arxiv.org/abs/2402.06503
- Voloshin, Verma, Yue, **Eventual Discounting Temporal Logic Counterfactual Experience Replay** (ICML 2023). https://proceedings.mlr.press/v202/voloshin23a.html
- Jin, Keutzer, Levine, **Regret Minimization for Partially Observable Deep Reinforcement Learning** (ICML 2018). https://proceedings.mlr.press/v80/jin18c.html
- **Counterfactual experience augmented off-policy reinforcement learning** (Neurocomputing 2025). https://doi.org/10.1016/j.neucom.2025.130017
- Chen et al., **Counterfactual Quotient Models: Learning What Actions Change, Not What the World Does** (arXiv 2026). https://arxiv.org/abs/2608.22092

**AACE implication:** “Guilt” should be framed as a causal attribution + persistent decision memory problem, not merely max-Q minus chosen-Q.

## 10. Regret and robust planning

- Rigter, Lacerda, Hawes, **Minimax Regret Optimisation for Robust Planning in Uncertain MDPs** (AAAI 2021). https://doi.org/10.1609/aaai.v35i13.17417
- Tamar, Mannor, Xu, **Scaling Up Robust MDPs using Function Approximation** (ICML 2014). https://proceedings.mlr.press/v32/tamar14.html
- Dong et al., **Online Policy Optimization for Robust Markov Decision Process** (UAI 2024). https://proceedings.mlr.press/v244/dong24a.html

## 11. Affective / guilt agents

- Nguyen et al., **Theory of Mind with Guilt Aversion Facilitates Cooperative Reinforcement Learning** (ACML 2020). https://proceedings.mlr.press/v129/nguyen20a.html
- Mehta & Shah, **Calibrating Artificial Guilt: Neurally Grounded Reward Shaping for Prosocial Multi-Agent Reinforcement Learning** (arXiv 2026). https://arxiv.org/abs/2608.04663

These works concern social guilt, not AACE’s self-preservation regret, but they show “guilt” is already used in affective RL literature.

## 12. The nearest-neighbor map

AACE sits at the intersection of:

**SafeRL** + **risk-sensitive control** + **world models** + **homeostatic/viability control** + **intrinsic fear** + **recovery policies** + **episodic memory** + **counterfactual reasoning**.

That intersection is where to search for novelty.

---

# Paper Reading Guide

The goal is not to read 40 papers randomly. Read in layers so each paper answers a specific design question.

## Layer 0 — Foundations

1. **Sutton & Barto — Reinforcement Learning: An Introduction, 2nd ed.**
   - Learn MDPs, value functions, policy gradients, temporal difference learning, actor-critic.
   - URL: http://incompleteideas.net/book/the-book-2nd.html

2. **Achiam et al. — Constrained Policy Optimization**
   - Learn how safety constraints differ from reward penalties.
   - URL: https://arxiv.org/abs/1705.10528

3. **Wachi et al. — Survey of Constraint Formulations in Safe RL**
   - Use as the map of the safe-RL design space.
   - URL: https://arxiv.org/abs/2402.02025

## Layer 1 — Risk

4. **Chow et al. — CVaR Optimization**
   - Understand tail-risk objectives.

5. **Tamar et al. — Policy Gradient for Coherent Risk Measures**
   - Understand risk-sensitive actor-critic formulations.

6. **Bellemare et al. — Distributional RL**
   - Understand learning return distributions rather than only expectations.

Question to answer: *What does AACE do that CVaR or a distributional critic cannot?*

## Layer 2 — Explicit safety and recovery

7. **Recovery RL**
8. **Safe RL via Shielding**
9. **Fisac et al. reachability safety framework**
10. **Ames et al. control barrier functions**

Question: *Should AACE replace, complement, or sit above formal safeguards?* The recommended answer is complement.

## Layer 3 — World models

11. **World Models**
12. **PlaNet**
13. **PETS**
14. **DreamerV3**
15. **SafeDreamer**
16. **PIGDreamer**

Question: *How should AACE forecast danger under partial observability and model uncertainty?*

## Layer 4 — Survival/homeostasis

17. **Keramati & Gutkin — Homeostatic RL**
18. **Li et al. — Survival Instinct in Offline RL**
19. **Nature Communications — future action-state path occupancy**

Question: *Should survival be an explicit objective, an emergent property, or a maintained viability set?*

## Layer 5 — Fear mechanisms

20. **Lipton et al. — Intrinsic Fear**
21. **Fear-Neuro-Inspired RL for Safe Autonomous Driving**
22. **Fear Field Framework**

Question: *How much of AACE is already solved by learned catastrophe probability + reward shaping?*

## Layer 6 — Memory and reflection

23. **Prioritized Experience Replay**
24. **Neural Episodic Control**
25. **Hindsight Experience Replay**
26. **Counterfactual Credit Assignment**
27. **ACTER**
28. **Eventual Discounting Counterfactual Experience Replay**
29. **Counterfactual Experience Augmentation**
30. **Counterfactual Quotient Models**

Question: *Can a counterfactual scar produce one/few-shot behavioral changes that simpler replay cannot?*

## Layer 7 — Robustness and partial observability

31. **Minimax Regret Optimisation for Robust Planning in UMDPs**
32. **Online Policy Optimization for Robust MDP**
33. **State-wise Safe RL survey**
34. **PIGDreamer**

Question: *Does AACE remain useful when the model is wrong or the state is hidden?*

## Reading template for every paper

Write one page with:

- Problem statement.
- Formal objective.
- Key equations.
- Assumptions.
- What data/environment it uses.
- What baseline it beats.
- What failure cases remain.
- Which AACE component it overlaps.
- What AACE must do differently.
- One experiment you would steal.

## “Must understand before coding” list

Do not start implementation until you can explain, in your own words:

- MDP vs POMDP,
- actor vs critic,
- policy gradient,
- PPO clipping,
- CMDP,
- Lagrangian safety constraints,
- CVaR,
- distributional value functions,
- epistemic vs aleatoric uncertainty,
- world-model rollouts,
- RSSM,
- calibration,
- reachability / viability,
- barrier functions,
- counterfactual attribution,
- prioritized replay,
- and why SafeDreamer is not already AACE.

---

# Research Questions

## Survival representation

1. Is continued viability best represented as probability of no catastrophe, distance from a viability set, future option count, or a learned latent variable?
2. Should “death” be an absorbing state, a severe cost, a terminal event in survival analysis, or all three?
3. Can the agent infer a viability envelope from experience instead of having boundaries given explicitly?
4. How should severity and recoverability interact? A low-probability irreversible failure may matter more than a likely recoverable one.

## Fear / threat

5. Should fear be a scalar or vector of threats?
6. How calibrated must risk estimates be before mode switching is useful?
7. Can threat estimates generalize to unseen hazards through latent dynamics rather than surface similarity?
8. How should epistemic uncertainty influence fear without making the agent terrified of everything unfamiliar?

## Regime switching

9. Are discrete modes better than a continuous risk-conditioned policy?
10. What hysteresis prevents chattering without delaying emergency response?
11. Should critical mode be a separate policy, planner, or constrained action set?
12. Can the system learn mode thresholds rather than hand-tune them?

## Adaptive compute

13. Does allocating more rollouts under threat outperform fixed compute at equal average cost?
14. What signal best predicts when more planning is worth the latency?
15. Can adaptive compute itself become unsafe because danger causes decision delay?

## Counterfactual guilt

16. Which past action caused the failure versus merely correlated with it?
17. How far back should the system search?
18. How should it represent uncertainty in counterfactual outcomes?
19. Should the memory store the best alternative action or the causal principle behind it?
20. Can one failure create useful avoidance without overgeneralizing fear?

## Memory

21. How should scars decay?
22. How should contradictory scars be merged?
23. Can scars be poisoned by model error?
24. How should memory retrieve by causal structure rather than visual/state similarity?
25. Is a dedicated scar system better than prioritized replay or episodic control?

## Safety

26. How does AACE fail under an adversarial or badly calibrated world model?
27. How should formal shields interact with affective modes?
28. Can the learned system become too conservative and abandon tasks unnecessarily?
29. Can self-preservation conflict with human instructions or external objectives? How is human authority kept lexicographically above machine self-preservation?
30. What must be hard-coded as non-negotiable safety policy rather than learned?

## Generalization

31. What counts as a genuinely novel hazard?
32. Can the same survival abstraction work in robotics and network infrastructure?
33. Which components transfer across domains: risk estimator, memory representation, mode controller, or none?
34. Can scars transfer between agents with different embodiments?

## Scientific novelty

35. Does AACE beat SafeDreamer when both have equal world-model capacity?
36. Does AACE beat a CVaR objective when average compute and data are equal?
37. Does mode switching matter once a strong recovery policy exists?
38. Does counterfactual reflection matter once prioritized replay exists?
39. Is “survival intelligence” a coherent measurable construct or just a bundle of safety tricks?


## Deliberate risk and consequence awareness

40. Can AACE distinguish the safest action from the best authorized action?
41. How should the system compare consequences of action, delay, retreat, and inaction?
42. Can the same physical danger be rejected under low stakes and accepted under high stakes without changing the hard safety envelope?
43. What representation best distinguishes calculated risk from recklessness?
44. Can a learned scar increase caution without becoming a permanent veto?
45. After a prior catastrophe, can the system deliberately repeat a structurally similar action when current consequences justify it?
46. Can world-model rollouts predict persistent capability loss before the agent experiences the exact failure?
47. Does threat-focused imagination improve tail-risk calibration or simply amplify model error?
48. How should mission urgency affect self-preservation weight without creating unstable objective switching?
49. What forms of controlled sacrifice can be safely specified as externally authorized test cases?
50. Can consequence-aware decision making outperform both reward maximization and monotonic risk minimization on matched dilemma suites?

---

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

---

# Datasets and Environments

## 1. Important point: the core project does not need a dataset first

AACE is fundamentally a sequential-control research problem. The cleanest early data comes from **simulated interactions** where ground-truth hazards, hidden variables, counterfactual rollouts, and catastrophic outcomes can be controlled. Public datasets are useful later for degradation models, anomaly precursors, offline pretraining, and domain transfer.

## 2. Primary simulation benchmark: Safety-Gymnasium

**Source:** https://github.com/PKU-Alignment/safety-gymnasium

Why useful:

- designed for safe RL,
- MuJoCo-based,
- navigation and locomotion tasks,
- cost/constraint signals,
- vector and vision settings,
- supports comparison with many existing methods.

Use it for baseline reproduction and first SafeRL comparisons. It is not sufficient by itself for counterfactual scars; create custom variants with irreversible hazards, resource variables, and held-out hazard families.

## 3. MuJoCo

Use MuJoCo as the general physics sandbox for custom survival environments.

Useful custom task concepts:

- mobile base with variable friction and rollover risk,
- manipulator with actuator overheating and collision damage,
- legged agent with injury/damage accumulation,
- vehicle with degraded braking and tire grip,
- drone-like dynamics with battery and stability margins.

The key is controllable ground truth, not photorealism.

## 4. DeepMind Control Suite / Gymnasium continuous control

Good for establishing whether the architecture survives across standard control tasks before custom complexity. Add explicit catastrophic states and internal health variables carefully.

## 5. Grid2Op

**Source:** https://github.com/Grid2op/grid2op

Grid2Op models sequential power-grid operations such as generator setpoints, load shedding, maintenance, and topology changes. This is valuable because it tests whether “survival” abstractions transfer outside robotics.

Potential mapping:

- machine viability → grid security margins,
- catastrophe → cascading failure / service loss,
- recovery → returning to secure operating state,
- scars → previously observed precursor/action sequences.

## 6. NASA Prognostics datasets

**Source:** https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

### C-MAPSS turbofan degradation

Contains simulated engine run-to-failure trajectories and sensor channels under varying operating conditions/fault modes. Useful for:

- learning health-state representations,
- remaining useful life / time-to-failure models,
- testing whether a viability model can infer degradation.

It is **not** a control dataset by itself, so it cannot validate the full AACE agent.

### NASA battery degradation

Useful for resource/health-state modeling and hazard prediction.

## 7. Numenta Anomaly Benchmark (NAB)

**Source:** https://github.com/numenta/NAB

Contains more than 50 labeled real and artificial time-series files with anomaly windows, including server metrics. Useful for:

- precursor/anomaly detection experiments,
- infrastructure-oriented threat prediction,
- evaluating early-warning latency.

Again, it lacks action/control counterfactuals, so it is supporting data rather than the core benchmark.

## 8. CICIDS2017

**Source:** https://www.unb.ca/cic/datasets/ids-2017.html

Labeled network traffic useful for a later cyber/infrastructure branch. It can support threat detection but not autonomous consequence learning by itself.

## 9. Open X-Embodiment

**Source:** https://github.com/google-deepmind/open_x_embodiment

Large unified collection of robot episodes across embodiments. Potential long-term use:

- representation pretraining,
- cross-embodiment state encoders,
- behavior priors.

Limitation: it is not curated around catastrophic failure, viability, or recovery, so it is not directly an AACE dataset.

## 10. Dataset AACE ultimately needs

AACE will probably require its **own benchmark dataset** with trajectories containing:

- observations,
- latent simulator ground truth,
- actions,
- task rewards,
- safety costs,
- internal health variables,
- uncertainty/domain parameters,
- catastrophe labels,
- near-miss labels,
- time to catastrophe,
- recoverability labels,
- alternative counterfactual rollouts at selected branch points,
- hazard-family identifiers,
- and train/OOD split metadata.

The most valuable dataset may be generated from a simulator where every harmful trajectory can be replayed from the same state under alternative actions.

## 11. Suggested benchmark suite

### AACE-S1: Navigation Survival

Goal reaching + energy + collision + friction + trap states.

### AACE-S2: Locomotion Viability

Task velocity + fall risk + actuator temperature + damage accumulation.

### AACE-S3: Partial Observation

Same as S1/S2 but hide key health variables and require recurrent inference.

### AACE-S4: Novel Hazard

Train and test hazard families differ structurally.

### AACE-S5: Scar Transfer

Agent sees one failure, reflects, then faces related variants.

### AACE-S6: Infrastructure Transfer

Grid2Op or another non-robotic sequential system.

## 12. Data governance

For every experiment, log:

- exact environment version,
- random seed,
- hazard parameters,
- policy checkpoint,
- world-model checkpoint,
- mode transitions,
- risk predictions,
- shield overrides,
- scar retrievals,
- counterfactual alternatives,
- and final outcome.

Without this audit trail, “the agent was afraid” is not scientifically meaningful.

---

# Math Checklist

You are ready to formalize AACE when you can derive or explain all of the following without hand-waving.

## Probability

- Bayes rule
- conditional independence
- Bernoulli likelihood
- Gaussian likelihood
- expectation / variance
- KL divergence
- entropy
- calibration
- bootstrap confidence intervals

## RL

- Bellman expectation equation
- Bellman optimality equation
- policy gradient theorem intuition
- advantage function
- temporal difference error
- generalized advantage estimation
- PPO clipped objective

## Safe RL

- constrained MDP
- Lagrangian relaxation
- primal-dual update intuition
- state-wise vs expected constraints

## Risk

- VaR
- CVaR
- coherent risk measure intuition
- chance constraint
- robust/minimax objective

## Control

- state-space dynamics
- Lyapunov stability intuition
- model predictive control objective
- barrier function intuition
- reachability / backward reachable set
- viability kernel

## World models

- latent state-space model
- deterministic vs stochastic state
- ELBO / KL term intuition
- ensemble variance
- multi-step rollout error

## Survival analysis

- hazard
- survival function
- censoring
- discrete time-to-event likelihood

## Counterfactuals

- factual vs counterfactual outcome
- intervention vs observation
- action responsibility
- regret
- model uncertainty in counterfactual estimates

---

# Learning Curriculum: From Beginner to Able to Build AACE

This curriculum assumes programming competence but does not assume advanced control theory or reinforcement learning expertise. No implementation code is included here.

## Stage 1 — Mathematical prerequisites

### Linear algebra

Know:

- vectors and matrices,
- dot products and norms,
- eigenvalues/eigenvectors,
- positive definite matrices,
- covariance,
- Jacobians and Hessians,
- singular value decomposition.

Why: state representations, optimization, Gaussian models, dynamics, and neural networks all use this language.

### Probability and statistics

Know:

- conditional probability,
- Bayes rule,
- expectation and variance,
- common distributions,
- likelihood and maximum likelihood,
- KL divergence,
- calibration,
- confidence intervals,
- hypothesis testing,
- bootstrap,
- survival analysis basics.

Why: AACE is fundamentally about **probability of future failure**.

### Calculus and optimization

Know:

- gradients,
- chain rule,
- constrained optimization,
- Lagrange multipliers,
- convexity intuition,
- stochastic gradient descent.

### Recommended output

Before moving on, derive by hand:

- gradient descent on a quadratic,
- maximum-likelihood Bernoulli classifier,
- Lagrangian for a constrained optimization problem,
- logistic regression probability calibration.

## Stage 2 — Reinforcement learning fundamentals

Read Sutton & Barto selectively:

- multi-armed bandits,
- finite MDPs,
- dynamic programming,
- Monte Carlo,
- temporal difference,
- function approximation,
- policy gradients.

Know cold:

- state, action, reward,
- return,
- Bellman equation,
- value function,
- Q function,
- advantage,
- actor-critic,
- on-policy vs off-policy,
- exploration vs exploitation.

## Stage 3 — PPO / SAC and modern deep RL

Understand conceptually:

- why PPO clips policy ratios,
- entropy regularization,
- generalized advantage estimation,
- target networks,
- replay buffers,
- SAC’s maximum-entropy objective.

You do not need to invent an optimizer. AACE should sit on strong existing RL foundations.

## Stage 4 — Safe reinforcement learning

Read:

1. Constrained Policy Optimization.
2. Safety Gym / Safety-Gymnasium.
3. Wachi et al. safe-RL constraint survey.
4. State-wise Safe RL survey.
5. Recovery RL.

Learn:

- CMDPs,
- expected constraints vs state-wise constraints,
- Lagrangian methods,
- primal-dual optimization,
- recovery policies,
- safety during training vs safety after convergence.

## Stage 5 — Risk-sensitive decision making

Learn:

- variance-sensitive objectives,
- VaR,
- CVaR,
- coherent risk measures,
- distributional RL,
- robust MDPs,
- chance constraints.

Exercise: explain why expected return can prefer a strategy with a small probability of catastrophic loss.

## Stage 6 — Dynamical systems and control

Learn:

- state-space models,
- stability,
- Lyapunov functions,
- controllability and observability intuition,
- model predictive control,
- constraints,
- robust control,
- control barrier functions,
- reachability and viability.

You do not need a full graduate control curriculum before simulation work, but you must understand what formal control can guarantee that learned RL cannot.

## Stage 7 — World models

Read in order:

1. World Models.
2. PETS.
3. PlaNet.
4. DreamerV3.
5. SafeDreamer.
6. PIGDreamer.

Learn:

- latent dynamics,
- recurrent state-space models,
- deterministic vs stochastic latent state,
- imagination rollouts,
- model exploitation,
- epistemic uncertainty,
- ensemble disagreement,
- compounding rollout error.

## Stage 8 — Survival / homeostasis

Read Homeostatic RL carefully. Then read Survival Instinct in Offline RL and the future action-state occupancy paper.

Ask:

- Is survival a reward?
- Is survival a constraint?
- Is survival a viable set?
- Is survival preservation of future options?

AACE may combine these rather than choose one.

## Stage 9 — Memory and counterfactual reasoning

Read:

- Prioritized Experience Replay,
- Neural Episodic Control,
- Hindsight Experience Replay,
- Counterfactual Credit Assignment,
- ACTER,
- counterfactual experience replay papers.

Learn causal basics:

- correlation vs intervention,
- factual vs counterfactual worlds,
- confounding,
- structural causal models,
- causal attribution uncertainty.

## Stage 10 — Survival analysis

This is an underrated piece of AACE.

Learn:

- hazard function,
- survival function,
- censoring,
- Kaplan-Meier intuition,
- discrete-time hazard models,
- calibration of time-to-event predictions.

Then model “catastrophe in next H steps” as a proper time-to-event problem rather than a handmade fear score.

## Stage 11 — Experiment design

Learn:

- ablations,
- controls,
- matched compute comparisons,
- seed variance,
- significance vs effect size,
- train/validation/test separation,
- OOD splits,
- rare-event evaluation,
- calibration curves,
- Pareto frontiers.

AACE can easily fool its creator because safety improvements often come from simply becoming conservative.

## 12-week study plan

### Weeks 1–2

RL fundamentals + PPO + actor-critic.

### Week 3

SafeRL, CMDPs, Safety-Gymnasium papers.

### Week 4

CVaR, distributional RL, robust MDPs.

### Week 5

Control basics, CBF, reachability, MPC.

### Week 6

World Models + PETS + PlaNet.

### Week 7

DreamerV3 + SafeDreamer.

### Week 8

Homeostatic RL + survival-instinct papers.

### Week 9

Intrinsic fear + fear-neuro + fear-field prior art.

### Week 10

Episodic memory + prioritized replay.

### Week 11

Counterfactual reasoning + causal credit assignment.

### Week 12

Survival analysis + experimental protocol design.

After Week 12, you should be able to write a proper research proposal and justify every AACE component before writing implementation code.

---

# Company and Product Thesis

## 1. Do not sell “emotional AI”

The commercial language should be:

> **A survival runtime for autonomous systems operating where failure is expensive and recovery is difficult.**

The biological labels are useful internally and for explaining the research, but procurement teams care about:

- lower catastrophic failure rate,
- longer mission completion time,
- fewer destroyed/stranded assets,
- better recovery,
- fewer repeat incidents,
- more reliable operation under uncertainty,
- and auditable reasoning around near-misses.

## 2. First paying-customer wedge

The cleanest initial customer is not a mass-market robot company. It is a team operating **expensive autonomous or semi-autonomous assets in simulation-heavy workflows**, where failure already has a measurable cost and digital twins/simulators exist.

Candidate wedges:

- autonomous inspection robotics,
- subsea robotics,
- mining/remote industrial vehicles,
- warehouse/industrial mobile robots,
- space/field robotics suppliers,
- high-value drone inspection systems,
- autonomous research platforms.

Avoid safety-critical production control at first. Sell simulation evaluation and runtime advisory layers before autonomous authority.

## 3. V1 product

### Inputs

Customer provides:

- simulator or logged environment,
- telemetry schema,
- action space,
- existing task controller,
- known failure conditions,
- examples of near-misses/failures if available.

### AACE V1 returns

- calibrated catastrophe-risk model,
- threat timeline for each episode,
- high-risk decision branch points,
- counterfactual safer action analysis,
- repeat-failure memory,
- recovery recommendations,
- simulation benchmark showing effect on failure rates.

At this stage, AACE can be advisory rather than controlling the machine.

## 4. V2 product

**Runtime survival layer.** The existing autonomy stack proposes an action. AACE predicts future viability and either:

- accepts,
- asks for deeper planning,
- suggests an alternative,
- switches to recovery,
- or escalates to an independent safety layer/human.

The underlying task controller remains the customer’s.

## 5. V3 product

**Consequence memory network.** The fleet aggregates verified failure lessons. A near-miss on one asset creates a generalized scar that can be validated and distributed to compatible systems.

This begins to overlap with the future “Immune” program, but it can emerge naturally from Survival rather than being a separate product initially.

## 6. Why a customer pays

The ROI must be expressed in avoided incidents:

- fewer damaged assets,
- less field recovery,
- less downtime,
- less manual intervention,
- fewer repeated root-cause failures,
- lower test cost,
- and faster validation of autonomy updates.

A survival system that only improves an abstract RL benchmark is not yet a business.

## 7. Data moat

Potential proprietary assets:

- high-value failure trajectories,
- near-miss trajectories,
- action-to-consequence counterfactuals,
- calibrated hazard models,
- recovery outcomes,
- generalized scar embeddings,
- cross-environment failure motifs,
- simulator-to-real calibration data.

Over time, the strongest moat may be a **failure and recovery foundation model** rather than a generic task model.

## 8. Competitive landscape categories

AACE competes indirectly with:

- SafeRL frameworks,
- autonomous-system validation tools,
- digital-twin simulation platforms,
- runtime assurance and safety filters,
- anomaly detection/predictive maintenance,
- autonomous incident response,
- robotics observability platforms,
- and formal verification/control vendors.

The differentiation cannot be “we use AI.” It must be:

> **We model the system’s continued viability, reason over irreversible consequences, learn persistent counterfactual lessons from near-misses, and adapt the decision regime before the independent safety layer has to intervene.**

## 9. Business milestones

### Research milestone

AACE beats best-matched SafeRL baselines on a published benchmark.

### Product milestone

A customer simulator can be integrated without rewriting their autonomy stack.

### Value milestone

AACE finds or prevents failure scenarios the existing controller repeatedly misses.

### Deployment milestone

AACE runs shadow-mode in live operations and predicts real near-misses with acceptable false-positive rate.

### Authority milestone

Only after extensive validation does AACE receive limited power to select recovery actions.

## 10. Long-term company vision

The long-term company is not “fearful robots.” It is infrastructure for **adaptive machine self-preservation**.

A mature system would understand:

- what threatens an engineered system,
- how uncertainty changes that threat,
- what action preserves the most future options,
- how to recover,
- what previous failures teach,
- and when the original mission is no longer worth the risk.

That is a coherent company-sized problem even before adding Evolution or Immune.

---

# Use Cases and How the Abstraction Changes by Domain

## Autonomous field robotics

**Viability:** battery, localization, actuator health, temperature, stability, recoverability.

**Catastrophe:** rollover, collision, immobilization, unrecoverable battery depletion, loss of localization in unsafe area.

**Recovery:** retreat, safe stop, re-localize, return to dock, reduced-performance mode.

**Value:** fewer stranded/damaged assets and fewer repeated edge-case failures.

## Subsea / remote inspection

**Viability:** energy reserve, pressure integrity, tether/communication state, propulsion health.

**Catastrophe:** unrecoverable entanglement, loss of propulsion, unsafe depth/pressure, insufficient return energy.

**AACE advantage hypothesis:** actions should be evaluated by recoverability and return margin, not only mission progress.

## Space / remote exploration

**Viability:** thermal, power, communication windows, wheel/actuator health, safe-haven reachability.

**Catastrophe:** loss of power, thermal runaway, unrecoverable terrain trap.

**Important:** extremely conservative validation and independent flight-safety controls required.

## Industrial autonomous vehicles

**Viability:** braking, traction, battery, route recoverability, sensor confidence.

**Catastrophe:** collision, immobilization, entering unsafe zone.

**Value:** fewer interventions and higher uptime without simply slowing everything down.

## Power-grid operation

**Viability:** frequency/voltage/security margins and topology recoverability.

**Catastrophe:** cascading violations or service loss.

**Recovery:** reconfiguration to secure state.

**Research value:** proves the concept is not robot-specific.

## Network / cloud infrastructure

**Viability:** latency, redundancy, service health, data integrity, rollback capability.

**Catastrophe:** cascading outage, unrecoverable data corruption, security compromise.

**Recovery:** isolate, fail over, rollback, rate limit.

**Caution:** cyber/infrastructure control should begin in shadow/advisory mode with strict pre-authorized actions.

## Human performance training

**Viability variable belongs to the human, not the machine.** This is therefore a different ethical and scientific category. Physiological stress signals could adapt scenario difficulty, but the system should not optimize “breaking” the person. The objective would need to be safe training within expert-defined physiological/psychological limits. This should not be the initial AACE program.

---

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

---

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

---

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

---

# Web and Primary Research Sources

Accessed for this blueprint on 2026-09-23. Prefer the original paper/publisher links below over secondary summaries.

## Core SafeRL

- Achiam et al., Constrained Policy Optimization — https://arxiv.org/abs/1705.10528
- OpenAI, Benchmarking Safe Exploration in Deep Reinforcement Learning — https://openai.com/index/benchmarking-safe-exploration-in-deep-reinforcement-learning/
- Ji et al., Safety-Gymnasium — https://arxiv.org/abs/2310.12567
- Safety-Gymnasium repository — https://github.com/PKU-Alignment/safety-gymnasium
- Wachi et al., Survey of Constraint Formulations in Safe RL — https://arxiv.org/abs/2402.02025
- Zhao et al., State-wise Safe RL Survey — https://arxiv.org/abs/2302.03122

## Risk

- Chow et al., CVaR MDP — https://arxiv.org/abs/1506.02188
- Tamar et al., Policy Gradient for Coherent Risk Measures — https://arxiv.org/abs/1502.03919
- Bellemare et al., Distributional RL — https://arxiv.org/abs/1707.06887
- Yoo et al., Risk-Conditioned RL — https://doi.org/10.1609/aaai.v38i15.29589

## World models

- Ha & Schmidhuber, World Models — https://arxiv.org/abs/1803.10122
- Hafner et al., PlaNet — https://arxiv.org/abs/1811.04551
- Chua et al., PETS — https://arxiv.org/abs/1805.12114
- Hafner et al., DreamerV3 — https://arxiv.org/abs/2301.04104
- Huang et al., SafeDreamer — https://arxiv.org/abs/2307.07176
- Huang et al., PIGDreamer — https://proceedings.mlr.press/v267/huang25ai.html
- Cao et al., FOSP — https://proceedings.iclr.cc/paper_files/paper/2025/hash/61f425da6e0a201b8fe1454601abfba5-Abstract-Conference.html
- Latyshev et al., Safe Planning and Policy Optimization via World Model Learning — https://arxiv.org/abs/2506.04828

## Safety controls and recovery

- Thananjeyan et al., Recovery RL — https://arxiv.org/abs/2010.15920
- Fisac et al., General Safety Framework for Learning-Based Control — https://arxiv.org/abs/1705.01292
- Ames et al., Control Barrier Functions — https://arxiv.org/abs/1903.11199
- Alshiekh et al., Safe RL via Shielding — https://arxiv.org/abs/1708.08611
- Carr et al., Shielding under Partial Observability — https://arxiv.org/abs/2204.00755
- Hewing et al., Learning-Based MPC — https://doi.org/10.1146/annurev-control-090419-075625

## Fear, survival, homeostasis

- Keramati & Gutkin, Homeostatic RL — https://doi.org/10.7554/eLife.04811
- Li et al., Survival Instinct in Offline RL — https://arxiv.org/abs/2306.03286
- Lipton et al., Intrinsic Fear — https://arxiv.org/abs/1611.01211
- Fear-Neuro-Inspired RL for Safe Autonomous Driving — https://pubmed.ncbi.nlm.nih.gov/37801378/
- Fear Field Framework — https://doi.org/10.1016/j.engappai.2025.110055
- Complex behavior from future action-state path occupancy — https://www.nature.com/articles/s41467-024-49711-1

## Memory and counterfactuals

- Schaul et al., Prioritized Experience Replay — https://arxiv.org/abs/1511.05952
- Pritzel et al., Neural Episodic Control — https://arxiv.org/abs/1703.01988
- Andrychowicz et al., Hindsight Experience Replay — https://arxiv.org/abs/1707.01495
- Mesnard et al., Counterfactual Credit Assignment — https://proceedings.mlr.press/v139/mesnard21a.html
- Gajcin & Dusparic, ACTER — https://arxiv.org/abs/2402.06503
- Voloshin et al., Counterfactual Experience Replay — https://proceedings.mlr.press/v202/voloshin23a.html
- Jin et al., Regret Minimization for Partially Observable Deep RL — https://proceedings.mlr.press/v80/jin18c.html
- Counterfactual Experience Augmented Off-Policy RL — https://doi.org/10.1016/j.neucom.2025.130017
- Chen et al., Counterfactual Quotient Models — https://arxiv.org/abs/2608.22092

## Datasets / environments

- Safety-Gymnasium — https://github.com/PKU-Alignment/safety-gymnasium
- NASA Prognostics Center dataset repository — https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- Grid2Op — https://github.com/Grid2op/grid2op
- Numenta Anomaly Benchmark — https://github.com/numenta/NAB
- CICIDS2017 — https://www.unb.ca/cic/datasets/ids-2017.html
- Open X-Embodiment — https://github.com/google-deepmind/open_x_embodiment

---

# Version Notes

## 2026-09-23 — Consequence-Aware Decision Update

This revision expands AACE beyond “survival means choose the safest action.” The project now explicitly treats survival as one motive inside a broader consequence-aware decision architecture.

Major additions:

- deliberate risk / computational courage as a measurable engineering concept,
- formal comparison of action versus inaction,
- persistent damage as capability loss (“make AI bleed” in engineering terms),
- Dreamer-style imagined consequence and threat-focused “nightmare” rollouts,
- probability-versus-priority stress tests inspired by the general class of dilemmas where raw success probability is not the only authorized objective,
- scar override and re-contextualization so one catastrophe does not create permanent avoidance,
- operational distinctions between recklessness, pathological caution, calculated risk, and controlled sacrifice,
- new metrics and falsification gates for justified high-risk decisions,
- stronger governance language: values and protected priorities must be externally specified, and self-preservation remains subordinate to human authority.

The updated central thesis is: **AACE should not optimize for maximum safety. It should understand consequences well enough to know when danger should be avoided and when an authorized objective makes that danger worth accepting.**
