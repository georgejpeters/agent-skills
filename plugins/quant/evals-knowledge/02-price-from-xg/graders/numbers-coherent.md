---
type: llm
---

Ground truth (independent Poisson, lambda_home=1.7, lambda_away=0.9): home 0.563, draw 0.240,
away 0.198 (sum 1); fair odds about 1.78 / 4.18 / 5.05; P(0-0)=0.074; P(1-1)=0.114.
Pass if the answer's home/draw/away probabilities are each within 0.01 of these, the fair odds
are the reciprocals of its probabilities (within rounding), and P(0-0) and P(1-1) are within 0.005.
