"""Trace explanations are derived from executed rules, never generated guesses."""

REASONS = {
    "heuristic_rule": "Selected by the declared waypoint/detour control rule; no forecasts were used.",
    "no_forecast_budget": "This alternative was listed but was not forecast by this controller.",
    "external_stop": "External stop overrode the proposed action with bounded braking.",
    "invalid_action": "Invalid controller output was replaced with bounded braking.",
    "action_clipped": "The proposed action exceeded the command range and was clipped.",
    "best_admissible_score": "Highest recorded objective among admissible evaluated plans.",
    "lower_score": "Admissible, but another evaluated plan had a higher recorded objective.",
    "failure_limit": "Estimated failure frequency exceeds the external mission limit.",
    "no_admissible_plan": "No evaluated plan met the risk rule; bounded braking fallback selected.",
}


def explain(reason_codes: list[str]) -> list[str]:
    return [REASONS.get(code, code) for code in reason_codes]


def source_provenance() -> dict:
    """Capture source identity when a session starts, including uncommitted work."""
    import hashlib
    import subprocess
    from pathlib import Path
    source = Path(__file__).resolve().parents[1]
    repository = source.parent.parent
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*.py")):
        digest.update(str(path.relative_to(source)).replace("\\", "/").encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    revision = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"],
                              capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(repository), "status", "--porcelain"],
                            capture_output=True, text=True)
    return {"git_revision": revision.stdout.strip() if revision.returncode == 0 else None,
            "git_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
            "python_source_sha256": digest.hexdigest()}
