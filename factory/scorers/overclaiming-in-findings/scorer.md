---
description: "Does a finding, or a review of it, use words that claim more than the locked rules gave?"
type: deterministic
check: overclaiming
applies_to: study
reads: [finding, review-after-opening]
phrases: overclaiming-in-leads/phrases.yaml
selfImprovement: false
---

Does a finding, or a review of it, use words that claim more than the locked rules gave?

The study tool works this out from the finding in force and the reviews of it (`sf.py attach` prints it, `sf.py scorecard` shows it, the signature request lists it); no model is asked. It uses the same list of phrases as the check of leads, and `confirms` is flagged unless the locked rules gave `supported`; a number is flagged when it is stated more finely than the interval or uncertainty in the opening's receipt supports. It warns and never blocks. It reads the finding, written after an opening, so its flags are counted and shown to people and never feed a proposal: the validator refuses `selfImprovement: true` here.
