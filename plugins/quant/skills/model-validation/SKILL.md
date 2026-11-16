---
name: model-validation
description: Establish whether a predictive model has genuine out-of-sample value — chronological train/test splits and walk-forward refits, data-leakage checks, log loss / Brier / RPS, probability calibration, benchmarking against the de-vigged market, overfitting and multiple testing, sample size and bootstrap confidence intervals on ROI. Use whenever a model is evaluated, compared or claimed to work, in sports, finance or any time-ordered prediction problem.
---

# Model validation

The question is never "does it fit?" but "would it have made money, or forecast better than
the alternative, on data it had not seen, using only what was knowable at the time?"
Metrics are in `${CLAUDE_PLUGIN_ROOT}/lib/quantkit.py`; a full walk-forward is in
`${CLAUDE_PLUGIN_ROOT}/examples/practice_pipeline.py`.

## 1. Split by time, never randomly

- Train on the past, test on the future. Random K-fold on matches leaks future form into the past.
- **Walk-forward:** for each test date, fit on everything strictly before it and predict that
  date's games. This is what you would have done live.
- Tune hyperparameters (half-life, ρ, ridge, EV threshold) on a validation period, then
  evaluate **once** on a final held-out period.

## 2. Leakage checklist

- Features computed with data from after kick-off: season totals, final tables, the match's own xG.
- Closing odds used as a feature for a bet placed earlier.
- Ratings fit on a window that includes the test match.
- Line-ups or injuries that weren't public at bet time.
- A "starters" filter defined by minutes played (only known afterwards).
- Outcomes from a source whose definition differs from how the market settles. Check that your
  "shot on target" or "card" counts the same events the bookmaker settles on.
- In-play prices treated as pre-match prices.

## 3. Score probabilities, not picks

| Metric | Use | Note |
|---|---|---|
| Log loss | Main score for probabilistic forecasts | Punishes confident mistakes; `log_loss` |
| RPS | Ordered outcomes (H/D/A) | Rewards being "close" (draw vs away); `rps` |
| Brier | Binary or multi-class | Less harsh than log loss; `brier` |
| Accuracy | Rarely | Ignores confidence and price; misleading for betting |

Always show two baselines: **base rates** (has the model learned anything?) and the
**de-vigged market** (is it better than the price?). Beating base rates is easy; beating the
market is the real test.

## 4. Calibration

When the model says 30%, does it happen 30% of the time? `calibration_table(p, hit, bins)`. A
miscalibrated but discriminating model can be fixed with isotonic or Platt scaling, fitted on
validation data only. Check calibration per market and per probability band: errors hide in the
tails, where the prices are long.

## 5. Is the edge real?

- **Sample size.** ROI standard error ≈ √(odds − 1)/√n at level stakes. At odds of 2.0 and
  n = 500, that's ±4.5% for one standard error. Most "edges" from a few hundred bets are noise.
- **Bootstrap CI** on per-bet returns: `bootstrap_ci(returns)`. Claim nothing unless the 95% CI
  excludes 0.
- **Multiple testing.** Trying many markets, thresholds or leagues and reporting the best one
  inflates false positives. Pre-register the rule, or apply Benjamini-Hochberg across the cells.
- **Stability.** Does the edge hold in each season, each league, both halves of the sample?
  An edge that comes from one sub-period is a story, not a strategy.
- **Costs and execution:** margin, commission, slippage, stake limits, and whether you could get
  the price at the time the signal existed.
- **Overfitting tell:** in-sample far better than out-of-sample; many parameters for few events;
  the ROI rising with each extra filter.

## 6. Say it straight

State the result with its uncertainty and the test that would change your mind. "Log loss
1.052 vs the market's 1.045; ROI +6% with a 95% CI of [−11%, +22%] on 420 bets: not
distinguishable from zero" is a good answer. A confident claim from an untested backtest is not.
