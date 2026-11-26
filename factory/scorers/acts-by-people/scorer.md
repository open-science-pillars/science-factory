---
description: "The lock and the signature were recorded as acts by people: a merged pull request with the people the platform recorded, or, for practice, a person's name with a link."
type: deterministic
check: acts-recorded-by-people
reads: [pre-lock-log, post-opening-log]
selfImprovement: false
---

The lock and the signature were recorded as acts by people: each is either a pull request merged on the protected branch, written into the log under the platform's name with the merge commit and at least one person who approved, or, in practice mode, an event under a person's name with an https link. A practice act passes this check and is labelled practice everywhere else; the check says how the act was recorded, not who the person was.

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
