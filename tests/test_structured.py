import json
import shutil
import time
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from aace.benchmarks.adaptive_history import episode
from aace.benchmarks.continuation import collect_continuations, load_continuations, public_contexts
from aace.benchmarks.rehearsal import WorkRehearsal, candidates, policy
from aace.decision import ActionAuthority, ComputeBudget, DecisionEngine
from aace.learning.continuation import ContinuationSettings, law_predictions, structural_diagnostics
from aace.learning.resources import digest
from aace.learning.structured import (StructuredHead, canonical_decoder, cue_likelihood_weights,
    load_structured_model, mixture_predictions, predict_structured, structured_forecast, train_structured)


def test_convex_mixture_grid_has_supported_consistent_consequences():
    output = mixture_predictions(np.linspace(0, 1, 501))
    assert all(row["subjects_with_any_contradiction"] == 0 for row in structural_diagnostics(output).values())
    np.testing.assert_allclose(output[0], canonical_decoder()[0], atol=1e-7)
    np.testing.assert_allclose(output[-1], canonical_decoder()[1], atol=1e-7)
    assert np.all(output[:, 5, 0] == 0)  # Careful cannot finish within six seconds.
    assert np.all(output[:, :, 3] == 0)  # These quotas cannot exhaust processing resources.


def test_mixture_is_not_physics_at_average_danger():
    mixed = mixture_predictions(np.array([.5]))
    plugin = law_predictions(np.array([.35]))
    assert abs(mixed[0, 0, 4]-plugin[0, 0, 4]) > .05


@pytest.mark.parametrize("kind,count", [("constant", 1), ("summary_linear", 11), ("summary_mlp", 169), ("gru", 1169)])
def test_initial_heads_share_half_mixture_and_decoder_is_not_learned(kind, count):
    model = StructuredHead(kind)
    sequence = torch.from_numpy(episode(82000)[0][None])
    assert sum(p.numel() for p in model.parameters()) == count
    assert not model.decoder.requires_grad
    with torch.no_grad():
        np.testing.assert_allclose(model(sequence).numpy(), mixture_predictions(np.array([.5])), atol=1e-7)


def test_likelihood_reads_query_matched_public_events_only():
    sequence = episode(82000)[0][None]
    sequence[:, :-1, :2] = [0, 1]; sequence[:, -1, :2] = [1, 0]
    sequence[:, :-1, 2] = .25; sequence[:, :-1, 4] = .75
    assert cue_likelihood_weights(sequence)[0] == .5
    sequence[:, :-1, :2] = [1, 0]
    assert cue_likelihood_weights(sequence)[0] > .99
    sequence[:, -4:-1, 2] = 0; sequence[:, -4:-1, 4] = 1
    assert cue_likelihood_weights(sequence, recent=True)[0] < cue_likelihood_weights(sequence)[0]


def test_new_check_contract_requires_explicit_opt_in(tmp_path):
    result = collect_continuations("check", 8, tmp_path, condition="stable", engineering=True, structured=True)
    directory = Path(result["directory"])
    with pytest.raises(ValueError, match="contract mismatch"): load_continuations(directory, "check")
    data, manifest = load_continuations(directory, "check", structured=True)
    assert manifest["seed_interval"] == [81000, 81032] and data["targets"].shape == (8, 6, 11)
    assert set(data) == {"sequences", "contexts", "targets"}
    with pytest.raises(ValueError): collect_continuations("train", 8, tmp_path, engineering=True, structured=True)


@pytest.fixture(scope="module")
def fitted(tmp_path_factory):
    directory = tmp_path_factory.mktemp("structured-fit")
    training = collect_continuations("train", 24, directory, engineering=True)
    selection = collect_continuations("selection", 12, directory, engineering=True)
    result = train_structured(ContinuationSettings(epochs=2), Path(training["directory"]),
                              Path(selection["directory"]), directory)
    return Path(result["directory"]), result, Path(training["directory"]), Path(selection["directory"])


def test_real_updates_and_restricted_checkpoint_reproduce(fitted):
    checkpoint, result, _, selection = fitted
    models, metadata = load_structured_model(checkpoint)
    assert result["updates_per_model"] == 2 and any(epoch > 0 for epoch in metadata["best_epochs"].values())
    assert metadata["decision_ready"] is False
    data, _ = load_continuations(selection, "selection")
    for model in models.values():
        output = predict_structured(model, data["sequences"], data["contexts"])
        assert output.shape == (12, 6, 11)
        assert all(row["subjects_with_any_contradiction"] == 0 for row in structural_diagnostics(output).values())


def test_known_decoder_tampering_is_rejected_even_if_file_rehashed(fitted, tmp_path):
    checkpoint, _, _, _ = fitted
    copied = tmp_path/"copied"; shutil.copytree(checkpoint, copied)
    weights = torch.load(copied/"weights.pt", weights_only=True)
    weights["constant"]["decoder"][0, 0, 0] = .123
    torch.save(weights, copied/"weights.pt")
    metadata = json.loads((copied/"model.json").read_text()); metadata["weights_sha256"] = digest(copied/"weights.pt")
    (copied/"model.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="decoder/capacity/weights"): load_structured_model(copied)


def test_model_cannot_claim_qualified_authority(fitted, tmp_path):
    checkpoint, _, _, _ = fitted
    copied = tmp_path/"copied"; shutil.copytree(checkpoint, copied)
    metadata = json.loads((copied/"model.json").read_text()); metadata["decision_ready"] = True
    (copied/"model.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="contract mismatch"): load_structured_model(copied)


def test_prediction_ignores_labels_and_rejects_changed_scope(fitted):
    checkpoint, _, _, selection = fitted
    models, _ = load_structured_model(checkpoint); data, _ = load_continuations(selection, "selection")
    before = predict_structured(models["summary_mlp"], data["sequences"], data["contexts"])
    data["targets"][:] = 0
    np.testing.assert_array_equal(before, predict_structured(models["summary_mlp"], data["sequences"], data["contexts"]))
    contexts = data["contexts"].copy(); contexts[0, 0] = .2
    with pytest.raises(ValueError, match="public task scope"): predict_structured(models["summary_mlp"], data["sequences"], contexts)


def test_coherent_forecasts_still_cannot_authorize_action():
    prediction = mixture_predictions(np.array([0.]))[0]
    environment = WorkRehearsal("normal", seed=82000, latent_probability=.05)
    authority = ActionAuthority()
    class Forecast:
        def forecast(self, context, candidate, *, deadline):
            return structured_forecast(prediction, context, candidate)
    decision = DecisionEngine().decide(environment.context(0), candidates()[:2], Forecast(), policy(), authority,
                                      ComputeBudget(max_forecasts=2, action_seconds=1))
    assert authority.commit(decision, environment.apply, clock=time.perf_counter).status == "abstained"
    assert environment.state.progress == 0
    assert all(row["forecast"]["evidence"]["model_version"] == "structured-consequence-mixture-v2" for row in decision.trace["candidates"])


def test_partial_recipe_is_retained_on_budget_failure(fitted, tmp_path):
    _, _, training, selection = fitted
    with pytest.raises(ValueError, match="budget expired"):
        train_structured(ContinuationSettings(max_seconds=1e-6), training, selection, tmp_path)
    partial = next(tmp_path.glob("structured-model-*/partial.json"))
    assert json.loads(partial.read_text())["status"] == "budget_expired"
    assert not (partial.parent/"model.json").exists()


def test_frozen_structured_fit_rejects_engineering_or_changed_recipe(fitted):
    from aace.learning.structured_pilot import frozen_structured_fit
    _, metadata, _, _ = fitted
    frozen_structured_fit(metadata, engineering=True)
    with pytest.raises(ValueError, match="engineering boundary"): frozen_structured_fit(metadata)
    changed = dict(metadata, engineering=False)
    with pytest.raises(ValueError, match="frozen recipe"): frozen_structured_fit(changed)


def test_source_index_binds_data_weights_and_engineering_scope(fitted, tmp_path):
    from aace.learning.continuation import train_continuations
    from aace.learning.structured_pilot import validated_source
    _, _, training, selection = fitted
    raw = train_continuations(ContinuationSettings(epochs=1), training, selection, tmp_path)
    datasets = {}
    for split, path in (("train", training), ("selection", selection)):
        _, manifest = load_continuations(path, split)
        datasets[split] = dict(manifest, directory=str(path))
    source = {"status": "complete", "engineering": True, "fits": [raw], "datasets": datasets}
    path = tmp_path/"index.json"; path.write_text(json.dumps(source))
    _, models, table = validated_source(path, engineering=True)
    assert len(models) == 1 and table.shape == (6, 11)
    with pytest.raises(ValueError, match="completed frozen"): validated_source(path)
    source["fits"][0]["weights_sha256"] = "0"*64; path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="source model changed"): validated_source(path, engineering=True)


def test_mixture_weights_outside_hypothesis_contract_are_refused():
    for weights in (np.array([-.1]), np.array([float("nan")]), np.array([1.1])):
        with pytest.raises(ValueError, match="mixture weights"): mixture_predictions(weights)
