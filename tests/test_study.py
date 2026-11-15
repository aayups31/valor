import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import subprocess
from urllib.error import HTTPError

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
    for path in ("/rover", "/study.js", "/study.css", "/studio.css", "/instruments.css", "/decision-paths.svg"):
        status, _, body = request(server,path)
        assert status == 200 and body
    status, headers, body = request(server, "/supervision-cell.webp")
    assert status == 200 and headers["Content-Type"] == "image/webp"
    assert body[:4] == b"RIFF" and body[8:12] == b"WEBP"


def test_recent_studies_are_replayable_and_expire_in_completion_order(server):
    assert json.loads(request(server, "/api/studies")[2]) == {"runs": []}

    example = json.loads(request(server, "/api/studies/example")[2])
    assert example["example"] is True and example["recorded_at"] is None
    assert (example["scenario"], example["seed"]) == ("degraded", 42)
    assert json.loads(request(server, "/api/studies")[2]) == {"runs": []}

    runs = [json.loads(request(server, "/api/study", {"scenario": "low_reserve", "seed": seed})[2])
            for seed in range(13)]
    latest = runs[-1]
    assert latest["example"] is False
    assert datetime.fromisoformat(latest["recorded_at"]).utcoffset() == timedelta(0)
    selected = json.loads(request(server, f"/api/studies/{latest['study_id']}")[2])
    assert selected == latest

    summaries = json.loads(request(server, "/api/studies")[2])["runs"]
    assert [entry["study_id"] for entry in summaries] == [run["study_id"] for run in reversed(runs[1:])]
    assert summaries[0] == {
        "study_id": latest["study_id"], "scenario": "low_reserve", "seed": 12,
        "recorded_at": latest["recorded_at"], "status": "abandoned", "progress": 0,
        "goal": latest["goal"], "decision_count": 1,
    }

    with pytest.raises(HTTPError) as error:
        request(server, f"/api/studies/{runs[0]['study_id']}")
    assert error.value.code == 404
    assert json.loads(request(server, "/api/studies/example")[2]) == example


def test_frontend_record_semantics_without_browser():
    if not shutil.which("node"):
        pytest.skip("Node is required for frontend source checks")
    studies = {name:create_study({"scenario":name,"seed":42}) for name in ("hazard","low_reserve")}
    studies["outage"] = create_study({"scenario":"hazard","seed":10028})
    result = subprocess.run(["node",str(Path(__file__).with_name("study_ui.cjs"))],
                            input=json.dumps(studies,allow_nan=False),text=True,capture_output=True,timeout=10)
    assert result.returncode == 0, result.stdout+result.stderr
