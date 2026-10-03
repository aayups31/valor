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

Conventional SAC competence/curriculum, learned-model validation, qualified memory/reflection, matched adaptation comparisons, locked final experiments and final research decision. No AACE benefit is claimed from implementation checks.

### Intermediate milestone: learning pipeline

- Demo commit `7179c00` pushed to `origin/main`.
- CPU PyTorch 2.7.1 tensor execution passed with two threads. SB3 2.7.1 imported and exercised by training tests; dependency consistency check passed.
- Bounded SAC trainer, progress ledger, periodic/final checkpoint bundles, source/version/hash records and frozen development-validation command implemented.
- Checkpoint continuation retains model/optimizer and replay history, while deliberately starting a fresh episode. Exact mid-episode continuation is not claimed.
- 54 tests passed before additional resource-cap checks were added; the tests verify actual gradient updates, save/load, hash integrity and resumed replay/update history.
- A bounded 12,000-step, 180-second, two-thread pilot is the next measurement. Policy competence and research advantage remain unestablished.

### Intermediate milestone: local demo

- Oracle-planner commit `0a3ff07` pushed to `origin/main`; 35 tests passed before that commit.
- Local browser interface and bounded background session worker implemented: paired maps, resource metrics, forecast paths, candidate inspection, real reason codes, step/run/pause/stop and JSON export.
- Demo server binds only to `127.0.0.1`; static assets are allowlisted, request inputs/session retention are bounded, and cross-origin control requests are rejected.
- Replays record start-time source provenance including uncommitted work; published paths do not mutate while a browser reads them.
- 45 tests passed, including HTTP/control/export and published-snapshot checks. JavaScript syntax check passed with Node.
- Live server/API available on port 8765. Browser render/interaction verification remains pending: the Codex browser webview failed to attach on both visible and background attempts. This did not block simulator, HTTP or source checks.
- PyTorch CPU 2.7.1 and SB3 2.7.1 installed in the project environment; neural runtime smoke and training pilot follow.

### Intermediate milestone: oracle planning

- Numerical-core commit `805b8d6` pushed to `origin/main`; 29 tests passed before that commit.
- Fixed-budget simulator-backed planner evaluates six plan continuations with independent future disturbances shared across candidates. It never reads the actual environment's future noise.
- Forecasts label finite horizon, sample count, raw failure frequency, sampling interval, terminal approximation and actual branch work. These forecasts are oracle calculations, not learned/calibrated predictions.
- Seed-42 shortcut episode: heuristic direct loses its actuator at step 35; the detour heuristic completes at step 158 without damage; oracle planner completes at step 146 without damage.
- Oracle episode measured 156,219 branch transitions, p50 25.62 ms / p95 62.98 ms / p99 81.66 ms decision time. This is one engineering episode, not a latency guarantee or comparative research result.

Full stop reports will record changes, commit/push status, commands and test results, measured limitations, next steps and user input needed.
