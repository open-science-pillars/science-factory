---
type: pitfall
spheres: []
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T08:00:00Z }
status: draft
---

# Compare how two sensors move, not where they sit

When two sensors measure the same level from different mounting heights, the difference between their readings is mostly the mounting offset, and nobody surveyed it. A level difference is therefore not an error of either sensor and should not be called a bias.

What can be compared without knowing the offset is how they move: the gain (how much the second sensor moves when the reference moves by one), fitted with an intercept that takes up the offset, or the changes from one reading to the next.

Do: fit the gain with an intercept and report it with how many readings went in. Do not: subtract one sensor from the other and report the mean.
