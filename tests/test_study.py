import json
from pathlib import Path
import shutil
import subprocess

import pytest

from aace.demo.study import create_study
from test_demo import server, request


def test_study_records_applied_outcomes_and_observer_boundary():
    result = create_study({"scenario":"hazard","seed":42})
    assert result["completed"] and result["state"]["progress"] == 8
    assert result["initial_state"]["progress"] == 0
    for row in result["decisions"]:
        assert row["commit"]["status"] == "applied"
        assert row["affect_observer"]["after"]["observation"]["integrity"] == row["actual_outcome"]["integrity"]
        assert row["affect_observer"]["after"]["decision_influence"].startswith("observer only")
    assert result["git_revision"] and result["python_source_sha256"]


def test_abandonment_is_not_completion():
    result = create_study({"scenario":"low_reserve","seed":42})
    assert result["abandoned"] and not result["completed"]
    assert len(result["decisions"]) == 1


@pytest.mark.parametrize("payload", [{"seed":True},{"seed":-1},{"scenario":"unknown"},{"seed":2**31}])
def test_invalid_study_request(payload):
    with pytest.raises(ValueError):
        create_study(payload)


def test_http_study_is_local_bounded_and_exports_provenance(server):
    status, _, body = request(server,"/api/study",{"scenario":"degraded","seed":42})
    result = json.loads(body)
    assert status == 201 and 1 <= len(result["decisions"]) <= 32
    assert result["forecast_source"].startswith("declared analytic")
    for path in ("/rover", "/study.js", "/study.css", "/decision-paths.svg"):
        status, _, body = request(server,path)
        assert status == 200 and body


def test_frontend_record_semantics_without_browser():
    if not shutil.which("node"):
        pytest.skip("Node is required for frontend source checks")
    studies = {name:create_study({"scenario":name,"seed":42}) for name in ("hazard","low_reserve")}
    studies["outage"] = create_study({"scenario":"hazard","seed":10028})
    result = subprocess.run(["node",str(Path(__file__).with_name("study_ui.cjs"))],
                            input=json.dumps(studies,allow_nan=False),text=True,capture_output=True,timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
