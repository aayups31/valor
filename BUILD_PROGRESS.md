# Build progress

### October 9 — scope clarification and general core

The user clarified that VALOR is a general open-source research decision model with fear/survival mechanisms, not a rover product. The rover remains one benchmark. Added a domain-independent decision contract/engine, fixed-policy threat constraints, resource/capability/time margins, bounded pressure ordering and a final stop/state/deadline authority gate. A non-robotic service-workflow simulation and rover adapter exercise the same core. The latter preserves coarse forecast evidence and abstains rather than pretending it is calibrated. Initial targeted regression: 32 passed. No new neural training or research advantage is claimed. [Architecture and boundaries](01_Architecture/GENERAL_DECISION_CORE.md).

Latest full stop report: [Build report 04 — learned dynamics and return competence](reports/2026-10-06-build-04.md). Previous: [Planning report 03 — fear, survival and pressure](reports/2026-10-03-planning-03-fear-pressure.md), [Build report 02 — premium UI redesign](reports/2026-10-03-build-02-ui.md), [Build report 01](reports/2026-10-03-build-01.md). The overall research build remains in progress.

### Stop 04 — verified state

- Three intermediate implementation commits pushed through `c285af4`; the full report and curated metrics follow separately.
- Final regression: 85 passed in 25.05 seconds; compilation and whitespace checks passed.
- Fresh ordinary SAC policy completes 20/20 benign development missions across two seed sets, but 0/10 hazardous-shortcut missions. One training seed and a changed recipe do not establish general robustness or curriculum attribution.
- Three-member learned dynamics model trained on 50,000 transitions in 101.61 seconds, using 443.60 MiB peak sampled working memory. It improves movement forecasts on 6,000 separate development transitions.
- Damage forecasting remains weak: health RMSE 0.04048 versus 0.04097 for no change, and nominal 90% health intervals cover only 52.75% of damage transitions. Model reports retain `planner_ready: false`.
- Training, selection and separate-check episode seeds are pairwise disjoint. Reserved final-test seeds remain unused. No AACE advantage or calibrated threat probability is claimed.
- All build jobs completed; local demo is stopped and can be opened with Start VALOR.cmd. Interface behavior is unchanged; rendered review remains pending. External compute/API/hosting spend remains $0.

### October 6 — return curriculum and learned dynamics implementation

- Diagnosed the earlier controller: it receives the correct home target after inspection, then drifts into a boundary and misses its deadline. No target-switch bug was found in this trace.
- Added an explicit training-only benign return curriculum and entropy preset; original full-mission evaluation remains unchanged. Commit `6482505` pushed during work.
- A fresh two-thread, ten-minute CPU pilot reached 64,557 steps / 16,014 gradient updates using 329.93 MiB peak sampled working memory. Its final policy completed all 10 benign development missions on seeds 10001–10010 without damage. This is one trained agent; hazardous transfer and research comparisons remain unvalidated.
- Added a compact probabilistic dynamics ensemble, episode bootstrap, training-only normalization, hashed restricted-load checkpoints, resource caps, physical/interval metrics, damage/return/boundary strata and recorded-action rollouts against simple controls.
- Dataset integrity now checks seed ranges, grouping, trajectory continuity and terminal placement. Full regression before the latest integrity/control additions: 80 passed; targeted learning/data/model checks after those additions: 36 passed.
- Bounded world-model training and separated development validation completed. Movement forecasts improved over simple controls, but damage prediction and its interval coverage remain weak. No learned model is approved for decision-making yet. External compute/API spend remains $0.

### Fear, survival, intuition and pressure — design recorded

The user's direction is specified in [the linked architecture extension](01_Architecture/FEAR_SURVIVAL_AND_PRESSURE_PLAN.md). Threat learning, resource margins, a fast response path and urgency-aware bounded planning have explicit interfaces, controls and E5 experiments. Primary memory comparisons remain separate. The design distinguishes mission time from action wall time, includes stale-warning and excessive-caution tests, and preserves external mission/override authority. Commit `2ed85dd` was pushed during work. Documentation links/fences and whitespace checks passed; a second design critique found no actionable issues. No new runtime mechanism, model training or benchmark was implemented in this planning turn.

### UI redesign — implementation complete; rendered review pending

User authorized a full premium, minimal interface redesign before further research implementation. Their lasting preferences are recorded in [UI design principles](UI_DESIGN_PRINCIPLES.md). The interface now uses an open light composition, rounded controls, contextual explanations, optional walkthrough, accessible candidate buttons and progressive detail. The double-click Windows launchers are implemented and checked on this laptop. Engine behavior and research claims are unchanged. Browser access was declined; source/API checks passed without browser workarounds.

### UI redesign — launcher milestone

- Interface commit `1ee252e` pushed to `origin/main` during work.
- Double-click Start/Stop VALOR launchers added; tested hidden startup, reuse without another server, verified process ownership, shutdown and reopening with browser launch suppressed.
- Installed laptop runtime reused. The optional neural stack is not required or installed by the launcher.
- Full Python regression: 65 passed in 20.08 seconds. Actual engine records also passed the Node plain-language evidence checks, including damage, completion, external braking and invalid-command overrides.
- Live HTTP shortcut comparison at speed 8: direct rule ended with actuator loss; oracle planner completed with 146 decisions and a complete export. This reproduces an engineering example, not a research result.
- JavaScript syntax, PowerShell syntax, HTML ID/reference contract and whitespace checks passed. Rendered layout, browser interactions and a fresh-machine bootstrap remain unverified.

## October 3, 2026 — implementation kickoff

User authorized implementation, use of https://github.com/aayups31/valor for version control, frequent intermediate commits, and a full report whenever work stops.

### Verified at kickoff

- Local research archive preserved and connected to the empty GitHub repository.
- Git 2.51.2 and Python 3.13.1 available; 541.79 GiB free disk reported.
- Python package metadata contains NumPy 2.2.5 / PyTorch 2.7.1; runtime compatibility still needs isolation and smoke tests.
- No applicable AGENTS.md was found in the workspace or checked ancestors.

### Current work

Stages 0–3 are implemented and checked at code/API level; browser visual verification remains pending. The conventional SAC pilot now completes the benign full mission but fails hazardous transfer. Learned dynamics training/evaluation is implemented; damage forecasting and calibration remain insufficient for planning. Qualified memory and matched research comparisons remain ahead. No build job remains active at the latest stop; the local demo is stopped.

### Intermediate milestone: runtime and numerical core

- Archive commit `398300c` pushed to `origin/main`.
- Isolated Python 3.13.1 runtime with NumPy 2.2.5, Gymnasium 1.2.1 and pytest 8.4.2 installed.
- Six initial scenarios, pure numerical transitions, persistent damage, resource accounting and distinct completion/catastrophe/deadline/truncation outcomes implemented.
- Snapshots preserve state, configuration, scenario and reset RNG; timestep-indexed disturbances permit paired branches.
- Heuristic controls, bounded action guard and JSON decision/outcome records implemented. External stop bypasses controller execution.
- First test run: 28 checks passed; an additional explicit stop-bypass check was added during review.
- Gym smoke and 100-step exact paired replay passed. The smoke measured 138.76 paired steps/s including per-step NumPy assertions; this is not a training/planner throughput measurement.

### Remaining research work

Replicated controller competence and hazardous controls, damage/threat forecast qualification, learned planning, qualified memory/reflection, matched adaptation comparisons, locked final experiments and final research decision. No AACE benefit is claimed from implementation checks.

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

### Stop 01 — verified state

- Seven intermediate commits pushed through `493fef9`; the full report/metrics are committed separately.
- Final regression: 63 tests passed; CPU tensor, dependency, JavaScript syntax and whitespace checks passed.
- SAC continuation completed 50,000 additional steps in 361.17 seconds, 138.44 steps/s, 331.90 MiB peak sampled working memory. Total model history is 62,000 environment steps / 15,373 gradient updates.
- Frozen development validation: inspected waypoint on 10/10 episodes but completed 0/10 full missions. Baseline competence remains unfinished.
- Collected 10,000 train / 3,000 validation transitions with disjoint declared episode seeds; reserved test seeds unused.
- External compute/API/hosting spend: $0. Browser rendering verification and the learned AACE components remain pending.

### Intermediate measurement and dataset preparation

- Learning-pipeline commit `cec8172` pushed to `origin/main`; 56 checks passed.
- Clean-source seed-42 SAC pilot: 12,000 environment steps, 2,874 gradient updates, 96.02 seconds, 124.97 steps/s, 328.34 MiB peak sampled working memory, $0 external spend.
- Initial frozen validation on seeds 10001–10003: 0/3 completions, all deadline misses. The policy is not yet a competent research reference.
- A bounded 50,000-step / 480-second continuation is running from the saved model/optimizer/replay bundle. This is development training, not a final hypothesis test.
- Seeded transition collection and hashed manifests added for later world-model work. Inputs exclude episode IDs/seeds/scenario labels; development train/validation seed groups are disjoint and the test range is reserved.
