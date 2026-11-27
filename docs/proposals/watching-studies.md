# Proposal: studies that keep watching, and choices that expire


This says which parts of the process plugin belong in the science factory, and under what names. The process plugin was designed in August and September 2026 as a layer with two ideas, decision records and standing hypotheses, and a companion bench of seeded experiments. It is read here from its design notes; its repositories are not in the organization.

## What the factory lacks that the process plugin has

**A way to look more than once.** The study tool refuses more than one opening of a test, because an ordinary test that is checked again and again raises false alarms far above its stated rate. The bench measured it: a daily test on pure noise raised a false alarm 37.4 percent of the time, where a running test held at 2.9 percent. So today a scheduled re-test is a series of separate studies, each with one opening on a new window, and a standing monitor has no honest method at all. The process plugin's standing hypothesis is that method.

**A record of the choices inside an analysis, and of when each stops being true.** The lock fixes every choice, but the plan does not say which choices matter, what each one rests on, or when it lapses. A finding today has no expiry of its own.

## What folds in, and what it is called here

| In the process plugin | Here | What it is |
|---|---|---|
| standing hypothesis | **watching study** | a kind of study whose held-out data arrives over time; each new batch is opened once, as it arrives |
| e-process, e-value, anytime-valid inference | **running test**, **evidence so far** | a test whose false-alarm rate holds however often it is checked and whenever it stops (statisticians call it anytime-valid) |
| wake, the wake gate | **arrival**, **the check before each opening** | before a new batch is opened the tool re-checks what the plan assumed |
| drift classification | **what changed since the last opening** | nothing; the data was revised; an assumption no longer holds. The plan says which of these continues, pauses with a note, or stops |
| decision record | **analysis choice** | one entry in the plan per fork: the choice, the alternatives, what it rests on, who may change it, when it expires |
| binds, data pinning | **rests on** | the data and versions a choice depends on, by checksum, as the tool already binds inputs |
| take, flag, ask | **the assistant decides; decides and notes; asks a person** | who may make a choice |
| expiry | **expires when** | the event that ends a choice's validity; a finding lapses with the choices it rests on, and that is what calls for a scheduled re-test |
| fork axes, the sweep, the flip condition | **sensitivity to choices** | the alternatives are run on the known-answer tests and the working data before the lock, and the review is told the smallest set of choices that would flip the answer |
| many hypotheses at once | **many questions at once** | one stated false-alarm rate across sites or rules |
| budgeted stopping | **stopping rule** | stop for evidence, for no prospect of evidence, or for budget, all written before the lock |
| the analysis ledger | the study log | already here |

## What does not fold in

The plugin's skills and hooks, which are packaging for one assistant app. The request and its four questions already do the eliciting; packaging the front door is a later question. The demonstration project and the bench stay as test material.

## Why the two belong together

The bench's own review said it in one sentence: a running test without recorded choices can be gamed, and recorded choices without a running test cannot hold a standing question honestly. In the factory's words: a running test is honest only if every choice in it was locked before the first batch was opened, and a lock is useful over time only if the test may be read as data arrives. The factory supplies the lock, the access gate and the record of what has been opened. The process plugin supplies the test.

## What it would take

1. **The plan.** `study_kind: watching`; a rule that is a running test, with how it handles serial correlation and its false-alarm rate; what one batch is; the stopping rule; the analysis choices, each with what it rests on and when it expires.
2. **The tool.** The lock binds the running test. Each opening takes one new batch and never recomputes an earlier one. The log check recomputes the evidence so far from the run receipts. Status reads "watching", with the evidence so far beside the threshold.
3. **Known-answer tests, required before the lock.** The bench's three lessons become criteria: the false-alarm rate under repeated looks when nothing is there; the same under realistic serial correlation (an uncorrected running test raised a false alarm 85 percent of the time on such data, and correcting it brought that to 4.1 percent after a long warm-up); and how long the study must watch to detect the difference that matters, printed for the people locking. That last number can be years, and people should see it before they commit.
4. **Sensitivity to choices** on the working data, reported to the review.
5. **A review round** by independent reviewers before any watching study on a real product.

Until this is built, the tool keeps refusing more than one opening of a test.
