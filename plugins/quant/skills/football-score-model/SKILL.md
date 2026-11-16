---
name: football-score-model
description: Build or explain a football score model — turning expected goals (xG / goal rates) into scoreline probabilities (0-0, 1-0, 1-1 …) and from there into 1X2, over/under, BTTS, Asian handicap and correct-score prices; fitting team attack/defence strengths (Maher, Dixon-Coles with time decay, xG-based ratings); Poisson assumptions and when they break. Use for any football prediction or pricing task. For converting probabilities to odds or finding value see betting-markets; for testing a model see model-validation.
---

# Football score model

Toolkit: `${CLAUDE_PLUGIN_ROOT}/lib/quantkit.py` (numpy only; copy the file into the project if
the plugin path isn't importable). Worked end to end in
`${CLAUDE_PLUGIN_ROOT}/examples/practice_pipeline.py`.

## The chain

```
team strengths ──► expected goals λ_home, λ_away ──► score matrix P(i, j) ──► every market
```

1. **Expected goals per side.** `log λ_home = μ + home_adv + attack_home − defence_away`,
   `log λ_away = μ + attack_away − defence_home`. Typical top-flight values: μ ≈ 0.1–0.15
   (≈1.2–1.4 goals), home advantage ≈ 0.15–0.3 in log terms (smaller since 2020).
2. **Scorelines.** With independent Poisson goals, `P(i, j) = Pois(i; λ_h) · Pois(j; λ_a)`:
   `score_matrix(lam_h, lam_a)`. Worked: λ_h = 1.6, λ_a = 1.1 → P(0-0) = e^−2.7 ≈ 0.067,
   P(1-0) = 1.6·e^−2.7 ≈ 0.108, P(1-1) = 1.6·1.1·e^−2.7 ≈ 0.119.
3. **Markets** are sums over the matrix: home = below the diagonal, draw = the diagonal, away =
   above it; over 2.5 = cells with i + j ≥ 3; BTTS = i ≥ 1 and j ≥ 1; handicaps from the goal
   difference distribution. `markets(grid)` returns them all.

Supremacy/total form, handy when you have a line rather than ratings: `λ_h = (T + S)/2`,
`λ_a = (T − S)/2`, where T = total expected goals and S = expected goal difference.

## The assumptions, and where they break

| Assumption | Reality | Fix |
|---|---|---|
| Goals arrive at a constant rate | Game state changes rates (a leading team sits deeper, a trailing one chases) | Fine for pre-match pricing; in-play needs state-dependent rates |
| Home and away goals are independent | Low scores are correlated; independent Poisson under-prices 0-0 and 1-1 | Dixon-Coles ρ (typically −0.05 to −0.15): `score_matrix(..., rho=-0.08)`, or a bivariate Poisson |
| Variance = mean | Mild overdispersion in some leagues | Negative binomial, or accept it (the effect on 1X2 is small) |
| Strengths are fixed | Form, injuries, transfers, managers | Time decay (`half_life_days`), refit often, adjust for confirmed line-ups |

## Estimating strengths

- **Goals-based (Maher / Dixon-Coles):** `fit_team_strengths(home, away, hg, ag, days_ago,
  half_life_days)`. A Poisson GLM; the ridge penalty identifies it and shrinks thin teams.
- **xG-based:** fit the same model to xG instead of goals. xG is less noisy than goals, so it
  converges faster early in a season; blend with goals once the sample is decent. Fill
  missing xG with goals (or drop those rows) and say which you chose.
- **Market-implied:** solve for the λ_h, λ_a that reproduce the de-vigged 1X2 and over/under 2.5
  prices (a 2-D search over the grid). That gives the market's own view as a feature or a
  benchmark, and is often the strongest single predictor available.
- **Elo / ratings → supremacy:** map rating difference to S by regression on past matches, and
  take T from league averages.

Choose the half-life by out-of-sample log loss, not by the fit to training points.

## Common mistakes

- Fitting on matches after the one being predicted (see model-validation: leakage).
- Using raw 1/odds as probabilities without removing the margin.
- Reporting accuracy instead of log loss / RPS.
- Treating promoted or unseen teams as errors: the toolkit gives them average ratings. Better
  still, a prior from the league they came from.
