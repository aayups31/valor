"""Bounded, reproducible examples for the shared-reserve replay."""

from functools import lru_cache

from aace.benchmarks.shared_reserve import GUARDED, play_pair

EXAMPLES = {"nominal": 113000, "volatile": 114000, "harsher": 115000, "damaged": 116000}


@lru_cache(maxsize=len(EXAMPLES))
def reserve_replay(scenario):
    if scenario not in EXAMPLES:
        raise ValueError("Unknown replay scenario")
    seed = EXAMPLES[scenario]
    return {
        "schema": "shared-reserve-replay-v1", "scenario": scenario, "seed": seed,
        "scope": "One recorded simulator example. Not aggregate evidence or an action authorization.",
        "evidence": "Known transition rules and a nominal Markov danger model. No learned fear signal.",
        "guarded": play_pair(seed, scenario, GUARDED, {}, trace=True),
        "baseline": play_pair(seed, scenario, "myopic_markov", {}, trace=True),
    }
