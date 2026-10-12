import itertools
import json
import time
from pathlib import Path

import numpy as np
import pytest

from aace.benchmarks.continuation import (CELLS, SCHEMA, collect_continuations, exact_consequences,
    load_continuations, outcome_vector, public_contexts, validate_public_sequences)
from aace.benchmarks.adaptive_history import episode
from aace.benchmarks.rehearsal import SCENARIOS, WorkRehearsal, candidates, operation, policy
from aace.decision import ActionAuthority, ActionIntent, ComputeBudget, DecisionEngine


@pytest.mark.parametrize("scene", list(SCENARIOS))
@pytest.mark.parametrize("action", ["fast", "careful"])
def test_exact_reference_matches_exhaustive_actual_paths(scene, action):
    probability = .65
    count, _, _, _, outage, harm, _ = operation(action, probability)
    chances = [outage, (1-outage)*harm, (1-outage)*(1-harm)]
    actual = np.zeros(11)
    for events in itertools.product(range(3), repeat=count):
        weight = float(np.prod([chances[e] for e in events]))
        env = WorkRehearsal(scene, seed=73000, latent_probability=probability)
        env._outage_draws[:] = 1; env._harm_draws[:] = 1
        for i, event in enumerate(events):
            if event == 0: env._outage_draws[i] = 0
            elif event == 1: env._harm_draws[i] = 0
        env.apply(ActionIntent(action))
        actual += weight*outcome_vector(env.state, SCENARIOS[scene][0])
    np.testing.assert_allclose(exact_consequences(scene, action, probability), actual, atol=1e-6)


def test_reference_counts_deadline_before_next_event_and_keeps_harm():
    fast = np.array(exact_consequences("normal", "fast", 0.))
    assert fast[0] == 1 and fast[4] == 0
    assert fast[5] == 1 and fast[8] == .5
    careful = np.array(exact_consequences("time_pressure", "careful", .65))
    assert careful[0] == 0
    assert careful[1] == pytest.approx(1-(1-.005*.65)**3, abs=1e-6)
    assert careful[2] == pytest.approx(1-careful[1], abs=1e-6)
    assert careful[4] > 0 and careful[6] > 0 and careful[7] == 0


def test_data_public_view_excludes_latent_future_and_ids(tmp_path):
    manifest = collect_continuations("train", 12, tmp_path, engineering=True)
    data, m = load_continuations(Path(manifest["directory"]), "train")
    assert set(data) == {"sequences", "contexts", "targets"}
    assert data["targets"].shape == (12, 6, 11)
    assert m["seed_interval"] == [70000, 70064] and m["schema"] == SCHEMA
    np.testing.assert_array_equal(data["contexts"], public_contexts())
    with np.load(Path(manifest["directory"])/"audit.npz") as audit:
        assert set(audit.files) == {"episode_seeds", "latent_probability", "conditions"}
    for n in range(12):
        sequence = episode(70000+n)[0]
        np.testing.assert_array_equal(data["sequences"][n], sequence)


def test_hash_and_repaired_query_checks_reject_changed_data(tmp_path):
    manifest = collect_continuations("train", 8, tmp_path, engineering=True)
    directory = Path(manifest["directory"])
    with (directory/"audit.npz").open("ab") as stream: stream.write(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"): load_continuations(directory, "train")
    sequence = episode(73000)[0][None]
    sequence[:, -1, 2] = .25
    with pytest.raises(ValueError, match="repaired query"): validate_public_sequences(sequence)


def test_invalid_split_and_regime_do_not_collect(tmp_path):
    for split, condition, subjects in (("train", "recurrence", 8), ("check", "mixed", 8), ("train", "mixed", 3001)):
        with pytest.raises(ValueError): collect_continuations(split, subjects, tmp_path, condition=condition)
    with pytest.raises(ValueError): exact_consequences("normal", "preserve", .5)
    with pytest.raises(ValueError): exact_consequences("normal", "fast", float("nan"))


@pytest.fixture(scope="module")
def fitted(tmp_path_factory):
    pytest.importorskip("torch")
    from aace.learning.continuation import ContinuationSettings, train_continuations
    directory = tmp_path_factory.mktemp("continuation-fit")
    train = collect_continuations("train", 24, directory, engineering=True)
    selection = collect_continuations("selection", 12, directory, engineering=True)
    result = train_continuations(ContinuationSettings(epochs=2), Path(train["directory"]), Path(selection["directory"]), directory)
    return Path(result["directory"]), result, Path(selection["directory"])


def test_real_updates_restricted_checkpoint_and_control_reproduction(fitted):
    from aace.learning.continuation import load_continuation_model, predict_continuations
    checkpoint, metadata, selection = fitted
    models, table, loaded = load_continuation_model(checkpoint)
    assert metadata["updates_per_model"] == 2 and loaded["decision_ready"] is False
    assert any(epoch > 0 for epoch in loaded["best_epochs"].values())
    assert set(models) == {"gru", "summary_mlp", "summary_linear"}
    data, _ = load_continuations(selection, "selection")
    for model in models.values():
        prediction = predict_continuations(model, data["sequences"], data["contexts"])
        assert prediction.shape == (12, 6, 11)
        np.testing.assert_allclose(prediction[:, :, :4].sum(axis=2), 1, atol=1e-6)
    assert table.shape == (6, 11)


def test_targets_are_not_prediction_inputs_and_context_action_matters(fitted):
    from aace.learning.continuation import predict_continuations, load_continuation_model
    checkpoint, _, selection = fitted
    models, _, _ = load_continuation_model(checkpoint)
    data, _ = load_continuations(selection, "selection")
    before = predict_continuations(models["summary_mlp"], data["sequences"], data["contexts"])
    data["targets"][:] = 0
    after = predict_continuations(models["summary_mlp"], data["sequences"], data["contexts"])
    np.testing.assert_array_equal(before, after)
    assert not np.array_equal(before[:, 0], before[:, 5])
    contexts = data["contexts"].copy(); contexts[0, 0] = .1
    with pytest.raises(ValueError, match="public scope"):
        predict_continuations(models["summary_mlp"], data["sequences"], contexts)


def test_future_checkpoint_cannot_claim_authority(fitted, tmp_path):
    import shutil
    from aace.learning.continuation import load_continuation_model
    checkpoint, _, _ = fitted
    copied = tmp_path/"checkpoint"; shutil.copytree(checkpoint, copied)
    metadata = json.loads((copied/"model.json").read_text())
    metadata["decision_ready"] = True
    (copied/"model.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="contract mismatch"): load_continuation_model(copied)
    metadata["decision_ready"] = False; (copied/"model.json").write_text(json.dumps(metadata))
    with (copied/"weights.pt").open("ab") as stream: stream.write(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"): load_continuation_model(copied)


def test_experimental_forecast_cannot_authorize_even_perfect_reference():
    pytest.importorskip("torch")
    from aace.learning.continuation import experimental_forecast, law_predictions
    env = WorkRehearsal("normal", seed=73000, latent_probability=.05)
    authority = ActionAuthority(); context = env.context(0)
    prediction = law_predictions(np.array([.05]))[0]
    class Forecast:
        def forecast(self, ctx, candidate, *, deadline):
            return experimental_forecast(prediction, ctx, candidate)
    decision = DecisionEngine().decide(context, candidates()[:2], Forecast(), policy(), authority,
                                      ComputeBudget(max_forecasts=2, action_seconds=1))
    assert authority.commit(decision, env.apply, clock=time.perf_counter).status == "abstained"
    assert env.state.status == "running" and env.state.progress == 0
    assert all("unqualified_forecast" in row["reason_codes"] for row in decision.trace["candidates"])


def test_reliability_bins_preserve_boundaries_and_are_not_individual_bounds():
    pytest.importorskip("torch")
    from aace.learning.continuation import reliability_bins, wilson_interval
    probability = np.array([0, .01, .025, .05, .1, .25, .5, .75, 1])
    rows = reliability_bins(probability, np.array([0]*8+[1]))
    assert sum(row["subjects"] for row in rows) == 9
    assert rows[-1]["subjects"] == 2 and rows[-1]["events"] == 1
    assert all(not row["sufficient_descriptive_support"] for row in rows)
    assert wilson_interval(0, 500)[1] > 0
    with pytest.raises(ValueError): wilson_interval(1, 0)


def test_preview_separates_predictions_and_has_no_permission_or_bounds():
    pytest.importorskip("torch")
    from aace.learning.continuation import branch_preview, law_predictions
    prediction = law_predictions(np.array([.65]))[0]
    preview = branch_preview(prediction, scenario="normal", model_reference="reference-test")
    assert preview["action_applied"] is False and len(preview["branches"]) == 2
    assert all(b["failure_upper_bound"] is None and not b["decision_ready"] for b in preview["branches"])
    assert all(b["structural_consistency"]["status"] == "no_contradiction_detected" for b in preview["branches"])
    assert "observed" not in preview and "latent_probability" not in preview
    assert preview["branches"][0]["expected_quantities"]["harm_received"] > 0


def test_frozen_fit_rejects_changed_recipe(fitted):
    from aace.learning.continuation_pilot import frozen_fit
    _, metadata, _ = fitted
    frozen_fit(metadata, engineering=True)
    with pytest.raises(ValueError, match="engineering boundary"): frozen_fit(metadata)
    changed = dict(metadata, engineering=False)
    with pytest.raises(ValueError, match="frozen recipe"): frozen_fit(changed)


def test_budget_expiration_retains_partial_and_does_not_publish_model(fitted, tmp_path):
    from aace.learning.continuation import ContinuationSettings, train_continuations
    checkpoint, _, selection = fitted
    training = next(checkpoint.parent.glob("continuation-train-*/manifest.json")).parent
    with pytest.raises(ValueError, match="budget expired"):
        train_continuations(ContinuationSettings(max_seconds=1e-6), training, selection, tmp_path)
    partial = next(tmp_path.glob("continuation-model-*/partial.json"))
    assert json.loads(partial.read_text())["status"] == "budget_expired"
    assert (partial.parent/"partial-selected-weights.pt").exists()
    assert not (partial.parent/"model.json").exists()


def test_invalid_learning_resources_are_rejected():
    pytest.importorskip("torch")
    from aace.learning.continuation import ContinuationSettings
    for changed in ({"threads": True}, {"max_seconds": float("nan")}, {"batch_size": 1}):
        with pytest.raises(ValueError): ContinuationSettings(**changed)


@pytest.mark.parametrize("probability", [.05, .65])
def test_known_law_expectations_pass_public_structural_invariants(probability):
    pytest.importorskip("torch")
    from aace.learning.continuation import law_predictions, structural_diagnostics
    rows = structural_diagnostics(law_predictions(np.array([probability])))
    assert all(r["subjects_with_any_contradiction"] == 0 for r in rows.values())


def test_structural_audit_flags_contradictions_without_rewriting_predictions():
    pytest.importorskip("torch")
    from aace.learning.continuation import law_predictions, structural_diagnostics
    prediction = law_predictions(np.array([.05]))
    prediction[0, 0, 9] = 0  # Zero elapsed time despite probable completion.
    prediction[0, 0, 10] = 0  # Zero integrity despite probable completion.
    before = prediction.copy()
    rows = structural_diagnostics(prediction)
    assert rows["normal/fast"]["counts"]["elapsed_below_distribution_minimum"] == 1
    assert rows["normal/fast"]["counts"]["integrity_below_completed_mass"] == 1
    np.testing.assert_array_equal(prediction, before)
    from aace.learning.continuation import branch_preview
    preview = branch_preview(prediction[0], scenario="normal", model_reference="bad-test")
    assert preview["branches"][0]["structural_consistency"]["status"] == "contradiction_detected"
