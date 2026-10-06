import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("torch")

from aace.learning.data import collect, load_features
from aace.learning.world import WorldTrainSettings, advance_vector, constant_velocity_delta, evaluate_world, load_world, train_world


@pytest.fixture(scope="module")
def world_bundle(tmp_path_factory):
    directory = tmp_path_factory.mktemp("world")
    training = Path(collect("train", 700, directory)["directory"])
    validation = Path(collect("validation", 400, directory)["directory"])
    result = train_world(WorldTrainSettings(members=2, epochs=3, batch_size=64), training, validation, directory)
    return result, training, validation


def test_ensemble_roundtrip_has_real_updates_and_decomposed_uncertainty(world_bundle):
    result, training, _ = world_bundle
    assert result["gradient_updates"] > 0 and 1 <= result["best_epoch"] <= 3
    first, second = load_world(Path(result["directory"])), load_world(Path(result["directory"]))
    inputs, _, _ = load_features(training, expected_split="train")
    a, b = first.predict(inputs[:20]), second.predict(inputs[:20])
    np.testing.assert_array_equal(a["mean"], b["mean"])
    np.testing.assert_allclose(a["variance"], a["aleatoric_variance"]+a["disagreement_variance"])
    assert np.all(a["variance"] > 0) and np.isfinite(a["mean"]).all()
    assert a["member_means"].shape == (2, 20, 6)
    assert first.metadata["normalization_source"] == "training data only"
    np.testing.assert_allclose(first.normalization["x_mean"], inputs.mean(axis=0))
    with pytest.raises(ValueError, match="public observation"):
        first.predict(np.zeros((2, 38), dtype=np.float32))
    with pytest.raises(ValueError, match="outside the public"):
        first.predict(np.full((2, 37), 2.0, dtype=np.float32))


def test_world_validation_retains_simple_controls_and_correlated_rollout_notice(world_bundle, tmp_path):
    result, _, validation = world_bundle
    report = evaluate_world(Path(result["directory"]), validation, tmp_path, rollout_starts=8)
    assert report["one_step"]["all"]["count"] == 400
    assert "no_change" in report["simple_baselines"]
    assert "constant_velocity" in report["simple_baselines"]
    assert report["open_loop_recorded_action_rollouts"]["20"]["count"] == 8
    assert report["open_loop_recorded_action_rollouts"]["80"]["count"] == 8
    assert report["evaluation_dataset_used_for_checkpoint_selection"]
    assert not report["planner_ready"] and report["remaining_gates"]
    assert "correlated" in report["rollout_notice"]


def test_separate_development_data_is_labeled_separately_from_selection(world_bundle, tmp_path):
    result, _, _ = world_bundle
    validation = Path(collect("validation", 400, tmp_path, seed_offset=500)["directory"])
    report = evaluate_world(Path(result["directory"]), validation, tmp_path, rollout_starts=2)
    assert not report["evaluation_dataset_used_for_checkpoint_selection"]
    assert "no locked final-test claim" in report["protocol"]


def test_constant_velocity_uses_public_velocity_and_clips_position():
    observations = np.zeros((2, 35), dtype=np.float32)
    observations[:, :4] = [[.5, .5, .5, -.25], [.999, .001, 1, -1]]
    delta = constant_velocity_delta(observations)
    np.testing.assert_allclose(delta[:, :2], [[.01, -.005], [.001, -.001]], atol=1e-7)
    np.testing.assert_array_equal(delta[:, 2:], 0)


def test_world_checkpoint_rejects_changed_weights(world_bundle, tmp_path):
    import shutil
    result, _, _ = world_bundle
    destination = tmp_path/"broken"
    shutil.copytree(result["directory"], destination)
    with (destination/"weights.pt").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_world(destination)


def test_validation_cannot_be_used_as_world_training(world_bundle, tmp_path):
    _, _, validation = world_bundle
    with pytest.raises(ValueError, match="split/schema"):
        train_world(WorldTrainSettings(epochs=1), validation, validation, tmp_path)


def test_tiny_time_budget_does_not_publish_an_unvalidated_model(world_bundle, tmp_path):
    _, training, validation = world_bundle
    with pytest.raises(ValueError, match="Budget expired"):
        train_world(WorldTrainSettings(max_seconds=.001), training, validation, tmp_path)
    assert not list(tmp_path.rglob("model.json"))


def test_decoder_carries_goal_switch_resources_and_clock_without_exact_dynamics():
    observation = np.zeros(35, dtype=np.float32)
    observation[:6] = [.79, .5, .1, 0, .9, .7]
    observation[10:12] = [.1, .5]
    observation[12] = .5
    nxt = advance_vector(observation, np.array([.03, 0, 0, 0, .1, .1]), np.array([.85, .5]))
    assert nxt[6] == 1
    np.testing.assert_allclose(nxt[8:10], observation[10:12]-nxt[:2])
    np.testing.assert_array_equal(nxt[4:6], observation[4:6])
    assert nxt[7] > observation[7] and nxt[12] < observation[12]


@pytest.mark.parametrize("kwargs", [{"epochs": 0}, {"members": 6}, {"max_seconds": float("nan")}, {"hidden": 999}])
def test_bad_model_budgets_are_rejected(kwargs):
    with pytest.raises(ValueError):
        WorldTrainSettings(**kwargs)
