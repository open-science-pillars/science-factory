# The system trial that runs from this repository alone

A system trial is the trial of the factory itself: one study through every stage, on a synthetic record whose answer is known, with the answer sealed until the steward has decided. This folder holds its plan. The two records are paired by a pairing step of this repository's own (`methods/built-in-pairing/pair_records.py`) and the gain is estimated by the built-in method (`methods/gain/`), so the whole procedure can be exercised from a bare clone, with no network and nothing checked out beside it.

**The record and its answer.** The data is made by `methods/gain/test_cases.py`: an invented river, a gauge that reads it every fifteen minutes, and a second sensor that passes about every ten days and sees the river through a gain that is put in by hand. The question is whether that gain is within five percent of one. The method is given the two records and never the gain. Given a seed and a gain the record is the same bytes every time.

**It is a template, and nothing is started here.** To run a system trial as a person, with your own lock and signature, copy the plan into a study in a repository of your own; `docs/PLAN.md`, Part A, has every command. The blind test of the system copies the plan into throwaway folders and runs each copy through every stage (known-answer tests, working data, a rehearsal, a lock recorded by the harness and labelled as the harness, the one opening, a finding, a review, the log check), then opens each seal and counts wrong verdicts:

```
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 20
```

It ends with `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true`, in two to three minutes. With `--n 200` (about six minutes on the machine this was written on) it gives the result the documents cite: of 100 cases where the idea is true, 82 supported and 18 inconclusive; of 100 where it is false, 94 refuted and 6 inconclusive; no wrong verdict. The plan check alone is `uv run tools/sf.py check-plan --study examples/stand-alone/system-trial`.

**The same thing as a benchmark.** `uv run tools/benchmark.py run --suite factory/benchmarks/built-in-gain` runs this plan on six sealed cases, twice each, under two configurations of the factory's definition, and compares them by the rule the suite states before the run (`docs/CREATE-A-FACTORY.md`, under benchmarks). Its cases include two near the difference that matters, at gains of 1.03 and 1.08, which the blind test above does not have.

**What this shows, and what it does not.** It shows that the study tool, the gain method and the pairing step written here hold together and reach right verdicts on kind cases. The false cases sit at gains of 0.90 and 1.10, twice the difference that matters, and the harness chooses them; the evidence right at the difference that matters, and on hard cases, is in the known-answer tests. It says nothing about any real record or about the pairing script of any discipline. The optional demo (`examples/baton-rouge`) runs the same plan with one such script in the pairing step's place.
