# Request

*Written for this example by the assistant that built it, in the voice of a river scientist. No person asked this: it stands in for a request so that the assistants have something real to work on. The data and the knowledge it points at are real.*

**What I want to know.** How well does SWOT river height follow the Baton Rouge gauge, and where does it not? No hypothesis yet beyond "probably well at high water". I want to know what is there before I decide what is worth testing.

**The thing.** SWOT RiverSP reach water surface elevation for the Mississippi reach at Baton Rouge (reach 74210000331), Version D, against the USGS gauge there (USGS-07374000).

**Why it matters.** I am deciding whether the reach product can stand in for stage on reaches that have no gauge. If it follows a good gauge here, that is the first thing I would want to test properly.

**The difference that matters, and where it comes from.** Nobody has stated one. If I had to say: the satellite should rise and fall with the gauge to within about five percent before I would use it as a stage record. That is my judgment, not a requirement.

**What I have already looked at.** Calendar 2024 only: the fixture the hydrology repository keeps (swot_gauge_baton_rouge_2024.json). I have plotted it.

**Data I have not looked at.** Nothing after 2024: I have not downloaded or looked at any of it.

**What I will do with each answer.**
- If it holds: write it up as a lead and ask for a proper test on the later data.
- If it does not: I want to know where it breaks, by stage and by quality flag.
- If it cannot tell: say so and say what would tell.

**By when.** No date.

**How I expect it to be fooled.** The two are on different vertical references, so a level difference means little. And I suspect the bad passes are not random: low water, or whatever the quality flag catches.

**Who is on it.** Me. The repository's steward for anything that would be signed.

**What I want back.** A page: what looks true, where it does not hold, what you chose along the way, and what you would test.

**Anyone else's product involved?** Yes: SWOT RiverSP is a named mission product.
