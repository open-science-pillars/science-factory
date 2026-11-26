# Instructions for assistants working in this repository

The roles of the science factory are the files in `assistants/`; read the one you were started as. Run every tool with `uv run`.

<!-- OPENWIKI:START -->
## The wiki

This repository keeps its knowledge base as a wiki in `openwiki/`: Markdown pages in the Open Knowledge Format v0.2, read as files. Start at `openwiki/quickstart.md`. When the tools `openwiki_search` and `openwiki_read` are available, use them: search first, then read the pages that bear on the question. Otherwise read the files, or run `uv run tools/knowledge.py about --question "..." --wiki openwiki`.

Do not write into `openwiki/`. A page there is working memory unless its own `verified` lines name a person. What you learn goes to a queue of drafts beside the work (`factory/agents/curating/skills/draft-a-knowledge-page`), and a person decides what enters the wiki.
<!-- OPENWIKI:END -->
