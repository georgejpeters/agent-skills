---
type: llm
weight: 2
---

Pass only if ALL hold:
1. Margin/overround given as about 4.8% (sum of 1/odds = 1.0476).
2. Gives de-vigged probabilities that sum to 1; proportional gives about 0.636 / 0.227 / 0.136.
3. Explains that bookmakers load relatively more margin on longshots (favourite-longshot bias),
   so a method like Shin or power (or similar non-proportional method) is generally better than
   simple proportional normalisation, which overstates the longshot's chance.
