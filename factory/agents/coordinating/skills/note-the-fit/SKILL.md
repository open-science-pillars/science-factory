---
name: note-the-fit
description: "Write a short fit note when a request arrives, before any work starts: how well the question suits agents, a verdict (good-fit, fit-with-a-person-steering, poor-fit) and what taste or expertise it needs from a person. Advice to the person; it never blocks work."
---

# Note the fit

Agents do well where the answer is exact or checkable, the data is at hand and the work is mostly computation; worse where the answer is a judgement or the hard part is knowing what matters. Say which this is before work starts, from the request alone, without opening data, so the person knows what they will have to bring.

Copy `fit-template.yaml` beside this skill and fill it in: `answer_is` (`exact`, `checkable`, `a judgement`), `data_at_hand` (`yes`, `partly`, `no`), `mostly` (`computation`, `reading`, `judgement`), `person_must_supply` (what only a person can give), `verdict` (`good-fit`, `fit-with-a-person-steering`, `poor-fit`) with `why` (for a poor fit, what would make it better), and `taste_needed` (which process someone must know, which plots someone must look at, which result an expert would find unremarkable).

Record it right after the start: `uv run tools/explore.py fit --exploration <x> --by <your name> --model <your model> --file <fit.yaml>`, or `uv run tools/sf.py fit --study <s> --by <your name> --model <your model> --file <fit.yaml>`. It is refused once a look or test has run. Status, the hand-over and the lock request show it. Tell the scientist the verdict and what they will need to bring. A poor fit never stops the work: the person decides.
