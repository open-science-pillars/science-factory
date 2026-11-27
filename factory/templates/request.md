# Request

*One page, in your own words and your own units. The analysis agent (an AI agent) turns it into a plan, and you see the plan before anything is locked. Leave a line empty if you do not know. The agent asks you four questions about the lines marked "asked back", and then stops. On GitHub this page is an issue form (`.github/ISSUE_TEMPLATE/request.yml`), and the issue becomes the study's tracking issue.*

*The study tool binds the finished request to the study by checksum (`sf.py start --request`), so it cannot change unnoticed after the lock. It checks nothing inside it.*

**What I want to know.** One to three sentences, as you would say it to a colleague. A suspicion is fine. "No idea yet, just look" is an honest answer too: it asks for exploring, which ends in a lead, a note, a method or a stop, never in a finding.

**The thing.** The product, record, budget, model or place this is about, with versions if you know them.

**Why it matters.** The decision or the paper this feeds.

**The difference that matters, and where it comes from** (asked back). The number that would change what you do. For example "within 10 cm, from our release rule" or "a residual under the combined uncertainty". If nobody has stated one, say so.

**What I have already looked at** (asked back). Years, places, products and versions you or your group have plotted or fitted. This is the one thing only you know. Everything here is treated as already seen.

**Data I have not looked at** (leave empty if unsure). A later period, a site you have not touched, a product you have never loaded, a release not yet out. You do not have to find it: an agent proposes the fresh data for the check, from descriptions of the data only, with its reasons, and you approve it when the plan is locked.

**What I will do with each answer** (asked back).
- If it holds:
- If it does not:
- If it cannot tell:

**By when** (asked back). A date, or none.

**How I expect it to be fooled.** The one thing about this data that trips people up. It becomes a hard case the method must survive in the known-answer tests.

**Who is on it.** Authors, and who should approve the plan with the steward at the lock. The lock is a pull request; the repository's code owners say who may approve it.

**What I want back.** A page, a plot, fields as files, a script to rerun, a memo for a manager.

**Anyone else's product involved?** If the answer says something about a named provider's product, the result goes to you privately at once, and to the provider before any public reference.
