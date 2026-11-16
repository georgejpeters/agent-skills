---
max_turns: 10
timeout_seconds: 300
allowed_tools: [Skill, Read, Grep, Glob]
runs: 3
---

I'm calibrating my 'player to have 1+ shot' model against exchange settlement data for player
markets: 30,000 settled markets. The model consistently over-predicts: average predicted 0.42,
observed win rate 0.33. Before I retrain, is the model really that biased?
