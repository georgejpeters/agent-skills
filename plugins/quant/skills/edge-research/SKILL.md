---
name: edge-research
description: Run an edge or trading-strategy investigation honestly from idea to verdict — the gates to pass (crowding, data definitions, look-ahead, realistic fills, survivorship, factor/beta stripping, costs and capacity) and how to decide whether to kill or keep a hypothesis. Use when exploring whether a betting, trading or market-anomaly idea is exploitable, when a backtest shows a profit, or before building infrastructure for a strategy.
---

# Edge research

Most backtest profits are artefacts. The job is to find the artefact before the money does.
Run the gates in order; each one is cheap compared with the next.

## Gate 0: is it crowded?

Before building anything: is this idea well publicised (papers, apps, ETFs, tipster sites)?
Published anomalies decay as capital arrives. Prefer edges that are capacity-limited (too small
for funds), operationally annoying, or rely on obscure or self-collected data.

## Gate 1: is the target the right event?

- Define the outcome **exactly as the market settles it**. Different data providers count
  "shots on target", "cards" or "assists" differently; a definitional mismatch can manufacture
  a large fake edge.
- Build the model's rate and the graded outcome from the **same** source and definition.
- Check settlement edge cases: voids, non-starters, abandoned matches, own goals, extra time.

## Gate 2: no look-ahead

- Prices: the last price before the decision time, never in-play or closing prices you couldn't
  have taken. Signals: only information public at the decision time, with its real timestamp.
- Slices and filters must be knowable in advance (actual line-ups, not "played 60+ minutes").
- See model-validation's leakage checklist.

## Gate 3: realistic execution

- **Fill timing:** when did the signal become public, and when could you actually trade? (A
  filing released after the market closes is a next-day fill. A line-up released 60 minutes
  before kick-off moves the price within seconds.) Re-run with a realistic lag; edges that live
  entirely in an inaccessible window are dead.
- Spread, commission, slippage, minimum stakes, account limits, liquidity at the price.

## Gate 4: is it alpha or exposure?

- Finance: strip market beta and factors (size, value, momentum: e.g. Fama-French) and test the
  residual.
- Betting: compare with simply backing the whole market segment (favourites, overs, a league) to
  check the "edge" isn't a known bias that's priced in or a margin artefact.
- **Survivorship:** price histories that drop delisted or relegated names inflate returns;
  stress-test by assigning the missing ones a loss.

## Gate 5: statistics

Out-of-sample ROI with a bootstrap CI that excludes 0; stable across periods; corrected for the
number of variants tried (model-validation §5). Prefer closing-line value as an early signal.

## Kill or keep

- **Don't kill a hypothesis just because the current model lost.** A weak model failing doesn't
  mean the market is efficient. Ask whether *any* public-in-advance signal predicts the outcome
  beyond the market-implied probability (residual predictability, soft pockets by league or
  market subtype, open vs close). Keep collecting forward data rather than judging on a thin
  sample.
- **Do kill it** when the market is efficient for everything you can observe in time, or when the
  edge only exists in a fill window you can't access, or after costs.
- Record each verdict with its evidence, so the same idea isn't re-tested blind later.

## Before staking real money

Keep a forward paper record with timestamps written before the event (an append-only,
hash-chained log is ideal). Compare its live results with the backtest. A gap between them is the
most informative number you have.
