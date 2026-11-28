#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""factory_server: the factory, reached from Claude by a scientist's plain words.

It speaks the Model Context Protocol over standard input and output
(newline-delimited JSON-RPC 2.0, as wiki_server.py does) and reaches one or
several workspaces, each with its own factory where it holds one, given at
the start. Every tool is a thin wrapper over a command of this package, run
as a separate process from this package's own tools/ (never a workspace's),
so the server and the command line give the same answer; each result names
the command line that gives it. It runs no language model.

Read (write nothing):
  waiting          what waits on a person, across the workspaces (waiting.py)
  status           where a study or an exploration stands (sf.py status, explore.py status)
  lead             the latest lead of an exploration: its summary block, its
                   reviews and their verdicts, and its standing
  figure           a figure, by the look or step that drew it and its checksum,
                   as a picture the client can show, with its caption
  report           what a workspace did (report.py), Markdown or JSON
  fit_note         the fit note recorded at intake, or that there is none
  contribution     who did each step (sf.py or explore.py contribution --print-only)
  knowledge        search and read the wiki (wiki_server.py's own search and read)
  factory_summary  each workspace's definition: version, checksum, validity (check_factory.py)
Intake (write only where a tool of this package writes, and never over a file):
  submit_request      a request from factory/templates/request.md, in the person's words
  propose_fresh_data  fresh_data.py describe or propose, from metadata only
  start_exploration   explore.py start, with a declared set aside and working data

Never a person's act. No tool records or prepares the so what, the lock,
the signature, a verification, a promotion, a change to the definition or
an opening of fresh data, and none acts as a `human:` or `platform:` actor;
none runs a look, a script or any other command. Where a person must act,
status and lead return waiting.py's exact next step and the GitHub page to
open. The commands the server can run are the list ALLOW below, checked
before every run; the server opens no file outside its roots (the
workspaces, the wiki, and this package's tools/ and factory/), and refuses
a path with `..`, a hidden part or a symbolic link in it.

Standings are as the command line gives them: the read commands get the
token variables the server was started with (GH_TOKEN, GITHUB_TOKEN,
SF_PLATFORM_TOKEN), so with a token an act is asked of GitHub now, and
without one the tools say what git shows and that an earlier answer is not
re-checked now. The intake commands get no token.

Why not the `mcp` package: this server starts itself clean (no PYTHON
variable, no user site, no start-up file), as every tool here does, and the
protocol it needs is four methods; the package would bring a stack of
dependencies into that clean start for no change in what it does.

Usage: factory_server.py --workspace DIR [--workspace DIR ...] [--wiki DIR]
       factory_server.py --selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site and "sf-no-bytecode" in str(sys.pycache_prefix)):
    # A clean start. This tool runs itself again in a Python that reads no PYTHON variable, no user site, no start-up
    # file (.pth, sitecustomize) and not the folder this file is in, so that none of those can change what it does.
    # What a hostile environment ran before this line has already run: a stated limit (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + ("/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(os.environ.get("TEMP", "."), f"sf-no-bytecode-{os.getpid()}")), os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
    # The packages this tool declares, from the environment its interpreter belongs to, put on the import path by
    # hand and last: nothing in that folder is run at start-up.
    import os
    import sysconfig
    _env = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    _lib = ([os.path.join(_env, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"),
             os.path.join(_env, "Lib", "site-packages")] if os.path.isfile(os.path.join(_env, "pyvenv.cfg"))
            else [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]])
    sys.path += [p for p in dict.fromkeys(_lib) if os.path.isdir(p) and p not in sys.path]

import argparse  # noqa: E402
import base64  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shlex  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path, PurePosixPath  # noqa: E402

sys.dont_write_bytecode = True  # the server loads wiki_server.py and fence.py from beside it and leaves no bytecode folder

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
PROTOCOL = "2024-11-05"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
AGENT = re.compile(r"agent:[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
TOKENS = ("GH_TOKEN", "GITHUB_TOKEN", "SF_PLATFORM_TOKEN")
PASSED_ON = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR", "TERM", "XDG_CACHE_HOME", "XDG_CONFIG_HOME",
             "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS", "SSL_CERT_FILE", "SSL_CERT_DIR",
             "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
             "ssl_cert_file", "ssl_cert_dir", "requests_ca_bundle", "curl_ca_bundle", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE")
PICTURES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
DRAWINGS = {".svg": "image/svg+xml", ".pdf": "application/pdf"}
MOST_BYTES = 10 * 1024 * 1024
NOT_A_FINDING = "nothing here is a finding unless a study's status says signed; a lead is never a finding"

# Every command this server can run: (tool file in tools/, its command or None), the options it may be given as
# --name=value, the flags it may be given bare, and how many positional words (each an absolute path). Nothing else is
# run, and a list of words that does not fit its entry is refused before anything starts. `reads` commands get the
# token variables, so a standing is asked of GitHub as on the command line; the others get none.
ALLOW = {
    ("waiting.py", None): {"options": {"--workspace", "--factory"}, "flags": {"--json"}, "reads": True},
    ("report.py", None): {"options": {"--workspace", "--factory"}, "flags": {"--json"}, "reads": True},
    ("check_factory.py", None): {"options": {"--repository"}, "fixed": {"--repository": str(PACKAGE)}, "flags": {"--checksum"}, "positional": 1,
                                 "reads": True},
    ("sf.py", "status"): {"options": {"--study", "--factory"}, "reads": True},
    ("sf.py", "contribution"): {"options": {"--study", "--factory"}, "flags": {"--print-only"}, "required_flags": {"--print-only"}, "reads": True},
    ("explore.py", "status"): {"options": {"--exploration"}, "reads": True},
    ("explore.py", "contribution"): {"options": {"--exploration"}, "flags": {"--print-only"}, "required_flags": {"--print-only"}, "reads": True},
    ("fresh_data.py", "describe"): {"options": {"--csv", "--date-column", "--series-column", "--period", "--subject", "--what", "--release",
                                                "--cadence", "--out"}},
    ("fresh_data.py", "propose"): {"options": {"--metadata", "--kind", "--from", "--until", "--sites", "--regions", "--release", "--periods",
                                               "--fraction", "--draw-over", "--what", "--why", "--unfair", "--by", "--model", "--out", "--studies"}},
    ("explore.py", "start"): {"options": {"--exploration", "--by", "--model", "--id", "--question", "--request", "--subject", "--boundary-from",
                                          "--how", "--set-aside-window", "--set-aside-sites", "--set-aside-release", "--release-cut-off",
                                          "--set-aside-path", "--fresh-data", "--why", "--working", "--working-data", "--working-window",
                                          "--studies"}},
}
# What no entry may ever name: the acts by people, their verification, an opening, a promotion, a change to the
# definition, anything that runs a script, and every option that types a person's act or records the platform's.
FORBIDDEN_COMMANDS = {"lock", "signature", "so-what", "verify-acts", "verify-so-what", "open-held-out", "void-unread", "promote", "log-change",
                      "look", "recheck", "test", "rehearse", "review", "lead", "end", "hand-over", "resolve", "close", "attach", "reveal",
                      "request-lock", "request-signature", "held-out-change", "reviewer", "ask-so-what", "correct", "fit", "note", "choice",
                      "known", "read", "selftest", "update", "pin"}
FORBIDDEN_OPTIONS = {"--local-practice", "--record-merge", "--platform-record", "--record-comment", "--people-not-verified", "--evidence",
                     "--nothing-set-aside", "--seed-file", "--merge-commit", "--asked-by", "--cost", "--summary", "--html"}


class Refusal(Exception):
    """A call the server refuses before any command runs."""


def allowed(argv: list) -> str | None:
    """None when this list of words fits an entry of ALLOW, otherwise why not."""
    if not argv or not isinstance(argv[0], str):
        return "no tool named"
    tool, rest = argv[0], list(argv[1:])
    entry, cmd = ALLOW.get((tool, rest[0] if rest else None)), None
    if entry is not None and rest:
        cmd, rest = rest[0], rest[1:]
    else:
        entry = ALLOW.get((tool, None))
    if entry is None:
        return f"{tool} {cmd or (argv[1] if len(argv) > 1 else '')} is not a command this server runs".strip()
    if cmd in FORBIDDEN_COMMANDS:
        return f"{cmd} is never run by this server"
    positional, flags = 0, set()
    for w in rest:
        if not isinstance(w, str) or "\x00" in w:
            return "a word that is not text"
        if w.startswith("--"):
            name, eq, value = w.partition("=")
            if name in FORBIDDEN_OPTIONS:
                return f"{name} is never passed by this server"
            if eq:
                if name not in entry["options"]:
                    return f"{name} is not an option this server passes to {tool} {cmd or ''}".rstrip()
                if name == "--by" and not AGENT.fullmatch(value):
                    return "--by is always an agent's name (agent:<id>) here"
                if name in entry.get("fixed", {}) and value != entry["fixed"][name]:
                    return f"{name} is always {entry['fixed'][name]} here"
            elif name in entry.get("flags", set()):
                flags.add(name)
            else:
                return f"{w} is not a flag this server passes"
        elif w.startswith("/") and positional < entry.get("positional", 0):
            positional += 1
        else:
            return f"a bare word is not passed: {w[:40]}"
    if entry.get("required_flags", set()) - flags:
        return f"{tool} {cmd} runs here only with {', '.join(sorted(entry['required_flags']))}"
    return None


def environment(reads: bool) -> dict:
    env = {k: os.environ[k] for k in PASSED_ON if k in os.environ}
    env.update({k: v for k, v in os.environ.items() if k.startswith("UV_") and v.strip()})
    if reads:
        env.update({k: os.environ[k] for k in TOKENS if os.environ.get(k)})
    return env


def as_typed(argv: list) -> str:
    """The command line that gives the same answer, as a person would type it from the package's top."""
    return shlex.join(["uv", "run", f"tools/{argv[0]}", *argv[1:]])


def run_tool(argv: list, cwd: Path) -> dict:
    """Run one command of ALLOW from this package's own tools/, and nothing else. The only place the server starts a process."""
    why = allowed(argv)
    if why:
        raise Refusal(f"not on the server's allow list: {why}")
    entry = ALLOW.get((argv[0], argv[1] if len(argv) > 1 else None)) or ALLOW[(argv[0], None)]
    done = subprocess.run([sys.executable, str(HERE / argv[0]), *argv[1:]], cwd=str(cwd), env=environment(bool(entry.get("reads"))),
                          capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=900)
    stderr = "\n".join(ln for ln in done.stderr.splitlines() if not ln.startswith("warning: "))  # uv's own warnings are not an answer
    return {"command": as_typed(argv), "exit": done.returncode, "stdout": done.stdout, "stderr": stderr.strip()}


def code_of(tree: Path) -> dict:
    """Every file of a definition tree that a tool could run or load (a .py file, a shell script, bytecode, anything
    executable), by path, with its checksum; a link counts, as a link."""
    out = {}
    for f in sorted(tree.rglob("*")):
        rel = f.relative_to(tree).as_posix()
        if f.is_symlink():
            out[rel] = "a link"
        elif f.is_file() and (f.suffix in (".py", ".sh", ".pyc") or "__pycache__" in f.parts or os.access(f, os.X_OK)):
            out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


class Workspace:
    """A folder the server reaches. Its own definition (factory/) is used when it has one, and only when every file of it a
    tool could run or load is this server's own, byte for byte: the tools load a definition's harness code (the verifier),
    so a workspace's own code would otherwise run in the server's name."""

    def __init__(self, folder: Path):
        self.root = Path(folder).resolve()
        self.name = self.root.name
        own = self.root / "factory"
        self.own_factory = (not own.is_symlink() and own.is_dir() and not (own / "factory.yaml").is_symlink()
                            and (own / "factory.yaml").is_file())
        self.factory = own if self.own_factory else (PACKAGE / "factory").resolve()
        if self.own_factory and self.factory.resolve() != (PACKAGE / "factory").resolve():
            mine, theirs = code_of((PACKAGE / "factory").resolve()), code_of(self.factory)
            differ = sorted(k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k))
            if differ:
                raise Refusal(f"the workspace {self.name} has its own definition whose code is not this server's ({', '.join(differ[:4])}"
                              f"{' and more' if len(differ) > 4 else ''}): this server would run that code in its name. Start a server from "
                              "that workspace's own tools to reach it")


def inside(root: Path, rel, what: str) -> Path:
    """`rel` below `root`, refused with `..`, `.`, a hidden part, an absolute or home path, or a symbolic link on the way."""
    text = str(rel if rel is not None else "")
    if not text.strip() or "\x00" in text or "\\" in text or text.startswith(("/", "~")) or len(text) > 400:
        raise Refusal(f"{what} is a path below the workspace (or the wiki), such as explorations/EXPLORATION-1: {text[:60]!r}")
    parts = PurePosixPath(text).parts
    if any(p in ("..", ".") or p.startswith(".") for p in parts):
        raise Refusal(f"{what} may not hold `..`, `.` or a hidden part: {text[:60]!r}")
    cur = root
    for p in parts:
        cur = cur / p
        if cur.is_symlink():
            raise Refusal(f"{what} passes through a symbolic link ({p}); the server follows none")
    return cur


def read_bytes(root: Path, rel, what: str, most: int = MOST_BYTES) -> bytes:
    f = inside(root, rel, what)
    try:
        fd = os.open(f, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        raise Refusal(f"{what} does not exist: {rel}")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise Refusal(f"{what} is not a file: {rel}")
        if st.st_size > most:
            raise Refusal(f"{what} is larger than {most} bytes: {rel}")
        with os.fdopen(fd, "rb", closefd=False) as fh:
            return fh.read(most + 1)
    finally:
        os.close(fd)


def write_new(root: Path, rel: str, text: str, what: str) -> Path:
    """A new file below the workspace, never over one, never through a link."""
    f = inside(root, rel, what)
    parent = f.parent
    if not parent.is_dir():
        parent.mkdir(parents=True, exist_ok=True)
        inside(root, str(PurePosixPath(rel).parent), what)  # made, then checked again: no link on the way
    try:
        fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    except FileExistsError:
        raise Refusal(f"{rel} already exists: the server writes a new file and never over one")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return f


def _source_module(name: str, path: Path):
    class _SourceOnly(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)
    spec = importlib.util.spec_from_file_location(name, path, loader=_SourceOnly(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- the tools' schemas

def _s(desc: str) -> dict:
    return {"type": "string", "description": desc}


def _list(desc: str) -> dict:
    return {"type": "array", "items": {"type": "string"}, "description": desc}


WS = _s("the workspace by its folder's name, as factory_summary lists it; may be left out when the server reaches one")
WORK = _s("the study or exploration: studies/NAME, explorations/NAME, or NAME alone")
BY = _s("the agent that asks, as agent:<id>; recorded as the tools require. A human: or platform: name is refused")
MODEL = _s("the model the agent runs as, said truthfully; recorded, and proven by nothing")
REQUEST_FIELDS = {
    "what_i_want_to_know": "What I want to know", "the_thing": "The thing", "why_it_matters": "Why it matters",
    "difference_that_matters": "The difference that matters, and where it comes from", "already_looked_at": "What I have already looked at",
    "not_looked_at": "Data I have not looked at", "what_i_will_do": "What I will do with each answer", "by_when": "By when",
    "how_fooled": "How I expect it to be fooled", "what_i_bring": "What I can bring that an agent cannot", "who_is_on_it": "Who is on it",
    "what_i_want_back": "What I want back", "others_product": "Anyone else's product involved?"}
LIST_FIELDS = {"if_it_holds": "If it holds:", "if_it_does_not": "If it does not:", "if_it_cannot_tell": "If it cannot tell:"}


def _tool(name, desc, props, required=()):
    return {"name": name, "description": desc,
            "inputSchema": {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}}


TOOLS = [
    _tool("waiting", "What waits on a person, or is stuck, across the workspaces, oldest first: what is wanted, since when, who acts, and the "
          "exact next step or the GitHub page to open (tools/waiting.py). Read-only.",
          {"workspace": WS, "format": {"type": "string", "enum": ["text", "json"], "description": "plain words (default) or JSON"}}),
    _tool("status", "Where a study or an exploration stands, as sf.py status or explore.py status says, with what waits on a person for it "
          "and the standing of its acts. Read-only.", {"workspace": WS, "path": WORK}, ["path"]),
    _tool("lead", "The latest lead of an exploration: its summary block, its reviews and their verdicts (and whether each reviewed the lead "
          "as it stands), its stage and so what, and what a person must do next. A lead is never a finding. Read-only.",
          {"workspace": WS, "path": WORK}, ["path"]),
    _tool("figure", "A figure a look or a step kept, as a picture with its caption, given the look (LOOK-003, or a study's test or rehearsal) "
          "and its sha256 (12 characters or more). With neither, the list of figures. Read-only.",
          {"workspace": WS, "path": WORK, "look": _s("the look or step that drew it"), "sha256": _s("the figure's checksum, or its first 12 or more characters")},
          ["path"]),
    _tool("report", "What a workspace's studies and explorations did, by stage, outcome, time and model (tools/report.py). It ranks nothing "
          "by findings supported. Read-only.", {"workspace": WS, "format": {"type": "string", "enum": ["markdown", "json"]}}),
    _tool("fit_note", "The fit note written at intake for a study or exploration (how well it suits agents, a verdict, what it needs from a "
          "person), or that none was written. Advice; it blocks nothing. Read-only.", {"workspace": WS, "path": WORK}, ["path"]),
    _tool("contribution", "Who did each step of a study or exploration, from its logs, as a paragraph for a paper, and what the logs cannot "
          "show (contribution --print-only: no file is written). Read-only.", {"workspace": WS, "path": WORK}, ["path"]),
    _tool("knowledge", "Search the wiki (give query) or read a page (give page, and a section if you like), as the wiki server does: each page "
          "with who signed it, or NOT SIGNED. Read-only.",
          {"query": _s("the question or words to search by"), "limit": {"type": "integer", "description": "how many pages at most (default 8)"},
           "page": _s("a page's path below the wiki, as search returns it"), "section": _s("a heading of the page")}),
    _tool("factory_summary", "Each workspace's factory: which definition it uses, its version and checksum, and whether it is valid "
          "(tools/check_factory.py). Read-only.", {"workspace": WS}),
    _tool("submit_request", "Write a request, in the person's own words, from factory/templates/request.md into requests/NAME.md of a "
          "workspace. Refuses to write over a file. It starts nothing.",
          {"workspace": WS, "name": _s("the file's name, letters, digits, - and _ (requests/NAME.md)"), "by": BY, "model": MODEL,
           **{k: _s(f"the person's words for: {v}") for k, v in REQUEST_FIELDS.items() if k != "what_i_will_do"},
           **{k: _s(f"the person's words for: What I will do with each answer, {v}") for k, v in LIST_FIELDS.items()}},
          ["name", "what_i_want_to_know", "by", "model"]),
    _tool("propose_fresh_data", "From metadata only: describe a CSV file by its date column (step describe), or propose the fresh data that "
          "will check an idea from a metadata file (step propose: the next release, a later period, another site, or a random set aside, "
          "drawn at the lock). Wraps tools/fresh_data.py; never opens fresh data.",
          {"workspace": WS, "step": {"type": "string", "enum": ["describe", "propose"]}, "by": BY, "model": MODEL,
           "csv": _s("describe: the data file below the workspace; only its date and series columns are read"),
           "date_column": _s("describe"), "series_column": _s("describe"), "period": _s("describe: year or month"),
           "subject": _s("describe: key=value,key=value"), "cadence": _s("describe: the release's cadence"),
           "metadata": _s("propose: the metadata file below the workspace"),
           "kind": _s("propose: next-release, later-period, another-site or random"), "from": _s("propose, later-period: YYYY-MM-DD"),
           "until": _s("propose, later-period"), "sites": _s("propose, another-site"), "regions": _s("propose, another-site"),
           "release": _s("the release's name"), "periods": {"type": "integer", "description": "propose, next-release"},
           "fraction": {"type": "number", "description": "propose, random"}, "draw_over": _s("propose, random: site or id"),
           "what": _s("exactly what data, in words"), "why": _s("propose: why it suits the question"),
           "unfair": _s("propose: what would make it unfair"), "out": _s("the .yaml file to write, below the workspace")},
          ["step", "out", "what"]),
    _tool("start_exploration", "Start an exploration (tools/explore.py start): the data set aside first, exactly as declared, and the working "
          "data the looks may be given. It runs no look.",
          {"workspace": WS, "id": _s("the exploration's id; it goes in explorations/ID"), "question": _s("one sentence ending in a question mark"),
           "request": _s("the request file below the workspace, such as requests/NAME.md"), "subject": _s("key=value,key=value"),
           "how": _s("how the data is held out, in the tool's words (a later period, ...)"), "set_aside_window": _s("START:END"),
           "set_aside_sites": _s("sites, separated by commas"), "set_aside_release": _list("releases or records set aside"),
           "release_cut_off": _s("with a new release: the last date of the data as it stands"),
           "set_aside_path": _list("where set-aside data would land, below the workspace"),
           "fresh_data": _s("the proposal (propose_fresh_data) this start sets aside, below the workspace"),
           "why": _s("why this is the data to set aside"), "working": _s("what will be explored, in words"),
           "working_data": _list("files or folders below the workspace that hold the data to explore"), "working_window": _s("START:END"),
           "boundary_from": _list("wiki pages the boundary was read from, as knowledge returns them"), "by": BY, "model": MODEL},
          ["id", "question", "request", "subject", "why", "working", "working_data", "by", "model"]),
]
TOOL_NAMES = [t["name"] for t in TOOLS]


# ---------------------------------------------------------------- the server

class Server:
    def __init__(self, workspaces: list, wiki: Path | None):
        try:
            self.workspaces = [Workspace(w) for w in workspaces]
        except Refusal as r:
            raise SystemExit(f"factory_server: {r}")
        names = [w.name for w in self.workspaces]
        if not self.workspaces or len(set(names)) != len(names):
            raise SystemExit("factory_server: give each workspace once, with folders of different names (" + ", ".join(names) + ")")
        self.wiki = Path(wiki).resolve() if wiki and Path(wiki).is_dir() else None
        self._wiki_server = None

    # -- choosing
    def ws(self, args: dict) -> Workspace:
        name = args.get("workspace")
        if name in (None, ""):
            if len(self.workspaces) == 1:
                return self.workspaces[0]
            raise Refusal("this server reaches several workspaces; say which: " + ", ".join(w.name for w in self.workspaces))
        for w in self.workspaces:
            if w.name == name:
                return w
        raise Refusal(f"no workspace named {str(name)[:40]!r}; this server reaches " + ", ".join(w.name for w in self.workspaces))

    def work(self, ws: Workspace, path) -> tuple:
        """(kind, folder, path from the workspace) of a study or exploration, refused unless it is one."""
        text = str(path or "").strip().rstrip("/")
        parts = PurePosixPath(text).parts if text else ()
        if len(parts) == 1:
            found = [k for k in ("studies", "explorations") if NAME.fullmatch(parts[0]) and (ws.root / k / parts[0]).is_dir()]
            if len(found) != 1:
                raise Refusal(f"{text[:40]!r} is not one study or exploration of {ws.name}; give studies/NAME or explorations/NAME")
            parts = (found[0], parts[0])
        if len(parts) != 2 or parts[0] not in ("studies", "explorations") or not NAME.fullmatch(parts[1]):
            raise Refusal(f"{text[:60]!r} is not studies/NAME or explorations/NAME")
        rel = f"{parts[0]}/{parts[1]}"
        d = inside(ws.root, rel, "the study or exploration")
        log = d / ("study-log.jsonl" if parts[0] == "studies" else "exploration-log.jsonl")
        if not d.is_dir() or log.is_symlink() or not log.is_file():
            raise Refusal(f"{rel} is not a study or exploration of {ws.name} (no log there)")
        return ("study" if parts[0] == "studies" else "exploration"), d, rel

    def events(self, ws: Workspace, rel: str, kind: str) -> list:
        raw = read_bytes(ws.root, f"{rel}/{'study-log.jsonl' if kind == 'study' else 'exploration-log.jsonl'}", "the log", 64 * MOST_BYTES)
        out = []
        for ln in raw.decode("utf-8", "replace").splitlines():
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if isinstance(e, dict) and isinstance(e.get("data"), dict):
                out.append(e)
        return out

    def waiting_for(self, ws: Workspace, rel: str | None = None) -> tuple:
        """(the run, the waiting JSON, the groups of `rel`) for one workspace."""
        r = run_tool(["waiting.py", f"--workspace={ws.root}", f"--factory={ws.factory}", "--json"], ws.root)
        try:
            w = json.loads(r["stdout"])
        except ValueError:
            return r, None, []
        return r, w, [g for g in w.get("groups", []) if rel is None or g.get("path") == rel]

    # -- the read tools
    def t_waiting(self, a):
        chosen = [self.ws(a)] if a.get("workspace") else self.workspaces
        by_factory = {}
        for w in chosen:
            by_factory.setdefault(w.factory, []).append(w)
        runs = [run_tool(["waiting.py", *[f"--workspace={w.root}" for w in ws_], f"--factory={f}", *(["--json"] if a.get("format") == "json" else [])],
                         ws_[0].root) for f, ws_ in by_factory.items()]
        return runs, {"say": "each item says who acts and the next step; where people act, the GitHub page to open. No tool of this server "
                             "makes a person's act."}

    def t_status(self, a):
        ws = self.ws(a)
        kind, d, rel = self.work(ws, a.get("path"))
        r = run_tool(["sf.py", "status", f"--study={d}", f"--factory={ws.factory}"] if kind == "study"
                     else ["explore.py", "status", f"--exploration={d}"], ws.root)
        wr, w, groups = self.waiting_for(ws, rel)
        return [r], {"standings": (w or {}).get("standings", {}).get("words"), "where_a_person_acts": [i for g in groups for i in g["items"]],
                     "same_as_also": wr["command"], "says": NOT_A_FINDING}

    def t_lead(self, a):
        ws = self.ws(a)
        kind, d, rel = self.work(ws, a.get("path"))
        if kind != "exploration":
            raise Refusal("a lead belongs to an exploration; a study has a plan and, after its opening, a finding (use status)")
        r = run_tool(["explore.py", "status", f"--exploration={d}"], ws.root)
        wr, w, groups = self.waiting_for(ws, rel)
        try:
            st = json.loads(r["stdout"])
        except ValueError:
            return [r], {}
        out = {"exploration": rel, "stage": st.get("stage"), "who": st.get("who"), "does": st.get("does")}
        sha = st.get("lead_json_sha256")
        if not sha:
            out["lead"] = "no lead has been recorded in this exploration"
        else:
            lead_json = read_bytes(ws.root, f"{rel}/lead.json", "the lead")
            md = read_bytes(ws.root, f"{rel}/lead.md", "the lead's page").decode("utf-8", "replace")
            first = next((ln for ln in md.splitlines() if ln.startswith("**Exploring.**")), "")
            short, on = [], False
            for ln in md.splitlines():  # the block between "## In short" and the line that says the rest is the lead in full
                if on and (ln.startswith("## ") or ln.startswith("The rest of this page")):
                    break
                if on:
                    short.append(ln)
                on = on or ln.strip() == "## In short"
            try:
                version = json.loads(lead_json).get("version")
            except ValueError:
                version = None
            ev = self.events(ws, rel, kind)
            reviews = []
            for e in ev:
                if e.get("kind") != "review.verdict":
                    continue
                v = e["data"]
                text = None
                if re.fullmatch(r"verdicts/[A-Za-z0-9][A-Za-z0-9_.-]*\.md", str(v.get("file") or "")):
                    kept = None
                    try:
                        b = read_bytes(ws.root, f"{rel}/{v['file']}", "a review")
                        kept = b.decode("utf-8", "replace") if hashlib.sha256(b).hexdigest() == v.get("sha") else None
                    except Refusal:
                        pass
                    text = kept if kept is not None else "the review file is missing or not the one recorded"
                reviews.append({"review": Path(str(v.get("file") or "")).stem, "by": e.get("actor"), "model_as_declared": e.get("model"),
                                "verdict": v.get("verdict"), "of_lead_version": v.get("of_lead_version"),
                                "of_the_lead_as_it_stands": v.get("of_lead_json_sha") == sha, "text": text})
            out.update({"lead": {"version": version, "lead_json_sha256": sha,
                                 "file_is_the_one_recorded": hashlib.sha256(lead_json).hexdigest() == sha,
                                 "first_line": first, "summary": "\n".join(short).strip(), "page": f"{rel}/lead.md"},
                        "reviews": reviews, "so_what": st.get("so_what"), "so_whats": st.get("so_whats", []),
                        "overclaiming": st.get("overclaiming", [])})
        out.update({"standings": (w or {}).get("standings", {}).get("words"), "where_a_person_acts": [i for g in groups for i in g["items"]],
                    "says": "a lead is never a finding: it is tested on nothing until a confirming study opens the data set aside"})
        return [r, wr], {"answer": out, "composed": True}

    def figures(self, ws: Workspace, rel: str, kind: str) -> list:
        figs = []
        for e in self.events(ws, rel, kind):
            d = e["data"]
            if kind == "exploration" and e.get("kind") == "look.run":
                for f in d.get("figures") or []:
                    if isinstance(f, dict):
                        figs.append({"look": d.get("id"), "file": f.get("file"), "sha256": f.get("sha256"),
                                     "caption": " ".join(str(d.get("why") or "").split())[:300]})
            elif kind == "study" and e.get("kind") == "study.started":
                for f in d.get("exploration_figures") or []:
                    if isinstance(f, dict):
                        figs.append({"look": f.get("look"), "file": f.get("file"), "sha256": f.get("sha256"), "caption": f.get("caption"),
                                     "drawn_by": f"the exploration's {f.get('look')}"})
            elif kind == "study" and isinstance(d.get("figures"), list):
                for f in d["figures"]:
                    if isinstance(f, dict) and f.get("sha256"):
                        figs.append({"look": d.get("id") or d.get("test"), "file": f.get("file"), "sha256": f.get("sha256"),
                                     "caption": f.get("shows"), "drawn_by": e.get("kind")})
        return figs

    def t_figure(self, a):
        ws = self.ws(a)
        kind, d, rel = self.work(ws, a.get("path"))
        figs = self.figures(ws, rel, kind)
        look, want = a.get("look"), str(a.get("sha256") or "").lower()
        if not look and not want:
            return [], {"answer": {"figures": figs, "say": "give look and sha256 to see one" if figs else "no figure was kept here"}, "composed": True}
        if not re.fullmatch(r"[0-9a-f]{12,64}", want):
            raise Refusal("sha256 is the figure's checksum, or its first 12 or more characters, as the list gives it")
        hit = [f for f in figs if f["look"] == look and str(f["sha256"]).startswith(want)]
        if len(hit) != 1:
            raise Refusal(f"no figure of {look} with that checksum in {rel}; the figures kept here: "
                          + ("; ".join(f"{f['look']} {str(f['sha256'])[:12]}" for f in figs) or "none"))
        f = hit[0]
        data = read_bytes(ws.root, f"{rel}/{f['file']}", "the figure")
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            raise Refusal(f"{f['file']} is not the picture that was kept (its checksum differs); nothing is shown")
        ext = Path(str(f["file"])).suffix.lower()
        words = (f"Figure from {f['look']} of {rel} (sha256 {f['sha256'][:12]}, checked now): {f['caption']}. Look at it yourself: "
                 "a caption says what the step meant to draw, not what the picture shows.")
        if ext in PICTURES:
            shown = {"type": "image", "data": base64.b64encode(data).decode(), "mimeType": PICTURES[ext]}
        elif ext == ".svg":
            shown = {"type": "resource", "resource": {"uri": f"factory://{ws.name}/{rel}/{f['file']}", "mimeType": DRAWINGS[ext],
                                                      "text": data.decode("utf-8", "replace")}}
        elif ext == ".pdf":
            shown = {"type": "resource", "resource": {"uri": f"factory://{ws.name}/{rel}/{f['file']}", "mimeType": DRAWINGS[ext],
                                                      "blob": base64.b64encode(data).decode()}}
        else:
            raise Refusal(f"{f['file']} is not a picture this server shows")
        return [], {"content": [{"type": "text", "text": words}, shown]}

    def t_report(self, a):
        ws = self.ws(a)
        return [run_tool(["report.py", f"--workspace={ws.root}", f"--factory={ws.factory}", *(["--json"] if a.get("format") == "json" else [])],
                         ws.root)], {}

    def t_fit_note(self, a):
        ws = self.ws(a)
        kind, d, rel = self.work(ws, a.get("path"))
        r = run_tool(["sf.py", "status", f"--study={d}", f"--factory={ws.factory}"] if kind == "study"
                     else ["explore.py", "status", f"--exploration={d}"], ws.root)
        try:
            words = json.loads(r["stdout"]).get("fit")
        except ValueError:
            return [r], {}
        fit = [e for e in self.events(ws, rel, kind) if e.get("kind") == "fit.noted"]
        note = ({k: v for k, v in fit[-1]["data"].items() if k != "way"} | {"noted_by": fit[-1].get("actor"), "model_as_declared": fit[-1].get("model"),
                                                                          "at": fit[-1].get("at")}) if fit else None
        return [r], {"answer": {"path": rel, "fit": words, "note_as_recorded": note,
                                "says": "a fit note is advice to the person and blocks nothing"}, "composed": True}

    def t_contribution(self, a):
        ws = self.ws(a)
        kind, d, rel = self.work(ws, a.get("path"))
        return [run_tool(["sf.py", "contribution", f"--study={d}", f"--factory={ws.factory}", "--print-only"] if kind == "study"
                         else ["explore.py", "contribution", f"--exploration={d}", "--print-only"], ws.root)], {}

    def t_knowledge(self, a):
        if self.wiki is None:
            raise Refusal("this server was started without a wiki (--wiki)")
        if self._wiki_server is None:
            self._wiki_server = _source_module("factory_server_wiki", HERE / "wiki_server.py")
        q, page = a.get("query"), a.get("page")
        if bool(q) == bool(page):
            raise Refusal("give query (to search) or page (to read), one of them")
        if q:
            text = self._wiki_server.search(self.wiki, str(q), a.get("limit") or 8)
            same = shlex.join(["uv", "run", "tools/knowledge.py", "about", "--question", str(q), "--wiki", str(self.wiki)])
        else:
            text = self._wiki_server.read(self.wiki, str(page), a.get("section"))
            same = "the wiki server's openwiki_read (tools/wiki_server.py)"
        return [], {"content": [{"type": "text", "text": text}, {"type": "text", "text": json.dumps({"same_as": same}, indent=1)}]}

    def t_factory_summary(self, a):
        chosen = [self.ws(a)] if a.get("workspace") else self.workspaces
        runs, out = [], []
        for w in chosen:
            v = run_tool(["check_factory.py", str(w.factory), f"--repository={PACKAGE}"], w.root)
            c = run_tool(["check_factory.py", str(w.factory), f"--repository={PACKAGE}", "--checksum"], w.root)
            runs += [v, c]
            try:
                stamp = json.loads(c["stdout"])
            except ValueError:
                stamp = {"not read": c["stdout"].strip()[-300:]}
            last = next((ln for ln in reversed(v["stdout"].splitlines()) if ln.startswith("check-factory: ")), "")
            out.append({"workspace": w.name, "definition": str(w.factory), "the_workspace_s_own": w.own_factory,
                        "name": stamp.get("name"), "version": stamp.get("version"), "sha256": stamp.get("sha256"), "files": stamp.get("files"),
                        "validity": last.removeprefix("check-factory: "), "problems": [ln for ln in v["stdout"].splitlines()
                                                                                       if ln.startswith("check-factory: ") and ln != last
                                                                                       and "cannot check" not in ln]})
        return runs, {"answer": {"factories": out, "tools": f"every command runs from {HERE}, this server's own tools, never a workspace's; a definition is validated against them"},
                      "composed": True}

    # -- the intake tools
    def agent(self, a) -> tuple:
        by, model = str(a.get("by") or ""), str(a.get("model") or "")
        if not AGENT.fullmatch(by):
            raise Refusal("`by` is an agent's name, agent:<id>. A person's acts (human:) and the platform's (platform:) are never made here: "
                          "a person acts on GitHub")
        if not model.strip() or len(model) > 200 or any(c in model for c in "\x00\n\r"):
            raise Refusal("`model` is the model the agent runs as, one line, said truthfully")
        return by, model

    def t_submit_request(self, a):
        ws = self.ws(a)
        by, model = self.agent(a)
        name = str(a.get("name") or "")
        if not NAME.fullmatch(name):
            raise Refusal("name is letters, digits, - and _ (it becomes requests/NAME.md)")
        if not str(a.get("what_i_want_to_know") or "").strip():
            raise Refusal("what_i_want_to_know is the one line a request cannot be without")
        root = ws.factory.parent if ws.own_factory else PACKAGE
        template = read_bytes(root, "factory/templates/request.md", "the request template").decode("utf-8")
        labels = {v: k for k, v in REQUEST_FIELDS.items()}
        items = {v: k for k, v in LIST_FIELDS.items()}
        out, seen = [], set()
        for ln in template.splitlines():
            m = re.match(r"^\*\*(.+?)\*\*", ln)
            li = re.match(r"^- (If [^:]+:)", ln)
            if ln.startswith("*") and not m:
                continue  # the template's guidance in italics is for whoever fills it in
            if m:
                label = m.group(1).rstrip(".") if not m.group(1).endswith("?") else m.group(1)
                if label not in labels:
                    raise Refusal(f"the template has a field this server does not know ({label}); nothing is written")
                seen.add(labels[label])
                answer = " ".join(str(a.get(labels[label]) or "").split()) if labels[label] != "what_i_will_do" else ""
                out.append(f"**{m.group(1)}**" + (f" {answer}" if answer else ""))
            elif li and li.group(1) in items:
                answer = " ".join(str(a.get(items[li.group(1)]) or "").split())
                out.append(f"- {li.group(1)}" + (f" {answer}" if answer else ""))
            else:
                out.append(ln)
        if seen != set(REQUEST_FIELDS):
            raise Refusal("the template does not have the fields this server knows; nothing is written")
        when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip() + (
            f"\n\n*Written at {when} by tools/factory_server.py from the template, in the words a person gave {by} (model {model}, as "
            "declared). Nothing is started: a study or an exploration binds this file by checksum when it starts.*\n")
        rel = f"requests/{name}.md"
        write_new(ws.root, rel, text, "the request")
        return [], {"answer": {"written": rel, "workspace": ws.name, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                               "next": "start_exploration with request " + rel + ", or a study by sf.py start --request (an agent's step)",
                               "text": text}, "composed": True}

    def t_propose_fresh_data(self, a):
        ws = self.ws(a)
        step = a.get("step")
        out = str(a.get("out") or "")
        if not out.endswith((".yaml", ".yml")):
            raise Refusal("out is a .yaml file below the workspace")
        if inside(ws.root, out, "out").exists():
            raise Refusal(f"{out} already exists: a proposal or metadata file is written once, never over")
        argv = []
        if step == "describe":
            for k in ("csv", "date_column", "subject"):
                if not a.get(k):
                    raise Refusal(f"describe needs {k}")
            argv = ["fresh_data.py", "describe", f"--csv={inside(ws.root, a['csv'], 'csv')}", f"--date-column={a['date_column']}",
                    f"--subject={a['subject']}", f"--what={a['what']}", f"--out={inside(ws.root, out, 'out')}"]
            argv += [f"--{k.replace('_', '-')}={a[k]}" for k in ("series_column", "period", "release", "cadence") if a.get(k) not in (None, "")]
        elif step == "propose":
            by, model = self.agent(a)
            for k in ("metadata", "kind", "why", "unfair"):
                if not a.get(k):
                    raise Refusal(f"propose needs {k}")
            argv = ["fresh_data.py", "propose", f"--metadata={inside(ws.root, a['metadata'], 'metadata')}", f"--kind={a['kind']}",
                    f"--what={a['what']}", f"--why={a['why']}", f"--unfair={a['unfair']}", f"--by={by}", f"--model={model}",
                    f"--out={inside(ws.root, out, 'out')}", f"--studies={ws.root / 'studies'}"]
            argv += [f"--{k.replace('_', '-')}={a[k]}" for k in ("from", "until", "sites", "regions", "release", "periods", "fraction", "draw_over")
                     if a.get(k) not in (None, "")]
        else:
            raise Refusal("step is describe or propose")
        return [run_tool(argv, ws.root)], {"says": "from metadata only: the tool reads one metadata file (or, to describe, one CSV file's "
                                                   "date and series columns) and opens no fresh data"}

    def t_start_exploration(self, a):
        ws = self.ws(a)
        by, model = self.agent(a)
        xid = str(a.get("id") or "")
        if not NAME.fullmatch(xid):
            raise Refusal("id is letters, digits, - and _")
        x = inside(ws.root, f"explorations/{xid}", "the exploration")
        if (x / "exploration-log.jsonl").exists() or (x.exists() and not x.is_dir()):
            raise Refusal(f"explorations/{xid} is already started: an exploration is started once")
        if not (a.get("set_aside_window") or a.get("set_aside_sites") or a.get("set_aside_release")):
            raise Refusal("an exploration started here declares what is set aside (set_aside_window, set_aside_sites or set_aside_release) "
                          "before anything is looked at")
        working = a.get("working_data") or []
        if not working:
            raise Refusal("working_data names the data the looks may be given")
        argv = ["explore.py", "start", f"--exploration={x}", f"--by={by}", f"--model={model}", f"--id={xid}", f"--question={a['question']}",
                f"--request={inside(ws.root, a['request'], 'request')}", f"--subject={a['subject']}", f"--why={a['why']}",
                f"--working={a['working']}", f"--studies={ws.root / 'studies'}"]
        argv += [f"--working-data={inside(ws.root, p, 'working_data')}" for p in working]
        argv += [f"--set-aside-path={inside(ws.root, p, 'set_aside_path')}" for p in a.get("set_aside_path") or []]
        argv += [f"--set-aside-release={r}" for r in a.get("set_aside_release") or []]
        if a.get("fresh_data"):
            argv.append(f"--fresh-data={inside(ws.root, a['fresh_data'], 'fresh_data')}")
        for page in a.get("boundary_from") or []:
            if self.wiki is None:
                raise Refusal("boundary_from names wiki pages, and this server was started without a wiki")
            f = inside(self.wiki, page, "boundary_from")
            if not f.is_file() or f.suffix != ".md":
                raise Refusal(f"no such page in the wiki: {page}")
            argv.append(f"--boundary-from={f}")
        argv += [f"--{k.replace('_', '-')}={a[k]}" for k in ("how", "set_aside_window", "set_aside_sites", "release_cut_off", "working_window")
                 if a.get(k) not in (None, "")]
        return [run_tool(argv, ws.root)], {"says": "started: from here the tool refuses a look that names what was set aside. The looks, the "
                                                   "lead and its review are the agents' work through the tools; the so what is a person's, on GitHub"}

    # -- the protocol
    def call(self, name: str, args: dict) -> dict:
        tool = next((t for t in TOOLS if t["name"] == name), None)
        schema = tool["inputSchema"]
        unknown = sorted(set(args) - set(schema["properties"]))
        if unknown:
            raise Refusal(f"{name} takes no argument named {', '.join(unknown)[:80]}")
        missing = [k for k in schema["required"] if args.get(k) in (None, "", [])]
        if missing:
            raise Refusal(f"{name} needs {', '.join(missing)}")
        for k, v in args.items():
            want = schema["properties"][k]
            ok = (isinstance(v, str) if want["type"] == "string" else isinstance(v, int) and not isinstance(v, bool) if want["type"] == "integer"
                  else isinstance(v, (int, float)) and not isinstance(v, bool) if want["type"] == "number"
                  else isinstance(v, list) and all(isinstance(i, str) for i in v) if want["type"] == "array" else False)
            if not ok or "\x00" in json.dumps(v):
                raise Refusal(f"{k} is {'a list of strings' if want['type'] == 'array' else 'a ' + want['type']}")
            if "enum" in want and v not in want["enum"]:
                raise Refusal(f"{k} is one of {', '.join(want['enum'])}")
        runs, extra = getattr(self, "t_" + name)(args)
        if "content" in extra:
            return {"content": extra["content"], "isError": False}
        failed = [r for r in runs if r["exit"] != 0]
        frame = {"tool": name, "same_as": [r["command"] for r in runs], **{k: v for k, v in extra.items() if k not in ("answer", "composed")}}
        if failed:
            frame["refused"] = failed[0]["stderr"] or failed[0]["stdout"][-2000:]
            frame["exit"] = failed[0]["exit"]
        if extra.get("composed"):
            doc = {**extra["answer"], **({"refused": frame["refused"]} if failed else {}), "same_as": frame["same_as"]}
            return {"content": [{"type": "text", "text": json.dumps(doc, indent=1)}], "isError": bool(failed)}
        main = runs[0]["stdout"] if len(runs) == 1 else "\n".join(r["stdout"] for r in runs)
        try:
            frame["answer"] = json.loads(main) if len(runs) == 1 else [json.loads(r["stdout"]) for r in runs]
            return {"content": [{"type": "text", "text": json.dumps(frame, indent=1)}], "isError": bool(failed)}
        except ValueError:
            return {"content": [{"type": "text", "text": main if main.strip() else (frame.get("refused") or "")},
                                {"type": "text", "text": json.dumps(frame, indent=1)}], "isError": bool(failed)}

    def answer(self, msg: dict) -> dict | None:
        mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if mid is None:
            return None
        if method == "initialize":
            result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                      "serverInfo": {"name": "science-factory", "version": "0.1.0"},
                      "instructions": "Read tools and three intake tools of a science factory. None makes a person's act (the so what, the "
                                      "lock, the signature): where a person acts, the result gives the GitHub page. Say a standing in the "
                                      "tool's words, and never call a lead a finding."}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            if name not in TOOL_NAMES:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"no such tool: {str(name)[:60]}. This server has "
                        + ", ".join(TOOL_NAMES) + "; none makes a person's act, opens fresh data, changes the definition or runs a command"}}
            if not isinstance(args, dict):
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "arguments are an object"}}
            try:
                result = self.call(name, args)
            except Refusal as r:
                result = {"content": [{"type": "text", "text": f"REFUSED by the factory server: {r}"}], "isError": True}
            except subprocess.TimeoutExpired:
                result = {"content": [{"type": "text", "text": "the command took longer than the server waits (900 seconds)"}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def serve(self, stdin=None, stdout=None) -> int:
        stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
            else:
                reply = self.answer(msg) if isinstance(msg, dict) else None
            if reply is not None:
                stdout.write(json.dumps(reply) + "\n")
                stdout.flush()
        return 0


def refuse_inside_a_look() -> None:
    fence = _source_module("factory_server_fence", HERE / "fence.py")
    why = fence.started_under()
    if why:
        raise SystemExit(f"factory_server: started from inside a look or a step of a plan ({why}); a script the tools run does not "
                         "start this server")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--workspace", action="append", type=Path, default=None, help="a workspace (studies/, explorations/); repeatable")
    ap.add_argument("--wiki", type=Path, default=PACKAGE / "openwiki", help="the wiki the knowledge tool searches (default: openwiki/)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    refuse_inside_a_look()
    if any(not Path(w).is_dir() for w in a.workspace or []) or not a.workspace:
        print("factory_server: each --workspace is a folder, and at least one is given", file=sys.stderr)
        return 2
    return Server(a.workspace, a.wiki).serve()


# ---------------------------------------------------------------- the self-test

AUDIT_DRIVER = r'''
import json, os, sys
log = open(sys.argv[1], "w")
def hook(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        log.write(json.dumps(["open", os.path.abspath(os.fsdecode(args[0]))]) + "\n")
    elif event == "subprocess.Popen":
        log.write(json.dumps(["run", [os.fsdecode(w) for w in (args[1] or [args[0]])]]) + "\n")
    elif event in ("os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.startfile", "ctypes.dlopen"):
        log.write(json.dumps([event, repr(args)[:300]]) + "\n")
    log.flush()
sys.addaudithook(hook)
import importlib.util
spec = importlib.util.spec_from_file_location("factory_server_under_audit", sys.argv[2])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.exit(mod.main(sys.argv[3:]))
'''
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
SECRET = "SECRET-LINE-OUTSIDE-EVERY-ROOT"
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    results = []

    def check(name: str, good) -> None:
        results.append((name, bool(good)))

    explore = _source_module("explore", HERE / "explore.py")
    sf = explore.sf
    sf.Study.default_model = "selftest-model"
    sf.Study.default_route = sf.PRACTICE
    sf.PLATFORM_CALL = sf._dead_platform
    A, SA = explore.A, sf.A
    tmp = Path(tempfile.mkdtemp(prefix="factory-server-")).resolve()
    quiet = contextlib.redirect_stdout(io.StringIO())
    try:
        alpha, beta, crafted, wiki = tmp / "alpha", tmp / "beta", tmp / "crafted", tmp / "wiki"
        for w in (alpha, beta, crafted):
            (w / "studies").mkdir(parents=True)
            (w / "explorations").mkdir()
        (tmp / "secret.md").write_text(f"# outside\n\n{SECRET}\n")
        wiki.mkdir()
        (wiki / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# toy\n')
        (wiki / "the-toy-record.md").write_text("---\ntype: dataset\nstatus: draft\n---\n\n# The toy record of y against x\n\nMonthly; "
                                                "2025 is a new year of the same record.\n\n## Where it changes\n\nNowhere known.\n")
        shutil.copytree(sf.FACTORY, beta / "factory", ignore=shutil.ignore_patterns("__pycache__"))
        # alpha: an exploration taken to a reviewed lead, with a fit note and a figure, and a study with a lock request
        with quiet:
            x = explore.Exploration(alpha / "explorations" / "X1")
            data = alpha / "data" / "X1" / "record.json"
            data.parent.mkdir(parents=True)
            data.write_text(json.dumps({"window": {"start": "2024-01-01", "end": "2024-12-31"},
                                        "rows": [{"time": f"2024-{m:02d}-15T00:00:00Z", "x": m * 1.0, "y": m * 2.0} for m in range(1, 13)]}))
            req = tmp / "request-x1.md"
            req.write_text("# Request\n\nDoes y follow x, and where does it not?\n")
            explore.cmd_start(x, A(by="agent:analysis-x", request=str(req), id="X1", subject="record=toy,case=X1",
                                   set_aside_window="2025-01-01:2025-12-31", working_data=[str(data)], question="Does y follow x?"))
            fit = tmp / "fit.yaml"
            fit.write_text("answer_is: checkable\ndata_at_hand: 'yes'\nmostly: computation\nperson_must_supply: the difference that matters\n"
                           "verdict: fit-with-a-person-steering\nwhy: a ratio a rule can test, on a toy record\ntaste_needed: which months to trust\n")
            explore.cmd_fit(x, A(by="agent:coordinating-x", file=str(fit)))
            explore.cmd_reviewer(x, A(by="agent:coordinating-x", reviewer="agent:review-x"))
            explore.cmd_known(x, A(by="agent:analysis-x", bundle=[]))
            (x.d / "looks").mkdir(exist_ok=True)
            (x.d / "looks" / "ratio.py").write_text("import json, sys\nrows = json.load(open(sys.argv[1]))['rows']\nprint('rows', len(rows))\n")
            (x.d / "looks" / "picture.py").write_text("import base64, os\nos.makedirs('figures', exist_ok=True)\nopen('figures/dot.png', 'wb').write("
                                                      f"base64.b64decode({base64.b64encode(PNG).decode()!r}))\nprint('drawn')\n")
            explore.cmd_look(x, A(by="agent:analysis-x", argv=["--", "{python}", "looks/ratio.py", str(data)], why="how many rows there are"))
            explore.cmd_look(x, A(by="agent:analysis-x", argv=["--", "{python}", "looks/picture.py"], why="a picture of one dot, for the self-test"))
            lead = {"summary": {"looks_true": "In 2024 y seems to follow x over twelve months.", "how_strong": "One look at one year of working data.",
                                "cannot_settle": "Whether it holds in 2025, which was set aside."},
                    "what_looks_true": "y looks as if it follows x over the 2024 rows.", "how_it_was_found": "One look at the rows.",
                    "evidence": ["LOOK-001"], "choices_that_would_change_it": [], "choices_that_would_not": [], "pitfalls": ["one year only"],
                    "proposed_plan": {"question": "Over 2025, does y follow x within five percent?", "quantity_estimated": "the ratio of y to x",
                                      "difference_that_matters": "five percent, proposed", "rule_sketch": "supported if the interval lies inside the band"}}
            lf = tmp / "lead.yaml"
            lf.write_text(json.dumps(lead))
            explore.cmd_lead(x, A(by="agent:analysis-x", file=str(lf)))
            rv = tmp / "review.md"
            rv.write_text("# Review (exploring)\n\nChecked the log and the look. One hole: one year only.\n")
            explore.cmd_review(x, A(by="agent:review-x", verdict="holes-found", file=str(rv), read_lead=sf.sha_file(x.d / "lead.json")))
            s1 = sf._fresh(alpha / "studies", "S1", start=SA(id="S1", question=sf.PLAN["question"], by="agent:coordinating"))
            sf.cmd_test(s1, SA(what="known-answers", by="agent:analysis"))
            sf.cmd_test(s1, SA(what="working-data", by="agent:analysis"))
            sf.cmd_request_lock(s1, SA(by="agent:coordinating"))
        (alpha / "data" / "X2").mkdir(parents=True)
        (alpha / "data" / "X2" / "record.json").write_text(data.read_text())
        (alpha / "source").mkdir()
        (alpha / "source" / "series.csv").write_text("Source,Date,Value\n" + "".join(
            f"A,{y}-{m:02d},{m / 10:.2f}\n" for y in (2024, 2025) for m in range(1, 13)))
        figure_sha = sf.sha_file(x.d / "figures" / "dot.png")
        # crafted: a workspace made to trick the server
        marks = tmp / "marks"
        marks.mkdir()
        (crafted / "tools").mkdir()
        for t in ("sf.py", "explore.py", "waiting.py", "report.py", "check_factory.py", "fresh_data.py"):
            (crafted / "tools" / t).write_text(f"open({str(marks / ('tools-' + t))!r}, 'w').write('ran')\n")
        evil = crafted / "evil.sh"
        evil.write_text(f"#!/bin/sh\ntouch {marks / 'git-ran'}\n")
        evil.chmod(0o755)
        if shutil.which("git"):
            subprocess.run(["git", "init", "-q", str(crafted)], capture_output=True)
            for k, v in (("core.fsmonitor", str(evil)), ("core.hooksPath", str(crafted)), ("core.pager", str(evil)), ("diff.external", str(evil)),
                         ("core.sshCommand", str(evil)), ("core.askPass", str(evil))):
                subprocess.run(["git", "-C", str(crafted), "config", k, v], capture_output=True)
            for hook in ("pre-commit", "post-checkout", "reference-transaction", "fsmonitor-watchman"):
                shutil.copyfile(evil, crafted / hook)
                (crafted / hook).chmod(0o755)
        shutil.copytree(sf.FACTORY, crafted / "factory", ignore=shutil.ignore_patterns("__pycache__"))
        (crafted / "explorations" / "LINKED").symlink_to(alpha / "explorations" / "X1")
        (crafted / "explorations" / "X9").mkdir()
        (crafted / "explorations" / "X9" / "exploration-log.jsonl").symlink_to(tmp / "secret.md")
        shutil.copytree(x.d, crafted / "explorations" / "X8")
        (crafted / "explorations" / "X8" / "lead.md").unlink()
        (crafted / "explorations" / "X8" / "lead.md").symlink_to(tmp / "secret.md")
        (crafted / "explorations" / "X8" / "figures" / "dot.png").unlink()
        (crafted / "explorations" / "X8" / "figures" / "dot.png").symlink_to(tmp / "secret.md")
        (crafted / "requests").symlink_to(tmp)

        def snapshot() -> dict:
            return {p.as_posix(): (p.read_bytes() if p.is_file() and not p.is_symlink() else str(os.readlink(p)) if p.is_symlink() else "")
                    for p in tmp.rglob("*") if "marks" not in p.parts and ".git" not in p.parts and p.name != "audit.jsonl"}

        def call(i, tool_, **kw):
            return {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": tool_, "arguments": kw}}

        reads = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
                 {"jsonrpc": "2.0", "method": "notifications/initialized"}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                 call(10, "waiting"), call(11, "waiting", format="json", workspace="alpha"),
                 call(12, "status", workspace="alpha", path="explorations/X1"), call(13, "status", workspace="alpha", path="S1"),
                 call(14, "lead", workspace="alpha", path="X1"), call(15, "figure", workspace="alpha", path="X1"),
                 call(16, "figure", workspace="alpha", path="X1", look="LOOK-002", sha256=figure_sha[:16]),
                 call(17, "figure", workspace="alpha", path="X1", look="LOOK-002", sha256="0" * 16),
                 call(18, "report", workspace="alpha"), call(19, "report", workspace="alpha", format="json"),
                 call(20, "fit_note", workspace="alpha", path="X1"), call(21, "fit_note", workspace="alpha", path="S1"),
                 call(22, "contribution", workspace="alpha", path="X1"), call(23, "contribution", workspace="alpha", path="S1"),
                 call(24, "knowledge", query="Is 2025 a new year of the toy record?"), call(25, "knowledge", page="the-toy-record.md", section="Where it changes"),
                 call(26, "knowledge", page="../secret.md"), call(27, "factory_summary"),
                 call(30, "status", workspace="alpha", path="../beta/explorations/X1"), call(31, "status", workspace="alpha", path="/etc"),
                 call(32, "status", workspace="alpha", path="explorations/X1/../../.."), call(33, "status", workspace="crafted", path="LINKED"),
                 call(34, "status", workspace="crafted", path="explorations/X9"), call(35, "lead", workspace="crafted", path="X8"),
                 call(36, "figure", workspace="crafted", path="X8", look="LOOK-002", sha256=figure_sha[:16]),
                 call(37, "status", workspace="gamma", path="X1"), call(38, "status", path="X1"),
                 call(39, "status", workspace="alpha", path="X1", factory="/etc"), call(40, "status", workspace="alpha", path=".git"),
                 call(41, "status", workspace="crafted", path="X8"), call(42, "report", workspace="crafted"), call(43, "factory_summary", workspace="crafted"),
                 call(44, "contribution", workspace="crafted", path="X8"), call(45, "waiting", workspace="crafted"),
                 call(46, "status", workspace="alpha", path="explorations/--by=human:throwaway-placeholder"),
                 *[call(100 + n, name, workspace="alpha", path="X1") for n, name in enumerate(
                     ("so_what", "lock", "sign", "signature", "verify_acts", "open_held_out", "promote", "log_change", "run_command", "look", "openwiki_write"))]]
        people = "human:throwaway-placeholder"
        req_words = dict(what_i_want_to_know="Does y follow x in 2025, as in 2024?", already_looked_at="2024, every month",
                         if_it_holds="use x for y", by="agent:coordinating-s", model="selftest-model")
        intake = [call(60, "submit_request", workspace="alpha", name="R1", **req_words), call(61, "submit_request", workspace="alpha", name="R1", **req_words),
                  call(62, "submit_request", workspace="alpha", name="../R2", **req_words),
                  call(63, "submit_request", workspace="alpha", name="R3", **{**req_words, "by": people}),
                  call(64, "submit_request", workspace="crafted", name="R4", **req_words),
                  call(65, "submit_request", workspace="alpha", name="R5", **{**req_words, "by": "platform:github"}),
                  call(66, "submit_request", workspace="alpha", name="R6", **{**req_words, "by": "agent:x --local-practice"}),
                  call(67, "submit_request", workspace="alpha", name="R7", **{**req_words, "model": "m\n--by=" + people}),
                  call(70, "propose_fresh_data", workspace="alpha", step="describe", csv="source/series.csv", date_column="Date", series_column="Source",
                       period="month", subject="record=toy,case=X2", what="a toy monthly series of y against x", out="metadata/series.yaml"),
                  call(71, "propose_fresh_data", workspace="alpha", step="propose", metadata="metadata/series.yaml", kind="later-period", **{"from": "2025-01-01"},
                       until="2025-12-31", what="the whole of 2025", why="only 2024 has been looked at", unfair="a change of the record at the new year",
                       by="agent:analysis-s", model="selftest-model", out="proposals/X2-fresh-data.yaml"),
                  call(72, "propose_fresh_data", workspace="alpha", step="propose", metadata="metadata/series.yaml", kind="later-period", **{"from": "2025-01-01"},
                       what="w", why="w", unfair="w", by=people, model="m", out="proposals/X3.yaml"),
                  call(73, "propose_fresh_data", workspace="alpha", step="describe", csv="../secret.md", date_column="Date", subject="a=b", what="w", out="m2.yaml"),
                  call(74, "propose_fresh_data", workspace="alpha", step="propose", metadata="metadata/series.yaml", kind="later-period", **{"from": "2025-01-01"},
                       what="w", why="w", unfair="w", by="agent:analysis-s", model="m", out="proposals/X2-fresh-data.yaml"),
                  call(80, "start_exploration", workspace="alpha", id="X2", question="Does y follow x over 2024?", request="requests/R1.md",
                       subject="record=toy,case=X2", how="a later period", set_aside_window="2025-01-01:2025-12-31",
                       fresh_data="proposals/X2-fresh-data.yaml", why="the following year --by=" + people + " --local-practice",
                       working="the 2024 record", working_data=["data/X2"], working_window="2024-01-01:2024-12-31",
                       boundary_from=["the-toy-record.md"], by="agent:analysis-s", model="selftest-model"),
                  call(81, "start_exploration", workspace="alpha", id="X2", question="Again?", request="requests/R1.md", subject="a=b",
                       set_aside_window="2025-01-01:2025-12-31", why="w", working="w", working_data=["data/X2"], by="agent:analysis-s", model="m"),
                  call(82, "start_exploration", workspace="alpha", id="X3", question="Nothing set aside?", request="requests/R1.md", subject="a=b",
                       why="w", working="w", working_data=["data/X2"], by="agent:analysis-s", model="m"),
                  call(83, "start_exploration", workspace="alpha", id="X4", question="q?", request="requests/R1.md", subject="a=b", why="w", working="w",
                       working_data=["data/X2"], by="agent:analysis-s", model="m", nothing_set_aside="none"),
                  call(84, "start_exploration", workspace="alpha", id="X5", question="q?", request="requests/R1.md", subject="a=b",
                       set_aside_window="2025-01-01:2025-12-31", why="w", working="w", working_data=["data/X2"], by=people, model="m"),
                  call(85, "start_exploration", workspace="alpha", id="X6", question="q?", request="requests/R1.md", subject="a=b",
                       set_aside_window="2025-01-01:2025-12-31", why="w", working="w", working_data=["/etc"], by="agent:analysis-s", model="m"),
                  call(86, "start_exploration", workspace="alpha", id="X7", question="q?", request="requests/R1.md", subject="a=b",
                       set_aside_window="2025-01-01:2025-12-31", why="w", working="w", working_data=["data/X2"], by="agent:analysis-s", model="m",
                       local_practice=True)]
        audit = tmp / "audit.jsonl"
        env = {k: v for k, v in os.environ.items() if k not in TOKENS}
        before = snapshot()
        driver = [sys.executable, "-I", "-B", "-c", AUDIT_DRIVER, str(audit), str(Path(__file__).resolve()),
                  "--workspace", str(alpha), "--workspace", str(beta), "--workspace", str(crafted), "--wiki", str(wiki)]
        done = subprocess.run(driver, input="\n".join(json.dumps(m) for m in reads) + "\n", capture_output=True, text=True, env=env, timeout=1800)
        after_reads = snapshot()
        got = {r["id"]: r for r in (json.loads(ln) for ln in done.stdout.splitlines() if ln.strip())}

        def cli(*argv):
            d = subprocess.run([sys.executable, str(HERE / argv[0]), *argv[1:]], capture_output=True, text=True, env=environment(True), cwd=str(alpha))
            return d.stdout

        own_factory = str((PACKAGE / "factory").resolve())
        said = {"waiting": [cli("waiting.py", f"--workspace={w}", f"--factory={f}") for w, f in
                            ((alpha, own_factory), (beta, (beta / "factory").resolve()), (crafted, (crafted / "factory").resolve()))],
                "report": cli("report.py", f"--workspace={alpha}", f"--factory={own_factory}"),
                "x1": cli("explore.py", "status", f"--exploration={x.d}"), "s1": cli("sf.py", "status", f"--study={s1.d}", f"--factory={own_factory}"),
                "cx": cli("explore.py", "contribution", f"--exploration={x.d}", "--print-only"),
                "cs": cli("sf.py", "contribution", f"--study={s1.d}", f"--factory={own_factory}", "--print-only"),
                "sum": cli("check_factory.py", own_factory, f"--repository={PACKAGE}", "--checksum")}
        done2 = subprocess.run(driver, input="\n".join(json.dumps(m) for m in intake) + "\n", capture_output=True, text=True, env=env, timeout=1800)
        got.update({r["id"]: r for r in (json.loads(ln) for ln in done2.stdout.splitlines() if ln.strip())})
        after = snapshot()

        def text(i, n=0):
            r = got.get(i, {}).get("result") or {}
            c = r.get("content") or [{}]
            return c[n].get("text", "") if len(c) > n else ""

        def doc(i):
            try:
                return json.loads(text(i))
            except ValueError:
                return {}

        def err(i):
            r = got.get(i, {})
            return "error" in r or (r.get("result") or {}).get("isError") is True

        def same(a_, b_):
            return STAMP.sub("T", a_) == STAMP.sub("T", b_)

        # the protocol and the list
        check("it answers the handshake, stays silent on a notification, and answers every request of both sessions",
              got.get(1, {}).get("result", {}).get("protocolVersion") == PROTOCOL and len(got) == len([m for m in reads + intake if "id" in m]))
        names = [t["name"] for t in got.get(2, {}).get("result", {}).get("tools", [])]
        check("it offers exactly the nine read tools and three intake tools", names == TOOL_NAMES and len(names) == 12)
        bad_words = ("lock", "sign", "so_what", "verify", "open", "promote", "change", "approve", "merge", "run", "shell", "exec", "look")
        check("no tool's name is a person's act, an opening, a promotion, a change to the definition or a command",
              not [n for n in names if any(w in n for w in bad_words)])
        check("every forbidden name is no tool: the act is unreachable by name",
              all("error" in got.get(100 + n, {}) and "no such tool" in got[100 + n]["error"]["message"] for n in range(11)))
        check("every tool takes only the arguments it lists", all(t["inputSchema"].get("additionalProperties") is False for t in TOOLS))
        # the allow list
        check("the allow list is exactly the ten commands the tools wrap",
              set(ALLOW) == {("waiting.py", None), ("report.py", None), ("check_factory.py", None), ("sf.py", "status"), ("sf.py", "contribution"),
                             ("explore.py", "status"), ("explore.py", "contribution"), ("fresh_data.py", "describe"), ("fresh_data.py", "propose"),
                             ("explore.py", "start")})
        check("no entry of the allow list is a forbidden command or carries a forbidden option",
              not {c for _, c in ALLOW} & FORBIDDEN_COMMANDS and not set().union(*(e["options"] | e.get("flags", set()) for e in ALLOW.values())) & FORBIDDEN_OPTIONS)
        refused_lists = [["sf.py", "lock", "--study=/s", f"--by={people}", "--local-practice"], ["explore.py", "so-what", "--exploration=/x"],
                         ["sf.py", "verify-acts", "--study=/s"], ["sf.py", "open-held-out", "--study=/s"], ["explore.py", "promote", "--exploration=/x"],
                         ["sf.py", "log-change", "--study=/s"], ["explore.py", "look", "--exploration=/x", "--", "python3", "x.py"],
                         ["fresh_data.py", "reveal", "--proposal=/p"], ["explore.py", "start", f"--by={people}"],
                         ["explore.py", "start", "--by=platform:github"], ["explore.py", "start", "--local-practice"],
                         ["explore.py", "start", "--why", "x"], ["explore.py", "start", "--nothing-set-aside=none"],
                         ["sf.py", "status", "--study=/s", "--by=agent:a"], ["sf.py", "contribution", "--study=/s"],
                         ["check_factory.py", "--summary=a"], ["check_factory.py", "relative/path"], ["../sf.py", "status"], ["bash", "-c", "x"],
                         ["factory_update.py", "update"], ["waiting.py", "--workspace=/w", "--selftest"], ["sf.py", "status", "--study=/s\x00"]]
        check("the allow check refuses every list of words that would make an act, run a script or pass a forbidden option",
              all(allowed(w) for w in refused_lists))
        try:
            run_tool(["sf.py", "lock", "--study=/s"], tmp)
            check("run_tool refuses what the allow check refuses, before starting anything", False)
        except Refusal:
            check("run_tool refuses what the allow check refuses, before starting anything", True)
        own = Path(__file__).read_text().split("# ---------------------------------------------------------------- the self-test")[0]
        check("the server starts a process in one place, run_tool, and nowhere calls a shell or exec",
              own.count("subprocess.run(") == 1 and "Popen" not in own and "os.system" not in own and "shell=True" not in own
              and "exec(" not in own.replace("exec_module(", ""))
        # what ran, and what was opened, under the audit hook
        ev = [json.loads(ln) for ln in audit.read_text().splitlines() if ln.strip()] if audit.is_file() else []
        ran = [e[1] for e in ev if e[0] == "run"]
        check("every process the server started was one of its own tools on the allow list, and it started some",
              ran and all(w[0] == sys.executable and w[1].startswith(str(HERE) + os.sep) and allowed([Path(w[1]).name, *w[2:]]) is None for w in ran))
        check("no command of a person's act, no look and no shell was ever started",
              not [w for w in ran if set(w[2:3]) & FORBIDDEN_COMMANDS] and not [e for e in ev if e[0] not in ("open", "run", "ctypes.dlopen")])
        roots = [str(p) for p in (alpha, beta, crafted, wiki, HERE, PACKAGE / "factory")]
        python = {os.path.realpath(p) for p in (sys.prefix, sys.base_prefix, sys.exec_prefix)} | {os.path.realpath(p) for p in sys.path if p}
        outside = sorted({p for kind_, p in ev if kind_ == "open" for rp in [os.path.realpath(p)]
                          if not any(rp == r or rp.startswith(r + os.sep) for r in roots + sorted(python))
                          and not rp.startswith(("/proc/", "/dev/null")) and rp != str(audit)})
        check("the server opened no file outside its roots (the workspaces, the wiki, its own tools and factory; Python's own files and "
              "/proc for the look check apart)", ev and not outside)
        if outside:
            print("opened outside the roots:", outside[:8])
        check("nothing the server returned holds the secret outside every root", SECRET not in done.stdout + done2.stdout)
        check("no tool in the crafted workspace's tools/ ran, and no git setting of it ran a command",
              not list(marks.iterdir()))
        check("the read tools changed no file anywhere", before == after_reads)
        # each read tool, against the command line
        check("waiting across three workspaces with their factories is the command line's answer for each, in its words",
              same(text(10), "\n".join(said["waiting"])) and "so-what-wanted" in text(10))
        wj = doc(11).get("answer") or {}
        sw = [i for g in wj.get("groups", []) for i in g["items"] if i["what"] == "so-what-wanted"]
        lk = [i for g in wj.get("groups", []) for i in g["items"] if i["what"] == "lock-request-not-merged"]
        check("waiting as JSON gives the so what wanted with the comment's lines, and the lock request with the GitHub page to open",
              len(sw) == 1 and "exploration: explorations/X1" in sw[0]["next_step"]["do"]
              and len(lk) == 1 and lk[0]["next_step"]["open"].startswith("https://github.com/") and "standings" in wj)
        check("status of an exploration is explore.py status's answer, with the so what wanted and the standings in the tools' words",
              same(json.dumps(doc(12).get("answer")), json.dumps(json.loads(said["x1"])))
              and [i["what"] for i in doc(12).get("where_a_person_acts", [])] == ["so-what-wanted"] and "not re-checked now" in str(doc(12).get("standings")))
        check("status of a study is sf.py status's answer, with the lock request waiting and the page to open",
              same(json.dumps(doc(13).get("answer")), json.dumps(json.loads(said["s1"])))
              and doc(13).get("where_a_person_acts", [{}])[0].get("next_step", {}).get("open", "").startswith("https://github.com/"))
        ld = doc(14)
        check("lead gives the summary block, the lead's first line, the review and its verdict on the lead as it stands, and the person's next step",
              "In 2024 y seems to follow x" in ld.get("lead", {}).get("summary", "") and "lead, not a finding" in ld.get("lead", {}).get("first_line", "")
              and ld.get("lead", {}).get("file_is_the_one_recorded") is True
              and [(r["by"], r["verdict"], r["of_the_lead_as_it_stands"]) for r in ld.get("reviews", [])] == [("agent:review-x", "holes-found", True)]
              and "One hole" in ld["reviews"][0]["text"] and ld.get("stage") == "so-what"
              and [i["what"] for i in ld.get("where_a_person_acts", [])] == ["so-what-wanted"] and "never a finding" in ld.get("says", ""))
        figs = doc(15).get("figures", [])
        check("figure lists the figures a look kept, by look and checksum, with the look's reason as the caption",
              figs == [{"look": "LOOK-002", "file": "figures/dot.png", "sha256": figure_sha, "caption": "a picture of one dot, for the self-test"}])
        c16 = (got.get(16, {}).get("result") or {}).get("content") or [{}, {}]
        check("figure returns the picture as an image the client can show, byte for byte, with its caption and checksum",
              len(c16) == 2 and c16[1].get("type") == "image" and c16[1].get("mimeType") == "image/png"
              and base64.b64decode(c16[1].get("data", "")) == PNG and "a picture of one dot" in c16[0].get("text", "") and figure_sha[:12] in c16[0]["text"])
        check("figure refuses a checksum that is not a kept figure's", err(17) and "no figure" in text(17))
        check("report in Markdown and in JSON is report.py's answer", same(re.sub(r"\d+", "#", text(18)), re.sub(r"\d+", "#", said["report"])) and (doc(19).get("answer") or {}).get("schema") == "science-factory/report/v1")
        check("fit_note gives the note as recorded and in the tools' words, and says when none was written",
              (doc(20).get("note_as_recorded") or {}).get("verdict") == "fit-with-a-person-steering" and "fit-with-a-person-steering" in str(doc(20).get("fit"))
              and doc(21).get("note_as_recorded") is None and "No fit note was written" in str(doc(21).get("fit")))
        check("contribution is the command line's statement, and no contribution file is written",
              same(text(22), said["cx"])
              and same(text(23), said["cs"])
              and "Who did what" in text(22) and not (x.d / "contribution.md").exists() and not (s1.d / "contribution.md").exists())
        ws_ = _source_module("factory_server_wiki_check", HERE / "wiki_server.py")
        check("knowledge searches and reads as the wiki server does, and refuses a page outside the wiki",
              text(24) == ws_.search(wiki, "Is 2025 a new year of the toy record?") and text(24).startswith("the-toy-record.md |")
              and text(25).startswith("## Where it changes") and "no such page" in text(26))
        fs = doc(27).get("factories", [])
        check("factory_summary names each workspace's definition, its version and checksum, and says it is valid, as check_factory.py does",
              [f["workspace"] for f in fs] == ["alpha", "beta", "crafted"] and [f["the_workspace_s_own"] for f in fs] == [False, True, True]
              and all(f["validity"].startswith("VALID") for f in fs)
              and fs[0]["sha256"] == json.loads(said["sum"])["sha256"])
        # path tricks and the crafted workspace
        check("a path that leaves the workspace, an absolute path, `..`, a hidden part or an option as a name is refused",
              all(err(i) and "REFUSED by the factory server" in text(i) for i in (30, 31, 32, 40, 46)))
        check("a study or exploration that is a link out of the workspace, or whose log is a link, is refused", err(33) and err(34))
        check("a lead page or a figure that is a link out of the workspace is refused, and the secret is not shown",
              err(35) and "symbolic link" in text(35) and err(36))
        check("an unknown workspace, a missing one when several are reached, and an argument no tool lists are refused",
              err(37) and err(38) and err(39) and "no argument named factory" in text(39))
        check("on the crafted workspace the server runs its own tools, never the workspace's: status, summary and contribution answer, "
              "and report and waiting give the tools' own refusal of the linked exploration", not err(41) and not err(43) and not err(44)
              and all(err(i) and "reached through a symlink" in text(i) for i in (42, 45)))
        planted = tmp / "planted"
        shutil.copytree(crafted / "factory", planted / "factory")
        (planted / "factory" / "harnesses" / "github" / "verify_acts.py").write_text("print('planted')\n")
        try:
            Workspace(planted)
            check("a workspace whose definition carries code other than the server's is refused at the start", False)
        except Refusal as r:
            check("a workspace whose definition carries code other than the server's is refused at the start", "verify_acts.py" in str(r))
        # intake
        r1 = alpha / "requests" / "R1.md"
        check("submit_request writes the request from the template, in the person's words, saying who typed it",
              r1.is_file() and "**What I want to know.** Does y follow x in 2025, as in 2024?" in r1.read_text()
              and "- If it holds: use x for y" in r1.read_text() and "agent:coordinating-s" in r1.read_text() and not err(60))
        check("submit_request refuses to write over a request, a name with a path in it, and a requests folder that is a link",
              err(61) and "already exists" in text(61) and err(62) and err(64) and not list(tmp.glob("R4*")))
        check("an intake tool refuses a person's name, the platform's, a name with an option in it and a model on two lines",
              all(err(i) and "REFUSED by the factory server" in text(i) for i in (63, 65, 66, 67)) and not (alpha / "requests" / "R3.md").exists())
        check("propose_fresh_data describes a CSV from its date column and proposes from that metadata, as fresh_data.py does",
              not err(70) and (alpha / "metadata" / "series.yaml").is_file() and not err(71) and "proposal written" in text(71)
              and (alpha / "proposals" / "X2-fresh-data.yaml").is_file())
        check("propose_fresh_data refuses a person, a file outside the workspace, and a proposal written twice",
              err(72) and err(73) and err(74) and "already exists" in text(74))
        x2 = alpha / "explorations" / "X2" / "exploration-log.jsonl"
        first = json.loads(x2.read_text().splitlines()[0]) if x2.is_file() else {}
        check("start_exploration starts the exploration as the agent, with its model recorded, setting aside the proposal's window",
              not err(80) and first.get("actor") == "agent:analysis-s" and first.get("model") == "selftest-model"
              and first.get("data", {}).get("set_aside", {}).get("window") == {"start": "2025-01-01", "end": "2025-12-31"})
        check("an option typed inside a value stays a value: the reason is recorded word for word and no practice act appears",
              first.get("data", {}).get("set_aside", {}).get("why", "").endswith("--local-practice") and people not in json.dumps(
                  [json.loads(ln).get("actor") for ln in x2.read_text().splitlines()] if x2.is_file() else [people]))
        check("start_exploration refuses a second start, nothing set aside, a person, working data outside the workspace, and the "
              "options no tool lists", all(err(i) for i in (81, 82, 83, 84, 85, 86)) and not any((alpha / "explorations" / n).exists() for n in ("X3", "X4", "X5", "X6", "X7")))
        made = sorted(k for k in set(after) - set(before))
        check("intake wrote only the request, the metadata, the proposal, the exploration and the record of what is set aside",
              all(m_.startswith(tuple(str(alpha / p) for p in ("requests", "metadata", "proposals", "explorations/X2", "studies/fresh-data.jsonl"))) for m_ in made)
              and {k for k in before if before[k] != after.get(k)} <= {str(alpha / "studies" / "openings.jsonl"), str(alpha / "studies" / "fresh-data.jsonl")})
        check("serving left no bytecode folder beside the tools", not (HERE / "__pycache__").exists())
        if done.stderr.strip() or done2.stderr.strip():
            print("server said on standard error:", (done.stderr + done2.stderr)[-600:])
    finally:
        sf.Study.default_model = None
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
