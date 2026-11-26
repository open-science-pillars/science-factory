---
description: "Held-out data was opened no more often than planned."
type: deterministic
check: openings-within-allowed
reads: [plan, post-opening-log]
selfImprovement: false
---

Held-out data was opened no more often than planned.

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
