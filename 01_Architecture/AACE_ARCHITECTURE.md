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
