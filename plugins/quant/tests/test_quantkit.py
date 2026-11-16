"""Tests for lib/quantkit.py. Run: `uv run --no-project --with numpy python plugins/quant/tests/test_quantkit.py`."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from quantkit import (bet_returns, bootstrap_ci, brier, calibration_table, devig, ev,  # noqa: E402
                      fair_odds, fit_team_strengths, kelly, log_loss, markets, overround,
                      poisson_pmf, rps, score_matrix)


def close(a, b, tol=1e-6):
    assert abs(a - b) < tol, f"{a} != {b}"


def test_poisson():
    p = poisson_pmf(1.5, 20)
    close(p.sum(), 1, 1e-9)
    close(p[2], np.exp(-1.5) * 1.5 ** 2 / 2)


def test_score_matrix_and_markets():
    m = score_matrix(1.6, 1.1)
    close(m.sum(), 1)
    mk = markets(m)
    close(mk["home"] + mk["draw"] + mk["away"], 1)
    close(mk["exp_home_goals"], 1.6, 1e-4)
    close(mk["exp_away_goals"], 1.1, 1e-4)
    close(mk["correct_score"]["0-0"], np.exp(-2.7), 1e-4)  # independent Poisson: e^-(lh+la)
    close(mk["btts_yes"], (1 - np.exp(-1.6)) * (1 - np.exp(-1.1)), 1e-4)
    close(mk["over_2.5"] + mk["under_2.5"], 1)


def test_dixon_coles_moves_low_scores():
    base, dc = score_matrix(1.4, 1.2), score_matrix(1.4, 1.2, rho=-0.1)
    assert dc[0, 0] > base[0, 0] and dc[1, 1] > base[1, 1]
    assert dc[1, 0] < base[1, 0] and dc[0, 1] < base[0, 1]
    close(dc.sum(), 1)


def test_devig():
    odds = [2.10, 3.40, 3.60]
    close(overround(odds), 1 / 2.1 + 1 / 3.4 + 1 / 3.6 - 1)
    for method in ("proportional", "power", "shin"):
        p = devig(odds, method)
        close(p.sum(), 1, 1e-9)
        assert np.all(np.diff(p) <= 0), method  # favourite stays favourite
    # power and shin load more margin on the longshot than proportional does
    assert devig(odds, "power")[2] < devig(odds, "proportional")[2]
    assert devig(odds, "shin")[2] < devig(odds, "proportional")[2]
    # a fair book is unchanged
    fair = fair_odds([0.5, 0.3, 0.2])
    for method in ("proportional", "power", "shin"):
        assert np.allclose(devig(fair, method), [0.5, 0.3, 0.2], atol=1e-6), method


def test_ev_kelly():
    close(float(ev(0.5, 2.2)), 0.1)
    close(float(kelly(0.5, 2.2)), 0.1 / 1.2)
    close(float(kelly(0.4, 2.2)), 0.0)


def test_metrics():
    probs = np.array([[0.5, 0.3, 0.2], [0.2, 0.3, 0.5]])
    out = np.array([0, 2])
    close(log_loss(probs, out), -np.log(0.5))
    close(brier(probs, out), 0.25 + 0.09 + 0.04)
    perfect = np.array([[1.0, 0, 0], [0, 0, 1.0]])
    close(rps(perfect, out), 0)
    assert rps(np.array([[0.2, 0.3, 0.5]]), np.array([0])) > rps(np.array([[0.5, 0.3, 0.2]]), np.array([0]))
    rows = calibration_table([0.05, 0.15, 0.95], [0, 0, 1], bins=10)
    assert [r[2] for r in rows] == [1, 1, 1]


def test_bootstrap_and_returns():
    r = bet_returns([0.6, 0.3, 0.55], [2.0, 2.0, 2.0], [1, 1, 0], min_ev=0.0)
    assert list(r) == [1.0, -1.0]  # the 0.3 selection has negative EV and is skipped
    mean, lo, hi = bootstrap_ci(np.r_[np.ones(60), -np.ones(40)])
    close(mean, 0.2)
    assert lo < 0.2 < hi


def test_fit_recovers_strengths():
    rng = np.random.default_rng(1)
    teams = [f"T{k}" for k in range(12)]
    att = dict(zip(teams, rng.normal(0, 0.3, 12)))
    dfn = dict(zip(teams, rng.normal(0, 0.3, 12)))
    att = {t: v - np.mean(list(att.values())) for t, v in att.items()}
    dfn = {t: v - np.mean(list(dfn.values())) for t, v in dfn.items()}
    h, a, hg, ag = [], [], [], []
    for _ in range(8):  # 8 double round-robins: plenty of data
        for x in teams:
            for y in teams:
                if x != y:
                    h.append(x), a.append(y)
                    hg.append(rng.poisson(np.exp(0.15 + 0.25 + att[x] - dfn[y])))
                    ag.append(rng.poisson(np.exp(0.15 + att[y] - dfn[x])))
    model = fit_team_strengths(h, a, hg, ag, ridge=0.01)
    close(model.home_adv, 0.25, 0.08)
    est = np.array([model.attack[t] for t in teams])
    assert np.corrcoef(est, [att[t] for t in teams])[0, 1] > 0.9
    lam_h, lam_a = model.predict("unseen FC", "T0")
    assert lam_h > 0 and lam_a > 0


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"{len(tests)}/{len(tests)} passed")
