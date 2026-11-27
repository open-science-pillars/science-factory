---
type: pitfall
spheres: []
title: "State the thing itself in one sentence, so the title alone would stop someone making the mistake"
description: "Two or three sentences: what happens, where it was seen, with the main number and its count, and what to do about it."
tags: [product, field, topic]
generated: { by: claude-code/MODEL, at: 2026-01-01T00:00:00Z }
status: draft
stale_after: 2027-01-01
seen_while: exploring
drafted_from: { exploration: EXPLORATION-0000, notes: [NOTE-001], log: "SEQ:HASH", by: "agent:curating-0000" }
relates_to:
  - { concept: an-existing-page.md, relation: extends, why: "what this adds to that page" }
sources:
  - id: look
    resource: https://github.com/ORG/REPO/blob/COMMIT/path/to/receipts/LOOK-001.json
    title: "The look this was seen in: what was run, on which data, read on which date"
  - id: product
    resource: https://example.org/the-providers-own-page
    title: "What the provider's page says about the field, read on which date"
---

# The same thing, as a heading

**Seen while exploring.** Where, when, on which data, how many observations. This page is a draft from one exploration and has not been tested or signed.[^look]

**What happens.** The mechanism if it is known, with its source.[^product] If it is not known, say that it is not.

**Measured.** The numbers, with units and counts, as that case's numbers.[^look]

**How it makes a wrong answer look right.** What a person would conclude if they did not know this.

**What to do.** The handling, and what it costs.

**How to check it.** What someone else would run to see the same thing.

[^look]: the look receipt
[^product]: the provider's page
