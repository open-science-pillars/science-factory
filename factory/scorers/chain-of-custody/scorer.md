---
description: "The study log, the run receipts, the record of what has been opened and the locked plan and code all check out."
type: deterministic
check: log-checks-out
reads: [plan, known-answer-tests, pre-lock-log, opening-outcome, post-opening-log]
selfImprovement: false
---

The study log, the run receipts, the record of what has been opened and the locked plan and code all check out, as far as the files in the workspace can show (a rewritten log shows only against a commit or a posted fingerprint).

The study tool works this out from the study's log (`sf.py scorecard`); no model is asked. A check that cannot be judged yet says `pending`, never `pass`. It reads material written after an opening, so it may be counted and shown to people and may never feed a proposal to change the factory: the validator refuses `selfImprovement: true` here.
