"""Experimental persistent affect observer, not calibrated risk or consciousness.

This state currently observes public experience. It has no action authority and
does not change the existing controller, risk policy, or consequence forecasts.
"""
from dataclasses import asdict, dataclass
from math import exp, isfinite


@dataclass(frozen=True)
class SurvivalObservation:
    integrity: float
    reserve_fraction: float
    elapsed_s: float
    cue: str
    safe_exposure: bool = False

    def __post_init__(self):
        for value in (self.integrity, self.reserve_fraction):
            if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Survival fractions must be finite in [0, 1]")
        if type(self.elapsed_s) not in (int, float) or not isfinite(self.elapsed_s) or self.elapsed_s < 0:
            raise ValueError("Observation time must be finite and nonnegative")
        if not isinstance(self.cue, str) or not 1 <= len(self.cue) <= 64 or type(self.safe_exposure) is not bool:
            raise ValueError("Provide a bounded cue and explicit safe-exposure flag")


class AffectiveObserver:
    """Hand-specified dynamics for experience-dependent internal activation.

    Cue association is an activation trace, never an event probability. Harm
    refers to observed simulated integrity loss, not evidence of felt pain.
    Safe exposures weaken activation only for the cue actually encountered.
    """

    version = "affective-observer-v1-experimental"

    def __init__(self):
        self.previous = None
        self.arousal = 0.0
        self.sensitization = 0.0
        self.associations = {}

    def observe(self, observation: SurvivalObservation):
        if not isinstance(observation, SurvivalObservation):
            raise ValueError("Expected a public survival observation")
        previous = self.previous
        if previous is not None and observation.elapsed_s < previous.elapsed_s:
            raise ValueError("Affect observations cannot move backward in time")
        dt = observation.elapsed_s-previous.elapsed_s if previous else 0.0
        harm = max(0.0, previous.integrity-observation.integrity) if previous else 0.0
        # The preceding cue gets credit for damage observed after its action.
        cause = previous.cue if previous else observation.cue
        association = self.associations.get(cause, 0.0)
        if harm:
            association += .6*min(1.0, 4*harm)*(1-association)
        elif observation.safe_exposure and previous:
            association *= .92
        if cause not in self.associations and len(self.associations) >= 32:
            del self.associations[next(iter(self.associations))]
        self.associations[cause] = association
        self.sensitization = max(self.sensitization*exp(-dt/120), min(1.0, 4*harm))
        needs = max(1-observation.integrity, 1-observation.reserve_fraction)
        activation = self.associations.get(observation.cue, 0.0)
        self.arousal = max(self.arousal*exp(-dt/8), min(1.0, 4*harm),
                           .5*needs+.3*activation+.2*self.sensitization)
        self.previous = observation
        return {"version":self.version, "observation":asdict(observation),
                "observed_harm":harm, "regulation_pressure":needs,
                "arousal":self.arousal, "sensitization":self.sensitization,
                "current_cue_activation":activation,
                "cue_associations":dict(self.associations),
                "decision_influence":"observer only; no change to action selection",
                "notice":"Hand-specified experimental activations, not felt emotion or calibrated probabilities"}
