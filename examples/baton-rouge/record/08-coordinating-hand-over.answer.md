Done as far as an assistant may go. It stops at the tests, short of the lock.

- `explore.py hand-over` wrote hand-over/request.md, analysis-plan.stub.yaml and hand-over.json for STUDY-0002.
- `sf.py start` started examples/baton-rouge/studies/STUDY-0002 from that request, bound by checksum.
- `explore.py check-study` first refused: no plan yet. The analysis assistant wrote analysis-plan.yaml (the package's first study asks the same question, so the method, tests and criteria are taken from it, with the lead's limits added). `sf.py check-plan`: complete. `explore.py check-study`: pass, the held-out window is inside what the exploration set aside and none of it was explored.
- The analysis assistant ran `sf.py test known-answers` and `sf.py test working-data`: both pass (working data: gain 1.0121 on 47 pairs, the number the lead already had, which is why it is working data).
- `sf.py status` says stage `test`, still needing the two rehearsals. Both need the provider's network (the rehearsal of the fetch) or a file in the hydrology repository that is not there yet, so they were not run. After them comes the lock, which is a person's.
- I asked for the lock once, to show what happens: the role file does not allow it and the command was not run.

Waiting for people: the scientist to confirm the five percent, the rehearsals where there is a network, then the lock by the scientist and the steward. The steward also has two drafts in the queue, one of which says it contradicts a signed recipe. EXPLORATION-0002 has one open note for the curating assistant.
