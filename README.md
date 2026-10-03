# VALOR / AACE

A local research system investigating whether verified counterfactual memory improves adaptation after limited failure exposure compared with equally resourced simpler methods.

Implementation began October 3, 2026. The numerical rover, public observation interface, snapshots, heuristic controls, action guard and decision records are implemented. No research advantage has been established.

## Setup and verified commands (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m aace doctor
.\.venv\Scripts\python.exe -m aace smoke
.\.venv\Scripts\python.exe -m pytest -q
```

Use Python 3.11+; the first verified runtime is Python 3.13.1. Exact installed dependencies are recorded in `requirements-core.lock.txt`. The optional learning stack is isolated from the basic simulator/demo.

## Scope

- Lightweight continuous-control inspection rover with battery and persistent damage.
- Conventional control baselines, a small learned world model, consequence planning and qualified incident memory.
- A local decision inspector using the same engine and recorded calculations.
- Reproducible comparisons with explicit observation, evidence and compute budgets.

Default external compute/API/hosting spend is $0. CPU is the reference backend. This project does not train an LLM.

## Documentation

- [Current implementation plan](IMPLEMENTATION_MASTER_PLAN.md)
- [Build progress and stop reports](BUILD_PROGRESS.md)
- [Project assessment](PROJECT_REVIEW_AND_WORKING_PLAN.md)
- [Research background](START_HERE.md)

The original blueprint describes research aspirations. The implementation plan and progress report distinguish implemented behavior from unvalidated claims.
