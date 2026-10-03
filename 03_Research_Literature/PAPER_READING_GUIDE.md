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
