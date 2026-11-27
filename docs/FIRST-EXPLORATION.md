# Your first exploration

An exploration by hand, in about ten minutes, on the synthetic record this repository ships (`examples/stand-alone/record-2024.json`: two sensors on one river, one year). An agent runs the same commands under its own name, following `factory/agents/analysis/skills/`. [HOW-IT-WORKS.md](HOW-IT-WORKS.md) says why.

Three people take part, since whoever explores may neither name the reviewer and hand over, nor review. They can be colleagues, or the coordinating and review agents.

## 1. A folder, the data, and your request

Run everything from the top of a clone. uv refuses its own settings when set and empty (`UV_NATIVE_TLS=`): unset them.

```
W=$(mktemp -d)
mkdir -p $W/data $W/explorations $W/studies
cp examples/stand-alone/record-2024.json $W/data/
printf '# Request\n\nHow closely does the second sensor follow the reference, and where does it not? Only 2024 has been looked at.\n' > $W/request.md
X=$W/explorations/EXPLORATION-1
ME=human:YOUR-ID
COORDINATOR=human:A-COLLEAGUE
REVIEWER=human:ANOTHER-COLLEAGUE
M=
```

Put your id in `ME` and your colleagues' in the other two. `M`, the model, stays empty for a person; for agents give their names (such as `agent:coordinating`, `agent:review`) and their model.

## 2. Read what is known

```
uv run tools/knowledge.py about --question "How closely does the second sensor follow the reference?" --wiki openwiki
```

Read the pages it lists before anything else. Here all are drafts, signed by nobody.

## 3. Propose the fresh data, and set it aside

Choose the data that will check what you find before you look, from a description of the data, never the data:

```
uv run tools/fresh_data.py propose --metadata examples/stand-alone/metadata.yaml \
  --kind later-period --from 2025-01-01 --until 2025-12-31 \
  --what "the whole of 2025, both sensors" \
  --why "only 2024 has been looked at, and the same two sensors keep running" \
  --unfair "a change of either sensor or its processing at the new year" \
  --by $ME --out $X/fresh-data.yaml --studies $W/studies
```

It prints the proposal in words, with the test size the metadata allows (12 months, 52 passes). Start the exploration, setting aside exactly that:

```
uv run tools/explore.py start --exploration $X --id EXPLORATION-1 --by $ME \
  --question "How closely does the second sensor follow the reference?" \
  --request $W/request.md --subject record=two-sensor,sensor=second \
  --how "a later period" --set-aside-window 2025-01-01:2025-12-31 \
  --why "the following year; only 2024 has been looked at" \
  --boundary-from openwiki/the-two-sensor-record.md \
  --working "the 2024 record" --working-window 2024-01-01:2024-12-31 \
  --working-data $W/data --fresh-data $X/fresh-data.yaml
```

From here on 2025 is not looked at by any route; the tool refuses a look that names it.

Before the start the coordinator wrote `fit.yaml` from `factory/agents/coordinating/skills/note-the-fit/fit-template.yaml`: a verdict (`good-fit`, `fit-with-a-person-steering`, `poor-fit`) and what the work needs from a person. It is advice, blocks nothing, and is recorded now, before the first look:

```
uv run tools/explore.py fit --exploration $X --by $COORDINATOR --model "$M" --file fit.yaml
```

## 4. Record what you read

```
uv run tools/explore.py known --exploration $X --by $ME --wiki openwiki
uv run tools/explore.py read --exploration $X --by $ME \
  --concept compare-changes-not-levels.md --takes "fit with an intercept: the mounting offset is not surveyed"
```

The first look is refused until a page is recorded as read. Add `--depth skimmed` for a page only skimmed.

## 5. Look, as often as you like

Each look is a script run through the tool, with a reason:

```
uv run tools/explore.py look --exploration $X --by $ME --why "the gain of the second sensor on the reference" \
  -- uv run $PWD/examples/stand-alone/looks/gain.py $W/data/record-2024.json
uv run tools/explore.py look --exploration $X --by $ME --why "the same, without the degraded readings" \
  -- uv run $PWD/examples/stand-alone/looks/gain.py $W/data/record-2024.json --exclude-flag-at-or-above 2
```

Each prints the gain and is logged by checksum. A look sees only itself and the files its command names; your own scripts go in `$X/looks/`.

## 6. Record the choice you made

```
uv run tools/explore.py choice --exploration $X --by $ME --choice "leave out readings flagged 2 or above" \
  --alternative "keep every reading" --rests-on "the wiki page on flagged readings" --look LOOK-002
```

The tool notes that this was written down after two looks, and the lead will say so. Record a choice before the look it governs when you can.

## 7. Write up the lead, and have it reviewed

The coordinator names the reviewer first; the lead is refused until then:

```
uv run tools/explore.py reviewer --exploration $X --by $COORDINATOR --model "$M" --reviewer $REVIEWER
```

Write the lead from `factory/agents/analysis/skills/write-up-a-lead/lead-template.yaml`, quoting numbers exactly as the looks printed them:

```
cat > $X/lead.yaml <<'LEAD'
summary:
  looks_true: "Over 2024 the second sensor looks to follow the reference with a gain of 1.0281, degraded readings left out."
  how_strong: "Two looks at one year of one pair of sensors; the flag screen was chosen after the first."
  cannot_settle: "Whether the gain holds in 2025, which was set aside, or for another pair of sensors."
what_looks_true: >
  Over 2024 the second sensor looks to follow the reference with a gain of 1.0281
  once the readings flagged 2 or above are left out (50 of 52 readings kept).
how_it_was_found: >
  A least-squares line with an intercept, first on every reading, then without the degraded ones.
evidence: [LOOK-001, LOOK-002]
choices_that_would_change_it:
  - {choice: CHOICE-001, how: "keeping every reading moves the gain; LOOK-001 shows it"}
choices_that_would_not: []
pitfalls:
  - "levels are not comparable, only changes: the wiki page on comparing changes"
proposed_plan:
  question: "In 2025, is the gain of the second sensor on the reference within five percent of one?"
  quantity_estimated: "the gain, by least squares with an intercept, after the flag screen"
  difference_that_matters: "nobody has stated one; five percent is proposed here, for the scientist to decide"
  rule_sketch: "supported if the interval lies inside 0.95 to 1.05, refuted if it lies outside; anything else is inconclusive"
  hard_cases: "degraded readings at low stage; an offset step inside the year"
  what_this_could_not_show: "anything about another pair of sensors"
LEAD
uv run tools/explore.py lead --exploration $X --by $ME --model "$M" --file $X/lead.yaml
```

A lead quoting a number no look printed is refused. The tool writes `lead.md`, whose first line says it is a lead, not a finding, with the summary on top for whoever says so what. The reviewer reads the lead, the log and the looks, writes the holes, and records a verdict on the lead as it stands:

```
SHA=$(uv run tools/explore.py status --exploration $X | python3 -c "import json,sys; print(json.load(sys.stdin)['lead_json_sha256'])")
printf '# Review\n\nChecked every number against LOOK-001 and LOOK-002.\nHoles: the choice was written down after the looks; one year only.\n' > $X/review/review.md
uv run tools/explore.py review --exploration $X --by $REVIEWER --model "$M" --verdict holes-found --file $X/review/review.md --read-lead $SHA
```

Answer each hole by looking again and revising, or by writing it in as a limit. A revised lead is reviewed again.

## 8. The so what: is it worth confirming?

A reviewed lead is often right and unremarkable, so a person who knows the field says so what. The coordinator may draft `question.yaml` from `factory/agents/analysis/skills/write-up-a-lead/so-what-question.yaml`; the answer is never an agent's:

```
uv run tools/explore.py ask-so-what --exploration $X --by $COORDINATOR --model "$M" --file question.yaml --read-lead $SHA
uv run tools/explore.py so-what --exploration $X --by $ME --answer worth-confirming --read-lead $SHA --local-practice
```

Other answers: `try-instead --direction "..."` (explore that way, then review and ask again), `not-interesting --reason "..."` (it ends as a lead noted), `needs-an-expert --expertise "..."`. Typed, a so what is practice. On GitHub it is a tracking-issue comment whose first lines are `so-what: worth-confirming`, `exploration: explorations/EXPLORATION-1` and `lead: ` with the first 16 characters of `$SHA`; the workflow records it and asks GitHub who wrote it.

## 9. End, and hand over

```
uv run tools/explore.py end --exploration $X --by $ME --model "$M" --outcome lead --summary "the gain looks close to one with degraded readings left out"
uv run tools/explore.py hand-over --exploration $X --by $COORDINATOR --model "$M" --study-id STUDY-1 --local-practice
```

Both are refused until a person said `worth-confirming` on the lead as it stands; `--local-practice` says the so what was typed. The hand-over writes into `$X/hand-over/` the request for a confirming study, a plan stub and a copy of the fresh-data proposal, and prints the `sf.py start` command; [FIRST-STUDY.md](FIRST-STUDY.md) goes on from there. An exploration may also end as a note, a method, a stop or a lead noted, all honest. A look worth keeping becomes a method with `explore.py promote` ([CREATE-A-FACTORY.md](CREATE-A-FACTORY.md)); the stand-alone example promotes `looks/gain.py`.
