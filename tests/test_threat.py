import json
from pathlib import Path

import numpy as np
import pytest

from aace.benchmarks.threat_data import collect_threat
from aace.learning.resources import digest
from aace.learning.threat_data import load_threat


def test_observed_labels_are_reproducible_and_metadata_is_not_a_feature(tmp_path):
    first, second = [Path(collect_threat("train",100,tmp_path)["directory"]) for _ in range(2)]
    a, metadata = load_threat(first,"train")
    b, _ = load_threat(second,"train")
    np.testing.assert_array_equal(a["features"],b["features"])
    np.testing.assert_array_equal(a["labels"],b["labels"])
    assert a["features"].shape == (100,10)
    assert {"oracle_probability","episode_seeds","outcomes"} <= set(metadata["metadata_not_features"])
    assert np.all(a["labels"] == (a["outcomes"] == "irreversible_failure"))
    with pytest.raises(ValueError,match="split/schema"):
        load_threat(first,"check")


def test_censored_outcome_cannot_be_silently_counted_as_safe(tmp_path):
    directory = Path(collect_threat("train",50,tmp_path)["directory"])
    source = directory/"outcomes.npz"
    with np.load(source,allow_pickle=False) as archive:
        data = {name:archive[name].copy() for name in archive.files}
    data["outcomes"] = data["outcomes"].astype("U40")
    data["outcomes"][0] = "running_unknown"
    np.savez_compressed(source,**data)
    manifest = json.loads((directory/"manifest.json").read_text())
    manifest["dataset_sha256"] = digest(source)
    (directory/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="Unknown/censored"):
        load_threat(directory,"train")


@pytest.fixture(scope="module")
def threat_bundle(tmp_path_factory):
    pytest.importorskip("torch")
    from aace.learning.threat import ThreatTrainSettings,train_threat
    output = tmp_path_factory.mktemp("threat")
    train = Path(collect_threat("train",600,output)["directory"])
    selection = Path(collect_threat("selection",200,output)["directory"])
    check = Path(collect_threat("check",200,output)["directory"])
    result = train_threat(ThreatTrainSettings(epochs=3,batch_size=64),train,selection,output)
    return Path(result["directory"]),train,selection,check


def test_threat_heads_train_roundtrip_and_keep_linear_control_matched(threat_bundle):
    import torch
    from aace.learning.threat import load_threat_model
    checkpoint,training,_,_ = threat_bundle
    a,metadata = load_threat_model(checkpoint)
    b,_ = load_threat_model(checkpoint)
    inputs,_ = load_threat(training,"train")
    x = torch.from_numpy(inputs["features"][:20])
    for name in a:
        np.testing.assert_array_equal(torch.sigmoid(a[name](x)).detach().numpy(),torch.sigmoid(b[name](x)).detach().numpy())
    assert metadata["updates_per_model"] > 0 and metadata["parameter_counts"]["linear"] < metadata["parameter_counts"]["neural"]
    assert "training-prevalence" in metadata["initialization"]
    assert not metadata["decision_ready"] and metadata["evidence_kind"] == "experimental"


def test_separate_threat_check_retains_proper_scores_and_oracle_reference(threat_bundle,tmp_path):
    from aace.learning.threat import evaluate_threat
    checkpoint,_,_,check = threat_bundle
    report = evaluate_threat(checkpoint,check,tmp_path)
    assert set(report["metrics"]) == {"neural","linear","constant_prevalence","analytic_oracle"}
    assert report["check_seed_range"][0] == 12000
    assert not report["decision_ready"] and report["remaining_gates"]
    assert all(np.isfinite(result["brier"]) for result in report["metrics"].values())


def test_changed_threat_checkpoint_is_rejected(threat_bundle,tmp_path):
    import shutil
    from aace.learning.threat import load_threat_model
    checkpoint,_,_,_ = threat_bundle
    broken = tmp_path/"broken"
    shutil.copytree(checkpoint,broken)
    with (broken/"weights.pt").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError,match="hash mismatch"):
        load_threat_model(broken)


def test_expired_threat_training_budget_does_not_publish_a_model(threat_bundle,tmp_path):
    from aace.learning.threat import ThreatTrainSettings,train_threat
    _,training,selection,_ = threat_bundle
    with pytest.raises(ValueError,match="Budget expired"):
        train_threat(ThreatTrainSettings(max_seconds=.001),training,selection,tmp_path)
    assert not list(tmp_path.rglob("model.json"))
