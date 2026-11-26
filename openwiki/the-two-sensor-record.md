---
type: dataset
spheres: []
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T08:00:00Z }
status: draft
---

# The two-sensor record of the stand-alone example

The stand-alone example ships a small synthetic record, `examples/stand-alone/record-2024.json`, made by `examples/stand-alone/make_record.py` from a fixed seed. It has one row a week for 2024 with a time, a reading from a reference sensor (`reference`), a reading from a second sensor (`sensor`), and a quality flag for the second sensor (`flag`, 1 for good and 2 for degraded).

The record has a known answer, written in the script that makes it: the second sensor moves by a fixed gain for every unit the reference moves, sits a fixed offset above it, and carries a little noise. The exploring loop is expected to come close to that gain. The script can also make the following year. The example sets that year aside before it looks at anything and never makes it.

Both sensors measure the same level. The offset between them is a mounting height that nobody surveyed, so see the page on comparing changes and not levels. Some rows are flagged; see the page on flagged readings.
