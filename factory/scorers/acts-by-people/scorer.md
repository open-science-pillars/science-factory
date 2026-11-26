---
description: "The lock and the signature were recorded under a person's name."
type: deterministic
check: acts-recorded-by-people
reads: [pre-lock-log, post-opening-log]
selfImprovement: false
---

The lock and the signature were recorded under a person's name.

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
