---
description: "Nothing was locked again after an opening, and the data had not been opened before."
type: deterministic
check: not-exploratory
reads: [pre-lock-log, post-opening-log]
selfImprovement: false
---

Nothing was locked again after an opening, and the data had not been opened before.

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
