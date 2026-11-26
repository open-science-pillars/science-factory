# Analysis assistant: answer on request 1 (exploring)

By `agent:analysis-0101`. Exploration: `examples/baton-rouge/with-assistants/explorations/EXPLORATION-0101`. Everything here is exploring; nothing is a finding. Status now names the review assistant, so I stopped. The exploration is not ended (the skill says to end only after the review is answered).

## What I set aside, and why

Everything from 2025-01-01 onward, as one open window ("a later period"), recorded with `explore.py start` before I read the knowledge or opened any data. The record is in `with-assistants/studies/openings.jsonl`, inside this folder. Reason: the request says only calendar 2024 has been seen and nothing later downloaded, and a later period on the same reach and gauge is what a test of this lead would use. I took the widest honest window because the role file has me set aside before reading, while the skill says the boundary is a fact to read from the knowledge. After reading, the signed `datasets/swot-lakes.md` gave a processing boundary inside the window (reprocessing PGD0 to 2025-04-27, forward processing PID0 from 2025-04-28). I did not narrow the window. That leaves about four months of held-out data on the same processing as 2024 and the rest on the newer processing, so a test can tell a change of year from a change of processing. I fetched, read and asked about nothing in the window; the fence refused nothing.

## What I read

`explore.py known` listed 12 pages of `../hydrology/knowledge`; I read all 12 whole plus `gotchas/nwis-provisional-data.md` (not listed, but the recipe leans on it), and recorded each with `explore.py read`. Eleven listed pages are signed by human:PaulMRamirez; `gotchas/swot-gauge-datum-mismatch.md` is NOT signed (a draft). `gotchas/swot-lake-identity-across-passes.md` is signed but carries status draft. No drafts queue was given to me, so none was read.

What changed the work: the signed recipe `recipes/swot-gauge-confrontation.md` rules in pairing within a stated tolerance and scoring changes, rules out scoring the level, and already holds the 2024 all-pass scores for this pair; `gotchas/hydrocron-collection-default.md` (signed) says to name the collection; `datasets/swot-river-lake.md` (signed) says flags are gates and elevation against a gauge is a real confrontation; `datasets/swot-lakes.md` (signed) gives the processing dates. Three pages (lake identity, groundwater, the model recipe) did not bear on the question.

## What I found (leads only, on data already looked at)

12 looks, 0 failed, 0 refused. Numbers below are from look receipts.

- The shipped executor, unmodified, reproduces the recipe exactly: 50 of 52 paired, change RMSD 0.3823 m, correlation +0.9567 (LOOK-003).
- Two passes carry 0.912 of the summed squared departure from the median difference (LOOK-004). 2024-10-30: lowest stage of the year, reach_q 2, ordinary wse_u (0.095 m), 1.776 m low. 2024-03-26: high water, reach_q 1, wse_u 0.296 m, dark_frac 0.692, 0.947 m high. The gauge is smooth around both and the neighbouring passes are ordinary (LOOK-012), so they look like satellite departures.
- Gain of satellite on gauge: all 50 pairs 1.0345 [1.0034, 1.0656], not inside 0.95 to 1.05; reach_q below 2: 1.0190 [0.9968, 1.0412]; reach_q below 2 and wse_u below 0.2 m: 1.0140 [1.0043, 1.0236] on 46 pairs, residual scatter 0.0815 m against a median stated uncertainty of 0.0957 m, change RMSD 0.1051 m (LOOK-005, LOOK-010).
- Where it does not follow: the two passes above; the flag catches one of them and flags two good passes. By stage, the lowest third sits lower against the gauge than the rest (-0.0594 m against +0.0402 m and +0.0287 m, LOOK-007), which is the gain a little above one. Not by track (LOOK-011), not by pairing rule (LOOK-009).

## Choices I made

Six, recorded as made: (1) the set-aside window, before looking; (2) 15-minute nearest pairing, as the recipe; (3) reading "within about five per cent" as a gain inside 0.95 to 1.05, chosen after seeing that the recipe's RMSD over spread (0.3197) could never meet five per cent; (4) the screen, reach_q below 2 and wse_u below 0.2 m, whose wse_u limit was set after seeing the one pass it removes; (5) a straight line with no time or slope term; (6) treating the two passes as satellite departures. The lead puts (3), (4), (5) and (6) among the choices that would change it, with the numbers for each alternative that was run.

## What I could not settle

- Why the gain sits about 1.4 per cent above one. A time term brings it to 1.0094, a reach-slope term to 1.0048 (plain standard error 0.0085); slope and stage are correlated at +0.876, so instrument, gauge position in the reach and drift cannot be separated on one year.
- Whether 2024 is all one processing: the file has no CRID, cycle, pass number, xovr_cal_q or bitwise flag (NOTE-001). I took it from the signed lakes page.
- What reach_q 2 means for a river reach, and why two flagged passes are fine. No page says (NOTE-002).
- Whether the screen generalises: it is tuned on one pass, and an unflagged gross error with an ordinary stated uncertainty would pass it.
- The gauge is provisional throughout 2024.

Notes raised: NOTE-001 (missing fields in the fixture), NOTE-002 (the signed recipe scores all passes and says nothing on screening; for the steward), NOTE-003 (`connectors/usgs-water.md` is past its stale_after of 2026-11-01), NOTE-004 (dead end: a split by pass minute in LOOK-010).

## What was unclear, wrong or in the way

- **A leak, which matters most.** I was told to do this fresh and not to read the earlier run's folders, and I did not. But `examples/baton-rouge/README.md` (which sits beside the request) and the docstring of `mvp/confront.py` both state the earlier run's main results: the set-aside date it chose, its gain, and that one flagged low-stage pass and one unflagged high pass depart. I read both while orienting, before any look. My looks found the same passes by name, but not blind. The lead says so. A fresh run needs those two texts kept away from the analysis assistant.
- **Order of set-aside and reading.** The role file says set aside before anything is looked at, then read what is known. The skill says the boundary is a fact to read from the knowledge. They only fit together through the skill's fallback (widest honest window). It would help for the role file to say that outright, and to say whether a window may be narrowed after reading (the tool offers no way; I assumed no).
- **Where to end.** The role file's step 6 reads as "`lead`, then `end`"; the skill says do not end before review. Status settled it (it names the review assistant after `lead`), and my task said to stop there.
- **`--subject`.** "As a plan's `pair` will say it" required reading the plan template to guess the keys. I used reach, gauge and product; I do not know whether `check-study` will match on exact text.
- **`may_call` and the shipped executor.** The skill says to use the method the capability ships. Running `load_swot_confrontation.py` through `explore.py look` is allowed as a look, but the executor is not in my `may_call` list and neither is `describe_record.py`; I read both as scripts run by `look`, not as tools called.
- **`explore.py known` matches by shared words**, so it listed the groundwater connector and lake pages and missed `nwis-provisional-data.md`, which the recipe depends on. Reading the pages a page points at caught it.
- **The lead's number check is useful and has an edge**: a number quoted from a knowledge page (the recipe's distance between reach and gauge) cannot appear in a lead unless some look prints it, so I left it out.
- **Paths.** Look commands run in the exploration directory, five levels down; I used absolute paths for the data and the skill's script. The skill's example (`<path to>/skills/...`) does not say which is expected. The fence also means a lead or script should avoid writing dates inside the set-aside window, so the lead names the processing boundary by its page and not by its date; nothing told me that, I inferred it from the tool's help.
- `uv` prints a deprecation warning for `UV_NATIVE_TLS` on every call; harmless noise.
