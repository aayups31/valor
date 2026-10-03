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
