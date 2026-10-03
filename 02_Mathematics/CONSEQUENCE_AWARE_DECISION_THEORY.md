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
