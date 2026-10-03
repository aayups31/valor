"""Check narration against actual engine records without browser automation."""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from aace.controllers import Proposal
from aace.runtime import Session


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node.js language checks")
def test_plain_language_uses_real_decisions_and_handles_overrides():
    planned = Session("shortcut", "oracle_planner", 42).step()
    direct_session = Session("shortcut", "heuristic_direct", 42)
    direct = direct_session.step()
    braked = direct_session.step(external_stop=True)
    invalid_session = Session("benign", "heuristic_direct", 42)
    invalid_action = (float("nan"), 0.0)
    invalid_session.controller.decide = lambda observation: Proposal(
        "direct", invalid_action, ({"plan": "direct", "action": invalid_action,
                                    "status": "selected", "reason_codes": ["heuristic_rule"],
                                    "forecast": None},))
    invalid = invalid_session.step()
    damage_session = Session("shortcut", "heuristic_direct", 42)
    while True:
        damage = damage_session.step()
        if "damage" in damage["actual_outcome"]["events"]:
            break
    finished = Session("benign", "heuristic_direct", 42)
    while not finished.ended:
        finished.step()
    traces = dict(planned=planned, direct=direct, braked=braked, invalid=invalid,
                  damage=damage, finished=finished.view())
    script = Path(__file__).with_name("ui_evidence.cjs")
    result = subprocess.run(["node", str(script)], input=json.dumps(traces, allow_nan=False),
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
