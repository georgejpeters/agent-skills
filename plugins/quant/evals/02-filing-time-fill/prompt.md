---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

Stock idea backtest: whenever an SEC Form 4 shows a corporate insider buying shares, I buy that
stock at the closing price on the filing date and hold for 5 trading days. Over 3,000 trades the
beta-adjusted abnormal return is +2.1% per trade, and the 95% CI excludes zero. It looks robust.
What would you check before trading it?
