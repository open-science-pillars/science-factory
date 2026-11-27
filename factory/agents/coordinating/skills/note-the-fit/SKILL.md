---
name: note-the-fit
description: "Write a short fit note when a request arrives, before any work starts: how well the question suits agents, a verdict (good-fit, fit-with-a-person-steering, poor-fit) and what taste or expertise it needs from a person. Advice to the person; it never blocks work."
---

# Note the fit

Agents do well on questions whose answer is exact or can be checked, whose data is at hand, and whose work is mostly computation. They do worse where the answer is a judgement, where the data has to be found or argued over, or where the hard part is knowing what matters. Say which this is, before work starts, so the person knows what they will have to bring. The note is advice: it never stops the work, and the person may disagree with it.

## 1. Read the request, and only the request

Read it in the scientist's own words. Do not look at any data to decide: a fit note is written from the question.

## 2. Answer five things

Copy `fit-template.yaml` beside this skill and fill it in:

- `answer_is`: `exact` (a number a rule can compare), `checkable` (a result someone can test against something else), or `a judgement` (what matters, what is interesting, what to believe).
- `data_at_hand`: `yes`, `partly` or `no`: is the data named and reachable, or does it have to be found first?
- `mostly`: `computation`, `reading` or `judgement`: where most of the work lies.
- `person_must_supply`: what only a person can give: the difference that matters, what they have already looked at, access, a decision.
- `verdict`: `good-fit`, `fit-with-a-person-steering` or `poor-fit`, and `why` in a sentence. A poor fit is an honest answer: say what would make it a better one.
- `taste_needed`: the taste or expertise the work will need from a person along the way: which instrument or process someone must know, which plots someone must look at, which result would be unremarkable to an expert.

## 3. Record it, and tell the person

`uv run tools/explore.py fit --exploration <x> --by <your name> --model <your model> --file <fit.yaml>` right after the exploration is started, or `uv run tools/sf.py fit --study <s> --by <your name> --model <your model> --file <fit.yaml>` right after the study is started. It is refused once the first look or test has run. Status shows it, the hand-over carries it, and the lock request shows it. Tell the scientist the verdict and what they will need to bring, in plain words.

## What this skill refuses

Deciding the question for the person, opening data to decide, and calling a poor fit a reason to stop: the person decides.
