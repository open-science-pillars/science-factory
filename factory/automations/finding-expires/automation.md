---
description: "When a signed page in the wiki passes its stale-after date, file a request to test it again."
wired: false                    # declared, not built: no trigger in this repository starts anything
stage: ask
agent: coordinating
triggers:
  - provider: schedule
    event: cron_fired
    schedule: {name: daily-stale-check, cron: "0 7 * * *"}
idempotency: [question, held-out-window]
---

Read the wiki's pages for a `stale_after` date that has passed (`tools/knowledge.py about` lists each page with who signed it). For each signed page that is past its date, write a request (templates/request.md) asking whether the page still holds, naming data that has arrived since as what could be held out, and hand it to the coordinating assistant.

You read knowledge and metadata only. You change no page: a page that is out of date stays as it is until a person decides.

This file is a declaration. Nothing in this repository runs a schedule; `wired: false` says so, and the validator refuses `true` until a trigger exists.
