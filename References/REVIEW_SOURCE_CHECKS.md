# Source checks for the project review

Checked October 2, 2026. This is a targeted primary-source check supporting the assessment and implementation choices. It does not validate every theorem, paper result, bibliography field, or codebase, and it is not an exhaustive literature/patent review.

The local review covered 25 files in 11 folders. All standalone Markdown content is reproduced in `MASTER_BLUEPRINT.md`; the separate CSV and BibTeX files were also read. There are 33 reading-list entries and 25 BibTeX records. Different coverage is acceptable for curated lists, but future publication should use one checked registry to avoid metadata drift.

## Existing sources checked

| Primary source | Finding relevant to AACE |
|---|---|
| [Intrinsic Fear](https://arxiv.org/abs/1611.01211) | The abstract describes a learned imminent-catastrophe predictor used for reward shaping. Catastrophe prediction plus a fear penalty is established prior art. |
| [Recovery RL](https://arxiv.org/abs/2010.15920) | The abstract explicitly separates a task policy and a recovery policy. AACE's task/recovery split needs a stronger comparative contribution. |
| [SafeDreamer](https://arxiv.org/abs/2307.07176) | The paper combines world-model planning and Lagrangian safety methods. Imagined futures with safety evaluation are already a close baseline. |
| [PIGDreamer](https://proceedings.mlr.press/v267/huang25ai.html) | The ICML 2025 proceedings describe privileged representation alignment and asymmetric actor-critic learning. Privileged training data must be controlled when comparing AACE. |
| [ACTER](https://arxiv.org/abs/2402.06503) | The preprint produces actionable alternative action sequences for diagnosing/avoiding failure. Counterfactual recourse alone is not new. |
| [Counterfactual Quotient Models](https://arxiv.org/abs/2608.22092) | The August 2026 arXiv record exists and describes action-effect modeling using synchronized counterfactual rollouts. The archive correctly treats it as a preprint. |
| [Calibrating Artificial Guilt](https://arxiv.org/abs/2608.04663) | The August 2026 arXiv record and title exist. Its prosocial multi-agent framing is distinct from the proposed machine-failure memory. |
| [Constraint formulation survey](https://arxiv.org/abs/2402.02025) | The referenced record exists; use it to distinguish expected, state-wise and other constraint formulations. |
| [CVaR decision-making paper](https://arxiv.org/abs/1506.02188) | The referenced risk-sensitive/robust decision-making record exists and remains relevant to the tail-risk comparison. |

These checks confirm source identity and the stated high-level overlap. They do not mean the papers' reported gains transfer to the proposed environment.

## Important additions to the reading map

### October 3: fear, physiological inspiration and time pressure

The [fear/survival/pressure extension](../01_Architecture/FEAR_SURVIVAL_AND_PRESSURE_PLAN.md) maps these primary sources to planned experiments. Source identity and abstract-level scope were checked; no reproduction or exhaustive novelty review was performed.

| Source | Relevant overlap and limit |
|---|---|
| [Lipton et al., Intrinsic Fear](https://arxiv.org/abs/1611.01211) | A learned imminent-catastrophe model shapes reward. Fear learning alone is existing work; it is not VALOR's differentiator. |
| [McDuff and Kapoor, Visceral Machines](https://arxiv.org/abs/1805.09975) | Physiological-signal-derived intrinsic rewards tested in simulated driving. VALOR does not currently collect physiology or implement this method. |
| [Pardo et al., Time Limits in Reinforcement Learning](https://proceedings.mlr.press/v80/pardo18a.html) | Distinguishes task deadlines from training cutoffs and supports including remaining task time in observations. Does not establish preemptive wall-clock control. |
| [Sezener and Dayan, Static and Dynamic Values of Computation in MCTS](https://proceedings.mlr.press/v124/sezener20a.html) | Values computations by their effect on action quality. Applying the principle to VALOR's urgency-aware scheduler is a proposed design inference. |

| Source | Why it changes the review | Priority |
|---|---|---|
| [Vaskov, Schwarting and Baker, Do no harm: A counterfactual approach to safe reinforcement learning (L4DC 2024)](https://proceedings.mlr.press/v242/vaskov24a.html) | Defines counterfactual harm relative to an alternate safe policy, including situations where violations are inevitable. This directly overlaps baseline-relative consequences and attribution. | Read before claiming novelty in consequence comparison |
| [Li, Wu and Shi, Counterfactually Safe Reinforcement Learning (May 2026 preprint)](https://arxiv.org/abs/2605.25114) | Defines individual harm when a chosen action is worse than a baseline alternative and proposes constrained policy learning around it. | Add to the claim chart; keep publication status explicit |
| [Xue et al., Model-Based Proactive Cost Generation for Learning Safe Policies Offline with Limited Violation Data (May 2026 preprint)](https://arxiv.org/abs/2605.01356) | Uses learned-model rollouts to synthesize counterfactual unsafe samples from limited-violation data. This overlaps imagined hazards before direct failure, with different assumptions. | Read before the imagination-before-injury experiment |

These sources narrow the novelty claim but do not establish that persistent, context-sensitive counterfactual retrieval has no room for improvement. That requires experiments and a broader search.

## Implementation sources and practical implications

| Official source | Checked statement and plan implication |
|---|---|
| [Safety-Gymnasium repository](https://github.com/PKU-Alignment/safety-gymnasium) | Its README provides benchmark installation/examples and notes a Python 3.11 limitation related to pygame. Treat documented dependency constraints seriously; verify pinned versions instead of assuming the newest interpreter works. |
| [OmniSafe repository](https://github.com/PKU-Alignment/omnisafe) | Its README reports testing Python 3.8–3.10 on Linux and says Windows is not officially supported. Use an isolated Linux/WSL2 reference environment if chosen. |
| [SafeDreamer repository](https://github.com/PKU-Alignment/SafeDreamer) | Reproduction instructions specify an older tested JAX stack, Python 3.8 examples and CUDA/cuDNN compatibility checks. Budget reproduction work and isolate dependencies. |
| [Recurrent PPO official documentation](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_recurrent.html) | Documents recurrent PPO policies. This is an available route for a controlled partial-observation comparison; it is not evidence that a particular AACE configuration works. |
| [Gymnasium time-limit guidance](https://gymnasium.farama.org/main/tutorials/handling_time_limits/) | Explains termination versus truncation. Store both and avoid classifying every timeout as catastrophe. |

No packages, reference code or checkpoints were installed or executed during this assessment. Upstream support statements are documentation checks, not local compatibility results. Exact dependencies belong in the implementation smoke-test output.

## Product adjacency checked

[Foxglove](https://foxglove.dev/) describes robotics data collection, recording visualization, triage, search and curation. [Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/latest/index.html) documents robot simulation, sensors, synthetic data and validation workflows. These official pages support the existence of adjacent tooling; they do not establish customer demand, market size, or comparative quality.

The recommendation to integrate with existing simulation/observability and focus on verified recurrence reduction is an inference from these product categories and the local project design. Interviews and a customer pilot are still needed.

## Check limitations

Direct retrieval of the Fear Field and risk-conditioned-RL DOI pages failed in this browsing session. Primary-publisher search results corroborated the Fear Field title/DOI, but this assessment does not rely on uninspected full-text claims from those pages. Other datasets and formal-control papers in the original archive were not comprehensively re-audited. Check relevant assumptions and licenses when a component becomes part of the build.

Maintain a claim chart with: proposed mechanism, closest primary reference, exact overlap, remaining hypothesis, comparison needed and evidence obtained. Keep source verification separate from proof that an implementation or business works.
