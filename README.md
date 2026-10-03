# VALOR / AACE

A local research system investigating whether verified counterfactual memory improves adaptation after limited failure exposure compared with equally resourced simpler methods.

Implementation began October 3, 2026. The numerical rover, public observation interface, snapshots, heuristic controls, action guard and decision records are implemented. No research advantage has been established.

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

## Development data collection

```powershell
.\.venv\Scripts\python.exe -m aace collect --split train --steps 10000
.\.venv\Scripts\python.exe -m aace collect --split validation --steps 3000
```

The packaged split manifest reserves separate episode-seed ranges. Collection crosses direct/detour/braking policies with all declared training scenarios and adds bounded random actions. Records include applied actions and episode grouping. The model-input loader exposes only the 35 public observation values and two actions; identifiers/seeds/scenario labels remain metadata. Its six targets are normalized physical-state deltas. Hashes and split checks reject changed or incorrectly assigned datasets. The reserved test range is not collectable through this development command; the final protocol remains pending.

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
