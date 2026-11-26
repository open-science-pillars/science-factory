---
description: "Did the review of a lead do the checking a review is for, or wave the work through?"
type: judge
applies_to: exploration
agents: [review]
reads: [exploration-log, lead, review-before-opening]
labels:
  - {value: checked, score: 1, description: "each claim of the review, hole or not, points at a file or a log line, and the lead's central numbers were rechecked"}
  - {value: thin, score: 0.5, description: "some checking is shown, and the central numbers or the order of choices were not examined"}
  - {value: waved-through, score: 0, description: "a verdict with no sign of checking behind it, or praise in place of checks"}
passingScore: 1
samplingRate: 100
model: claude-opus-5-5
selfImprovement: true
---

You are given an exploration's log, its lead, and the review recorded of that lead before anything was opened. You are judging the review, not the lead.

A review that finds no holes can be a good review, and one that finds five can be a poor one. What matters is whether the reviewer did the work: checked the record before the argument, checked the lead's numbers against the receipts of the looks that produced them, looked for choices made after looking, and compared what the lead leans on with what the knowledge says. A review shows this by pointing: each thing it asserts names the file, the look or the log line that shows it.

Return `checked` when every assertion in the review, whether it is a hole or a statement that something holds, points at where it can be seen, and the review shows that the lead's central numbers and the order of its looks and choices were examined. Return `thin` when the review points at evidence for some of what it says and never examines the central numbers or the order of choices. Return `waved-through` when the review gives a verdict with nothing behind it, restates the lead, or praises it.

Use the log to test the review: where the review says a look reproduces or a choice came first, see whether the log agrees. Do not judge whether the lead later turned out true; you have not been given that, and a review is not better for having agreed with a result. Give the label, then for each assertion of the review whether it points at evidence and whether the log bears it out.
