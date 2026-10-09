# VALOR

A general research decision model combining threat appraisal (the fear analogy), resource preservation, time pressure and eventually qualified experience. The rover is one benchmark, not the product. AACE is the hypothesis that verified counterfactual memory improves adaptation beyond equally resourced simpler methods inside this architecture.

The domain-independent core now accepts public context, finite candidates, scoped consequence forecasts and a fixed external policy. A simulated service workflow demonstrates the same core outside robotics. Existing trained task/dynamics weights remain rover-specific; a reusable interface is not evidence of universal learned intelligence. See [the general core architecture](01_Architecture/GENERAL_DECISION_CORE.md).

Project-original source and documentation use [Apache 2.0](LICENSE), selected by the project owner. See [NOTICE](NOTICE) for attribution and third-party scope.

Implementation began October 3, 2026. The numerical rover, public observation interface, snapshots, heuristic controls, action guard and decision records are implemented. No research advantage has been established.

Latest milestone: an ordinary learned controller completes the checked benign full missions, and a compact learned dynamics ensemble is trained and evaluated. Hazardous controller transfer and damage-model calibration remain insufficient; learned planning and incident memory are still pending. See [build report 04](reports/2026-10-06-build-04.md) for results, limitations and next steps.

## Open the demo

On this Windows computer, double-click **Start VALOR.cmd** in the project folder. It starts the engine quietly and opens the demo in your default browser. Press **Start the demo** on the page. An optional **Show me around** walkthrough explains the mission, both approaches and the recorded decisions.

Use **Pause** to explore a choice, **One decision** to advance each unfinished rover once, and the mission selector to try different conditions. The advanced controls and full records are available below the explanation. **Stop VALOR.cmd** closes the engine started by the launcher. Closing a browser tab alone does not stop the engine.

The runtime is already installed on this laptop. On another Windows machine the launcher can set up the small demo environment if Python 3.11+ is installed; first setup needs internet. It does not install the optional neural training stack. No account or paid API is required.

Your interface preferences are maintained in [UI design principles](UI_DESIGN_PRINCIPLES.md).

## Developer setup and commands (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m aace doctor
.\.venv\Scripts\python.exe -m aace smoke
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m aace run --scenario shortcut --controller oracle_planner
.\.venv\Scripts\python.exe -m aace demo
```

Use Python 3.11+; the first verified runtime is Python 3.13.1. Exact installed dependencies are recorded in `requirements-core.lock.txt`. The optional learning stack is isolated from the basic simulator/demo.

Open http://127.0.0.1:8765 for the local demo. It begins paused. Start the mission, inspect candidate options, compare observed outcomes with forecasts, or download the full trace. The worker owns both engine instances; browser polling does not drive their decisions. Apply brakes bypasses the controllers and applies one bounded braking action; momentum still follows physics.

The first demo contains direct/detour heuristics and an **oracle planner**. It does not demonstrate learned AACE or counterfactual memory yet. Every oracle forecast reports its horizon, independent samples, sampling uncertainty, terminal approximation and branch work. Three samples are coarse engineering checks, not calibrated risk estimates. Missing evaluation and uncertainty remain visible.

`run` exports to ignored `artifacts/replays/` and stops at its wall-clock cap. Each replay records the start-time Git revision, dirty-worktree flag and Python-source hash. Curated episodes are not aggregate research results.

## CPU learning pilot

```powershell
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e '.[learning]'
.\.venv\Scripts\python.exe -m aace train --scenario benign --steps 12000 --max-seconds 180 --threads 2
.\.venv\Scripts\python.exe -m aace evaluate --checkpoint artifacts/training/RUN-ID/final --scenario benign
```

Replace `RUN-ID` with the printed run directory. `--resume` accepts a trusted checkpoint bundle created by this project. Bundles include weights/optimizer, replay buffer, hashes, versions, budgets, source identity and exact update counts. Resume begins a fresh episode; it is not exact mid-episode RNG continuation. Initialization/checkpoint I/O and completion of an in-progress operation can exceed the callback's wall-clock target slightly.

The controller uses the established [SB3 SAC implementation](https://stable-baselines3.readthedocs.io/en/v2.7.1/modules/sac.html), two 64-unit hidden layers, one environment and bounded CPU threads. Progress is logged every 1,000 steps and checkpoints every 5,000. Validation is explicitly a development pilot; final research manifests and statistical comparisons are still to be built. `requirements-learning.lock.txt` records the full tested CPU environment.

## General decision core and non-robotic examples

```powershell
.\.venv\Scripts\python.exe -m aace decision-example --domain service --scenario hazard
.\.venv\Scripts\python.exe -m aace evaluate-core --episodes 20 --seed-start 10000
.\.venv\Scripts\python.exe -m aace decision-example --domain rover --scenario shortcut
```

The service workflow is a local simulation of processing work under threat, quota and integrity constraints. It controls no real service or computer tool. Its analytic forecasts make fast/checked/restoration/abandonment choices inspectable. Core records distinguish forecasts, proposed actions, guarded application and actual outcomes. Unknown or experimental forecasts do not silently become safe probabilities. The rover adapter probe deliberately applies no action when its coarse evidence is unqualified. External stop, stale state and expired results are checked again at the action handoff; blocking calls are not preempted.

The package also declares a `valor` console entry point for fresh installs; the existing `aace` command and `python -m aace` remain compatible. The current browser viewer displays the rover benchmark; the new general-core examples are available through these commands and their exported JSON records.

## Experimental learned threat head

```powershell
.\.venv\Scripts\python.exe -m aace collect-threat --split train --episodes 6000
.\.venv\Scripts\python.exe -m aace collect-threat --split selection --episodes 800
.\.venv\Scripts\python.exe -m aace collect-threat --split check --episodes 800
.\.venv\Scripts\python.exe -m aace train-threat --training artifacts/datasets/TRAIN-ID --selection artifacts/datasets/SELECTION-ID
.\.venv\Scripts\python.exe -m aace evaluate-threat --checkpoint artifacts/threat-models/MODEL-ID --check artifacts/datasets/CHECK-ID
```

Use the printed directories. Observed whole-continuation outcomes train a small neural event head and a simpler linear head on identical public features, batches and update opportunities. Episode IDs, outcome labels and analytic probabilities are not inputs; analytic probabilities are scoring references only. Unknown/censored endings are excluded. The feature-vector learner has no domain dynamics imports; the first feature encoder and trained weights are service-specific. Proper Brier/log-loss scores and reliability bins use separate development episodes. Outputs remain experimental and are not wired into action permission until independent calibration, applicability and risk-bound checks pass.

## Development data collection

```powershell
.\.venv\Scripts\python.exe -m aace collect --split train --steps 10000
.\.venv\Scripts\python.exe -m aace collect --split validation --steps 3000
```

The packaged split manifest reserves separate episode-seed ranges. Collection crosses direct/detour/braking policies with all declared training scenarios and adds bounded random actions. Records include applied actions and episode grouping. The model-input loader exposes only the 35 public observation values and two actions; identifiers/seeds/scenario labels remain metadata. Its six targets are normalized physical-state deltas. Hashes and split checks reject changed or incorrectly assigned datasets. The reserved test range is not collectable through this development command; the final protocol remains pending.

## Learned dynamics development

```powershell
.\.venv\Scripts\python.exe -m aace train-world --training artifacts/datasets/TRAIN-ID --validation artifacts/datasets/VALIDATION-ID --epochs 30 --max-seconds 180
.\.venv\Scripts\python.exe -m aace evaluate-world --checkpoint artifacts/world-models/MODEL-ID --validation artifacts/datasets/VALIDATION-ID
```

Replace the directory placeholders with printed run directories. The optional learning dependencies are required. Three small probabilistic networks predict changes in position, velocity, battery and health from public observations and applied actions. Each member bootstraps whole recorded episode groups; collection's last episode may be partial. Normalization uses training data only. Checkpoints record data/source hashes, bootstrap groups, work, resource caps and validation-based selection. Weights load with PyTorch's restricted `weights_only` mechanism.

Validation reports no-change, training-mean and constant-velocity controls, damage/return/boundary strata, predictive interval coverage and 5/20/80-step rollouts using recorded actions. Rollouts start from one observed state and carry their own predictions; future observed states are scoring targets only. The decoder's physical clipping and known task geometry are explicitly reported. Trajectory checks reject interleaved episodes, broken state chains and premature terminal labels. Reports identify whether evaluation uses the same dataset hash as checkpoint selection; a different hash alone does not prove disjoint episodes. These are correlated development samples, not final-test results or calibrated failure probabilities. A model is not approved for planning until candidate ranking, threat calibration and closed-loop/terminal/policy-shift checks also pass.

For the SAC return-phase development pilot, use `train --curriculum mixed_return --entropy auto_0.1`. This training-only reset mixture includes complete missions and already-inspected return journeys on benign terrain. `evaluate` always starts the original full mission. Share this assistance and count its data/work in any matched research comparison. Changing curriculum or entropy requires a fresh run; it cannot silently change a resumed checkpoint.

## Scope

- Lightweight continuous-control inspection rover with battery and persistent damage.
- Conventional control baselines, a small learned world model, consequence planning and qualified incident memory.
- A local decision inspector using the same engine and recorded calculations.
- Reproducible comparisons with explicit observation, evidence and compute budgets.

Default external compute/API/hosting spend is $0. CPU is the reference backend. This project does not train an LLM.

## Documentation

- [Current implementation plan](IMPLEMENTATION_MASTER_PLAN.md)
- [Fear, survival, intuition and pressure design](01_Architecture/FEAR_SURVIVAL_AND_PRESSURE_PLAN.md)
- [Build progress and stop reports](BUILD_PROGRESS.md)
- [Project assessment](PROJECT_REVIEW_AND_WORKING_PLAN.md)
- [Research background](START_HERE.md)

The original blueprint describes research aspirations. The implementation plan and progress report distinguish implemented behavior from unvalidated claims.
