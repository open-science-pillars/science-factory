# Bringing a workflow into the factory

*A checklist for a coding assistant (an AI agent) working in the scientist's own repository. Nothing here asks for a rewrite: it adds four entry points around the pipeline that already exists. It has not yet been tried on a pipeline from outside; that is scheduled.*

**1. A fetch with two modes.** `fetch --window W --fields metadata` returns only observation metadata: values that cannot move the answer whatever the withheld values turn out to be, given that every choice in the analysis is already fixed. Times, positions, masks, grids, quality flags and processing identifiers usually pass that test. Whether an independent record belongs in this mode is decided for each plan and written into it; where that record is what the product is scored against, it does not belong. `fetch --window W --fields withheld` returns everything, the withheld values included. Both write a manifest: where each input lives and its checksum. The metadata mode may be run before the lock. The withheld mode is to be run only by the access gate, which is a step of the study tool. In your own repository nothing but that rule stops anyone running it: the tool cannot see a fetch made outside it.

**2. One run entry point.** `run --inputs MANIFEST --out RECEIPT` is the whole analysis, and what it writes is a run receipt (item 3). It is the same command for known-answer tests, for working data (data already seen) and for the one opening of the held-out data. It exits nonzero when it fails. A long job submits and waits.

**3. The run receipt.** The record the run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it. It is one JSON file (called a receipt below):
- `data.sha256`: the checksum of the file the fetch wrote at the plan's held-out data path. The tool checks that one file today and nothing it points to: when the file is a manifest, the inputs it lists are not checked (checking by manifest is scheduled)
- the code commit and the environment (lockfile or container digest)
- every number a decision rule in the analysis plan reads, as a finite number, at the field path the plan names
- `refused`, with a reason, when the method declines to estimate
- the handling the plan wrote down beforehand that it applied (screens, tolerances) and what each removed
- checksums and locations of the fields it wrote, so maps and spectra come back as files

**4. A generator of known-answer test cases.** `test-cases --seed S --put-in NAME` writes synthetic inputs in exactly the layout `run` reads, on the real sampling, from known parameters (a modeler would call it a twin experiment). The values put in are never visible to `run`: write them to a separate file that `run` is not given. Include the case where the idea is true, cases right at the difference that matters on both sides, a case where it is far from true, each way the data is known to lie (the hard cases), and the one the scientist named in the request.

**5. A runner for the known-answer tests.** It runs the test cases through `run`, reports how often the interval covers the value put in and how often the plan's decision rule is right, at the true value and right at the difference that matters on both sides, and echoes the rule it tested as `tested_rule`. The plan's criteria (pass or fail thresholds on those rates) read the runner's receipt by field name. The study tool requires four of them of every rule and refuses the lock when the receipt misses one: `false_confirm_at_edge_max`, `false_refute_at_edge_max`, `power_to_refute_when_false` and `coverage_when_true`. Test cases that cost a model run are a small ensemble with a stated bound on each rate; the tool does not read such bounds yet (scheduled).

**6. The analysis plan.** Copy `mvp/templates/analysis-plan.yaml`, which explains every key the tool reads, to `analysis-plan.yaml` in the study directory, and run `sf.py check-plan`. Roots that point at this repository; the subject (`pair`) and the window; `withheld_values` and `observation_metadata` listed apart; the test commands above; one rehearsal that runs the fetch and the run end to end on working data.

**What stays the scientist's.** Notebooks, the cluster, plotting, co-authors. **What has to move.** Any judgment made after seeing the answer becomes a screen written into the plan beforehand or a note raised afterwards.
