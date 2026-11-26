# Examples

| Folder | What it is | What it needs |
|---|---|---|
| `stand-alone/` | The exploring loop and the knowledge loop run end to end on a small synthetic record with a known answer, reading the wiki in `openwiki/`. It is the tools driven from the command line with every step checked; no assistant runs in it. The checks workflow runs it. | Nothing but this repository and `uv`. |
| `baton-rouge/` | A demo: the factory used with skills, knowledge and data from elsewhere in Open Science Pillars. Two questions about SWOT river height and width at Baton Rouge, taken through the roles, with the whole record kept. | The `hydrology` and `nasa-daac-knowledge` checkouts beside this repository (README.md, "Try it"). Nothing in the tools, the roles, the skills or the checks depends on it. |
