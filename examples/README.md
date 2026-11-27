# Examples

Examples here are inputs and recipes. No run is kept: each example makes its run fresh, in a scratch folder outside the repository.

| Folder | What it is | What it needs |
|---|---|---|
| `stand-alone/` | The example that runs from a bare clone. The exploring loop and the knowledge loop run end to end on a small synthetic record with a known answer, reading the wiki in `openwiki/`; then a study is taken through its tests to the lock. It is the tools driven from the command line with every step checked; no agent runs in it. It leaves what it made in a scratch folder and prints where, so you can see what an exploration and a study look like on disk. `stand-alone/system-trial/` holds the plan of a system trial for the confirming loop, and the blind test of the system runs on it. The checks workflow runs all of it. | Nothing but this repository and `uv`. |
| `baton-rouge/` | An optional demo, as a recipe: the factory pointed at another repository's knowledge and data for one river gauge, with the commands to run it yourself with separate agents, and a summary of what was found when it was run in November 2026. The record of that run is at the branch `records-2026-11`. | The `hydrology` and `nasa-daac-knowledge` repositories checked out beside this one. Nothing in the tools, the roles, the skills or the checks depends on it. |
