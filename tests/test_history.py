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
