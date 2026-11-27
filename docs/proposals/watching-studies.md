# Proposal: studies that keep watching, and choices that expire

*Proposed; nothing here is built. Until it is, the study tool refuses more than one opening of a test.*

Two ideas the factory lacks. Both came from an earlier design of a layer for running analyses over time, read here from its notes, and they are named here in the factory's own words.

## What the factory lacks

**A way to look more than once.** The study tool refuses a second opening of a test, because an ordinary test checked again and again raises false alarms far above its stated rate. In seeded experiments of that earlier design, a daily test on pure noise raised a false alarm 37.4 percent of the time, where a running test held at 2.9 percent. So today a scheduled re-test is a series of separate studies, each with one opening on a new window, and a standing monitor has no honest method at all.

**A record of the choices inside an analysis, and of when each stops being true.** The lock fixes every choice, but the plan does not say which choices matter, what each rests on, or when it lapses. A finding today has no expiry of its own.

## What it would be

| Idea | Here | What it is |
|---|---|---|
| a standing question | **watching study** | a study whose fresh data arrives over time; each new batch is opened once, as it arrives |
| anytime-valid inference | **running test**, **evidence so far** | a test whose false-alarm rate holds however often it is checked and whenever it stops |
| a check on arrival | **the check before each opening** | before a new batch is opened, the tool checks again what the plan assumed |
| drift | **what changed since the last opening** | nothing; the data was revised; an assumption no longer holds. The plan says which continues, pauses with a note, or stops |
| a choice on record | **analysis choice** | one entry in the plan per fork: the choice, the alternatives, what it rests on, who may change it, when it expires |
| pinning | **rests on** | the data and versions a choice depends on, by checksum, as the tool already binds inputs |
| who may choose | **the agent decides; decides and notes; asks a person** | who may make a choice |
| expiry | **expires when** | the event that ends a choice's validity; a finding lapses with the choices it rests on, and that calls for a re-test |
| sensitivity | **sensitivity to choices** | the alternatives are run on the known-answer tests and the working data before the lock, and the review is told the smallest set that would flip the answer |
| many at once | **many questions at once** | one stated false-alarm rate across sites or rules |
| stopping | **stopping rule** | stop for evidence, for no prospect of evidence, or for budget, all written before the lock |

## Why the two belong together

A running test without recorded choices can be gamed, and recorded choices without a running test cannot hold a standing question honestly. In the factory's words: a running test is honest only if every choice in it was locked before the first batch was opened, and a lock is useful over time only if the test may be read as data arrives.

## What it would take

1. **The plan.** `study_kind: watching`; a rule that is a running test, with how it handles serial correlation and its false-alarm rate; what one batch is; the stopping rule; the analysis choices, each with what it rests on and when it expires.
2. **The tool.** The lock binds the running test. Each opening takes one new batch and never recomputes an earlier one. The log check recomputes the evidence so far from the run receipts. Status reads "watching", with the evidence so far beside the threshold.
3. **Known-answer tests, required before the lock**: the false-alarm rate under repeated looks when nothing is there; the same under realistic serial correlation (an uncorrected running test raised a false alarm 85 percent of the time on such data, and correcting it brought that to 4.1 percent after a long warm-up); and how long the study must watch to detect the difference that matters, printed for the people locking. That last number can be years, and people should see it before they commit.
4. **Sensitivity to choices** on the working data, reported to the review.
5. **A review round** by independent reviewers before any watching study on a real product.

On GitHub the arrival of a batch would be an Actions trigger (`on: schedule`, or a `data-release` label on an issue) that opens the next opening's request; it would never open the data itself.
