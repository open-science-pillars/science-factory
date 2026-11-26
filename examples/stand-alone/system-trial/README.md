# The system trial that runs from this repository alone

A system trial is the trial of the factory itself: one study through every stage, on a synthetic record whose answer is known, with the answer sealed until the steward has decided. `studies/STUDY-0000` is the one planned for people to run, and it borrows one script from the hydrology capability: the step that pairs the two records. This folder holds the same plan with that one script replaced by a pairing step of this repository's own (`methods/built-in-pairing/pair_records.py`), so that the whole procedure can be exercised from a bare clone, with no network and nothing checked out beside it.

**The record and its answer.** The data is made by `methods/gain/test_cases.py`: an invented river, a gauge that reads it every fifteen minutes, and a second sensor that passes about every ten days and sees the river through a gain that is put in by hand. The question is whether that gain is within five percent of one. The method is given the two records and never the gain. Given a seed and a gain the record is the same bytes every time.

**It is a template, and nothing is started here.** The blind test of the system copies this plan into throwaway folders and runs each copy through every stage (known-answer tests, working data, a rehearsal, a lock recorded by the harness and labelled as the harness, the one opening, a finding, a review, the log check), then opens each seal and counts wrong verdicts:

```
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 20
```

It ends with `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true`, in two to three minutes. The plan check alone is `uv run tools/sf.py check-plan --study examples/stand-alone/system-trial`.

**What this shows, and what it does not.** It shows that the study tool, the gain method and the pairing step written here hold together and reach right verdicts on kind cases. It is not the blind test whose result is kept in `studies/exhibits/blind-test-200.json`, and it does not stand in for it: those 200 cases, and every known-answer number in the practice runs, were made with the hydrology capability's own script, and the checks that reproduce them still need that capability beside this repository. On ten test cases the two pairing steps give the same pairs and the same scores (`uv run methods/built-in-pairing/pair_records.py --selftest --compare-with <the hydrology script>`), which is a comparison on ten cases and not a proof that they are the same computation.
