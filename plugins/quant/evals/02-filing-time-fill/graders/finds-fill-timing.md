---
type: llm
weight: 3
---

Pass only if the answer identifies that buying at the filing date's CLOSE is likely look-ahead:
many Form 4s are filed/accepted after the market closes (or late in the day), so the signal was
not public in time to trade at that close. It must recommend using the filing acceptance
timestamp and a realistic entry (next open/close for after-hours filings) and re-running.
Mentioning generic look-ahead without tying it to filing time vs the close does NOT pass.
