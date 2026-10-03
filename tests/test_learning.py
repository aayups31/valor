import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("stable_baselines3")
from stable_baselines3 import SAC

from aace.envs.rover import RoverEnv
from aace.learning.sac import TrainSettings, evaluate, train, verify_bundle


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    root = tmp_path_factory.mktemp("sac")
    settings = TrainSettings(steps=64, buffer_size=256, batch_size=16,
                             learning_starts=16, checkpoint_freq=32, max_seconds=30)
    result = train(settings, root)
    return result, settings, root


def test_training_updates_and_checkpoint_are_bounded(bundle):
    result, settings, _ = bundle
    assert result["environment_steps"] <= settings.steps
    assert result["gradient_updates"] > 0
    metadata = verify_bundle(Path(result["checkpoint"]))
    assert metadata["device"] == "cpu" and metadata["net_arch"] == [64, 64]
    assert metadata["replay_size"] <= settings.steps


def test_loaded_policy_is_repeatable(bundle):
    result, _, _ = bundle
    env = RoverEnv()
    obs, _ = env.reset(seed=9)
    first = SAC.load(Path(result["checkpoint"])/"policy.zip", device="cpu")
    second = SAC.load(Path(result["checkpoint"])/"policy.zip", device="cpu")
    np.testing.assert_array_equal(first.predict(obs, deterministic=True)[0],
                                  second.predict(obs, deterministic=True)[0])


def test_resume_preserves_update_and_replay_history(bundle, tmp_path):
    result, settings, _ = bundle
    resumed = train(settings, tmp_path, Path(result["checkpoint"]))
    metadata = verify_bundle(Path(resumed["checkpoint"]))
    assert metadata["total_environment_steps"] > result["environment_steps"]
    assert metadata["replay_size"] > settings.steps
    assert resumed["environment_steps"] <= settings.steps


def test_bundle_detects_modified_manifest_hash(bundle, tmp_path):
    result, _, _ = bundle
    import shutil
    destination = tmp_path/"modified"
    shutil.copytree(result["checkpoint"], destination)
    path = destination/"checkpoint.json"
    metadata = json.loads(path.read_text())
    metadata["policy_sha256"] = "wrong"
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_bundle(destination)


def test_validation_is_separate_and_frozen(bundle, tmp_path):
    result, _, _ = bundle
    checkpoint = Path(result["checkpoint"])
    before = verify_bundle(checkpoint)
    report = evaluate(checkpoint, "benign", [10001], tmp_path)
    assert report["episodes"][0]["seed"] == 10001
    assert verify_bundle(checkpoint) == before
    assert "development validation" in report["protocol"]


@pytest.mark.parametrize("kwargs", [{"steps": 0}, {"max_seconds": float("nan")},
                                    {"threads": 8}, {"batch_size": 60000},
                                    {"buffer_size": 100000000}])
def test_bad_training_budgets_are_rejected(kwargs):
    with pytest.raises(ValueError):
        TrainSettings(**kwargs)


def test_wall_clock_cap_stops_before_requested_steps(tmp_path):
    settings = TrainSettings(steps=10000, max_seconds=0.001, buffer_size=256,
                             batch_size=16, learning_starts=16)
    result = train(settings, tmp_path)
    assert result["stop_reason"] == "wall_clock_budget"
    assert result["environment_steps"] < settings.steps
    assert verify_bundle(Path(result["checkpoint"]))["total_environment_steps"] == result["environment_steps"]
