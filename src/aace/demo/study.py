"""Bounded non-robotic decision records for the local visual inspector."""
from uuid import uuid4

from aace.benchmarks.run import service_episode
from aace.benchmarks.service import SCENARIOS
from aace.decision import ComputeBudget
from aace.decision.affect import AffectiveObserver, SurvivalObservation
from aace.telemetry import source_provenance


def create_study(payload):
    scenario, seed = payload.get("scenario", "hazard"), payload.get("seed", 42)
    if scenario not in SCENARIOS or type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("Choose a known study and a whole-number seed in [0, 2^31)")
    source = source_provenance()
    settings = SCENARIOS[scenario]
    initial = {"quota":settings.get("quota",20), "integrity":settings.get("integrity",1),
               "progress":0, "elapsed_s":0, "status":"running"}
    run = service_episode(scenario, seed=seed, budget=ComputeBudget(action_seconds=2))
    observer, state = AffectiveObserver(), initial
    for row in run["decisions"]:
        action = row["proposed_action"]
        cue = action["name"] if action else "no_supported_action"
        before = observer.observe(SurvivalObservation(state["integrity"],
            min(1, state["quota"]/initial["quota"]),state["elapsed_s"],cue))
        outcome = row["actual_outcome"]
        after = observer.observe(SurvivalObservation(outcome["integrity"],
            min(1, outcome["quota"]/initial["quota"]),outcome["elapsed_s"],cue,
            safe_exposure=row["commit"]["status"] == "applied" and outcome["integrity"] >= state["integrity"]))
        row["affect_observer"] = {"before":before,"after":after}
        state = outcome
    return {"study_id":uuid4().hex, "protocol":"finite local simulation; replay records are computed before playback",
            "initial_state":initial, "goal":8, "deadline_s":settings.get("deadline_s",30),
            "public_load":settings["load"], "forecast_source":"declared analytic simulation equations",
            "affect_notice":"Experimental observer; activation does not change decisions or establish subjective feeling",
            "claim":"Engineering study; not AACE advantage, calibrated learned fear or real service execution",
            **source, **run}
