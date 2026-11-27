# Instructions for agents working in this repository

The factory is defined in `factory/` (`factory.yaml` and the folders beside it; `docs/CREATE-A-FACTORY.md` says what each is). Each agent is defined by a file `factory/agents/<name>/agent.md`; read the one you were started as. Run every tool with `uv run`. Every command you run with `--by agent:<name>` also takes `--model`: the name of the model you run as. Say it truthfully; the log records it and nothing checks it.

You do not edit anything in `factory/`: a change to the definition is a person's pull request, checked by `uv run tools/check_factory.py`. You never make a lock or a signature: each is a pull request a person approves and merges. An agent may write the request (`sf.py request-lock`, `sf.py request-signature`) and nothing more, and never types a person's name. An act in a study log has a standing (`practice`; `merge found, people not verified`; `verified`): say which, in the tool's words, and never say people approved an act that is not `verified`. `docs/WHAT-IS-ENFORCED.md` says which of these rules a tool holds and which rest on you. You never read the acceptance set of blind cases, a folder named `acceptance-cases`, or any file that holds its seed. You choose fresh data from metadata only (`tools/fresh_data.py propose`, the skill `propose-fresh-data`), never by opening data.

<!-- OPENWIKI:START -->
## The wiki

This repository keeps its knowledge base as a wiki in `openwiki/`: Markdown pages in the Open Knowledge Format v0.2, read as files. Start at `openwiki/quickstart.md`. When the tools `openwiki_search` and `openwiki_read` are available, use them: search first, then read the pages that bear on the question. Otherwise read the files, or run `uv run tools/knowledge.py about --question "..." --wiki openwiki`.

Do not write into `openwiki/`. A page there is working memory unless its own `verified` lines name a person. What you learn goes to a queue of drafts beside the work, as the skill `draft-a-knowledge-page` says, and a person decides what enters the wiki.
<!-- OPENWIKI:END -->
