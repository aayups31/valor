# VALOR

A general research decision model investigating threat appraisal, vulnerability, resource preservation, time pressure and experience that persists after damage. The rover is one benchmark. AACE is the hypothesis that verified counterfactual memory improves adaptation beyond equally resourced simpler methods inside this architecture.

The domain-independent core now accepts public context, finite candidates, scoped consequence forecasts and a fixed external policy. A simulated service workflow demonstrates the same core outside robotics. Existing trained task/dynamics weights remain rover-specific; a reusable interface is not evidence of universal learned intelligence. See [the general core architecture](01_Architecture/GENERAL_DECISION_CORE.md).

The intended product is [a proctor for AI agents doing consequential work](01_Architecture/AGENT_PROCTOR_DIRECTION.md), combining learned harmful experience with explicit consequence assessment, human permissions and inspectable predicted branches. External-agent integrations and qualified learned action permission are future work; current actions run only in simulations.

Project-original source and documentation use [Apache 2.0](LICENSE), selected by the project owner. See [NOTICE](NOTICE) for attribution and third-party scope.

Implementation began October 3, 2026. The numerical rover, public observation interface, snapshots, heuristic controls, action guard and decision records are implemented. No research advantage has been established.

Latest milestone: public-history action-conditioned models predict terminal outcomes, experienced harm, work, recovery, resources, time and integrity. A 635-parameter summary head improves harm Brier by 17.63% relative to a context/action table on 12,000 check records from 500 paired episode IDs, but terminal prediction is worse and strong known-law controls remain better on outages. Public-law auditing exposes contradictions across every learned fit's check contexts; predictions remain unchanged and unqualified. Twelve structured consequence previews and a curated audited example are exported. All 226 regression tests pass. See [build report 11](reports/2026-10-12-build-11.md) and [the frozen continuation protocol](01_Architecture/CONTINUATION_MODEL_PROTOCOL.md). [Report 10](reports/2026-10-12-build-10.md) retains the earlier negative behavior comparison. The premium local demo still uses analytic service forecasts and a hand-specified observer without learned action influence. No felt fear, calibrated learned survival policy or AACE advantage is established.

## Open the demo

On this Windows computer, double-click **Start VALOR.cmd** in the project folder. It starts the engine quietly and opens the experiment in your default browser. Press **Try VALOR**, or choose a situation and use **Run this scenario** beside it. **How it works** explains the task and controls. If an earlier interface is still running, the launcher asks you to open **Stop VALOR.cmd**, then start again.

Choose everyday work, pressure, damage, low reserves or a short deadline. The engine computes a finite simulated run; **Play record**, **Next decision** and the numbered timeline let you inspect it. Opening alternatives, internal state or complete evidence pauses playback. Download the complete record for all actual decisions and outcomes. Changing conditions clears the previous evidence.

**Rover benchmark** opens the existing paired comparison at `/rover`. Use **Start mission**, **One decision** and the mission selector there. **Stop VALOR.cmd** closes the engine started by the launcher. Closing a browser tab alone does not stop the engine.

The runtime is already installed on this laptop. On another Windows machine the launcher can set up the small demo environment if Python 3.11+ is installed; first setup needs internet. It does not install the optional neural training stack. No account or paid API is required.

Your interface preferences are maintained in [UI design principles](UI_DESIGN_PRINCIPLES.md) and [the product experience direction](01_Architecture/PRODUCT_EXPERIENCE_DIRECTION.md). The Scale-inspired redesign and its verification are recorded in [UI build report 07](reports/2026-10-12-build-07-ui.md).

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

Open http://127.0.0.1:8765 for the general decision study. The service core uses analytic benchmark forecasts; its experimental affect observer is processed over the recorded public states and has no action authority. Playback changes only the view. It controls no real service or user file.

The rover comparison at http://127.0.0.1:8765/rover begins paused. Its worker owns both engines; browser polling does not drive their decisions. Apply brakes bypasses the controllers and applies one bounded braking action; momentum still follows physics.

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

The package also declares a `valor` console entry point for fresh installs; the existing `aace` command and `python -m aace` remain compatible. The browser's main study and these commands use the same service decision core. The rover probe applies no action with its unqualified evidence.

## Experimental learned threat head

The action-conditioned continuation experiment runs independently of earlier fitted artifacts:

```powershell
.\.venv\Scripts\python.exe scripts/Run-ContinuationPilot.py
```

`aace continuation-pilot --smoke` runs a separate small engineering cohort. The complete pilot creates mixed training/selection data, three fits and four paired checks. Its `previews.json` separates predicted action consequences from observed offline outcomes; this is a structured export, not yet a new browser view. No prediction can authorize an action. [Report 11](reports/2026-10-12-build-11.md) documents reproduction, qualification gaps and strong controls.

The offline behavior rehearsal reuses a completed adaptive v2 fit index:

```powershell
.\.venv\Scripts\python.exe scripts/Run-DecisionRehearsal.py --pilot-index artifacts/adaptive-history-pilots/pilot-v2-0a91c83b/index.json
```

On a fresh checkout, run the adaptive pilot below first and use its printed index path. `aace decision-rehearsal --pilot-index PATH` exposes the same command; `--smoke` runs two separate engineering subjects. Frozen predictors rank experimental proposals only; qualified action evidence comes from a guard that knows this simulator's latent danger. This is separate from the browser demo and controls no real tools or services. [Report 10](reports/2026-10-12-build-10.md) explains the negative comparative result, actual failures, work accounting and limitations.

The adaptive repaired-body experiment can be reproduced with:

```powershell
.\.venv\Scripts\python.exe scripts/Run-AdaptiveHistoryPilot.py
```

It trains on mixed stable/extinction/reversal histories and checks those conditions plus unseen recurrence. `collect-adaptive`, `train-history --adaptive` and `evaluate-history` expose individual stages. A compact learned summary model and adaptive count controls are included; settings are selected without check access. All outputs remain experimental. [Report 09](reports/2026-10-12-build-09.md) explains results and reproduction artifacts.

The earlier frozen v1 experiment remains reproducible separately:

```powershell
.\.venv\Scripts\python.exe scripts/Run-HistoryPilot.py
```

It creates new datasets, four learned controls for each of three training seeds, and stable/extinction/reversal development checks. Individual commands are `collect-history`, `train-history` and `evaluate-history`; use `--help` for arguments. This requires the optional learning stack and controls no real service. The frozen pilot found mean Brier 0.21693 for its recurrent head versus 0.17097 for simple cue counts. Its checkpoints are experimental and do not select demo actions. Full results and limitations are in [report 08](reports/2026-10-12-build-08.md).

The earlier candidate-conditioned threat head remains available separately:

```powershell
.\.venv\Scripts\python.exe -m aace collect-threat --split train --episodes 6000
.\.venv\Scripts\python.exe -m aace collect-threat --split selection --episodes 800
.\.venv\Scripts\python.exe -m aace collect-threat --split check --episodes 800
.\.venv\Scripts\python.exe -m aace train-threat --training artifacts/datasets/TRAIN-ID --selection artifacts/datasets/SELECTION-ID
.\.venv\Scripts\python.exe -m aace evaluate-threat --checkpoint artifacts/threat-models/MODEL-ID --check artifacts/datasets/CHECK-ID
```

Use the printed directories. Observed whole-continuation outcomes train a small neural event head and a simpler linear head on identical public features, batches and update opportunities. Episode IDs, outcome labels and analytic probabilities are not inputs; analytic probabilities are scoring references only. Unknown/censored endings are excluded. The feature-vector learner has no domain dynamics imports; the first feature encoder and trained weights are service-specific. Proper Brier/log-loss scores and reliability bins use separate development episodes. Outputs remain experimental and are not wired into action permission until independent calibration, applicability and risk-bound checks pass.

Both heads start from the training event rate; the constant prior is also an eligible checkpoint. The 1,441-parameter neural head achieved Brier 0.03686 / log loss 0.13473 on 800 separate synthetic episodes, versus 0.03778 / 0.14631 for the 11-parameter linear head. This is one training seed after two development recipe trials, with only 34 failure events. It does not establish AACE benefit, individual risk bounds or general transfer. Complete controls and reliability bins are in [report 05](reports/2026-10-09-build-05.md).

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

- A general decision core for threat appraisal, resource/capability preservation and time pressure under external authority.
- Simulated service and rover benchmarks, with scoped numerical threat and dynamics models.
- Conventional controls and qualified incident memory experiments; memory and learned planning remain pending.
- A premium local decision inspector and reproducible comparisons with explicit evidence and compute budgets.

Default external compute/API/hosting spend is $0. CPU is the reference backend. This project does not train an LLM.

## Documentation

- [Current implementation plan](IMPLEMENTATION_MASTER_PLAN.md)
- [Fear, survival, intuition and pressure design](01_Architecture/FEAR_SURVIVAL_AND_PRESSURE_PLAN.md)
- [Persistent affect, vulnerability and survival research](01_Architecture/AFFECTIVE_SURVIVAL_RESEARCH_PLAN.md)
- [Build progress and stop reports](BUILD_PROGRESS.md)
- [Project assessment](PROJECT_REVIEW_AND_WORKING_PLAN.md)
- [Research background](START_HERE.md)

The original blueprint describes research aspirations. The implementation plan and progress report distinguish implemented behavior from unvalidated claims.
