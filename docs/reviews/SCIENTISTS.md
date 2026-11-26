# The Science Factory from a scientist's chair

*History. The records this document cites (practice runs, study and exploration logs, receipts, drafted pages, the demo's runs) were removed from `main` and are at the branch `records-2026-11` of this repository; every path in it is as it was on the day it was written.*

*This review was written on 2026-11-25 in the package's earlier vocabulary and was put into the present words later the same day. Its findings, numbers and dispositions were meant to stay as they were. After the third review round a few sentences were corrected: the one about the word nobody said, which the rewording had emptied, was restored; the table of kinds was brought into line with the catalog; and sentences that called something done when it is convention or scheduled now say so. The original is not kept in this package. WORDS.md maps the earlier words to the present ones. README.md says where things stand now.*

**Open Science Pillars (OSP), a personal project (personal hat) · 2026-11-25 · a review by the people who would ask it questions, how they would ask, what else they would use it for, and how their own workflows come in.**

The rest of this package was written from the factory's side: stages, acts by people, study logs. This document turns the chair around. Three reviewers were each asked to stay in one role, read the package cold, and answer as that person would: a research hydrologist and oceanographer who runs a group and distrusts AI doing science; an applied scientist at a water and coastal agency who has to defend a decision to a board; and a postdoctoral modeler whose work is a 400 gigabyte pipeline on a cluster. They were language models playing roles, so this is a design review, not a user study, and the first real scientist to try it outranks all three. What they said was consistent enough to act on.

## The short version

A scientist does not arrive with an analysis plan. They arrive with a sentence, usually a suspicion about a thing they have already plotted. The factory as first drafted can only receive the analysis plan. Four things have to sit in front of it: a request in the scientist's own words, a short round of questions back that turns the request into a plan, a catalog of kinds of question wider than one number against one threshold, and a place for exploration that ends in something, namely a hypothesis written down in advance with data fenced off for it. None of that changes the study tool's discipline. It changes who can use it.

## How they actually ask

These are the reviewers' own requests, lightly trimmed. Nobody said "estimand", the word this package then used for the quantity estimated.

| Who | What they said | Kind of question |
|---|---|---|
| Researcher | "Does the Mississippi water budget close? And tell me which term eats the residual." | closure |
| Researcher | "The spectra south of the Agulhas look flatter in winter. No hypothesis yet, just poke at it." | exploratory |
| Researcher | "Is the subpolar North Atlantic still freshening after 2016, or is that float sampling?" | trend |
| Applied | "The board votes March 12 on retiring two gauges. Is the satellite within 10 cm of our gauge at release stages? Need it by end of February." | equivalence |
| Applied | "Can twenty years at the harbor gauge give a rate, or is it mush?" | trend, maybe unanswerable |
| Applied | "Which snow product would have given the better April 1 forecast? We pay for one." | ranking |
| Modeler | "Did heatwave days really go up after 2014 once mean warming is removed?" | difference between periods |
| Modeler | "Does my emulator beat damped persistence at 3 to 6 month leads, and where?" | forecast skill |
| Modeler | "The salinity residual near the plume looks weird after 2012. Dig around." | exploratory |

Every one has the same anatomy: a thing (a product, a budget, a place), a suspicion or a decision hanging on it, sometimes a threshold that comes from a rule the scientist lives under, sometimes a date, and very often no hypothesis at all. The request template (`mvp/templates/request.md`) asks for exactly that and nothing more.

## What the factory has to ask back

Across fifteen requests the reviewers each listed the fewest questions that would let an analysis assistant write a plan. They collapse to four, and an analysis assistant should ask these four and stop.

**What number would change what you do, and where does it come from?** The applied scientist's 10 centimetres comes from an operating rule; the researcher's "closed" means within combined uncertainty. This is the difference that matters, and it is the scientist's, not the factory's. The first draft of this package set its difference that matters from what the sample could resolve, and all three reviewers named that as a reason to distrust the result. The difference that matters has a source or the plan says it has none.

**What have you already looked at?** Nobody in the field has an unseen record. So the honest question is exposure: which years, places, products and versions this person and their group have plotted. Whatever they have touched is working data. What can still be fenced off is the next question's answer.

**What will you do with each answer?** Supported, refuted and inconclusive each need an action before the opening of the held-out data. "The board still votes" was the applied reviewer's point: an inconclusive result with no consequence written into the plan is useless to them. The modeler's version: what would you do with an answer at all? If nothing, it is exploration.

**By when, and who is on it?** A date makes the analysis assistant answer a question the first draft never asked: can this be answered in time, and what is the chance it comes back inconclusive at that difference? Known-answer tests on the real sampling give that number once a method exists to run them. And the plan carries its authors; the idea is theirs.

## Kinds of question, and what each needs

The study tool as built judges one scalar field against one threshold. That covers equivalence and direction. The reviewers' requests need the rest of this table. Each row says what a known-answer test means for that kind of question and where honest held-out data can come from, which is the part the reviewers were most inventive about. The same table, in a form an analysis assistant can read, is `mvp/templates/kinds-of-question.yaml`.

| Kind of question | Known-answer test | Honest held-out data |
|---|---|---|
| Equivalence, direction | a known gain or offset on the real sampling | the next window; a site never opened |
| Trend | a known trend with red noise at real sampling positions | an independent instrument over the same years; a later period long enough to move the rate |
| Difference between periods | surrogates with the mean changed and the variance not, then the reverse | a product never opened; future years |
| Threshold exceedance | events put in above and below the trigger | storms not yet compared |
| Closure of a budget | fluxes that close exactly on the real grid, then one term dropped | years a new release adds; otherwise it is an identity and belongs with the working data |
| Ranking of methods | a case where the baseline is optimal, then skill put in | sites or years no method was tuned on |
| Forecast skill | red noise where persistence wins, then predictability put in | forecasts issued now, scored on months not yet observed |
| Attribution of a residual | a cause put in among several candidates | usually none: this is exploration until it yields a claim |
| Exploratory, no claim | a feature put in that the diagnostics must find | fence something off first, then explore the rest |

Three things in that table are new to the design. A spatial holdout (basins, floats, reaches nobody has opened) is as good as a temporal one and far more available. A prospective holdout (forecasts issued now, verified later) is the cleanest of all. And a budget closure on a state estimate is an identity, not a discovery, so it is checked in the freely repeated tests and no opening of the held-out data is spent on it.

## Where the design loses them, and what changes

Fifteen objections, most made by more than one reviewer. Grouped, with what is done about each. "Convention" means a line in the request, or a key in the analysis plan that is there for people, which the study tool carries and does not check; "study tool" means code that is not written yet and is scheduled.

**Exploration has no home.** In the first draft exploring was something that happened to you: a second opening made your study exploratory. Papers start there. *Change (study tool, scheduled):* an exploratory study as a first-class kind. Its first act is to fence off a holdout; its product is a hypothesis card that names a kind of question, a difference that matters and the fenced data; its close starts the confirmatory study. Fence first, then explore.

**"Read by nobody" is almost never true.** *Change (convention now, study tool later):* the request declares exposure; the analysis plan names its kind of holdout (later window, unopened sites, a new release, a product never opened, prospective). The record of what has been opened is keyed by subject and window today and gains sites.

**One number against one threshold.** Spectra, maps and budget terms are fields. *Change (study tool, scheduled):* rule families with a multiplicity correction written into the plan, whose error rate is evidenced on known-answer tests like any other rule; run receipts (a run receipt is the record a run writes, with its code and inputs by checksum and every number it produced, so anyone can re-check the result without trusting whoever ran it; below, a receipt) carry scalar summaries the rules read plus the hash of the field they summarize, and the fields come back to the scientist as files.

**The difference that matters was sized to the sample.** *Change (convention now):* the line "The difference that matters, and where it comes from" in the request. Scheduled, not built: the plan stage reports the chance of an inconclusive answer at that difference, once a method exists to run the known-answer tests. That report is itself a product: several reviewers ranked "can this even be answered" among the most valuable things the factory could tell them.

**Deadlines against one opening and a thirty-day hold.** *Change (convention now):* the line "By when" in the request and a feasibility answer at the plan stage. The third-party policy holds public reference, not delivery to the person who asked; the build plan now says the requester receives the result at once, in the private clone. *Undecided:* a one-sitting path for questions that touch no third party and need no signed finding. The practice runs show the study tool's part takes minutes; the acts by people are the cost, and which may be merged for a low-stakes question is a steward's call, not a default.

**Inconclusive is useless without a consequence.** *Change (convention now):* the lines "What I will do with each answer" in the request, one action per outcome, written before the opening.

**Whose idea, whose signature.** The first draft had a requester who asks and a steward who decides. *Change (convention now, doctrine question):* the plan carries its authors; the requester is to approve the plan at the lock alongside the steward, because the difference that matters and the window are theirs (the tool records one person at the lock today, and the second approval is scheduled); and the finding says what the steward's signature attests (that the process was followed and the knowledge is sound) and what it does not (authorship). Whether a requester may steward their own study is a governance question for the organization.

**The language.** *Change (now):* the request is plain words in the scientist's units, and every result opens with one paragraph in those units. The quantity estimated, claim class and processing identifier stay in the analysis plan, where the analysis assistant wrote them.

**Known-answer tests written by the analysis assistant.** "I trust it if one hard case is mine." *Change (convention now):* the request asks the scientist for the one way they expect the method to be fooled, and that case goes among the required cases. It also splits the work the right way: the scientist knows how the data lies, the assistant knows how to generate it.

**Scale.** The modeler's five are precise and all correct against the code: an opening blocks on a subprocess, so a cluster walltime kill spends it; hashing reads whole files and the held-out data must be one file inside the study; code identity is files and a Python version, while results move with compiled dependencies; a typo fix in the analysis plan reruns every known-answer test; and two thousand cheap synthetic datasets is not what a perturbed model run looks like. *Change (study tool, scheduled as one deliverable):* submit and collect for an opening, with the job on the study log; data named by a manifest of locations and provider checksums, which is what gets hashed; the environment bound by commit plus lockfile or container digest; known-answer evidence bound to the rules, the code and a manifest of test cases instead of the whole analysis plan; small ensembles accepted with binomial bounds on the rates.

## Bringing a workflow in

Nobody will rewrite a pipeline for this. The reviewers described their real work (pull to the cluster, mask and integrate, argue over plots, bootstrap, figures, co-authors) and where it meets the factory. The meeting point is small, and it is the same four files whatever the science. `mvp/templates/workflow-adapter.md` is the checklist a coding assistant can follow in the scientist's own repository.

| The scientist adds | It must | Why |
|---|---|---|
| a fetch with two modes | return observation metadata alone, or everything, and write a manifest | so power can be computed before the opening, and so the opening reads only what the plan names |
| one run entry point | take a manifest, write a receipt, exit nonzero on failure | the same code for known-answer tests, seen data and the opening |
| a generator of test cases | write synthetic inputs in the real layout, on the real sampling, from a seed | known-answer tests; the values put in never reach the run |
| a runner for the known-answer tests | report error rates for the planned rule and echo the rule it tested | the lock refuses evidence for some other rule |

The receipt is the contract: what data it read (by hash), what code and environment ran, every number a rule reads as a finite number, the word `refused` when the method declines, and hashes of the fields it wrote. Everything else stays the scientist's: the notebooks, the cluster, the plotting.

What does not fit, and the reviewers were clear about it. The phone call to the hydrographer about an outlier is real science and has to become either a screen written beforehand or a note afterwards; it cannot happen between the opening and the answer. Choosing the evaporation product after seeing the residual is exploration and belongs in an exploratory study. "Which term is to blame" is attribution, which a pass or fail rule cannot carry. And a method fitted to products that were tuned to each other needs the independence statement to say so, in the finding, in plain words.

A workflow matures in four steps, and each is useful on its own: a notebook that someone can rerun; a script that writes a receipt; the same script with known-answer tests that show where it fails; an attested computation in a capability, with a golden and a gate.

## What else they would use it for

Asked what they would do with this beyond single findings, the three converged. In rough order of how much they said they would value it:

**A red team of my own draft before submission.** Known-answer tests against my method before a referee does it. The researcher ranked this first.

**Can this even be answered?** A power check before commissioning a study or buying a product: the plan stage alone, on observation metadata, with no opening of held-out data. The applied reviewer would use this more than the findings.

**Re-checks when a product is reprocessed.** Which published numbers moved. All three asked for it; it is the scheduled re-test, with the analysis plan reused.

**A standing monitor.** A residual or trend written into a plan, re-tested once a year without a student.

**A bake-off on blind test cases.** Algorithms, emulators, or a vendor's product before paying for it, with test years sealed so nothing leaks. The blind test of the system in this package is that mechanism pointed at the factory itself.

**A regression rig for my own pipeline.** The known-answer tests rerun on every dependency bump.

**Referee responses and audit trails.** A rerun under a locked plan; a decision that can be defended years later by someone who was not there.

**A register of dead ends and of gauge oddities.** What failed to close and why, and what the hydrographer knows, written down where it survives staff turnover. This is the knowledge factory, seen from the user's side.

Four of these need no opening of held-out data at all, which matters for adoption: a scientist can get value from the plan stage and the freely repeated tests on day one, before trusting the factory with a confirmatory claim.

## What they want back

Not a verdict word. A page that opens in their units; the interval and where it fails; the plot; the fields as files beside the receipt; a notebook or script they can rerun and match in their own environment; what was tried and dropped; for a decision, the action per outcome and an expiry date; and who signed what. They trust it when they can break it themselves, when one of the hard cases is theirs, when the difference that matters came from them before the data, and when it sometimes says it cannot tell. They distrust a "supported" that was predictable in advance, known-answer tests made of white noise, and an unseen window they have already plotted.

## What is scheduled

Two deliverables are added to the initiative (`roadmap-initiative.yaml`). `science-factory-scientist-intake`: the request, the four questions back, the catalog of kinds of question, the request's fields checked at the plan check, the exploratory study, and delivery to the requester during a hold. `science-factory-scale-adapter`: manifests, submit and collect, environment identity, rule families, ensemble-sized known-answer tests. A worked request for the first real study is in `mvp/studies/STUDY-0001/request.md`; reading it beside that study's analysis plan shows what the questions back have to produce.
