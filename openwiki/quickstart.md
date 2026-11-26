---
type: quickstart
spheres: []
generated: { by: claude-code/claude-fable-5-2, at: 2026-11-26T08:00:00Z }
status: draft
---

# Quickstart: the wiki of this repository

This wiki holds what is known about the small synthetic record that the stand-alone example explores (`examples/stand-alone`). Three pages:

- [the-two-sensor-record.md](the-two-sensor-record.md): what the record is and where it comes from.
- [compare-changes-not-levels.md](compare-changes-not-levels.md): a pitfall. The level difference between the sensors is mostly an unsurveyed offset.
- [flagged-readings.md](flagged-readings.md): a pitfall. A degraded reading can steer a fitted gain.

How to read it. Use the `openwiki_search` and `openwiki_read` tools when you have them; otherwise read these files, or run `uv run tools/knowledge.py about --question "..." --wiki openwiki`, which lists the pages that bear on a question with each page's status and who signed it.

What a page is worth. Every page here is working memory at status draft. None is signed: a page is signed only when its own `verified` lines name a person, and only a person adds those. Use a draft, say that it is a draft, and check it against your data before leaning on it.

Assistants do not write into this directory. What they learn goes to a queue of drafts beside the work, in the same form, and a page enters the wiki only when a person accepts it.
