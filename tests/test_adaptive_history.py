import json
from pathlib import Path

import numpy as np
import pytest

from aace.benchmarks.adaptive_history import collect_adaptive, episode, load_adaptive
from aace.benchmarks.history import load_history
from aace.learning.adaptive_controls import fit_controls,predict_control
from aace.learning.resources import digest


def test_mixed_history_reproduces_with_hidden_schedule_and_new_groups(tmp_path):
    paths = [Path(collect_adaptive("train",100,tmp_path)["directory"]) for _ in range(2)]
    a,m = load_adaptive(paths[0],"train");b,_ = load_adaptive(paths[1],"train")
    for name in a:
        np.testing.assert_array_equal(a[name],b[name])
    assert a["episode_seeds"][0] == 3000 and a["episode_seeds"][-1] == 3099
    assert all(m["regime_counts"][name] > 0 for name in ("stable","extinction","reversal"))
    assert m["regime_counts"]["recurrence"] == 0
    assert "schedules.npz" in m["metadata_not_features"]
    assert not {"conditions","change_at","return_at"} & a.keys()
    np.testing.assert_array_equal(a["sequences"][:,-1,2:],np.tile([0,0,1,1],(100,1)))
    with pytest.raises(ValueError,match="split/schema"):
        load_history(paths[0],"train")


def test_check_conditions_share_cues_and_keep_different_latent_changes():
    records = {c:episode(14005,c) for c in ("stable","extinction","reversal","recurrence")}
    for record in records.values():
        np.testing.assert_array_equal(record[0][:,:2],records["stable"][0][:,:2])
        np.testing.assert_array_equal(record[0][-1,2:],[0,0,1,1])
    assert records["extinction"][2] == .05
    audit = records["recurrence"][4]
    assert 4 <= audit["change_at"] <= 6 and 9 <= audit["return_at"] <= 11


@pytest.mark.parametrize("split,condition", [("train","recurrence"),("train","stable"),("selection","reversal"),("check","mixed")])
def test_fit_and_check_conditions_are_separated(split,condition,tmp_path):
    with pytest.raises(ValueError,match="must be mixed"):
        collect_adaptive(split,10,tmp_path,condition=condition)


def test_changed_schedule_is_rejected_with_and_without_updated_hash(tmp_path):
    path = Path(collect_adaptive("train",20,tmp_path)["directory"])
    with np.load(path/"schedules.npz",allow_pickle=False) as z:
        audit = {name:z[name].copy() for name in z.files}
    audit["conditions"][0]="recurrence"
    np.savez_compressed(path/"schedules.npz",**audit)
    with pytest.raises(ValueError,match="hash mismatch"):
        load_adaptive(path,"train")
    m=json.loads((path/"manifest.json").read_text());m["schedule_sha256"]=digest(path/"schedules.npz")
    (path/"manifest.json").write_text(json.dumps(m))
    with pytest.raises(ValueError,match="types/conditions"):
        load_adaptive(path,"train")


def controlled_history(outcomes):
    x=np.zeros((1,13,6),dtype=np.float32);x[:,:,0]=1
    x[:,:-1,2]=np.asarray(outcomes)*.25;x[:,:-1,3]=1
    x[:,:,4]=1-x[:,:,2];x[:,:-1,5]=.95;x[:,-1,5]=1
    return x


def test_forgetting_and_windows_respond_to_recent_safety_more_than_plain_counts():
    x=controlled_history([1]*8+[0]*4)
    plain=predict_control(x,{"kind":"counts","strength":2},.35)[0]
    recent=predict_control(x,{"kind":"window","strength":2,"window":4},.35)[0]
    forgetting=predict_control(x,{"kind":"forgetting","strength":2,"decay":.5},.35)[0]
    assert recent < forgetting < plain
    reversed_x=controlled_history([0]*8+[1]*4)
    detector=predict_control(reversed_x,{"kind":"cusum","strength":2,"threshold":.75},.35)[0]
    plain=predict_control(reversed_x,{"kind":"counts","strength":2},.35)[0]
    assert detector > plain


def test_markov_reference_increases_danger_after_observed_harm():
    safe=controlled_history([0]*12);hurt=controlled_history([1]*12)
    spec={"kind":"markov_bayes","hazard":.05}
    low=predict_control(safe,spec,.35)[0];high=predict_control(hurt,spec,.35)[0]
    assert .05 <= low < high <= .65


def test_controls_are_selected_on_selection_only_and_record_opportunities(tmp_path):
    training,_=load_adaptive(Path(collect_adaptive("train",60,tmp_path)["directory"]),"train")
    selection,_=load_adaptive(Path(collect_adaptive("selection",60,tmp_path)["directory"]),"selection")
    result=fit_controls(training["labels"],selection["sequences"],selection["labels"])
    assert result["selection_opportunities"] == {"cue_counts":3,"forgetting_counts":12,"window_counts":12,"change_detector":3,"markov_bayes_reference":4}
    for family,trials in result["selection_trials"].items():
        best=min(trials,key=lambda t:t["selection_log_loss"])
        assert result["settings"][family] == best["setting"]
        probability=predict_control(selection["sequences"],result["settings"][family],result["prior"])
        assert np.isfinite(probability).all() and np.all((probability>=0)&(probability<=1))


@pytest.fixture(scope="module")
def adaptive_bundle(tmp_path_factory):
    pytest.importorskip("torch")
    from aace.learning.history import HistoryTrainSettings,train_history
    output=tmp_path_factory.mktemp("adaptive-model")
    train=Path(collect_adaptive("train",600,output)["directory"])
    selection=Path(collect_adaptive("selection",100,output)["directory"])
    check=Path(collect_adaptive("check",100,output,condition="recurrence")["directory"])
    result=train_history(HistoryTrainSettings(epochs=3,batch_size=64),train,selection,output,adaptive=True)
    return Path(result["directory"]),train,selection,check


def test_summary_features_use_matched_query_cue_and_only_observed_history():
    torch=pytest.importorskip("torch")
    from aace.learning.history import summary_features
    x=torch.from_numpy(controlled_history([1]*8+[0]*4))
    values=summary_features(x)
    assert values.shape==(1,10)
    assert values[0,0]==1 and values[0,2]==1
    assert values[0,1] > values[0,3]
    torch.testing.assert_close(values[0,-2:],torch.ones(2),rtol=0,atol=0)
    y=x.clone();y[:,-1,:2]=torch.tensor([0.,1.])
    other=summary_features(y)
    assert other[0,0]==0 and other[0,1]==.5


def test_adaptive_heads_reload_and_keep_summary_control_and_streaming(adaptive_bundle):
    import torch
    from aace.learning.history import load_history_model
    checkpoint,train,_,_=adaptive_bundle
    models,metadata=load_history_model(checkpoint)
    second,_=load_history_model(checkpoint)
    data,_=load_adaptive(train,"train");x=torch.from_numpy(data["sequences"][:10])
    assert metadata["parameter_counts"]["summary_mlp"]==169
    assert metadata["parameter_counts"]["gru"]==1169
    assert metadata["dataset_schema"]=="adaptive-repaired-body-history-v2"
    assert metadata["adaptive_controls"]["selection_opportunities"]["window_counts"]==12
    with torch.no_grad():
        for name,model in models.items():
            torch.testing.assert_close(model(x),second[name](x),rtol=0,atol=0)
        state=None
        for row in x.unbind(dim=1):
            prediction,state=models["gru"].step(row,state)
        torch.testing.assert_close(prediction,models["gru"](x),rtol=1e-5,atol=1e-6)
    assert not metadata["decision_ready"]


def test_v2_evaluation_uses_frozen_controls_and_new_episode_group(adaptive_bundle,tmp_path):
    from aace.learning.history import evaluate_history
    checkpoint,_,_,check=adaptive_bundle
    report=evaluate_history(checkpoint,check,tmp_path)
    assert report["check_seed_range"]==[14000,14099]
    assert report["condition"]=="recurrence"
    assert {"summary_mlp","summary_mlp_shuffled_history","forgetting_counts","window_counts","change_detector","markov_bayes_reference"} <= report["metrics"].keys()
    assert not report["decision_ready"]
    assert report["control_selection"]["notice"].startswith("Selection labels only")


def test_v1_and_v2_checkpoints_cannot_silently_mix_tasks(adaptive_bundle,tmp_path):
    from aace.benchmarks.history import collect_history
    from aace.learning.history import evaluate_history
    checkpoint,_,_,_=adaptive_bundle
    old=Path(collect_history("check",10,tmp_path)["directory"])
    with pytest.raises(ValueError,match="split/schema"):
        evaluate_history(checkpoint,old,tmp_path)


def test_adaptive_expired_budget_publishes_no_checkpoint(adaptive_bundle,tmp_path):
    from aace.learning.history import HistoryTrainSettings,train_history
    _,train,selection,_=adaptive_bundle
    with pytest.raises(ValueError,match="Budget expired"):
        train_history(HistoryTrainSettings(max_seconds=.001),train,selection,tmp_path,adaptive=True)
    assert not list(tmp_path.rglob("model.json"))


def test_unrecorded_control_tuning_is_rejected(adaptive_bundle,tmp_path):
    import shutil
    from aace.learning.history import load_history_model
    checkpoint,_,_,_=adaptive_bundle
    copy=tmp_path/"changed";shutil.copytree(checkpoint,copy)
    m=json.loads((copy/"model.json").read_text())
    m["adaptive_controls"]["settings"]["change_detector"]["threshold"]=999
    (copy/"model.json").write_text(json.dumps(m))
    with pytest.raises(ValueError,match="selected by recorded"):
        load_history_model(copy)
