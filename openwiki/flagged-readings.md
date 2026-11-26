---
type: pitfall
spheres: []
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T08:00:00Z }
status: draft
---

# Flagged readings of the second sensor

The second sensor in the two-sensor record carries a quality flag: 1 is good, 2 is degraded. The flag is a gate, not a size of error: a degraded reading may be fine or may be far off, and its value does not say which.

Leave out readings flagged 2 before comparing the sensors, and say how many were left out. Give the result both ways when the difference is large, because one degraded reading at the end of the range can steer a fitted gain.
