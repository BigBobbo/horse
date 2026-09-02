import numpy as np
import pytest

from furlong.features.builder import FEATURE_COLUMNS
from furlong.features.dataset import Dataset, build_dataset, chronological_splits
from furlong.modeling.blend import BlendParams, blend_probabilities, fit_blend
from furlong.modeling.conditional_logit import ConditionalLogit, race_softmax
from furlong.modeling.evaluate import mcfadden_r2, uniform_log_likelihood
from furlong.modeling.gbm import GbmModel
from furlong.modeling.train import attach_market, train_on_frames


@pytest.fixture(scope="module")
def trained_world(world_settings):
    """Train once per module: dataset, splits and a fitted model."""
    from furlong.db import init_db

    conn = init_db(world_settings.database_path)
    frame = attach_market(conn, build_dataset(conn).frame, prefer="bsp")
    splits = chronological_splits(Dataset(frame=frame))
    trained = train_on_frames(
        frame.loc[splits.train], frame.loc[splits.valid], frame.loc[splits.test], kind="gbm"
    )
    conn.close()
    return frame, splits, trained


def _groups(frame):
    _, idx, counts = np.unique(frame["race_id"].to_numpy(), return_index=True,
                              return_counts=True)
    return counts[np.argsort(idx)]


# -- softmax / conditional logit -------------------------------------------

def test_race_softmax_sums_to_one_per_race():
    scores = np.array([1.0, 2.0, 3.0, 0.5, 0.5])
    groups = np.array([3, 2])
    probs = race_softmax(scores, groups)
    assert probs[:3].sum() == pytest.approx(1.0, abs=1e-12)
    assert probs[3:].sum() == pytest.approx(1.0, abs=1e-12)
    assert probs[3] == pytest.approx(probs[4])  # equal scores -> equal probs


def test_conditional_logit_learns_signal():
    rng = np.random.default_rng(0)
    n_races, field = 400, 8
    groups = np.full(n_races, field)
    X = rng.normal(size=(n_races * field, 2))
    scores = 1.5 * X[:, 0]  # only the first feature matters
    probs = race_softmax(scores, groups)
    y = np.zeros(len(X))
    for r in range(n_races):
        sl = slice(r * field, (r + 1) * field)
        y[sl][rng.choice(field, p=probs[sl])] = 1

    model = ConditionalLogit(l2=0.01).fit(X, y, groups)
    assert model.coef_[0] > 0.5           # signal found
    assert abs(model.coef_[1]) < 0.3      # noise feature suppressed

    fitted = model.predict_proba(X, groups)
    uniform_ll = uniform_log_likelihood(groups)
    fitted_ll = float(np.sum(y * np.log(fitted)))
    assert fitted_ll > uniform_ll         # beats the 1/field baseline


def test_conditional_logit_probabilities_normalised(trained_world):
    frame, splits, _ = trained_world
    test = frame.loc[splits.test]
    groups = _groups(test)
    model = ConditionalLogit().fit(
        frame.loc[splits.train][FEATURE_COLUMNS].to_numpy(float),
        (frame.loc[splits.train]["win_flag"] == 1).to_numpy(float),
        _groups(frame.loc[splits.train]),
    )
    probs = model.predict_proba(test[FEATURE_COLUMNS].to_numpy(float), groups)
    start = 0
    for size in groups:
        assert probs[start:start + size].sum() == pytest.approx(1.0, abs=1e-9)
        start += size


# -- GBM --------------------------------------------------------------------

def test_gbm_beats_uniform_and_is_deterministic(trained_world):
    frame, splits, trained = trained_world
    test = frame.loc[splits.test]
    groups = _groups(test)
    X = test[FEATURE_COLUMNS].to_numpy(float)
    y = (test["win_flag"] == 1).to_numpy(float)

    probs = trained.model.predict_proba(X, groups)
    assert mcfadden_r2(probs, y, groups) > 0.03

    again = trained.model.predict_proba(X, groups)
    np.testing.assert_allclose(probs, again)


def test_gbm_save_load_parity(trained_world, tmp_path):
    frame, splits, trained = trained_world
    test = frame.loc[splits.test]
    X = test[FEATURE_COLUMNS].to_numpy(float)
    path = tmp_path / "gbm.txt"
    trained.model.save(path)
    reloaded = GbmModel.load(path)
    np.testing.assert_allclose(trained.model.raw_scores(X), reloaded.raw_scores(X))


# -- the Benter blend -------------------------------------------------------

def test_blend_finds_planted_edge(trained_world):
    """The model must add information the market lacks (Benter's Delta R2)."""
    _, _, trained = trained_world
    metrics = trained.metrics
    assert metrics.delta_r2 > 0.0005, "planted inefficiency was not found"
    assert metrics.blend_log_loss <= metrics.market_log_loss + 1e-9
    # The model must earn real weight, not merely a non-negative clamp.
    assert metrics.blend_params["alpha"] > 0.02


def test_blend_beats_both_components(trained_world):
    frame, splits, trained = trained_world
    metrics = trained.metrics
    # The blend is never worse than either component alone.
    assert metrics.blend_log_loss <= min(metrics.model_log_loss,
                                         metrics.market_log_loss) + 1e-6


def test_useless_model_collapses_to_market():
    """A model with no information must get ~zero weight in the blend."""
    rng = np.random.default_rng(3)
    n_races, field = 800, 8
    groups = np.full(n_races, field)
    n = n_races * field

    strength = rng.normal(size=n)
    true_probs = race_softmax(strength, groups)
    y = np.zeros(n)
    for r in range(n_races):
        sl = slice(r * field, (r + 1) * field)
        y[sl][rng.choice(field, p=true_probs[sl])] = 1

    market = race_softmax(strength + rng.normal(0, 0.15, n), groups)
    noise_model = race_softmax(rng.normal(size=n), groups)

    params = fit_blend(noise_model, market, y, groups)
    assert params.alpha < 0.1, "a useless model must not earn blend weight"
    assert params.beta > 0.5

    blended = blend_probabilities(noise_model, market, groups, params)
    assert mcfadden_r2(blended, y, groups) == pytest.approx(
        mcfadden_r2(market, y, groups), abs=0.01
    )


def test_blend_probabilities_normalised():
    groups = np.array([4, 3])
    model = np.array([0.4, 0.3, 0.2, 0.1, 0.5, 0.3, 0.2])
    market = np.array([0.3, 0.3, 0.3, 0.1, 0.4, 0.4, 0.2])
    out = blend_probabilities(model, market, groups, BlendParams(0.5, 0.5))
    assert out[:4].sum() == pytest.approx(1.0)
    assert out[4:].sum() == pytest.approx(1.0)


def test_blend_weights_never_negative():
    """Negative weights (fading our own model or the market) are meaningless."""
    rng = np.random.default_rng(9)
    groups = np.full(200, 6)
    n = 200 * 6
    market = race_softmax(rng.normal(size=n), groups)
    # a deliberately anti-correlated "model"
    inverted = race_softmax(-np.log(market), groups)
    y = np.zeros(n)
    for r in range(200):
        sl = slice(r * 6, (r + 1) * 6)
        y[sl][rng.choice(6, p=market[sl])] = 1
    params = fit_blend(inverted, market, y, groups)
    assert params.alpha >= 0.0
    assert params.beta >= 0.0
    # The meaningful claim: an anti-correlated model earns no weight, and the
    # blend falls back on the market.
    assert params.alpha < 0.05
    assert params.beta > 0.5


# -- metrics ---------------------------------------------------------------

def test_metrics_serialise_and_summarise(trained_world):
    _, _, trained = trained_world
    payload = trained.metrics.to_dict()
    assert set(payload) >= {
        "n_races", "n_runners", "log_loss", "mcfadden_r2", "delta_r2",
        "brier", "top_pick_strike_rate", "blend_params", "reliability",
    }
    assert payload["log_loss"]["blend"] > 0
    assert isinstance(payload["reliability"], list) and payload["reliability"]
    assert "Delta R2" in trained.metrics.summary()


def test_reliability_is_broadly_calibrated(trained_world):
    """Higher predicted deciles must win more often than lower ones."""
    _, _, trained = trained_world
    table = trained.metrics.reliability
    lowest, highest = table[0], table[-1]
    assert highest["actual"] > lowest["actual"]
    assert highest["predicted"] > lowest["predicted"]


def test_blend_is_not_fitted_on_the_early_stopping_set():
    """Sharing one validation set inflates alpha: the model looks better there."""
    import pandas as pd

    from furlong.modeling.train import _split_validation

    valid = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "race_id": [1, 2, 3, 4],
    })
    early_stop, blend_fit = _split_validation(valid)
    assert not set(early_stop["date"]) & set(blend_fit["date"])
    assert max(early_stop["date"]) < min(blend_fit["date"])

    # degenerate inputs fall back to using the whole window
    single = pd.DataFrame({"date": ["2024-01-01"], "race_id": [1]})
    a, b = _split_validation(single)
    assert len(a) == len(b) == 1
    empty = pd.DataFrame({"date": [], "race_id": []})
    assert _split_validation(empty)[0].empty


# -- the alpha = 0 gate -----------------------------------------------------
#
# The regression these guard against was found on real racing data, not in a
# unit test: over 27,381 Betfair-priced UK and Irish races the blend fitted
# alpha to exactly zero and beta to 0.906, and the engine advised 10,747
# bets. None of them carried any model information. They existed because
# beta below one flattens the market's own prices, lifting every longshot's
# implied probability past the edge filter.


def _race_world(n_races=600, field=8, market_noise=0.35, model_noise=0.35,
                seed=0):
    """Races with a true strength, a noisy market, and a noisy model.

    Both observers see the truth imperfectly and differently, so the model
    holds information the market does not -- the situation the blend exists
    to exploit. Nothing here is separable: the MLE is interior, as it is on
    real racing.
    """
    rng = np.random.default_rng(seed)
    groups = np.full(n_races, field)
    truth = rng.gamma(2.0, 1.0, size=n_races * field)

    def observed(noise):
        seen = truth * np.exp(rng.normal(0.0, noise, size=truth.shape))
        return np.concatenate([s / s.sum() for s in np.split(seen, n_races)])

    true_probs = np.concatenate([s / s.sum() for s in np.split(truth, n_races)])
    market = observed(market_noise)
    model = observed(model_noise)

    y = np.zeros(n_races * field)
    for i in range(n_races):
        y[i * field + rng.choice(field, p=true_probs[i * field:(i + 1) * field])] = 1.0
    assert y.sum() == n_races, "one winner per race"
    return model, market, y, groups


def test_a_useless_model_fails_the_alpha_test():
    from furlong.modeling.blend import model_adds_information

    _, market, y, groups = _race_world(seed=3)
    rng = np.random.default_rng(11)
    noise = rng.random(len(market))
    useless = np.concatenate([s / s.sum() for s in np.split(noise, len(groups))])

    statistic, p_value = model_adds_information(useless, market, y, groups)
    assert p_value > 0.05, (
        f"pure noise was judged informative (LR {statistic:.2f}, p={p_value:.4f})"
    )


def test_reshaping_the_market_is_not_information():
    """A blend that only flattens the market must not pass the test.

    This is the exact failure found on real data. The "model" here is the
    market raised to a power: a monotone rescaling carrying not one bit the
    market did not already have. Because the null keeps beta free, the
    rescaling is absorbed there and alpha earns nothing -- which is the whole
    reason the null is not simply beta = 1.
    """
    from furlong.modeling.blend import model_adds_information

    _, market, y, groups = _race_world(seed=7)
    reshaped = np.concatenate([
        (s ** 0.85) / (s ** 0.85).sum() for s in np.split(market, len(groups))
    ])
    _, p_value = model_adds_information(reshaped, market, y, groups)
    assert p_value > 0.05, "a rescaling of the market was mistaken for information"


def test_a_genuinely_informative_model_passes():
    """A model that sees the truth as clearly as the market must be heard."""
    from furlong.modeling.blend import model_adds_information

    model, market, y, groups = _race_world(n_races=1500, seed=5)
    statistic, p_value = model_adds_information(model, market, y, groups)
    assert p_value < 0.01, f"real information was missed (LR {statistic:.2f})"


def test_thin_evidence_fails_closed():
    """The same informative model, on too few races, must not be trusted.

    Failing to reject on thin evidence is the point: for a betting system,
    "not shown" has to mean "do not bet".
    """
    from furlong.modeling.blend import model_adds_information

    model, market, y, groups = _race_world(n_races=25, seed=5)
    _, p_value = model_adds_information(model, market, y, groups)
    assert p_value > 0.05


def test_market_only_fit_leaves_alpha_at_zero():
    from furlong.modeling.blend import fit_market_only

    _, market, y, groups = _race_world(seed=1)
    params = fit_market_only(market, y, groups)
    assert params.alpha == 0.0
    assert params.beta > 0.0


def test_fit_never_ships_a_blend_worse_than_the_market():
    """Weights are clamped inside the search, not after it.

    Clamping afterwards moves the answer to a point the optimiser never
    scored. On a separable problem the unconstrained fit runs to
    (alpha 96, beta -96.9) -- a perfect in-sample fit -- and clamping that to
    (96, 0) shipped a blend whose log-loss was four times worse than
    ignoring the model altogether.
    """
    from furlong.modeling.blend import (
        BlendParams, blend_log_likelihood, fit_blend)

    _, market, y, groups = _race_world(n_races=800, seed=5)
    # Separable by construction: the winner's probability is lifted, so the
    # unconstrained likelihood is unbounded along beta = -alpha.
    leaked = market * np.where(y == 1, 1.6, 1.0)
    leaked = np.concatenate([s / s.sum() for s in np.split(leaked, len(groups))])

    params = fit_blend(leaked, market, y, groups)
    assert params.alpha >= 0.0 and params.beta >= 0.0
    fitted = blend_log_likelihood(leaked, market, y, groups, params)
    market_only = blend_log_likelihood(market, market, y, groups,
                                       BlendParams(alpha=0.0, beta=1.0))
    assert fitted >= market_only, (
        f"shipped a blend fitting worse than the market alone "
        f"({fitted:.1f} vs {market_only:.1f})"
    )
