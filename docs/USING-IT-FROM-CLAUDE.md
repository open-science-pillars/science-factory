# Using it from Claude

`tools/factory_server.py` lets you ask the factory in plain words from your own Claude session. It is a Model Context Protocol server whose tools each wrap a command of `tools/`, so it gives the command line's answer and names that command. Nine tools read (what waits on you, where work stands, a lead and its reviews, a figure, the report, the fit note, who did what, the wiki, the definition's version and validity); three take in work (your request, the fresh data proposed from metadata, the start of an exploration). What it refuses is row 1.33 of [WHAT-IS-ENFORCED.md](WHAT-IS-ENFORCED.md). Claude has not called it yet; it has run by hand over standard input.

## In Claude Code

The repository's `.mcp.json` names the server `factory`, with the repository as its one workspace, beside the wiki server. The harness writes that file (`uv run factory/harnesses/claude-code/render.py`; `--check` fails when it drifts), so a study repository's copy gets it too. Open the repository in Claude Code and approve the project's servers. Rendered agents are not given these tools.

## In Claude Desktop

Add the server to Claude Desktop's configuration file (Settings, Developer, Edit Config) with absolute paths, one `--workspace` for each repository where your science lives, and restart it:

```json
{
  "mcpServers": {
    "science-factory": {
      "command": "uv",
      "args": ["run", "--script", "/home/you/my-science/tools/factory_server.py",
               "--workspace", "/home/you/my-science",
               "--workspace", "/home/you/other-science",
               "--wiki", "/home/you/my-science/openwiki"]
    }
  }
}
```

If `uv` is not found, give its full path as `command`. A workspace is named by its folder. One with its own `factory/` is served with it only when every file there a tool could run is the server's own; otherwise the server does not start, and you start one from that workspace's own tools.

## Five things you might type

**"What is waiting on me?"** The agent calls `waiting`: each item, since when, and the exact step or the GitHub page to open.

**"Where does EXPLORATION-1 stand, and what did the reviewer find?"** It calls `lead`: the summary block, each review's verdict and whether it read the lead as it stands, and, when the lead waits for your so what, the lines to write on the tracking issue and its address.

**"Show me the figures behind that lead."** It calls `figure` for the list, then each by look and checksum, with its caption, and asks you to look yourself.

**"Does the second gauge drift in summer? We have only looked at 2023 and 2024."** It writes your request in your words (`submit_request`), describes the data from its date column and proposes a later period as the fresh data (`propose_fresh_data`), and shows you what would make it unfair. When you agree, it starts the exploration with that set aside (`start_exploration`).

**"Is our definition valid, and what has the factory done?"** It calls `factory_summary` and `report`.

Standings come in the tools' words: with a read token in the server's environment an act is asked of GitHub now; without one the answer says what git shows and that an earlier answer is not re-checked now.

## Why your acts are not tools

The so what, the lock and the signature each say that a person decided, and they are worth something because GitHub, not a typed name, says who decided. A tool the agent could call would let a conversation make them, and the agent would be typing your name. So no tool records, prepares or verifies one, opens fresh data, promotes a method or changes the definition; where you must act, the answer gives you the page where you act yourself.
