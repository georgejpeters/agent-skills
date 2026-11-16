---
max_turns: 8
timeout_seconds: 300
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

I built a match-outcome model on 5 seasons of data. I shuffled all the matches and did an
80/20 train/test split; test log loss is great, better than the bookmaker. Anything wrong
with my setup? Short answer.
