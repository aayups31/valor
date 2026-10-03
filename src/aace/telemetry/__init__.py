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

