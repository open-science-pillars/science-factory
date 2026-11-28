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
    ("check_factory.py", None): {"options": set(), "flags": {"--checksum"}, "positional": 1, "reads": True},
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


class Workspace:
    def __init__(self, folder: Path):
        self.root = Path(folder).resolve()
        self.name = self.root.name
        own = self.root / "factory"
        self.own_factory = (not own.is_symlink() and own.is_dir() and not (own / "factory.yaml").is_symlink()
                            and (own / "factory.yaml").is_file())
        self.factory = own if self.own_factory else (PACKAGE / "factory").resolve()


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
        self.workspaces = [Workspace(w) for w in workspaces]
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
            v = run_tool(["check_factory.py", str(w.factory)], w.root)
            c = run_tool(["check_factory.py", str(w.factory), "--checksum"], w.root)
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
        return runs, {"answer": {"factories": out, "tools": f"every command runs from {HERE}, this server's own tools, never a workspace's"},
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
        if x.exists():
            raise Refusal(f"explorations/{xid} already exists: an exploration is started once")
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


# SELFTEST


if __name__ == "__main__":
    sys.exit(main())
