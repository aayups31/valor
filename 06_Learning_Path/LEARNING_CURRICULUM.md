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
