---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Can you sanity-check my player-props backtest before I stake real money? The model predicts
P(player has 1+ shot on target). Training rates and graded outcomes both come from our data
provider's shot map, which flags a shot as "on target" if it was heading on target. The bet
universe is players with 60+ minutes played. Prices are the last odds snapshot we stored for
each market. The bookmaker settles on official Opta stats. Backing whenever model EV > 10%
returned +14% ROI over 2,000 bets. What could be wrong?
