# The system trial that runs from this repository alone

A system trial is a trial of the factory itself: one study through every stage on a synthetic record whose answer is sealed until the steward has decided. Its fresh data is a blind case the tool makes and seals at the opening. This folder holds the plan. Pairing (`methods/built-in-pairing/pair_records.py`) and the gain method (`methods/gain/`) are this repository's own, so every stage runs from a bare clone with no network.

**The record.** `methods/gain/test_cases.py` makes an invented river, a gauge reading it every fifteen minutes, and a second sensor passing about every ten days that sees it through a gain put in by hand; the same seed and gain give the same bytes. The question is whether the gain is within five percent of one; the method never sees the gain.

**A template; nothing is started here.** To run one yourself, with your own lock and signature, see `docs/FIRST-STUDY.md`. The blind test copies the plan into throwaway folders, runs each through every stage (tests, working data, a rehearsal, a lock labelled as the driver's, the opening, a finding, a review, the log check), then opens each seal and counts wrong verdicts:

```
uv run methods/gain/system_trial.py blind-test \
  --template examples/stand-alone/system-trial --n 20
```

It ends with `"wrong_verdicts": 0` and `"every_run_ready_for_signature": true` in about five minutes. With `--n 200` it counts the true and false cases supported, refuted and inconclusive; on its last run no verdict was wrong. The plan check alone is `uv run tools/sf.py check-plan --study examples/stand-alone/system-trial`.

**As a benchmark**, `uv run tools/benchmark.py run --suite factory/benchmarks/built-in-gain` runs this plan on six sealed cases, twice each, under two configurations, compared by the rule the suite states first. Two of its cases sit near the difference that matters (gains 1.03 and 1.08), which the blind test lacks.

**What it shows**: the study tool, gain method and pairing step hold together and reach right verdicts on kind cases. The driver's false cases sit at gains 0.90 and 1.10, twice the difference that matters; the evidence at that difference and on hard cases is in the known-answer tests. It says nothing about any real record or discipline's pairing script; `examples/baton-rouge` runs the plan with one such script.
