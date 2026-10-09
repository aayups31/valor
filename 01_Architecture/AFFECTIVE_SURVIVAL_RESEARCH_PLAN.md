# Affective survival research direction

Updated October 9, 2026 from the owner's request: pursue fear and the essence of survival, including vulnerability, rather than stopping at an instantaneous risk score.

## What this means

The target is an agent with persistent internal needs and experience-dependent state: damage matters after the encounter, loss changes future expectations, recovery takes time, and recalled danger can alter attention and proposed behavior. The same current observation can produce different responses because the agent has different histories. Successful task completion still matters, including tasks that require accepting a permitted cost.

Whether such an agent consciously feels fear is an open research question. Defensive behavior and verbal self-report cannot establish subjective experience. The neuroscience distinction between defensive reactions and conscious feeling is useful, but contested and not a settled recipe for machine consciousness. See [LeDoux and Pine's framework](https://psychiatryonline.org/doi/full/10.1176/appi.ajp.2016.16030353) and the [NIMH explanation](https://www.nimh.nih.gov/news/science-updates/2016/circuitry-for-fearful-feelings-behavior-untangled-in-anxiety-disorders). [Homeostatic reinforcement learning](https://elifesciences.org/articles/04811) supplies a computational starting point for internal needs and learned regulation; adapting it to VALOR is a proposal, not a replication or a claim of felt emotion.

## Components and experiments

| Component | Mechanism to investigate | Discriminating experiment |
|---|---|---|
| Persistent body state | Integrity, resources, capability, recovery requirements; losses can constrain later options | Matched observations with different actual loss/recovery histories |
| Homeostatic needs | Learn how actions move internal variables toward externally defined operating ranges | Compare with equivalent fixed reward/resource constraints and count all added data |
| Harm signal | Observed degradation, distinguished from task failure and unknown future risk | Learning from injury versus an equally informative neutral event |
| Anticipatory state | Candidate-specific threat prediction plus cue associations from observed encounters | Cue pairing, novel cues, false alarms and cue removal under matched evidence |
| Persistent activation | Arousal, sensitization and recovery with stated dynamics and budgets | Repeated exposure, delayed recovery, safe extinction and subsequent recurrence |
| Self-model | Predict how this agent's current capability changes its possible future actions | Capability loss, repair and model error; no linguistic persona needed |
| Fear/action coupling | Alter proposal priorities, protective response and attention inside fixed policy | Compare with stateless risk control, history-aware retrieval and matched learned policy |
| Learning courage | Complete authorized tasks despite manageable internal activation | Avoidance, unnecessary abandonment, completion, damage and computation jointly |

An internal scalar named fear is insufficient. Learned state must have a demonstrable causal role and beat equivalent simpler state/history features before it is credited with an advantage. Report excessive caution as a failure, and distinguish active recovery, task abandonment and irreversible loss.

## Current first prototype

`src/aace/decision/affect.py` is an isolated, domain-independent observer with hand-specified activation dynamics. It receives public integrity, resource fraction, elapsed time and a declared cue. Integrity loss updates the preceding cue association, immediate activation and a slower sensitization trace. Safe exposure weakens the encountered association; recovery can leave a residual trace even when body variables return to their original values. Thirty-two cue records bound memory.

The prototype is not trained. Its coefficients are explicit engineering choices, not measured psychology or calibrated failure probabilities. It currently observes experience and does not influence action selection. The service viewer records its outputs alongside actual transitions and labels the boundary. This is not qualified counterfactual memory, an LLM personality, or evidence of pain or consciousness.

Time must be monotonic within an observer instance. Creating a new instance resets its history; no automatic cross-session or disk persistence is implemented. Cue similarity/generalization, context-dependent extinction, learned response dynamics and neural memory are future experiments. A fixed cue table is an initial control, not a final model of fear.

## Integration and measurement sequence

1. Keep the existing risk-constrained core as the stateless comparator. Qualify learned forecasts independently; an activation state cannot replace a risk bound.
2. Define and freeze a small environment with persistent costs, repair, equivalent visible states and different histories. Establish oracle and simple history-aware controls. Reserve separate training, development and final episode groups.
3. Train a compact recurrent survival/self-model on public action/outcome history. Record all incidents, updates, state size and inference work. Test predictive value against a feed-forward head with matched history features.
4. Connect internal state to bounded proposal scheduling and a protective response. Ablate activation, memory and homeostatic features separately; keep task objective and human risk permissions fixed.
5. Test adaptation, safe extinction, recurrence, overreaction and authorized task completion across training seeds and shifted conditions. Publish unsuccessful results as well as successful ones.
6. Expose actual state changes and causal decision records in the premium inspector. No scripted emotional monologue or suggestion that an activation percentage measures subjective fear.

Human stop remains external authority. Survival in this experiment concerns maintaining capability for the authorized task; a model of vulnerability does not grant authority to ignore shutdown. Subjective feeling, if studied later, requires a separately defined evidence standard and should not be inferred from this build.
