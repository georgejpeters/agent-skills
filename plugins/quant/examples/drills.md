# Timed drills: football modelling with an AI assistant

Practice for live, think-aloud modelling sessions: someone hands you data and a laptop, you shape
it with an AI assistant, build something predictive, and explain whether it would make money.

**Setup:** `uv run --no-project --with numpy --with pandas python practice_pipeline.py --csv`
writes `matches.csv`: 3 seasons × 380 matches with columns season, date, week, home, away,
home_goals, away_goals, home_xg, away_xg, odds_h, odds_d, odds_a, result. It has a few missing
values. Change `RNG` in the script for a fresh league each time.

**Rules for every drill**
- Start a timer. Talk out loud (record yourself, or explain to a rubber duck).
- Use the assistant for typing speed, not for decisions: tell it what to build, check what comes back.
- Don't open `practice_pipeline.py` until afterwards: it's the answer key.
- Finish with a 60-second verdict: what you found, how sure you are, what you'd test next.

---

## Drill 1: first look (10 min)

> "Here's three seasons of results with xG and closing odds. What do you see?"

Checkpoints:
1. Shape, date range, teams, missing values. Say what you'll do about each gap and why.
2. Base rates: home / draw / away, goals per game home and away.
3. Per-team home and away scoring averages (`groupby`), and xG vs goals per team.
4. Overround per match from the odds: its mean and spread.

Good looks like: decisions stated in one sentence each ("missing draw odds: drop those rows
from betting only, keep them for fitting"), no rabbit holes.

## Drill 2: xG to scorelines (10 min)

> "This weekend: Team A expected 1.7 goals, Team B 0.9. Price it."

1. Score grid by hand with `scipy.stats.poisson` or numpy; P(0-0), P(1-0), P(1-1), P(2-1).
2. 1X2, over/under 2.5, BTTS from the grid; fair odds for each.
3. Name the assumptions (independence, constant rate) and the fix for the draw problem
   (Dixon-Coles ρ). Show how ρ = −0.1 changes P(0-0) and P(draw).

Good looks like: the grid sums to ~1, the 1X2 probabilities sum to 1, and you can explain why
independent Poisson underestimates draws.

## Drill 3: the model (20 min)

> "Build something that predicts next season."

1. Chronological split: seasons 1–2 train, season 3 test. Say why random splits leak.
2. Team attack/defence ratings: start with simple ratios (team's goals for/against vs league
   average, home and away separately), then a Poisson GLM if time allows.
3. Predict λ for every test match, then 1X2 probabilities.
4. Stretch: refit weekly (walk-forward) using only earlier matches; fit to xG instead of goals.

Good looks like: a working baseline in the first 10 minutes, improved after; no test-season data
in any fit.

## Drill 4: is it any good? (15 min)

> "Your model gets 48% of results right. Is it good?"

1. Log loss and RPS for: base rates, your model, the market (margin removed). Accuracy too, to
   show why it misleads.
2. Calibration table for home-win probability (bins of 0.1).
3. Answer the question: accuracy isn't the measure; the market is the benchmark.

Good looks like: a three-row comparison table, and a sentence on where the model sits between
base rates and the market.

## Drill 5: make it profitable (15 min)

> "Can we make money with this?"

1. Remove the margin (proportional; then Shin or power, and explain the favourite-longshot bias).
2. EV = p × odds − 1 for each outcome; back when EV > threshold; ROI at level stakes.
3. Bootstrap 95% CI on ROI. How many bets? Does the CI exclude 0?
4. Compare with "always back the favourite": hit rate vs ROI.
5. Name what's missing before real money: closing-line value, commission/limits, more seasons,
   multiple-testing across thresholds.

Good looks like: "+6% ROI on 400 bets, CI [−11%, +22%]: not distinguishable from zero; here's
what I'd do next." Never "it makes 6%".

## Drill 6: the curveball (10 min each, pick one at random)

- "Recent form matters more. Add it." → time-decay weights; choose the half-life on validation
  log loss, not the training fit.
- "Here's extra data: shots, possession, red cards." → which are pre-match knowable? Leakage check
  first; then add as features or adjust λ.
- "A promoted team has no history." → shrinkage to a prior (promoted sides' average), not zero
  data.
- "Price over/under 2.5 instead." → the same grid, a different sum; compare with the 1X2 market's
  implied total.
- "The model and the market disagree hugely on one match. Bet big?" → check data errors and news
  first; big disagreement is usually your error, not the market's; size with fractional Kelly.
- "Where would you look for a real edge?" → thin markets, early prices, info timing (line-ups),
  props; crowded vs uncrowded; CLV as the early test.

## Scoring yourself

| | 1 | 3 | 5 |
|---|---|---|---|
| Pace | stuck on setup | baseline by the midpoint | baseline fast, then iterated |
| Leakage | random split or future data | chronological | walk-forward, called out unprompted |
| Evaluation | accuracy only | log loss | vs market + calibration + CI |
| Honesty | claims profit | hedged | verdict + uncertainty + next test |
| Talking | silent typing | narrates | explains choices and trade-offs as made |
