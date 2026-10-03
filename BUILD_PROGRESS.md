# Build progress

## October 3, 2026 — implementation kickoff

User authorized implementation, use of https://github.com/aayups31/valor for version control, frequent intermediate commits, and a full report whenever work stops.

### Verified at kickoff

- Local research archive preserved and connected to the empty GitHub repository.
- Git 2.51.2 and Python 3.13.1 available; 541.79 GiB free disk reported.
- Python package metadata contains NumPy 2.2.5 / PyTorch 2.7.1; runtime compatibility still needs isolation and smoke tests.
- No applicable AGENTS.md was found in the workspace or checked ancestors.

### Current work

Build stages 0–3: isolated runtime, numerical rover, observation/snapshot invariants, external guard, structured records and local replay/demo.

### Intermediate milestone: runtime and numerical core

- Archive commit `398300c` pushed to `origin/main`.
- Isolated Python 3.13.1 runtime with NumPy 2.2.5, Gymnasium 1.2.1 and pytest 8.4.2 installed.
- Six initial scenarios, pure numerical transitions, persistent damage, resource accounting and distinct completion/catastrophe/deadline/truncation outcomes implemented.
- Snapshots preserve state, configuration, scenario and reset RNG; timestep-indexed disturbances permit paired branches.
- Heuristic controls, bounded action guard and JSON decision/outcome records implemented. External stop bypasses controller execution.
- First test run: 28 checks passed; an additional explicit stop-bypass check was added during review.
- Gym smoke and 100-step exact paired replay passed. The smoke measured 138.76 paired steps/s including per-step NumPy assertions; this is not a training/planner throughput measurement.

### Remaining research work

Conventional SAC training, learned-model validation, qualified memory/reflection, matched adaptation comparisons, locked final experiments and final research decision. No AACE benefit is claimed from implementation checks.

### Intermediate milestone: oracle planning

- Numerical-core commit `805b8d6` pushed to `origin/main`; 29 tests passed before that commit.
- Fixed-budget simulator-backed planner evaluates six plan continuations with independent future disturbances shared across candidates. It never reads the actual environment's future noise.
- Forecasts label finite horizon, sample count, raw failure frequency, sampling interval, terminal approximation and actual branch work. These forecasts are oracle calculations, not learned/calibrated predictions.
- Seed-42 shortcut episode: heuristic direct loses its actuator at step 35; the detour heuristic completes at step 158 without damage; oracle planner completes at step 146 without damage.
- Oracle episode measured 156,219 branch transitions, p50 25.62 ms / p95 62.98 ms / p99 81.66 ms decision time. This is one engineering episode, not a latency guarantee or comparative research result.

Full stop reports will record changes, commit/push status, commands and test results, measured limitations, next steps and user input needed.
