"""quantkit: small, dependency-light (numpy only) toolkit for football score models and betting maths.

    from quantkit import *
    model = fit_team_strengths(home, away, home_goals, away_goals, days_ago=age, half_life_days=180)
    lam_h, lam_a = model.predict("Arsenal", "Chelsea")
    grid = score_matrix(lam_h, lam_a, rho=-0.05)          # P(home=i, away=j)
    mk = markets(grid)                                    # 1X2, over/under, BTTS, correct scores
    p_fair = devig([2.10, 3.40, 3.60], method="shin")     # book odds -> fair probabilities
    ev(mk["home"], 2.10)                                  # expected profit per unit staked

Every function takes plain floats / sequences / numpy arrays. No pandas needed.
"""
from dataclasses import dataclass, field

import numpy as np

# --------------------------------------------------------------------------- score model


def poisson_pmf(lam, max_goals=10):
    """P(X=k) for k = 0..max_goals, built iteratively (no factorial overflow)."""
    p = np.empty(max_goals + 1)
    p[0] = np.exp(-lam)
    for k in range(1, max_goals + 1):
        p[k] = p[k - 1] * lam / k
    return p


def dixon_coles_tau(i, j, lam_h, lam_a, rho):
    """Dixon-Coles low-score correction. rho < 0 raises 0-0 and 1-1, lowers 1-0 and 0-1."""
    if i == 0 and j == 0:
        return 1 - lam_h * lam_a * rho
    if i == 0 and j == 1:
        return 1 + lam_h * rho
    if i == 1 and j == 0:
        return 1 + lam_a * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


def score_matrix(lam_h, lam_a, max_goals=10, rho=0.0):
    """Joint scoreline probabilities, rows = home goals, cols = away goals.

    Independent Poisson by default; rho != 0 applies the Dixon-Coles correction. The tail beyond
    max_goals is renormalised away (it is ~1e-6 for typical football rates at max_goals=10).
    """
    m = np.outer(poisson_pmf(lam_h, max_goals), poisson_pmf(lam_a, max_goals))
    if rho:
        for i in (0, 1):
            for j in (0, 1):
                m[i, j] *= dixon_coles_tau(i, j, lam_h, lam_a, rho)
    return m / m.sum()


def markets(m, lines=(0.5, 1.5, 2.5, 3.5, 4.5)):
    """Derive common markets from a score matrix."""
    n = m.shape[0]
    i, j = np.indices(m.shape)
    total = i + j
    out = {
        "home": float(np.tril(m, -1).sum()),
        "draw": float(np.trace(m)),
        "away": float(np.triu(m, 1).sum()),
        "btts_yes": float(m[1:, 1:].sum()),
        "home_clean_sheet": float(m[:, 0].sum()),
        "away_clean_sheet": float(m[0, :].sum()),
        "exp_home_goals": float((i * m).sum()),
        "exp_away_goals": float((j * m).sum()),
    }
    out["btts_no"] = 1 - out["btts_yes"]
    for line in lines:
        over = float(m[total > line].sum())
        out[f"over_{line}"], out[f"under_{line}"] = over, 1 - over
    out["correct_score"] = {f"{a}-{b}": float(m[a, b]) for a in range(min(n, 6)) for b in range(min(n, 6))}
    return out


# --------------------------------------------------------------------------- team strengths


@dataclass
class TeamStrengths:
    """log E[goals] = intercept + home_adv*(is home) + attack[scorer] - defence[conceder]."""
    intercept: float
    home_adv: float
    attack: dict = field(default_factory=dict)
    defence: dict = field(default_factory=dict)

    def predict(self, home, away):
        """Expected goals (home, away). Unseen teams get average (0) ratings, never an error."""
        a, d = self.attack, self.defence
        lam_h = np.exp(self.intercept + self.home_adv + a.get(home, 0.0) - d.get(away, 0.0))
        lam_a = np.exp(self.intercept + a.get(away, 0.0) - d.get(home, 0.0))
        return float(lam_h), float(lam_a)


def fit_team_strengths(home, away, home_goals, away_goals, days_ago=None, half_life_days=None,
                       ridge=0.1, iters=50):
    """Maher-style Poisson team strengths by ridge-penalised IRLS (numpy only).

    days_ago + half_life_days give recent matches more weight (Dixon-Coles time decay): weight =
    0.5 ** (days_ago / half_life_days). The ridge penalty on team ratings identifies the model
    (ratings centre on 0) and shrinks teams with few matches. Pass only matches played BEFORE the
    games you will predict.
    """
    home, away = np.asarray(home), np.asarray(away)
    teams = sorted(set(home) | set(away))
    idx = {t: k for k, t in enumerate(teams)}
    n_t, n_m = len(teams), len(home)
    # Two rows per match: home scoring and away scoring. Columns: intercept, home_adv, att, def.
    x = np.zeros((2 * n_m, 2 + 2 * n_t))
    x[:, 0] = 1
    x[:n_m, 1] = 1
    hi = np.array([idx[t] for t in home])
    ai = np.array([idx[t] for t in away])
    r = np.arange(n_m)
    x[r, 2 + hi] = 1
    x[r, 2 + n_t + ai] = -1
    x[n_m + r, 2 + ai] = 1
    x[n_m + r, 2 + n_t + hi] = -1
    y = np.concatenate([home_goals, away_goals]).astype(float)
    w = np.ones(n_m)
    if days_ago is not None and half_life_days:
        w = 0.5 ** (np.asarray(days_ago, float) / half_life_days)
    w = np.concatenate([w, w])
    pen = np.full(x.shape[1], ridge)
    pen[:2] = 0  # don't shrink intercept or home advantage
    beta = np.zeros(x.shape[1])
    beta[0] = np.log(max(y.mean(), 1e-3))
    for _ in range(iters):
        eta = x @ beta
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        xw = x * (w * mu)[:, None]
        new = np.linalg.solve(xw.T @ x + np.diag(pen), xw.T @ z)
        if np.max(np.abs(new - beta)) < 1e-8:
            beta = new
            break
        beta = new
    return TeamStrengths(
        intercept=float(beta[0]), home_adv=float(beta[1]),
        attack={t: float(beta[2 + k]) for t, k in idx.items()},
        defence={t: float(beta[2 + n_t + k]) for t, k in idx.items()},
    )


# --------------------------------------------------------------------------- odds and prices


def implied(odds):
    """Raw implied probabilities 1/odds (they sum to 1 + overround)."""
    return 1 / np.asarray(odds, float)


def overround(odds):
    """Bookmaker margin: sum(1/odds) - 1. 0.05 = a 5% book."""
    return float(implied(odds).sum() - 1)


def devig(odds, method="proportional"):
    """Fair probabilities from one market's odds.

    proportional: scale 1/odds to sum to 1 (simple; over-weights longshots' share of the margin).
    power:        p_i = (1/o_i)^k with k solved so they sum to 1 (puts more margin on longshots).
    shin:         Shin's insider-trading model (also loads margin on longshots; good default for 1X2).
    """
    q = implied(odds)
    if method == "proportional":
        return q / q.sum()
    if method == "power":
        lo, hi = 1.0, 10.0
        for _ in range(100):
            k = (lo + hi) / 2
            lo, hi = (k, hi) if (q ** k).sum() > 1 else (lo, k)
        p = q ** ((lo + hi) / 2)
        return p / p.sum()
    if method == "shin":
        s = q.sum()

        def probs(z):
            return (np.sqrt(z ** 2 + 4 * (1 - z) * q ** 2 / s) - z) / (2 * (1 - z))

        lo, hi = 0.0, 0.5
        for _ in range(100):
            z = (lo + hi) / 2
            lo, hi = (z, hi) if probs(z).sum() > 1 else (lo, z)
        p = probs((lo + hi) / 2)
        return p / p.sum()
    raise ValueError(f"unknown method {method!r}")


def fair_odds(p):
    """Decimal odds with zero margin."""
    return 1 / np.asarray(p, float)


def ev(p, odds):
    """Expected profit per 1 unit staked: p*odds - 1. Positive = value at that price."""
    return np.asarray(p, float) * np.asarray(odds, float) - 1


def kelly(p, odds, fraction=1.0):
    """Kelly stake as a fraction of bankroll (0 when there's no edge). Use fraction=0.25-0.5 in practice."""
    p, o = np.asarray(p, float), np.asarray(odds, float)
    return np.maximum(0.0, (p * o - 1) / (o - 1)) * fraction


def clv(taken_odds, closing_fair_prob):
    """Closing-line value: EV of the price you took, measured against the de-vigged closing line."""
    return ev(closing_fair_prob, taken_odds)


# --------------------------------------------------------------------------- evaluation


def log_loss(probs, outcome):
    """Mean negative log-likelihood. probs: (n, k); outcome: (n,) column index of what happened."""
    probs = np.clip(np.asarray(probs, float), 1e-15, 1)
    return float(-np.mean(np.log(probs[np.arange(len(outcome)), np.asarray(outcome)])))


def brier(probs, outcome):
    """Multi-class Brier score (sum over classes, mean over rows). Lower is better."""
    probs = np.asarray(probs, float)
    onehot = np.eye(probs.shape[1])[np.asarray(outcome)]
    return float(np.mean(((probs - onehot) ** 2).sum(axis=1)))


def rps(probs, outcome):
    """Ranked probability score for ordered outcomes (home, draw, away). Lower is better."""
    probs = np.asarray(probs, float)
    onehot = np.eye(probs.shape[1])[np.asarray(outcome)]
    diff = np.cumsum(probs, axis=1) - np.cumsum(onehot, axis=1)
    return float(np.mean((diff[:, :-1] ** 2).sum(axis=1) / (probs.shape[1] - 1)))


def calibration_table(p, hit, bins=10):
    """Rows of (bin_lo, bin_hi, n, mean predicted, observed rate) for a binary event."""
    p, hit = np.asarray(p, float), np.asarray(hit, float)
    edges = np.linspace(0, 1, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & ((p < hi) | (hi == 1))
        if mask.any():
            rows.append((lo, hi, int(mask.sum()), float(p[mask].mean()), float(hit[mask].mean())))
    return rows


def bootstrap_ci(values, stat=np.mean, n_boot=5000, alpha=0.05, seed=0):
    """Percentile bootstrap CI for a statistic of per-bet returns (or any iid sample)."""
    values = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    boots = np.array([stat(values[rng.integers(0, len(values), len(values))]) for _ in range(n_boot)])
    return float(stat(values)), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2))


def bet_returns(p_model, odds, won, min_ev=0.0, stake=1.0):
    """Per-bet profit for every selection where model EV > min_ev (level stakes)."""
    p_model, odds, won = (np.asarray(a, float) for a in (p_model, odds, won))
    pick = ev(p_model, odds) > min_ev
    return np.where(won[pick] > 0, (odds[pick] - 1) * stake, -stake)


__all__ = [n for n in dir() if not n.startswith("_") and n not in ("dataclass", "field", "np")]
