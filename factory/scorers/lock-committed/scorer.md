---
description: "The lock was in a commit before the held-out data was opened."
type: deterministic
check: lock-committed-before-opening
reads: [pre-lock-log, post-opening-log]
selfImprovement: false
---

The lock was in a commit before the held-out data was opened (the blind test harness, in its throwaway directories, is the one named exception).

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
