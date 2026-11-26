# Two ways of working: exploring and confirming

**Open Science Pillars (personal hat) · 2026-11-25 · how scientists actually work, what the factory does for each way, and why the two are kept apart.**

A scientist works in two ways, and most days in the first. **Exploring** is looking at data to find out what is there. **Confirming** is testing one claim that was stated before the data that tests it was seen. Methodologists call them hypothesis-generating and hypothesis-testing research. Both are real science. The trouble starts only when a result found the first way is reported as if it had come from the second.

Status, plainly. The factory has built the confirming way: five stages, a study tool, tests. The exploring way is used throughout the practice runs but has no stages or tool support of its own yet; what is written about it here is the design.

## Exploring: most of the work

This is what a scientist does with a new dataset, a new question or a result that looks odd: plot it, compare it with another record, try a method, see where it breaks, change it, look again. It runs the way software work runs: try, look, revise, and ask a colleague to pick holes in it. Nothing about that loop needs to be slowed down or locked, and an assistant is at its most useful inside it.

What exploring produces:

- an understanding of the data: how it was sampled, where it is unreliable, which flags matter;
- pitfalls, written down as notes, which become shared knowledge once a steward signs them;
- a method, with the choices made while building it;
- a **lead**: something that looks true and is worth testing.

What exploring cannot produce is a tested claim. Every choice made after looking (which passes to drop, which model to fit, which period to show) was made knowing how the answer would move, and the count of things tried is usually forgotten. A lead found this way is right more often than chance and less often than it feels.

The one rule for exploring is to say that it was exploring. The factory's part is to make that easy and to keep exploring from spending the data a later test will need:

1. **Set data aside first.** Before anything is looked at, decide what will not be looked at, and let the access gate hold it. Everything else is working data, to be used freely.
2. **Explore freely.** On working data, and on synthetic data with a known answer, as often as wanted. Review and revision run in both directions, as in software.
3. **Write down the lead and the choices.** What looks true, how it was found, what was tried on the way, and which choices would change the answer if made differently.
4. **Hand the lead to the confirming way,** or stop. A lead that is not worth a test is still worth recording, and so is a method that did not work.

## Confirming: when a claim is to be signed

When a lead is going to be written down as a finding that others will rely on, it is tested once on data nobody has opened. That is the five stages of this package: ask, plan, test on known answers, open the held-out data once, then review, sign and learn. Between the tests and the opening, people lock the plan and the code together.

None of this is new. The same shape appears wherever a field has needed its results to hold:

- **Clinical trials** finish the statistical analysis plan before the data is unblinded, and mark any analysis thought of afterwards as exploratory.
- **Particle physics and cosmology** use blind analysis: every analysis decision is finished and every program debugged before the result is shown to the people doing the analysis.
- **Preregistration**, in psychology and beyond, writes the question and the analysis plan down before the outcomes are observed, so that testing can be told apart from exploring.
- **Hydrology** has the split-sample test: calibrate a model on one period and test it on another it has not seen, with harder versions for another basin and for contrasting conditions.
- **Earth observation** defines validation as assessing a product by independent means, and counts a product's validation in stages that are repeated when a new version is released.
- **Machine learning** learned that a held-out test set which is checked again and again while the method is tuned stops being a test.

Formal locking of this kind is still rare in Earth science. Validation against independent data is everyday practice; a plan locked before the comparison is not. So the factory does not ask that every piece of work pass through the confirming way. It asks it of claims that are to be signed.

## The wall between them

Data that was used to explore cannot be used to confirm what the exploring found. That is the whole wall, and everything else follows from it:

- Working data and held-out data are named in the plan, and only the access gate fetches the held-out data.
- The held-out data is opened once. If the result is inconclusive, that is the result for that data; the next chance is the next data held out.
- After the opening, a review can send back the write-up, never the analysis. A change to the analysis after the opening makes the study an exploration again, and it is recorded as one.

Ways to hold data out, with the names hydrology already uses where it has them:

| Hold out | Known as | Suits |
|---|---|---|
| a later period | the split-sample test | most questions about a record that keeps growing |
| sites or basins never opened | the proxy-basin test | whether a method travels |
| a period of contrasting conditions | the differential split-sample test | whether a method holds when conditions change |
| a new release of the product | re-validation on a new version | a claim about a product |
| a different instrument or record | independent validation | agreement between products |
| forecasts scored later | prospective testing | predictions |

When nothing can be held out, because there is one record and all of it has been seen, the alternative is to hide the answer and not the data: shift or scramble the quantity of interest by an amount nobody in the analysis knows, finish every decision, then remove the shift. That is blind analysis. It is not built here.

When data keeps arriving and the question is whether something has changed, the test has to be one that may be read as each batch comes in. Trials do this with interim analyses planned in advance. Here it is the watching study, proposed in `proposals/watching-studies.md` and not built.

## Beside the software loop

| | Exploring | Confirming | Software |
|---|---|---|---|
| Revise after review | yes, freely | only before the lock | yes, freely |
| What a person approves | nothing is locked | the plan and the code, before the opening | the spec, then the merge |
| What ends it | a lead, a note, or a stop | a signed finding or a recorded no | a merged change |
| What is scarce | attention | held-out data | time |

Exploring is the software loop. Confirming is the software loop up to the lock, and after that it runs once.

## Sources

- Nosek, Ebersole, DeHaven and Mellor, "The preregistration revolution", PNAS 2018: https://pmc.ncbi.nlm.nih.gov/articles/PMC5856500
- MacCoun and Perlmutter, "Blind analysis: Hide results to seek the truth", Nature 2015: https://www.nature.com/articles/526187a.pdf
- Klemeš, "Operational testing of hydrological simulation models", 1986, as described in Nicolle and others, HESS 2021: https://hess.copernicus.org/articles/25/5013/2021/hess-25-5013-2021.pdf
- The CEOS validation hierarchy, Land Product Validation subgroup: https://lpvs.gsfc.nasa.gov
- NASA Earthdata, data maturity levels: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-maturity-levels
- Dwork and others, "Generalization in adaptive data analysis and holdout reuse", 2015: https://arxiv.org/abs/1506.02629
- "Not all pre-registrations are equal", 2022: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9630412/
- "Registered Report for climate research", editorial, Nature Climate Change 2024: https://www.nature.com/articles/s41558-024-01932-4
- A confirmatory trial protocol stating that its analysis plan is finished before unblinding: https://cdn.clinicaltrials.gov/large-docs/84/NCT02287584/Prot_000.pdf
