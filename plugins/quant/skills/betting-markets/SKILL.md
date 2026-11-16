---
name: betting-markets
description: Betting-market maths and judgement — odds formats, implied probability, bookmaker margin / overround, removing the vig (proportional, power, Shin), fair odds, expected value, Kelly staking, closing-line value, exchanges vs bookmakers, and why a model that picks more winners is not a better betting model. Use whenever probabilities meet prices: finding value bets, comparing a model to the market, sizing stakes, or explaining a bookmaker's margin.
---

# Betting markets

Functions are in `${CLAUDE_PLUGIN_ROOT}/lib/quantkit.py`.

## Prices ↔ probabilities

| Quantity | Formula | Toolkit |
|---|---|---|
| Implied probability | 1 / decimal odds | `implied(odds)` |
| Overround (margin) | Σ 1/odds − 1 | `overround(odds)` |
| Fair probabilities | remove the margin | `devig(odds, method)` |
| Fair odds | 1 / p | `fair_odds(p)` |
| Expected value per unit | p · odds − 1 | `ev(p, odds)` |
| Kelly fraction | (p · odds − 1) / (odds − 1) | `kelly(p, odds, fraction)` |

Worked: 1X2 at 2.10 / 3.40 / 3.60 → implied 0.476 + 0.294 + 0.278 = 1.048, so a 4.8% overround.
Proportional de-vig gives 0.454 / 0.281 / 0.265. If your model says the home win is 0.50, then
EV at 2.10 = 0.50 × 2.10 − 1 = **+5%**, and the fair price is 2.00.

Fractional odds a/b → decimal 1 + a/b. American +150 → 2.50; −200 → 1.50.

## Which de-vig method

Bookmakers load more margin onto longshots (the favourite-longshot bias), so proportional
de-vigging overstates longshots' true chances. **Shin** or **power** move margin onto the
longshot and are better defaults for 1X2. For two-way markets close to evens, the methods agree.
On an exchange with no overround, use the mid-price (or the back price, conservatively).

## Why more winners ≠ a better betting model

Profit comes from **prices that are wrong**, not from picking likely outcomes. Backing every
favourite has a high hit rate and a negative ROI, because the price already includes the
favourite's chance plus the margin. Judge models by:
1. probability quality against the de-vigged market (log loss / RPS: see model-validation);
2. out-of-sample ROI at the prices you could actually have taken, with a confidence interval;
3. **closing-line value** (`clv(taken_odds, closing_fair_p)`): consistently beating the closing
   price is the fastest, lowest-variance sign of real edge, available long before ROI is
   significant.

## Staking

- Kelly maximises long-run growth *if p is right*. It never is exactly, so use ¼–½ Kelly, and cap
  any single stake.
- Level stakes are simplest for evaluating a model; use them in backtests.

## Market realities (state them when relevant)

- Bookmakers limit or restrict ("gub") winning accounts, so the edge you can actually stake is
  capped. Exchanges don't limit, but charge commission on net winnings (~2–5%): include it in EV.
- Closing prices in major leagues are close to efficient; edges are usually in thin markets,
  early prices, information the market hasn't priced yet (line-ups, injuries), or props.
- Use prices that were available **before kick-off** and at a stake you could have got on.
