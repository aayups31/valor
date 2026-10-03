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
