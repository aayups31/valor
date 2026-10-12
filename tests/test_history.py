import json
from pathlib import Path

import numpy as np
import pytest

from aace.benchmarks.history import collect_history, episode, history_controls, load_history
from aace.learning.resources import digest


def test_repaired_body_and_query_do_not_disclose_next_damage():
    records = [episode(seed) for seed in range(100)]
    for sequence, label, reference, cost in records:
        np.testing.assert_array_equal(sequence[-1,2:], [0,0,1,1])
        assert label in (0,1) and reference in (.05,.65)
        assert cost == 2*int((sequence[:-1,2]/.25).sum())
    # The same current public query can have different latent risk and history.
    group = [r for r in records if r[0][-1,0] == 1]
    assert set(r[2] for r in group) == {.05,.65}
    assert any(r[0][:-1,2].sum() > 0 for r in group)


def test_history_dataset_reproduces_and_keeps_audit_metadata_outside_inputs(tmp_path):
    paths = [Path(collect_history("train",40,tmp_path)["directory"]) for _ in range(2)]
    a, manifest = load_history(paths[0],"train")
    b, _ = load_history(paths[1],"train")
    for name in a:
        np.testing.assert_array_equal(a[name],b[name])
    assert a["sequences"].shape == (40,13,6)
    assert {"labels","episode_seeds","reference_probability"} <= set(manifest["metadata_not_features"])
    with pytest.raises(ValueError,match="split/schema"):
        load_history(paths[0],"check")


@pytest.mark.parametrize("condition", ["extinction","reversal"])
def test_shift_conditions_are_check_only(condition,tmp_path):
    with pytest.raises(ValueError,match="checks only"):
        collect_history("train",10,tmp_path,condition=condition)
    directory = Path(collect_history("check",40,tmp_path,condition=condition)["directory"])
    data, _ = load_history(directory,"check")
    if condition == "extinction":
        assert np.all(data["reference_probability"] == .05)


def test_tampered_future_feature_is_rejected_even_with_updated_hash(tmp_path):
    directory = Path(collect_history("train",10,tmp_path)["directory"])
    data, manifest = load_history(directory,"train")
    data["sequences"][0,-1,2] = .25
    np.savez_compressed(directory/"episodes.npz",**data)
    manifest["dataset_sha256"] = digest(directory/"episodes.npz")
    (directory/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="future outcome"):
        load_history(directory,"train")


def test_simple_controls_use_only_history_and_match_current_body():
    sequence = np.zeros((2,13,6),dtype=np.float32)
    sequence[:,:,0]=1
    sequence[:,:-1,3]=1
    sequence[:,:,4:]=1
    sequence[1,:-1,2]=.25
    sequence[1,:-1,4]=.75
    np.testing.assert_array_equal(sequence[0,-1],sequence[1,-1])
    controls = history_controls(sequence)
    assert controls["cue_counts"][0] < .1 and controls["cue_counts"][1] > .9
    assert controls["public_history_bayes"][0] < .06 and controls["public_history_bayes"][1] > .64


@pytest.mark.parametrize("payload", [{"episodes":True},{"episodes":0},{"split":"final"},{"max_seconds":float("nan")}])
def test_invalid_history_collection_is_rejected(payload,tmp_path):
    values={"split":"train","episodes":10,"output":tmp_path};values.update(payload)
    with pytest.raises(ValueError):
        collect_history(**values)
    assert not list(tmp_path.rglob("manifest.json"))


@pytest.fixture(scope="module")
def history_bundle(tmp_path_factory):
    pytest.importorskip("torch")
    from aace.learning.history import HistoryTrainSettings,train_history
    output = tmp_path_factory.mktemp("history-model")
    train = Path(collect_history("train",600,output)["directory"])
    selection = Path(collect_history("selection",100,output)["directory"])
    check = Path(collect_history("check",100,output)["directory"])
    result = train_history(HistoryTrainSettings(epochs=3,batch_size=64),train,selection,output)
    return Path(result["directory"]),train,selection,check


def test_history_heads_update_roundtrip_and_stream_with_episode_reset(history_bundle):
    import torch
    from aace.learning.history import load_history_model
    checkpoint,train,_,_ = history_bundle
    models,metadata = load_history_model(checkpoint)
    reloaded,_ = load_history_model(checkpoint)
    data,_ = load_history(train,"train")
    x = torch.from_numpy(data["sequences"][:16])
    with torch.no_grad():
        for name,model in models.items():
            torch.testing.assert_close(model(x),reloaded[name](x),rtol=0,atol=0)
        state = None
        for row in x.unbind(dim=1):
            prediction,state = models["gru"].step(row,state)
        torch.testing.assert_close(prediction,models["gru"](x),rtol=1e-5,atol=1e-6)
        reset_prediction,_ = models["gru"].step(x[:,0],None)
        repeated_prediction,_ = models["gru"].step(x[:,0],None)
        torch.testing.assert_close(reset_prediction,repeated_prediction,rtol=0,atol=0)
        # Stateless control cannot respond to history when current inputs match.
        changed = x.clone();changed[:,:-1]=torch.flip(x[:,:-1],dims=[0])
        torch.testing.assert_close(models["stateless"](x),models["stateless"](changed),rtol=0,atol=0)
    assert metadata["updates_per_model"] > 0 and metadata["parameter_counts"]["gru"] == 1169
    assert metadata["parameter_counts"]["history_mlp"] == 1121
    assert metadata["recurrent_state_float32_bytes"] == 64
    assert not metadata["decision_ready"]
    assert any(epoch > 0 for epoch in metadata["best_epochs"].values()),"actual learning beyond the eligible prior"


def test_history_evaluation_keeps_strong_controls_and_ablation(history_bundle,tmp_path):
    from aace.learning.history import evaluate_history
    checkpoint,_,_,check = history_bundle
    report = evaluate_history(checkpoint,check,tmp_path)
    assert {"gru","history_mlp","history_linear","stateless","cue_counts","public_history_bayes","hidden_state_reference","gru_shuffled_history"} <= set(report["metrics"])
    assert report["check_seed_range"] == [12000,12099]
    assert not report["decision_ready"]
    for result in report["metrics"].values():
        assert np.isfinite(result["brier"]) and result["count"] == 100
    assert report["gru_brier_differences"]["cue_counts"]["notice"]
    assert Path(report["episode_scores_file"]).exists()


def test_corrupt_history_model_is_not_loaded(history_bundle,tmp_path):
    import shutil
    from aace.learning.history import load_history_model
    checkpoint,_,_,_ = history_bundle
    broken = tmp_path/"broken"
    shutil.copytree(checkpoint,broken)
    with (broken/"weights.pt").open("ab") as f:
        f.write(b"changed")
    with pytest.raises(ValueError,match="hash mismatch"):
        load_history_model(broken)


def test_budget_expiry_publishes_no_history_checkpoint(history_bundle,tmp_path):
    from aace.learning.history import HistoryTrainSettings,train_history
    _,train,selection,_ = history_bundle
    with pytest.raises(ValueError,match="Budget expired"):
        train_history(HistoryTrainSettings(max_seconds=.001),train,selection,tmp_path)
    assert not list(tmp_path.rglob("model.json"))


@pytest.mark.parametrize("settings", [{"seed":True},{"epochs":0},{"threads":True},{"max_seconds":float("inf")},{"max_memory_mb":-1}])
def test_history_training_settings_are_bounded(settings):
    pytest.importorskip("torch")
    from aace.learning.history import HistoryTrainSettings
    with pytest.raises(ValueError):
        HistoryTrainSettings(**settings)
