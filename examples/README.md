# Examples

Examples are inputs and recipes. No run is kept: each makes its run fresh, in a scratch folder outside the repository.

**`stand-alone/`** runs from a bare clone with nothing but `uv`. On a small synthetic record whose answer is known, it proposes the fresh data from a description of the data, explores, drafts what it learned into a queue for the wiki, and takes a study through its tests to the lock. It is the tools driven from the command line with every step checked; no agent runs in it. `stand-alone/system-trial/` holds the plan of a system trial, on which the blind test of the system runs. The checks on GitHub run all of it.

**`baton-rouge/`** is optional: an example of pointing the factory at another repository. A hydrology repository kept elsewhere supplies the knowledge and the pairing script for one river gauge; the page has the commands to run it, and a summary of what was found when separate agents ran it in November 2026. It needs that repository, and the knowledge format's checker, checked out beside this one. Nothing in the tools, the agents, the skills or the checks depends on it.
