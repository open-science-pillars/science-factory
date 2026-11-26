#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""wiki_server: a read-only server for a wiki directory, with the two tool names OpenWiki uses.

It speaks the Model Context Protocol over standard input and output and
offers exactly two tools, both read-only, both local, neither calling a
model:

  openwiki_search   ranked, compact results for a query: for each page its
                    path, title, status, who signed it and why it matched
  openwiki_read     a page in full, or one section of it by heading

There is no tool that writes, and the server opens no file outside the
wiki directory it was started on. The search is knowledge.py's `about`,
so the server and the command line give the same answer.

Why it exists. The OpenWiki tool is described (its repository's README,
as relayed to this project) as serving a wiki through two read-only tools
of these names. An assistant whose instructions say "use openwiki_search,
then openwiki_read" can then be given either that tool's server or this
one. What is this project's guess: the arguments (`query` and `limit`;
`path` and `section`) and the shape of the results. The real tool's may
differ; this was not run against it.

Usage: wiki_server.py --wiki DIR      serve (newline-delimited JSON-RPC 2.0 on stdin and stdout)
       wiki_server.py --selftest
"""
import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # the server loads knowledge.py from beside it and leaves no bytecode folder in the package

HERE = Path(__file__).resolve().parent
PROTOCOL = "2024-11-05"
TOOLS = [
    {"name": "openwiki_search",
     "description": "Search the wiki. Returns the pages that bear on a query, best first, each with its path, title, status and who signed it. Read-only.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "the question or words to search by"},
                                                     "limit": {"type": "integer", "description": "how many pages at most (default 8)"}},
                     "required": ["query"]}},
    {"name": "openwiki_read",
     "description": "Read one wiki page in full, or one section of it. Read-only.",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "description": "the page's path below the wiki, as search returns it"},
                                                     "section": {"type": "string", "description": "a heading of the page; omit for the whole page"}},
                     "required": ["path"]}},
]


def knowledge():
    spec = importlib.util.spec_from_file_location("knowledge", HERE / "knowledge.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge"] = mod
    spec.loader.exec_module(mod)
    return mod


def search(wiki: Path, query: str, limit: int = 8) -> str:
    k = knowledge()
    try:
        found = k.about(query, [wiki], limit=max(1, min(int(limit or 8), 25)))
    except k.Refused as r:
        return f"no search: {r}"
    if not found:
        return "nothing in the wiki bears on this query. That is a result: say so."
    lines = []
    for c in found:
        rel = Path(c["file"]).relative_to(wiki.resolve()).as_posix()
        signed = "signed by " + ", ".join(c["signed_by"]) if c["signed"] else "NOT SIGNED: working memory"
        lines.append(f"{rel} | {c['title']} | status {c['status'] or 'not stated'} | {signed} | {c['why']}")
    return "\n".join(lines)


def read(wiki: Path, path: str, section: str | None = None) -> str:
    root = wiki.resolve()
    f = (root / str(path)).resolve()
    if not f.is_relative_to(root) or not f.is_file() or f.suffix != ".md" or any(part.startswith(".") for part in f.relative_to(root).parts):
        return f"no such page in the wiki: {path}"
    text = f.read_text(encoding="utf-8")
    if not section:
        return text
    want = " ".join(str(section).casefold().split())
    lines, out, level = text.split("\n"), [], None
    for ln in lines:
        m = re.match(r"^(#+)\s+(.*?)\s*$", ln)
        if m and level is None and " ".join(m.group(2).casefold().split()) == want:
            level = len(m.group(1))
            out.append(ln)
        elif m and level is not None and len(m.group(1)) <= level:
            break
        elif level is not None:
            out.append(ln)
    return "\n".join(out) if out else f"the page {path} has no section headed `{section}`"


def answer(wiki: Path, msg: dict) -> dict | None:
    """The reply to one message, or None for a notification."""
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if mid is None:
        return None
    if method == "initialize":
        result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": {"name": "science-factory-wiki", "version": "0.1.0"}}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name == "openwiki_search":
            text = search(wiki, str(args.get("query") or ""), args.get("limit") or 8)
        elif name == "openwiki_read":
            text = read(wiki, str(args.get("path") or ""), args.get("section"))
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"no such tool: {name}. This server has openwiki_search and openwiki_read, and nothing that writes"}}
        result = {"content": [{"type": "text", "text": text}], "isError": False}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def serve(wiki: Path) -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = answer(wiki, msg) if isinstance(msg, dict) else None
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()
    return 0


def selftest() -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="wiki-server-")).resolve()
    try:
        wiki = tmp / "openwiki"
        wiki.mkdir()
        (wiki / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# toy\n')
        (wiki / "tide-gauge-drift.md").write_text("---\ntype: pitfall\nstatus: draft\n---\n\n# The harbour tide gauge drifts in summer\n\nIt reads high in warm months. See [the sensor](sensor.md).\n\n## What to do\n\nCompare changes.\n\n## Why\n\nNot known.\n")
        (wiki / "sensor.md").write_text("---\ntype: dataset\nstatus: stable\nverified: { by: human:toy-steward, at: 2026-01-02T00:00:00Z }\n---\n\n# The harbour pressure sensor\n\nA pressure sensor on the harbour quay, beside the tide gauge.\n")
        (wiki / ".claims").mkdir()
        (wiki / ".claims" / "x.md").write_text("# managed by another tool\n\nharbour tide gauge\n")
        (tmp / "secret.md").write_text("# outside the wiki\n")
        sent = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "openwiki_search", "arguments": {"query": "Does the harbour tide gauge drift in warm months?"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "openwiki_read", "arguments": {"path": "tide-gauge-drift.md", "section": "What to do"}}},
                {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "openwiki_read", "arguments": {"path": "../secret.md"}}},
                {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "openwiki_write", "arguments": {"path": "x.md", "text": "y"}}},
                {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "openwiki_read", "arguments": {"path": "sensor.md"}}},
                {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "openwiki_read", "arguments": {"path": ".claims/x.md"}}}]
        before = sorted((p.as_posix(), p.read_bytes()) for p in tmp.rglob("*") if p.is_file())
        done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--wiki", str(wiki)], input="\n".join(json.dumps(m) for m in sent) + "\n",
                              capture_output=True, text=True)
        got = {r["id"]: r for r in (json.loads(ln) for ln in done.stdout.splitlines() if ln.strip())}

        def text(i):
            return got[i]["result"]["content"][0]["text"]

        results.append(("it answers the handshake and stays silent on a notification", got[1]["result"]["protocolVersion"] == PROTOCOL and len(got) == 8))
        results.append(("it offers exactly two tools, openwiki_search and openwiki_read", [t["name"] for t in got[2]["result"]["tools"]] == ["openwiki_search", "openwiki_read"]))
        results.append(("search returns the page that bears on the query first, marked as working memory",
                        text(3).splitlines()[0].startswith("tide-gauge-drift.md |") and "NOT SIGNED" in text(3).splitlines()[0]))
        results.append(("search says who signed a signed page", any(ln.startswith("sensor.md") and "signed by human:toy-steward" in ln for ln in text(3).splitlines())))
        results.append(("search does not list files another tool manages", ".claims" not in text(3)))
        results.append(("read returns one section when asked for it", text(4).startswith("## What to do") and "Compare changes." in text(4) and "Not known" not in text(4)))
        results.append(("read returns a whole page, front matter included, so its own signature lines can be seen", "verified:" in text(7) and "pressure sensor" in text(7)))
        results.append(("read refuses a path outside the wiki", "no such page" in text(5)))
        results.append(("read refuses a file another tool manages", "no such page" in text(8)))
        results.append(("a tool that writes does not exist", "error" in got[6] and "nothing that writes" in got[6]["error"]["message"]))
        results.append(("serving changed no file", before == sorted((p.as_posix(), p.read_bytes()) for p in tmp.rglob("*") if p.is_file())))
        k = knowledge()
        results.append(("the server's search and knowledge.py give the same pages in the same order",
                        [ln.split(" | ")[0] for ln in text(3).splitlines()]
                        == [Path(c["file"]).name for c in k.about("Does the harbour tide gauge drift in warm months?", [wiki], limit=8)]))
        results.append(("loading the knowledge helpers leaves no bytecode folder beside the tools", not (HERE / "__pycache__").exists()))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wiki", type=Path, default=HERE.parent / "openwiki")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.wiki.is_dir():
        print(f"{a.wiki} is not a directory", file=sys.stderr)
        return 2
    return serve(a.wiki)


if __name__ == "__main__":
    sys.exit(main())
