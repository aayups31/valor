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
