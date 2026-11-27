---
description: "Does a lead, or a review of it, use words that claim more than an exploration can show?"
type: deterministic
check: overclaiming
applies_to: exploration
reads: [lead, review-before-opening]
phrases: overclaiming-in-leads/phrases.yaml
selfImprovement: true
---

Does a lead, or a review of it, use words that claim more than an exploration can show?

The exploring tool works this out from the lead as it stands and the reviews of it (`explore.py lead` prints it, `explore.py status` shows it); no model is asked. It flags each phrase of `phrases.yaml` beside this file, and a number stated more finely than the uncertainty beside it supports, naming the phrase and the line. It warns and never blocks. It reads only what was written before any opening, so its flags may feed a proposal to change the factory.
