# Examples

| Folder | What it is | What it needs |
|---|---|---|
| `stand-alone/` | The exploring loop and the knowledge loop run end to end on a small synthetic record with a known answer, reading the wiki in `openwiki/`. It is the tools driven from the command line with every step checked; no assistant runs in it. The checks workflow runs it. `stand-alone/system-trial/` holds the plan of a system trial for the confirming loop that needs nothing beside this repository, and the blind test of the system runs on it. | Nothing but this repository and `uv`. |
| `baton-rouge/` | A demo: the factory used with skills, knowledge and data from elsewhere in Open Science Pillars. Two questions about SWOT river height and width at Baton Rouge, run twice: by separate assistants, each started from its role file (`with-assistants/`), and earlier by one instance playing every role. Both records are kept, with a working hydrologist's review of the earlier one and what the comparison shows. | The `hydrology` and `nasa-daac-knowledge` checkouts beside this repository (README.md, "Try it"). Nothing in the tools, the roles, the skills or the checks depends on it. |
