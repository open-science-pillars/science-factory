---
description: "No opening was used up on a run that crashed."
type: deterministic
check: no-failed-opening
reads: [opening-outcome]
selfImprovement: false
---

No opening was used up on a run that crashed: the tests and rehearsals should have caught it. This check reads how an opening ended (finished or failed), never which way its result fell.

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
