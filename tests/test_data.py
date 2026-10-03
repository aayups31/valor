import json

import numpy as np
import pytest

from aace.learning.data import collect, load_features, split_manifest


def test_split_seed_groups_are_disjoint_and_test_is_reserved():
    manifest = split_manifest()
    assert manifest["train"]["seed_stop"] <= manifest["validation"]["seed_start"]
    assert manifest["validation"]["seed_stop"] <= manifest["reserved_test"]["seed_start"]
    assert not manifest["reserved_test"]["collection_allowed"]


def test_collection_is_reproducible_and_metadata_does_not_enter_features(tmp_path):
    from pathlib import Path
    a = collect("train", 300, tmp_path)
    b = collect("train", 300, tmp_path)
    x, y, metadata = load_features(Path(a["directory"]), expected_split="train")
    second_x, second_y, _ = load_features(Path(b["directory"]), expected_split="train")
    np.testing.assert_array_equal(x, second_x)
    np.testing.assert_array_equal(y, second_y)
    assert x.shape == (300, 37) and y.shape == (300, 6)
    assert metadata["features"] == ["observations", "actions"]
    assert np.all(np.abs(x[:, -2:]) <= 1)
    assert np.all(y[:, 5] <= 0)  # The source environment never heals health.


def test_validation_cannot_be_loaded_as_training_data(tmp_path):
    from pathlib import Path
    result = collect("validation", 20, tmp_path)
    with pytest.raises(ValueError, match="split/schema"):
        load_features(Path(result["directory"]), expected_split="train")


def test_reserved_test_collection_is_blocked(tmp_path):
    with pytest.raises(ValueError, match="Only development"):
        collect("reserved_test", 20, tmp_path)


def test_changed_dataset_is_rejected(tmp_path):
    from pathlib import Path
    result = collect("train", 10, tmp_path)
    source = Path(result["dataset_file"])
    source.write_bytes(source.read_bytes()+b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_features(source.parent, expected_split="train")


def test_collection_contains_dangerous_and_recovery_evidence(tmp_path):
    from pathlib import Path
    result = collect("train", 4000, tmp_path)
    manifest = json.loads((Path(result["directory"])/"manifest.json").read_text())
    assert manifest["damage_transitions"] > 0 and manifest["catastrophic_transitions"] > 0
    assert any(e["scenario"] == "shortcut" and e["policy"].startswith("direct") for e in manifest["episodes"])
    assert any(e["scenario"] == "shortcut" and e["policy"].startswith("detour") for e in manifest["episodes"])
