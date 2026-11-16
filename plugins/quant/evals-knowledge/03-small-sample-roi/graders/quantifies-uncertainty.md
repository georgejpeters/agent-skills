---
type: llm
weight: 2
---

Pass only if ALL hold:
1. The answer concludes the result is NOT statistically convincing / could easily be luck.
2. It quantifies the uncertainty with a number: a standard error, a confidence interval, a
   p-value or a required sample size. (Standard error of ROI here is about 10 percentage points,
   i.e. sqrt(odds-1)/sqrt(n); a 95% CI of roughly -12% to +28% or similar is correct.)
3. It mentions at least one other check beyond sample size: out-of-sample / walk-forward testing,
   multiple testing or overfitting, closing-line value, costs/limits, or leakage.
