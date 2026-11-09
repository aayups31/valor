import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aace.demo.reserve import reserve_replay


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node.js language checks")
def test_replay_controls_against_real_records():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["node", str(root/"tests/reserve_controls.cjs"),
                             str(root/"src/aace/demo/static/reserve.js")],
                            input=json.dumps({s: reserve_replay(s) for s in ("nominal", "damaged")}),
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
