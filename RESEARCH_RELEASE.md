# VALOR 0.2.0 research release

This research prerelease contains a local visual replay, the scoped simulator evidence, and a read-only SQLite shadow observer. It has no authority to control an external agent. The selected shared-reserve policy uses a conventional Markov forecast and guarded lookahead. Learned-memory superiority remains unproven.

## Run the release

In the repository, double-click **Start VALOR.cmd** on Windows, then choose **Explore two releases sharing one reserve**. If an earlier instance is already running, stop it with the provided launcher before starting the new version. For a wheel installation, install the release asset into a Python 3.11+ virtual environment with the declared core dependencies and run `valor demo`. The local server prints its address; open the replay at `/reserve`.

Choose a situation, load its paired replay, and step through either policy. The outcome summaries are observed simulator results. The expandable screen explains the lookahead decision, and the alternatives show the model's expected consequences. You can download the complete evidence. Each displayed case is one example, not a benchmark average.

## Reproduce the checkpoint 8 and 9 results

Use a full Git clone with the optional learning dependencies installed (the historical runner imports Torch). This command creates a fresh disposable clone; it leaves the active checkout alone.

```powershell
.\.venv\Scripts\python.exe scripts/Reproduce-Research.py
```

The script pins research revision `64fdca033f23cfff5141229becbaa7f8d9655a50`, reproduces the replication first, verifies its rows and selected policy, then runs the four shifts with the reproduced selection report. This rebinds the selection to the clone's actual input bytes, which may use different line endings from the historical working copy. It verifies **both complete row hashes and all paired intervals**. Runtime, local paths, and provenance fields need not match. See [report 15](reports/2026-11-09-build-15.md) for the frozen comparisons and limitations.

## Rebuild and check the wheel

The tested build used Python 3.13.1 and setuptools 78.1.0 with no build isolation or dependency download. Set `SOURCE_DATE_EPOCH` to `1794182400` (November 9, 2026 at midnight UTC), then run:

```powershell
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --no-build-isolation --no-index --wheel-dir artifacts/wheel
.\.venv\Scripts\python.exe scripts/Verify-ResearchWheel.py artifacts/wheel/valor_aace-0.2.0-py3-none-any.whl artifacts/wheel-installed
```

The verifier checks source, web assets and license bytes, then imports a separate installation using the current environment's core dependencies. It exercises the installed replay and shadow observer. Two builds in the stated environment produced identical bytes. Compare against the release's SHA-256 file; other build tool versions may produce different bytes.

## Shadow a supported local action

The [shadow protocol](01_Architecture/SHADOW_SQLITE_PROTOCOL.md) specifies the supported schema, two operations and three observed cases. Create fresh disposable data:

```powershell
.\.venv\Scripts\python.exe scripts/New-ShadowFixture.py artifacts/my-shadow-trial
.\.venv\Scripts\python.exe -m aace.shadow observe artifacts/my-shadow-trial/bounded.sqlite3 --operation archive_pending --output artifacts/my-shadow-trial/proposal.json
```

Have a separate worker perform the intended operation and close its connection, then inspect the actual result:

```powershell
.\.venv\Scripts\python.exe -m aace.shadow review artifacts/my-shadow-trial/bounded.sqlite3 --observation artifacts/my-shadow-trial/proposal.json --output artifacts/my-shadow-trial/outcome.json
```

VALOR writes evidence files only. It does not intercept, approve, block or execute an action. It detects differences between snapshots, not their cause. The [observed pilot records](reports/examples/sqlite-shadow-pilot-v1.json) come from actual local database changes by a tool-using coding agent on synthetic records. They are not a field estimate of effectiveness.
