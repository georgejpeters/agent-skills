"""End-to-end practice: from a match table with odds to an honest verdict on a betting model.

    uv run --no-project --with numpy --with pandas python plugins/quant/examples/practice_pipeline.py

Synthetic league (so the true answer is known): 20 teams, 3 seasons, team strengths drifting
between seasons, xG per match, bookmaker 1X2 odds with a margin, a few missing values. Steps:

  1. look at the data           5. calibration
  2. naive baselines            6. betting: EV filter, ROI with a confidence interval
  3. walk-forward model         7. "more winners" is not "more profit"
  4. score vs the market        8. verdict

Pass --csv to also write the synthetic data to matches.csv for your own practice.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from quantkit import (bet_returns, bootstrap_ci, calibration_table, devig, fit_team_strengths,  # noqa: E402
                      log_loss, markets, rps, score_matrix)

RNG = np.random.default_rng(7)
OUTCOMES = ["H", "D", "A"]


def simulate(n_teams=20, seasons=3, margin=0.055):
    teams = [f"Team {chr(65 + k)}" for k in range(n_teams)]
    att = RNG.normal(0, 0.25, n_teams)
    dfn = RNG.normal(0, 0.25, n_teams)
    rows, day0 = [], pd.Timestamp("2023-08-12")
    for s in range(seasons):
        att += RNG.normal(0, 0.08, n_teams)  # strengths drift between seasons
        dfn += RNG.normal(0, 0.08, n_teams)
        fixtures = [(i, j) for i in range(n_teams) for j in range(n_teams) if i != j]
        RNG.shuffle(fixtures)
        per_week = n_teams // 2
        for k, (i, j) in enumerate(fixtures):
            week = k // per_week
            date = day0 + pd.Timedelta(days=365 * s + 7 * week)
            lam_h = np.exp(0.12 + 0.22 + att[i] - dfn[j])
            lam_a = np.exp(0.12 + att[j] - dfn[i])
            hg, ag = RNG.poisson(lam_h), RNG.poisson(lam_a)
            # The book sees the truth with noise, then adds margin (power method style).
            p = np.array([markets(score_matrix(lam_h * np.exp(RNG.normal(0, 0.07)),
                                               lam_a * np.exp(RNG.normal(0, 0.07)), rho=-0.05))[o]
                          for o in ("home", "draw", "away")])
            k_pow = np.log(1 + margin) / 3 + 1
            q = p ** (1 / k_pow)
            q *= (1 + margin) / q.sum()
            odds = np.round(1 / q, 2)
            rows.append(dict(season=f"{2023 + s}/{24 + s}", date=date, week=week + 1,
                             home=teams[i], away=teams[j], home_goals=hg, away_goals=ag,
                             home_xg=round(lam_h * np.exp(RNG.normal(0, 0.3)), 2),
                             away_xg=round(lam_a * np.exp(RNG.normal(0, 0.3)), 2),
                             odds_h=odds[0], odds_d=odds[1], odds_a=odds[2]))
    df = pd.DataFrame(rows).sort_values(["date", "home"]).reset_index(drop=True)
    for col in ("home_xg", "away_xg", "odds_d"):  # real data has holes
        df.loc[RNG.random(len(df)) < 0.02, col] = np.nan
    df["result"] = np.select([df.home_goals > df.away_goals, df.home_goals == df.away_goals], ["H", "D"], "A")
    return df


def header(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main():
    df = simulate()
    if "--csv" in sys.argv:
        df.to_csv("matches.csv", index=False)
        print("wrote matches.csv")

    header("1. Look at the data before modelling")
    print(df.head(3).to_string())
    print("\nmissing values:\n" + df.isna().sum()[lambda s: s > 0].to_string())
    print(f"\nhome win / draw / away: {df.result.value_counts(normalize=True).reindex(OUTCOMES).round(3).to_dict()}")
    print(f"goals per game home {df.home_goals.mean():.2f}, away {df.away_goals.mean():.2f}")
    home_avg = df.groupby("home").home_goals.mean().rename("home_scored")
    away_avg = df.groupby("away").away_goals.mean().rename("away_scored")
    print("\nper-team scoring averages (top 5 by home scoring):")
    print(pd.concat([home_avg, away_avg], axis=1).sort_values("home_scored", ascending=False).head().round(2).to_string())
    print("\nDecision: missing odds_d -> drop those rows from betting only; missing xG -> fall back to goals.")

    header("2+3. Chronological walk-forward: refit each week on matches BEFORE it")
    test = df[df.season == df.season.max()].copy()
    preds = []
    for date, games in test.groupby("date"):
        past = df[df.date < date]  # the only rows allowed: no leakage
        age = (date - past.date).dt.days.to_numpy()
        goals = fit_team_strengths(past.home, past.away, past.home_goals, past.away_goals,
                                   days_ago=age, half_life_days=240)
        xg_h = past.home_xg.fillna(past.home_goals)
        xg_a = past.away_xg.fillna(past.away_goals)
        xg = fit_team_strengths(past.home, past.away, xg_h, xg_a, days_ago=age, half_life_days=240)
        for idx, g in games.iterrows():
            for name, model in (("goals", goals), ("xg", xg)):
                mk = markets(score_matrix(*model.predict(g.home, g.away), rho=-0.05))
                preds.append(dict(idx=idx, model=name, pH=mk["home"], pD=mk["draw"], pA=mk["away"]))
    p = pd.DataFrame(preds).pivot(index="idx", columns="model")
    for name in ("goals", "xg"):
        for o in OUTCOMES:
            test[f"{name}_p{o}"] = p[(f"p{o}", name)]
    print(f"test season: {len(test)} matches, {test.date.nunique()} refits, train = all earlier matches (time-decayed)")

    header("4. Score the probabilities (lower is better) against baselines and the market")
    y = test.result.map({o: k for k, o in enumerate(OUTCOMES)}).to_numpy()
    train_rates = df[df.season != df.season.max()].result.value_counts(normalize=True).reindex(OUTCOMES).to_numpy()
    book = test.dropna(subset=["odds_h", "odds_d", "odds_a"])
    yb = y[test.index.get_indexer(book.index)]
    book_p = np.vstack([devig(r, "shin") for r in book[["odds_h", "odds_d", "odds_a"]].to_numpy()])
    rows = [("base rates (train H/D/A)", np.tile(train_rates, (len(test), 1)), y)]
    for name in ("goals", "xg"):
        rows.append((f"model: {name}", test[[f"{name}_p{o}" for o in OUTCOMES]].to_numpy(), y))
    rows.append(("bookmaker (shin de-vig)", book_p, yb))
    print(f"{'':28}{'log loss':>10}{'RPS':>8}{'accuracy':>10}")
    for label, probs, yy in rows:
        print(f"{label:28}{log_loss(probs, yy):>10.4f}{rps(probs, yy):>8.4f}{(probs.argmax(1) == yy).mean():>10.3f}")
    print("Read: beating base rates means the model learned something; the market is the bar that matters.")

    header("5. Calibration: home-win probability (xG model)")
    print(f"{'bin':>12}{'n':>6}{'predicted':>11}{'observed':>10}")
    for lo, hi, n, pred, obs in calibration_table(test.xg_pH, test.result == "H", bins=8):
        print(f"{lo:5.2f}-{hi:4.2f}  {n:>6}{pred:>11.3f}{obs:>10.3f}")

    header("6. Betting: back selections where model EV > threshold, at the offered odds")
    b = test.dropna(subset=["odds_h", "odds_d", "odds_a"])
    for name in ("goals", "xg"):
        for min_ev in (0.0, 0.05, 0.10):
            rets = np.concatenate([
                bet_returns(b[f"{name}_p{o}"], b[f"odds_{o.lower()}"], b.result == o, min_ev=min_ev)
                for o in OUTCOMES])
            if len(rets) < 20:
                print(f"{name:6} EV>{min_ev:.2f}: only {len(rets)} bets, too few to judge")
                continue
            mean, lo, hi = bootstrap_ci(rets)
            print(f"{name:6} EV>{min_ev:.2f}: {len(rets):4} bets, ROI {mean:+.1%}  95% CI [{lo:+.1%}, {hi:+.1%}]")
    print("Read: a CI that straddles 0 is not an edge, however good the point estimate looks. And six")
    print("cells were tried: picking the best one after the fact is multiple testing, not discovery.")
    print("Note the models lose to the market on log loss yet show +ROI: that's noise, not skill.")

    header("7. More winners is not more profit")
    fav = b[["odds_h", "odds_d", "odds_a"]].to_numpy().argmin(1)
    yb2 = y[test.index.get_indexer(b.index)]
    fav_odds = b[["odds_h", "odds_d", "odds_a"]].to_numpy()[np.arange(len(b)), fav]
    fav_ret = np.where(fav == yb2, fav_odds - 1, -1)
    print(f"always back the favourite: hit rate {(fav == yb2).mean():.1%}, ROI {fav_ret.mean():+.1%}")
    print("High accuracy, negative ROI: the price already contains the favourite's chance plus margin.")
    print("A betting model wins by finding prices that are wrong, not by picking the likeliest outcome.")

    header("8. Verdict")
    print("- Report log loss / RPS against the de-vigged market, not accuracy.")
    print("- Only claim an edge with an out-of-sample ROI CI above 0, after costs, on enough bets.")
    print("- Next: closing-line value, more seasons, a held-out league, and a pre-registered threshold.")


if __name__ == "__main__":
    main()
