# Curating EXPLORATION-0101: answer from `agent:curating-0101`

I read the six open notes, lead version 3, REVIEW-001, the receipts the notes and the lead rest on, and the signed pages of `../hydrology/knowledge` that bear on them. I drafted four pages into `examples/baton-rouge/with-assistants/knowledge-queue/gotchas/`, linked one note and declined one. I signed nothing, wrote nothing into the knowledge base, and set no status other than `draft`. `knowledge.py check-drafts` passes with the organization's checker named (`../nasa-daac-knowledge/tools/check_okf_v02.py`: 0 errors, 4 warnings, all W4 "unverified", which is what a draft is). `explore.py curation-list` now shows 0 open notes and `check-log` passes (59 events).

I did not open `examples/baton-rouge/explorations`, the other `knowledge-queue`, `record` or `studies` directly under `examples/baton-rouge`. No network was used.

## What I drafted

All four are type `dataset-gotcha`, status `draft`, `seen_while: exploring`, with no `verified` key, and each says in its first paragraph that it is one reach, one year, one working file, untested and unsigned.

| Page | From | What it says | Relation to signed pages |
|---|---|---|---|
| `gotchas/swot-reach-q-values-undefined-and-never-zero.md` | NOTE-005, part of NOTE-002 | A census: `reach_q` is 1 on 49 of 52 passes, 2 on 3, never 0 (LOOK-013; the Version C block also has no 0, LOOK-001). The bundle gives no meaning for any value on a river reach. | extends `datasets/swot-river-lake.md`; beside `datasets/swot-lakes.md`, the recipe and the reach and node gotcha |
| `gotchas/swot-gauge-change-scores-carried-by-two-passes.md` | NOTE-002 | On the recipe's own 50 pairs, two passes carry 0.912 of the summed squared departure; change RMSD 0.3823 m with them, 0.1043 m without (LOOK-004, LOOK-017). List passes by name before reading a summary score. No screen proposed. | **narrows** `recipes/swot-gauge-confrontation.md` and `gotchas/hydrocron-collection-default.md`; beside two others |
| `gotchas/swot-reach-against-point-gauge-distance-reads-as-gain.md` | NOTE-006 | A reach height against a point gauge carries slope times distance; in 2024 the product slope rose 3.179 ppm per metre of stage on 46 pairs, so each km reads as 0.0032 of gain (LOOK-015). The recipe's 0.44 km does not say between which points. | extends the recipe and `gotchas/swot-reach-node-scope.md`; beside two others |
| `gotchas/swot-gauge-baton-rouge-fixture-lacks-processing-fields.md` | NOTE-001 | The fixture keeps eight fields per pass: no CRID, cycle, pass, `xovr_cal_q` or random uncertainty parts; gauge readings only within 60 minutes of a pass, as few as two (LOOK-001, LOOK-009, LOOK-013). | extends the recipe; beside three others |

No draft says `contradicts`. Two say `narrows`, and the steward should read those first:

- The change scores page does not dispute any number in the signed recipe (LOOK-003 reproduces them exactly). It narrows the recipe's reading "the disagreement is not explained by the stated precision: the RMSD is about four times it": on this file that ratio is 4.0 with all pairs and 1.1 with two passes left out by date.
- The same page narrows the signed collection default gotcha: the lower end of the Version D range it quotes for this reach (-0.534 m) is the single pass of 2024-10-30, about 2 m below the gauge; the next lowest paired height is 1.295 m. Its point that Versions C and D differ by metres stands.

Sources are the look receipts (repository path plus the receipt's sha256), REVIEW-001 where the reasoning is the reviewer's, and the signed pages. One external document is named, the LakeSP product description the signed lakes page cites, and its source title says I did not read it and that it describes lakes, not rivers.

## What I kept out of the pages, on purpose

- **No meaning for any flag value.** The reach_q page does not call 1 "suspect" or "good". It states the lake ladder as the lakes page's, for the lake flag, and says no source read carries it to reaches. From my own recollection I believe the river product description gives a ladder; I did not write it, because no page or document available here says it.
- **No statement that the flag or the stated uncertainty marks, or fails to mark, bad passes.** That rests on two departing passes and three flagged ones in one year at one reach. The reach_q page gives the four counts under "what this page does not claim", as an example for a steward.
- **No screen and no threshold.** The 0.2 m limit on `wse_u`, the cuts on `dark_frac` and slope, and every two part rule of LOOK-016 are each fitted to one or two passes.
- **No gain.** 1.0140 appears once, on the distance page, labelled as the untested lead's and "for scale only", beside the four fits that this year cannot tell apart.
- **No cause for either gross pass**, no rate of gross passes, no claim about low water or high water, no rising against falling difference, no track effect. These are the lead's.
- **The confounding of stage, time and slope in one year** is a pitfall in the lead. I did not make it a page: it is about how to analyse this comparison, it has no source beyond the lead's own fits, and it belongs in the plan for the confirming study.

## What I linked or declined

- **NOTE-003, linked** to `connectors/usgs-water.md`. The signed page itself states its `stale_after` (2026-11-01), why it sits there and the one year depth of the continuous collection. Nobody probed the host, so a draft would have no source. The page needs a steward, not a new page.
- **NOTE-004, declined.** A bad grouping key inside one look, replaced in LOOK-011. The null result (no track stands out) is three groups of 15 to 17 passes in one year, already in the lead. Why the key was needed (no pass number in the file) is on the fixture page.

## What a steward must decide

1. **The meaning of `reach_q` for RiverSP reach Version D**: the value ladder, any bitwise flag behind it, and which fields say a reach was partly observed. From the river product description, into `datasets/swot-river-lake.md`. Until then no screen for the confirming study can be written from the knowledge. This is the lead's first prerequisite.
2. **What the recipe's "0.44 km apart" joins**, and the along-river distance and direction from the gauge to the point the reach height refers to, from SWORD and the site file. Whether to amend the signed recipe.
3. **Whether the recipe's worked example should say its RMSD is carried by two passes**, and whether the collection default gotcha should say its Version D minimum is one departing pass. Both pages are signed; I edited neither.
4. **Whether the fixture page is a knowledge page or an issue** on `verification/fixtures/fetch_confrontation_fixtures.py` (refetch with CRID, cycle, pass, `xovr_cal_q`, the bitwise flag if there is one). I drafted it because the recipe's worked example and any confirming study run on that file; it is the weakest of the four as knowledge.
5. **`connectors/usgs-water.md` is past its `stale_after`** (NOTE-003): re-check the legacy host and the continuous collection's depth, and re-sign or amend.
6. **Two things seen in the bundle while reading**, not from any note: `gotchas/swot-lake-identity-across-passes.md` carries a `verified` event by a person and `status: draft` at once; `gotchas/swot-gauge-datum-mismatch.md` is an unsigned draft that the signed recipe's reasoning leans on in the lead.
7. **The two gross passes** (2024-10-30 and 2024-03-26) and what the flag and stated uncertainty did on them stay with the lead as a note for the steward and the scientist. Whether the gauge has been revised since the retrieval of 2026-09-08 is also open.

## Friction with the role file, the skills and the tools

- **Who I am.** I was told to act as `agent:curating-0101`. The organization's checker refuses that as `generated.by` (E8 wants `harness/model` or `process:`); the skill says "you, as the platform names you" and its template shows `claude-code/MODEL`. I wrote `generated.by: claude-code/fable-5-2` and put `curating: "agent:curating-0101"` inside `drafted_from`, an extra key nothing checks. `resolve --by` takes the `agent:` form. Two namings for one actor.
- **"The receipt's path in the repository at a commit."** This repository is not under version control, so there is no commit. I gave the repository path and put the receipt's sha256 in the source title. The checker accepts any non-empty `resource`.
- **Sources that are bundle pages.** I followed the bundle's own convention (`../datasets/swot-lakes.md`), which resolves only after a merge into `gotchas/`, not from the queue. Neither checker tests it.
- **No tool checks that a statement has a footnote** or that a footnote's source supports it. `check-drafts` passed on the first run, including a footnote I had mislabelled and a sentence citing the wrong receipt, both of which I found by rereading. The skill's rule "every statement carries a footnote" rests on the drafter.
- **The overlap check asked for nothing.** I declared sixteen relations by reading; the tool would have passed with fewer. It cannot tell `narrows` from `contradicts`, as its own help says, so that judgment is mine and should be reviewed.
- **Role file step 1 and the queue's location.** `writes` says `knowledge-queue/*.md`; the task put the queue under `with-assistants/`. `resolve` writes into the exploration log and `curation-list` writes `curation-list.json` in the exploration, neither of which is in `writes`, though both are in `may_call`. This answer file is also outside `writes`; I wrote it because the coordinating assistant asked.
- **`linked` has no fixed form for `--ref`.** I gave the path below the bundle (`connectors/usgs-water.md`). For `declined` there is no ref and the reason lives only in `--comment`.
- **A stale signed page has no route.** A note of kind `stale` can only be drafted, linked or declined. I linked it to the page that is stale, which records it and prompts nobody.
- **One thing per page against one file.** NOTE-001 holds two things (missing satellite fields, sparse gauge readings). I kept them on one page as "what the working file does not carry"; a stricter reading would split them or drop the second.
- **The role points at `openwiki/` and `openwiki_*` tools**, which do not apply to this bundle; `knowledge.py about --wiki ../hydrology/knowledge` worked. Its ranking is by shared words: the question about reach to gauge distance returned an NLDI page first.
- **Dates.** The system clock and the notes read 2026-11-26 UTC while the session's stated date is 2026-11-25. I used the clock for `generated.at`.
- **A leak, for completeness.** The lead declares that `mvp/gain.py`, `mvp/confront.py` and the example README had told the analyst about the two passes and the screen. I opened none of those. It is one more reason the pages carry no screen and no gain as fact.
