#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""sf: the study tool. It keeps the study log and enforces the procedure.

One study is one directory: an analysis plan (analysis-plan.yaml: the
question, the quantity estimated, which data is working data and which is
held out, the code, and the decision rules), a study log (study-log.jsonl),
run receipts (a run receipt is the record a run writes, with its code and
inputs by checksum and every number it produced), notes and reviews. The
tool only ever adds to the study log and chains each event to the one
before it by hash, so a later edit can be detected against a commit or a
log fingerprint posted outside the workspace (the third limit below says
what that does not cover). This tool holds no opinion and runs no language
model. It keeps the order of events honest.

Commands, by stage. Each has one name.

  Ask
    start                 a study exists; with --request, the request it
                          answers is bound to it by checksum
    status                where the study stands, read from the procedure
    close                 the study ends: answered already, a signed
                          result, or a recorded decision not to sign
  Plan
    check-plan            the analysis plan is complete and well formed
  Test (repeat freely; every attempt is logged)
    test known-answers    synthetic data with the truth put in
    test working-data     data already looked at
    rehearse              a required rehearsal of what the opening
                          depends on (its fetch, the form of the finding)
    held-out-change       the coordinating step records that what the
                          plan holds out has changed, and why; without
                          it the tests and the lock refuse a plan whose
                          held-out block is not the one on record
  Open the held-out data, once
    request-lock          write the lock request into the study: an
                          evidence summary in plain words and a manifest
                          of checksums, once the tests have passed on
                          exactly this plan and code and every decision
                          rule has met its criteria. Nothing is locked
    check-request         does a request still match the files? (the
                          required check of the pull request)
    lock                  the lock itself, which is a person's act. In a
                          real study it is the merge of the pull request
                          that carries the request, on the protected
                          branch, recorded with --record-merge by the
                          job that follows the merge. --local-practice
                          records a lock typed at a command line, for
                          trying the tools out: such a study says so
                          everywhere and never closes as a signed finding
    open-held-out         the access gate fetches the held-out data
                          and runs the locked analysis, once; the
                          opening is used up the moment it starts. It
                          needs a lock that is a merge on the protected
                          branch, reachable from what is checked out,
                          whose manifest matches the files, and a
                          definition that has not changed since the lock
    void-unread           a person voids an opening whose fetch failed
                          and left nothing behind
  Review, sign and learn
    attach                the written finding joins the record
    review                a review assistant that did none of the study
                          records approve or block, after the finding
    request-signature     write the signature request into the study:
                          the finding, the review, the outcome, and
                          what merging would sign. Nothing is signed
    signature             the steward signed, or declined, which finding,
                          and where: the merge of the pull request that
                          carries the request (--record-merge), or, for
                          practice, typed (--local-practice)
    note                  something missing or wrong, with evidence
    curation-list         open notes, for the curating assistant
    resolve               a note is accepted, linked or declined
    scorecard             the procedure's process checks for this study
    log-change            a change to the procedure, with its prediction
  The log
    fingerprint           the log's fingerprint, to post outside the workspace
    check-log             everything re-checked from the files and
                          against posted fingerprints
    selftest              the tool tests itself, attacks included

What a command is. Every command in a plan (a test, a fetch, a rehearsal
step) is a launcher the tool knows, then a script file, then the script's
own arguments. The launchers are `{python}` followed directly by the
script, and `uv run` followed by the script (a file whose name ends in
.py, or any file after --script). The script has to exist, and the lock
binds it and prints, for each command, which script that is. Anything the
tool cannot take apart this way is refused by the plan check, whatever the
program: a shell, `env`, `make`, `{python} -c`, `uv run python`. This is a
rule about what is allowed, not a list of what is not, because a script
named inside another program's text is a script the lock never sees.

How a command runs. Like a look of the exploring tool, through
tools/fence.py: in a scratch copy of the study that holds no study log, no
notes and no verdicts; with an interpreter prepared before it starts
(`uv run` does not run the launcher beside the script: uv builds a
throwaway environment from the script's own inline dependencies, from
wheels only, and a project file above the study is not used); under the
kernel fence where the machine has one, so that it can read its copy, the
folders of the files the lock binds and the system's folders, and write
its copy and nothing else; and with a keeper that ends whatever it leaves
running. What it wrote is brought back into the study afterwards; a change
to a file the tool keeps fails the run. Every command of this tool refuses
to run when a step of a plan, a look or a keeper is anywhere above it.

What a command is given. Its environment is built, not inherited: a PATH
of its interpreter's folder and the system's, a home, a temporary folder
and a bytecode cache inside its scratch folder, the caller's language and
time zone when they are plain names, three Python settings and a mark the
tool makes itself, and the names its plan step lists under
`passes_environment` (a data provider's token on a fetch). No UV_
variable, certificate setting or folder of the caller's arrives. The
names a step was given, never the values, are recorded in its event, with
whether the kernel fence was applied and tried. git, which the tool also
runs, is given a short list of its own.

What "the code" means here. The code list in the plan; the script every
command runs; every other existing file a test, fetch or rehearsal command
names, inside the study or outside it, each word read from the study
directory and never from where the tool was called; every file a rehearsal
lists under `needs`; everything Python could import from the folder of one
of those (every .py, every .pyc and extension module sitting there, and
every package folder, all the way down), because a script imports its
neighbours; when a command runs through `uv run`, the settings uv reads
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site):
    # A clean start. This tool runs itself again in a Python that reads no PYTHON variable, no user site, no start-up
    # file (.pth, sitecustomize) and not the folder this file is in, so that none of those can change what it does.
    # What a hostile environment ran before this line has already run: a stated limit (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", os.path.abspath(__file__), *sys.argv[1:]]
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

from the study directory and every folder above it (pyproject.toml,
uv.toml, uv.lock, .python-version); and this file. A .venv folder in one
of those places, whose interpreter uv runs, is recorded by the lock (its
pyvenv.cfg and its interpreter) and the opening refuses one that appeared
or changed since. The plan's declared outputs are left out: its
receipts, its held-out data path, and the files a step says it writes,
which the tool removes before a test or a rehearsal and requires absent
before an opening. A path under one of the plan's roots that does not
exist is recorded as missing, so the identity never changes silently with
what is checked out. Folders named __pycache__ are not hashed: every
command the tool runs has Python's bytecode cache pointed at a new empty
folder, so nothing in them is ever loaded. The code is not every imported
library and it is not the interpreter: both are stated limits.

What it cannot do, said plainly. Four things.
One. It cannot stop someone reading public data outside the access gate.
Nothing in the tool answers that, and neither does where the opening runs:
only an analysis assistant working where it has no route to the withheld
values would, and that is not built. Until it is, the barrier for public
data is instruction and evidence. The same holds for a system trial's
sealed answer: the seal writes it to a file inside the study, the tool
passes that file to no command, and nothing in the tool stops a locked
script from opening it. What stands against that is that the code is read
at the lock by the people who lock it.
Two. Names of who did what are typed, not proven, and on a machine where
agents and people share one account nothing typed can be. So the two acts
by people are not typed: a real study's lock and signature are pull
requests merged on a protected branch, and the tool checks the merge with
git (the commit exists, is one of the protected branch's own commits, is
reachable from what is checked out, brought the request in, and its
manifest matches the files). git cannot say who approved, or that the
branch is protected: the platform's record says that, and the recording
job copies the names into the log. A local branch with the protected
branch's name looks the same to git alone, so an opening that matters runs
from a fresh clone. Every other name in a log is still typed.
Three. A log that is rewritten from its first line, cut short, or added
to by hand with the right hashes checks out on its own. A later edit is
detectable only against a commit or a log fingerprint posted outside the
workspace, and before the first of those nothing protects the log.
Four. It cannot defend itself against the Python it runs in. The tool
starts itself again in a Python that reads no PYTHON variable, no user
site, no start-up file and not its own folder, and it refuses to run while
a PYTHON variable other than PYTHONDONTWRITEBYTECODE and PYTHONUNBUFFERED
is visible; a script it runs cannot write the environment the tool runs
from where the kernel fence holds. But code that a hostile environment
loads when Python first starts has already run by then, with the caller's
rights, and can do anything (two red-team reviews did exactly that). No
check inside a process survives a hostile process, and on a machine with
no kernel fence a script the tool ran can have planted such code.
The second is answered for the two acts by where they are made: on the
platform, as merged pull requests. The third is answered the way the
organization already answers it for signatures: the log's fingerprint is
posted on the tracking issue at the lock and after every opening, and
`check-log --anchor SEQ:HASH` refuses a log that does not contain what was
posted.
The fourth is answered by where the opening runs: somewhere clean that is
not the workspace where the method was built. The first is not answered by
where the opening runs.

Usage: sf.py <command> --study STUDY_DIR [...]; sf.py selftest
"""
import sys

sys.dont_write_bytecode = True  # the tool never leaves bytecode beside its own source
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    # Run as a script, Python puts the script's own folder first on the import path, so a file beside sf.py named
    # like a module it imports would be loaded in its place. `sys` is built in, so dropping the folder needs nothing
    # that could itself be shadowed.
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import contextlib  # noqa: E402
import datetime as dt  # noqa: E402
import getpass  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import operator  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import urllib.parse  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402


def _beside(name: str):
    """Another file of this package, loaded from beside this one by its path, so that nothing can stand in for it by name."""
    if name not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


fence = _beside("fence")  # how a script the tool does not trust is run: a plan's commands here, a look in explore.py

try:
    import fcntl
except ImportError:  # not POSIX: appends are then unlocked, which is said here
    fcntl = None

# tests that repeat freely before the lock, and tests that open held-out data
FREE_TESTS, HELD_OUT_TESTS = ("known-answers", "working-data"), ("held-out", "independent-site")
TEST_NAMES = {"known-answers": "known-answer tests", "working-data": "working data"}
OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "==": operator.eq}
ACTOR = re.compile(r"(human|agent):[A-Za-z0-9_.@/-]+")  # matched whole: a name with a line break after it is not a name
PLATFORM_ACTOR = re.compile(r"platform:[a-z][a-z0-9.-]{1,62}")  # who records an act that was a merged pull request: the host
PLACEHOLDER_ACTORS = ("human:you", "human:name", "human:id", "agent:name", "agent:id")
HOST = re.compile(r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}$")
KEPT_PYTHON = ("PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED")  # the only PYTHON variables a command may run under
IMPORTABLE = (".py", ".pyc", ".so", ".pyd")  # what Python can import from a folder: source, bytecode, extension modules
TOOL = Path(__file__).resolve()
REPO = TOOL.parent.parent  # the repository: tools/ holds this file, factory/ the definition, methods/ the method scripts
FENCE = TOOL.parent / "fence.py"  # how every command of a plan is run; bound into every lock with this file
FACTORY = REPO / "factory"  # this factory's definition: a folder rooted at factory.yaml (tools/check_factory.py validates it)
# the statuses a log check can give; the others are built where they are decided
INVALID = "the study log or its files do not check out"
EXPLORATORY = "exploratory study"
NO_FINDING = "confirmatory study, waiting for the finding to be attached"
NO_REVIEW = "confirmatory study, waiting for the review assistant"
READY = "confirmatory study, ready for the steward's signature"
SIGNED = "confirmatory study, signed by the steward"
DECLINED = "confirmatory study, the steward declined to sign"
ACTS_BY_PEOPLE = ("lock.recorded", "signature.recorded")
HARNESS_PERSON = "human:blind-test-harness"  # the one named exception: the blind test harness records its own locks
# events an actor may have recorded and still be a review assistant: reviews, notes and change records
NOT_PART_OF_THE_WORK = ("review.verdict", "note.raised", "note.resolved", "change.recorded")
# Paths inside a study that no plan may name as something a step writes: the tool or people write them
PROTECTED = ("study-log.jsonl", "analysis-plan.yaml", "scorecard.json", "curation-list.json", "request.md")
PROTECTED_FOLDERS = ("notes", "verdicts", "finding", "request")
ACT_FOLDERS = ("lock-request", "signature-request")  # what a person's act is asked for with; written by the tool only

# The criteria every decision rule must meet on the known-answer tests before the lock. The names are fields the
# known-answers receipt reports for the rule (under power_evidence.path), each a rate between 0 and 1.
REQUIRED_CRITERIA = {
    "false_confirm_at_edge_max": ("at most", "how often the rule confirms when the truth sits right at the difference that matters"),
    "false_refute_at_edge_max": ("at most", "how often the rule refutes when the truth sits right at the difference that matters"),
    "power_to_refute_when_false": ("at least", "how often the rule refutes when the idea is false"),
    "coverage_when_true": ("at least", "how often the interval covers the value that was put in"),
}
DIRECTION_OPS = {"at most": ("<=", "<"), "at least": (">=", ">")}

# Every key the plan check accepts. A key outside these is refused, so a misspelled key cannot hide.
PLAN_KEYS = ("study", "study_kind", "question", "claim_class", "quantity_estimated", "roots", "code", "data", "tests",
             "rehearsals", "rules", "openings_allowed", "planned_handling", "independence", "what_this_can_show",
             "overturn", "limitations", "scheduled_retest")
PLAN_NEEDS = {
    "study": "the study's id, such as STUDY-0002",
    "question": "one question, ending in a question mark",
    "quantity_estimated": "what is estimated, in a sentence or two",
    "data": "a mapping with `working` and `held_out`",
    "code": "a list of the files that make up the method",
    "tests": "a mapping with `known-answers`, `working-data` and `held-out`",
    "rules": "a list of decision rules",
    "openings_allowed": "1, or a mapping such as {held-out: 1}",
    "overturn": "what result would overturn the claim, in a sentence",
    "independence": "how independent the comparison record is, in a sentence",
    "limitations": "a list of what the study cannot show",
}
STUDY_KINDS = ("confirmatory", "system_trial")
DATA_KEYS = ("working", "held_out")
HELD_OUT_KEYS = ("window", "pair", "withheld_values", "path", "observation_metadata", "why_this_window", "metadata_note")
TEST_KEYS = ("command", "receipt", "fetch", "data", "window", "pair", "writes", "passes_environment")
REHEARSAL_KEYS = ("id", "why", "steps", "receipt", "writes", "needs", "passes_environment")
# The launchers the tool knows. A command is one of them followed by a script file, then the script's own
# arguments; the script is what the lock binds. Nothing else is run: not a shell, not a program that takes its
# code as text.
UV_RUN_FLAGS = ("--script", "--quiet", "-q", "--no-project", "--isolated", "--frozen", "--locked", "--offline",
                "--no-sync", "--no-cache")
UV_RUN_VALUED = ("--python", "-p")  # each takes one value: a version such as 3.12, never the path of an interpreter
UV_VERSION = re.compile(r"^[A-Za-z0-9.@<>=~!,*+-]+$")
# What `uv run` picks up from the folder it runs in (the study directory) and from every folder above it. When
# a plan has a `uv run` command, both kinds are held:
#   its settings, a project and a pinned Python version (UV_READS) are part of the code identity, like any file
#   a command names, so none can be planted, changed or removed after the lock;
#   a virtual environment folder (UV_ENVIRONMENT), whose interpreter uv runs, is recorded by the lock, and the
#   opening refuses one that appeared or changed since. One that was there at the lock and is gone is no
#   problem, so a lock made beside a developer's environment still opens from a fresh clone.
UV_READS = ("pyproject.toml", "uv.toml", "uv.lock", ".python-version", ".python-versions")
UV_ENVIRONMENT = ".venv"
LAUNCHERS = ("`{python}` followed by a script file, or `uv run` (with no options but "
             + ", ".join(UV_RUN_FLAGS + UV_RUN_VALUED) + ") followed by a script file whose name ends in .py")
# What a command the tool runs is given of the caller's environment: these names when they are set, every UV_
# variable, the names its plan step lists under `passes_environment`, and the three PYTHON settings the tool
# makes itself. Nothing else arrives: no token, no library path, no variable the plan did not ask for.
PASSED_ON = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR", "TERM",
             "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR",
             "XDG_CONFIG_DIRS", "XDG_DATA_DIRS")
CERTIFICATES_AND_PROXIES = ("SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
                            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")
PASSED_ON += CERTIFICATES_AND_PROXIES + tuple(n.lower() for n in CERTIFICATES_AND_PROXIES)
SET_BY_THE_TOOL = ("PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "PYTHONPYCACHEPREFIX", "SF_INSIDE_A_STEP")
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# The one required criterion no rule may waive: a rule has a refutation, and this is what shows it can refute.
NEVER_WAIVED = ("power_to_refute_when_false",)
RULE_KEYS = ("id", "role", "statement", "supported_if", "refuted_if", "power_evidence")
EVIDENCE_KEYS = ("path", "require", "waived")
ROLES = ("primary", "secondary")


class Refused(Exception):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def sha_file(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def dig(obj, path: str):
    for part in path.split("."):
        obj = obj[part]
    return obj


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def holds(conds: list, receipt: dict) -> bool:
    """Every condition holds. A missing, non-numeric or non-finite field
    makes the whole thing false, so a refused estimate is never support."""
    try:
        for c in conds:
            v = dig(receipt, c["field"])
            if not is_num(v) or not OPS[c["op"]](float(v), float(c["value"])):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def git(*args) -> subprocess.CompletedProcess | None:
    """Run git with the short list of variables every child of the tool gets (see PASSED_ON), so no GIT_
    variable and nothing else inherited can point it at another repository or at none. `--no-optional-locks`
    keeps a status query from writing to the repository."""
    env = {k: os.environ[k] for k in passed_names()}
    try:
        return subprocess.run(["git", "--no-optional-locks", *args], capture_output=True, text=True, env=env,
                              stdin=subprocess.DEVNULL)
    except OSError:
        return None


def repository_state(folder: Path) -> dict:
    """The commit a folder is checked out at and whether its work tree is clean."""
    top = git("-C", str(folder), "rev-parse", "--show-toplevel") if folder.is_dir() else None
    if top is None or top.returncode != 0:
        return {"commit": None, "clean": None, "note": "not in a git work tree"}
    head = git("-C", str(folder), "rev-parse", "HEAD")
    dirty = git("-C", str(folder), "status", "--porcelain")
    return {"repository": Path(top.stdout.strip()).name,
            "commit": head.stdout.strip() if head and head.returncode == 0 else None,
            "clean": (dirty.stdout.strip() == "") if dirty and dirty.returncode == 0 else None}


def visible_python_variables() -> list:
    return sorted(k for k, v in os.environ.items() if k.startswith("PYTHON") and k not in KEPT_PYTHON and v)


def refuse_dirty_environment() -> None:
    dirty = visible_python_variables()
    if dirty:
        raise Refused(f"{', '.join(dirty)} is set: every command of the study tool runs with a clean Python environment. "
                      f"Unset it and run again (only {' and '.join(KEPT_PYTHON)} may stay)")


def evidence_ok(url) -> bool:
    """An https link with a host name in it. `https://` and `https://.../pull/N` are not links to anything."""
    try:
        u = urllib.parse.urlsplit(str(url or ""))
        return u.scheme == "https" and bool(HOST.match((u.hostname or "").lower()))
    except ValueError:
        return False


def as_date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v).strip())
    except ValueError:
        return None


def window_of(w) -> dict | None:
    """A window as two ISO dates, or None when it is not one."""
    if not isinstance(w, dict) or set(w) != {"start", "end"}:
        return None
    a, b = as_date(w["start"]), as_date(w["end"])
    return {"start": a.isoformat(), "end": b.isoformat()} if a and b and a <= b else None


class _NoDuplicateKeys(yaml.SafeLoader):
    """YAML keeps the last of two equal keys and says nothing. A plan must say one thing, so a repeat is refused."""


def _mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            repeated = key in seen
            seen.add(key)
        except TypeError:
            raise Refused(f"analysis-plan.yaml uses something other than a word or a number as a key (line {key_node.start_mark.line + 1})")
        if repeated:
            raise Refused(f"analysis-plan.yaml gives the key `{key}` twice (the second time on line {key_node.start_mark.line + 1}); "
                          "YAML would keep only the last one, so say it once")
    return loader.construct_mapping(node, deep=True)


_NoDuplicateKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_plan_text(text: str) -> dict:
    try:
        plan = yaml.load(text, Loader=_NoDuplicateKeys)
    except yaml.YAMLError as e:
        raise Refused(f"analysis-plan.yaml does not parse: {str(e).splitlines()[0]}")
    if not isinstance(plan, dict):
        raise Refused("analysis-plan.yaml is not a mapping of keys (see factory/templates/analysis-plan.yaml)")
    return plan


MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{1,99}$")
NOT_A_MODEL = ("auto", "router", "inherit", "default", "none", "unknown", "model", "any")
NO_MODEL = ("an event an agent writes names the model that wrote it: pass --model <the model's name>. The model is declared by "
            "whoever calls the tool (a harness, or the agent itself) and nothing proves it; a person's event needs none")


def model_problem(model) -> str | None:
    """Why a value is not the name of a concrete model, or None."""
    m = str(model or "")
    if not MODEL.match(m):
        return "it is not a model's name (letters, digits and . _ : @ / -, with no spaces)"
    if m.casefold() in NOT_A_MODEL or m.casefold().startswith(("auto-", "auto:", "router:", "routers/")):
        return "it is a router or a stand-in, not a concrete model"
    return None


def models_recorded(ev: list) -> dict:
    """{actor: [models]} for every agent that wrote an event, in the order the models first appear. An event with
    no model (possible only in a log written before models were recorded, or by hand) shows as `none recorded`."""
    out = {}
    for e in ev:
        if str(e.get("actor", "")).startswith("agent:"):
            m = e.get("model") or "none recorded"
            if m not in out.setdefault(e["actor"], []):
                out[e["actor"]].append(m)
    return out


class Study:
    default_model = None  # a model for every agent event of this process; only the self-tests and the blind test harness set it
    default_route = None  # `practice` in the self-tests and the blind test harness, which type their locks; never set by a command

    def __init__(self, d):
        self.model = None  # the model the caller declares for the events of this command (--model)
        given = Path(os.path.abspath(d))
        self.d = Path(d).resolve()
        if given.is_symlink() or given.parent.resolve() / given.name != self.d:
            raise Refused(f"the study directory {given} is reached through a symlink (it is really {self.d}). The record of "
                          "what has been opened sits beside the real directory, so name the real directory")
        self.log = self.d / "study-log.jsonl"
        self.plan_path = self.d / "analysis-plan.yaml"

    # ---- the study log --------------------------------------------------
    @staticmethod
    def _parse(text: str) -> list:
        out = []
        for i, ln in enumerate(text.splitlines()):
            if not ln.strip():
                continue
            try:
                e = json.loads(ln)
                if not isinstance(e, dict) or not {"seq", "at", "actor", "kind", "data", "prev", "hash"} <= set(e):
                    raise ValueError("not an event")
            except ValueError:
                raise Refused(f"the study log has an unreadable line ({i + 1})")
            out.append(e)
        return out

    def events(self) -> list:
        return self._parse(self.log.read_text()) if self.log.exists() else []

    @staticmethod
    def _digest(prev: str, body: dict) -> str:
        return hashlib.sha256((prev + json.dumps(body, sort_keys=True, separators=(",", ":"))).encode()).hexdigest()

    def _chain(self, ev: list) -> list:
        prev = "genesis"
        for i, e in enumerate(ev):
            body = {k: e[k] for k in ("seq", "at", "actor", "kind", "data")}
            if "model" in e:  # the model that wrote an agent's event is part of what the hash covers
                body["model"] = e["model"]
            if e["seq"] != i or e["prev"] != prev or e["hash"] != self._digest(prev, body):
                return [f"study log broken at event {i} ({e.get('kind')})"]
            prev = e["hash"]
        return []

    def chain_problems(self) -> list:
        try:
            return self._chain(self.events())
        except Refused as r:
            return [str(r)]

    @contextlib.contextmanager
    def held(self):
        """The study log, held for one writer. Whatever is decided from the log and then written to it (the
        openings allowed, then the opening) is decided while it is held, so two commands cannot both pass."""
        self.d.mkdir(parents=True, exist_ok=True)
        with self.log.open("a+") as f:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_EX)
            yield f

    def read_held(self, f) -> list:
        f.seek(0)
        ev = self._parse(f.read())
        if self._chain(ev):
            raise Refused("the study log does not check out; nothing more is written to it")
        return ev

    @staticmethod
    def check_actor(actor) -> None:
        if PLATFORM_ACTOR.fullmatch(actor or ""):
            return  # only `--record-merge` takes one, and it checks the merge and the platform's record before it writes
        if not ACTOR.fullmatch(actor or ""):
            raise Refused("the actor is human:<id> or agent:<id>")
        if actor.lower() in PLACEHOLDER_ACTORS:
            raise Refused(f"`{actor}` is the placeholder from the documents; give the actor's own id, such as human:jdoe")

    def append(self, actor: str, kind: str, data: dict, f=None) -> dict:
        self.check_actor(actor)
        if PLATFORM_ACTOR.fullmatch(actor or "") and not (kind in ACTS_BY_PEOPLE and data.get("route") == "pull-request" and data.get("merge")):
            raise Refused("an actor `platform:<host>` records one thing only: a lock or a signature that was a merged pull request "
                          "(`--record-merge`). Everything else is written by human:<id> or agent:<id>")
        if f is None:
            with self.held() as g:
                return self._append(g, actor, kind, data)
        return self._append(f, actor, kind, data)

    def _append(self, f, actor: str, kind: str, data: dict) -> dict:
        ev = self.read_held(f)  # the chain is re-read while the file is held
        if any(e["kind"] == "study.closed" for e in ev) and kind not in ("note.resolved", "change.recorded"):
            raise Refused("this study is closed; a new question is a new study that cites it")
        prev = ev[-1]["hash"] if ev else "genesis"
        body = {"seq": len(ev), "at": now(), "actor": actor, "kind": kind, "data": data}
        if str(actor).startswith("agent:"):
            model = self.model or Study.default_model
            if not model:
                raise Refused(NO_MODEL)
            why = model_problem(model)
            if why:
                raise Refused(f"--model `{model}`: {why}")
            body["model"] = str(model)
        e = {**body, "prev": prev, "hash": self._digest(prev, body)}
        f.write(json.dumps(e, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
        return e

    def committed_log(self) -> tuple:
        """(in a git work tree?, the study log as last committed or None).
        The commit history is the one record a workspace cannot quietly
        redo once it is pushed, so the opening and the log check lean on
        it. The tool takes any local commit; that the commit is a reviewed
        one on a protected branch is the organization's to hold."""
        try:
            top = git("-C", str(self.d), "rev-parse", "--show-toplevel")
            if top is None or top.returncode != 0:
                return False, None
            root = Path(top.stdout.strip()).resolve()
            rel = self.log.resolve().relative_to(root).as_posix()
            out = git("-C", str(root), "show", f"HEAD:{rel}")
            return True, (out.stdout if out and out.returncode == 0 else None)
        except (OSError, ValueError):
            return False, None

    def last(self, kind: str, **match):
        for e in reversed(self.events()):
            if e["kind"] == kind and all(e["data"].get(k) == v for k, v in match.items()):
                return e
        return None

    # ---- the analysis plan ----------------------------------------------
    def plan(self) -> dict:
        if not self.plan_path.is_file():
            raise Refused("there is no analysis-plan.yaml (the analysis plan) in this study")
        return load_plan_text(self.plan_path.read_text())

    def plan_sha(self) -> str:
        return sha_file(self.plan_path)

    def expand(self, token, plan: dict, study_dir: Path | None = None) -> str:
        """A word of a command with its roots filled in. `study_dir` stands in for the study when the command runs
        in a scratch copy of it; a plan's other roots are always the real folders, which a command only reads."""
        roots = plan.get("roots") if isinstance(plan.get("roots"), dict) else {}
        roots = {str(k): str((self.d / str(v)).resolve()) for k, v in roots.items()}
        try:
            return str(token).format(study=str(study_dir or self.d), python=sys.executable, **roots)
        except (KeyError, IndexError, ValueError):
            known = ", ".join("{" + k + "}" for k in ["study", "python", *roots])
            raise Refused(f"`{token}` names a root the analysis plan does not define (it can use {known})")

    def word(self, token, plan: dict) -> Path:
        """What a word of a command points at. A relative word is read from the study directory, where the
        command will run, and never from the directory the tool was called from."""
        return self.d / self.expand(token, plan)

    def declared_outputs(self, plan: dict) -> dict:
        """The paths the plan says a step writes, resolved, each with what declares it: the held-out data path,
        every receipt, and every `writes` entry. They are results, so they are not locked with the code."""
        out = {}

        def add(rel, what):
            if isinstance(rel, str) and rel:
                out.setdefault((self.d / rel).resolve(), what)
        held = (plan.get("data") or {}).get("held_out") or {}
        add(held.get("path"), "data.held_out.path")
        for t, spec in (plan.get("tests") or {}).items():
            spec = spec if isinstance(spec, dict) else {}
            add(spec.get("receipt"), f"tests.{t}.receipt")
            add(spec.get("data"), f"tests.{t}.data")
            for w in spec.get("writes") or []:
                add(w, f"tests.{t}.writes")
        for i, reh in enumerate(plan.get("rehearsals") or []):
            reh = reh if isinstance(reh, dict) else {}
            add(reh.get("receipt"), f"rehearsals[{reh.get('id', i)}].receipt")
            for w in reh.get("writes") or []:
                add(w, f"rehearsals[{reh.get('id', i)}].writes")
        return out

    @staticmethod
    def commands(plan: dict) -> list:
        """Every command the plan would have the tool run, with where the plan says it."""
        out = []
        for t, spec in (plan.get("tests") or {}).items():
            spec = spec if isinstance(spec, dict) else {}
            for k in ("command", "fetch"):
                if isinstance(spec.get(k), list):
                    out.append((f"tests.{t}.{k}", spec[k]))
        for i, reh in enumerate(plan.get("rehearsals") or []):
            reh = reh if isinstance(reh, dict) else {}
            for j, st in enumerate(reh.get("steps") or []):
                if isinstance(st, list):
                    out.append((f"rehearsals[{reh.get('id', i)}].steps[{j}]", st))
        return out

    @staticmethod
    def importable(folder: Path) -> dict:
        """Everything Python could import from a folder, by path below it: every .py, every .pyc and extension
        module sitting in it, and everything of those kinds inside each sub-folder that is a package (it holds an
        __init__.py), all the way down. A file or a package added later changes this, which is the point."""
        out = {}
        try:
            entries = sorted(folder.iterdir())
        except OSError:
            return out
        for p in entries:
            if p.is_file() and p.suffix in IMPORTABLE:
                out[p.name] = sha_file(p)
            elif p.is_dir() and p.name != "__pycache__" and (p / "__init__.py").is_file():
                for base, dirs, files in os.walk(p):
                    dirs[:] = sorted(x for x in dirs if x != "__pycache__")
                    for name in sorted(files):
                        if Path(name).suffix in IMPORTABLE:
                            q = Path(base) / name
                            out[q.relative_to(folder).as_posix()] = sha_file(q)
        return out

    def uv_picks_up(self) -> dict:
        """The settings `uv run` would read from the study directory, where the tool runs it, and from every
        folder above it, by path from the study (UV_READS). Only what exists is listed, so one that appears
        later shows as new."""
        out = {}
        for up, folder in enumerate([self.d, *self.d.parents]):
            for name in UV_READS:
                if (folder / name).is_file():
                    out["{study}/" + "../" * up + name] = sha_file(folder / name)
        return out

    def uv_environments(self) -> dict:
        """Every virtual environment folder `uv run` would find from the study directory or a folder above
        it, by path from the study, each as one checksum over its pyvenv.cfg and the interpreter it holds
        (uv runs that interpreter). What else is inside it is not hashed."""
        out = {}
        for up, folder in enumerate([self.d, *self.d.parents]):
            venv = folder / UV_ENVIRONMENT
            if venv.exists() or venv.is_symlink():
                parts = ("pyvenv.cfg", "bin/python", "bin/python3", "Scripts/python.exe")
                out["{study}/" + "../" * up + UV_ENVIRONMENT] = sha_text("\n".join(f"{part} {sha_file(venv / part)}" for part in parts))
        return out

    def code_hashes(self, plan: dict) -> dict:
        """Everything that decides a result is locked: the plan's code
        list; every existing file a test command, a fetch or a rehearsal
        step names, inside the study or outside it (a script, a generator
        of known-answer test cases, a working-data fixture, a parameter
        file); and everything importable from the folder of one of those.
        The plan's declared outputs are left out. Keys are the unexpanded
        words, so the same plan hashes the same on another machine and
        from any directory the tool is called from."""
        tokens = [str(c) for c in plan["code"]]
        outputs = self.declared_outputs(plan)
        for _, argv in self.commands(plan):  # the script each command runs: bound even when absent, so the lock refuses
            launcher, script = launch(argv)
            if launcher and script not in tokens:
                tokens.append(script)
        for reh in plan.get("rehearsals") or []:
            tokens += [str(n) for n in (reh or {}).get("needs") or [] if str(n) not in tokens]
        for _, argv in self.commands(plan):
            for word in argv:
                word = str(word)
                for tok in ([word] + ([word.split("=", 1)[1]] if word.startswith("-") and "=" in word else [])):
                    if tok in tokens or tok == "{python}" or not tok:
                        continue
                    f = self.word(tok, plan)
                    if f.resolve() in outputs:
                        continue
                    rooted = tok.startswith("{") and not tok.startswith("{study}")
                    # a file is bound; a path under one of the plan's roots that does not exist is bound as missing,
                    # so the identity never changes silently with what happens to be checked out
                    if f.is_file() or (rooted and not f.exists()):
                        tokens.append(tok)
        out = {c: sha_file(self.word(c, plan)) for c in tokens}
        # the code that evaluates the rules is locked with them: this file, and the fence it runs every command through
        out["(the study tool)"] = f"{sha_file(TOOL)}+fence:{sha_file(FENCE)}"
        if uses_uv(plan):
            for key, sha in self.uv_picks_up().items():
                out.setdefault(key, sha)
        for c in tokens:
            folder = self.word(c, plan).resolve().parent
            prefix = c.rsplit("/", 1)[0] if "/" in c else "{study}"
            for rel, sha in self.importable(folder).items():
                out.setdefault(f"{prefix}/{rel}", sha)
        return out

    def path(self, rel: str) -> Path:
        return self.d / rel

    def inside(self, rel) -> bool:
        return (isinstance(rel, str) and bool(rel) and (self.d / rel).resolve().is_relative_to(self.d)
                and (self.d / rel).resolve() != self.d)

    def listing(self) -> dict:
        """Every file in the study directory with its checksum, the study log apart (the tool itself adds to it)."""
        out = {}
        for base, dirs, files in os.walk(self.d):
            dirs.sort()
            for name in sorted(files):
                p = Path(base) / name
                rel = p.relative_to(self.d).as_posix()
                if rel != self.log.name:
                    out[rel] = sha_file(p)
        return out

    def allowed(self, plan: dict | None, test: str) -> int:
        return 1  # one opening of each held-out test; more needs sequential inference, which is not built


def same_code(a: dict | None, b: dict | None, tool_too: bool = True) -> bool:
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    if tool_too:
        return a == b
    return {k: v for k, v in a.items() if k != "(the study tool)"} == {k: v for k, v in b.items() if k != "(the study tool)"}


def code_difference(locked: dict, here: dict) -> list:
    """Which bound things differ between two identities, the study tool apart."""
    keys = sorted((set(locked) | set(here)) - {"(the study tool)"})
    out = []
    for k in keys:
        if k not in here:
            out.append(f"{k} (bound at the lock, not here now)")
        elif k not in locked:
            out.append(f"{k} (new since the lock)")
        elif locked[k] != here[k]:
            out.append(f"{k} (changed)" if here[k] else f"{k} (missing)")
    return out


def env_stamp(study: Study | None = None, plan: dict | None = None) -> dict:
    """Where a run happened: the interpreter, the machine, the user, and for every root the plan names the
    commit it is checked out at and whether its work tree was clean."""
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = None
    stamp = {"python": platform.python_version(), "platform": sys.platform, "host": platform.node() or None, "user": user}
    if study is not None:
        roots = plan.get("roots") if isinstance(plan, dict) and isinstance(plan.get("roots"), dict) else {}
        stamp["roots"] = {str(k): repository_state((study.d / str(v)).resolve()) for k, v in roots.items()}
        stamp["roots"]["(the study)"] = repository_state(study.d)
    return stamp


# ---- the plan check -------------------------------------------------------
def condition_problem(c) -> str | None:
    """What is wrong with one condition, or None."""
    if not isinstance(c, dict):
        return "is not a mapping"
    extra = sorted(set(map(str, c)) - {"field", "op", "value"})
    if extra:
        return f"has the unknown key `{extra[0]}`"
    if not isinstance(c.get("field"), str) or not c["field"]:
        return "needs `field`, a dotted path into the receipt such as gain.ci_low"
    if c.get("op") not in OPS:
        return f"needs `op`, one of {', '.join(OPS)}"
    if not is_num(c.get("value")):
        return "needs `value`, a finite number"
    return None


def conds_problem(conds) -> str | None:
    if not isinstance(conds, list) or not conds:
        return "is a list of one or more conditions"
    for i, c in enumerate(conds):
        why = condition_problem(c)
        if why:
            return f"[{i}] {why}"
    return None


def conds_ok(conds) -> bool:
    return conds_problem(conds) is None


CONDITION = "a condition is {field: a.dotted.path, op: one of >= <= > < ==, value: a number}"


def cannot_fail(c: dict) -> bool:
    """A criterion on a rate between 0 and 1 that every such rate meets: it could not fail, so it shows nothing."""
    if c["op"] == "==":
        return False
    return OPS[c["op"]](0.0, float(c["value"])) and OPS[c["op"]](1.0, float(c["value"]))


def rule_as_tested(r: dict) -> dict:
    """The part of a rule that the known-answer tests must have exercised,
    in a form that compares equal whether it came from YAML or from a JSON
    receipt."""
    return json.loads(json.dumps({"supported_if": r["supported_if"], "refuted_if": r["refuted_if"]}))


def launch(argv: list) -> tuple:
    """Read a command as a launcher the tool knows and the script it runs: (launcher, the script word), or
    (None, why it cannot be read that way). This is a positive rule. A command the tool cannot take apart
    like this is refused, whatever its program is, because a script named inside some other program's
    arguments (a shell string, `env`, `perl -e`) is a script the lock would never see."""
    words = [str(w) for w in argv]
    if words[0] == "{python}":
        if len(words) < 2 or words[1].startswith("-"):
            return None, ("`{python}` is followed directly by the script file; it takes no options here, so not -m or -c, "
                          "which name no file")
        return "{python}", words[1]
    if words[:2] == ["uv", "run"]:
        i, as_script = 2, False
        while i < len(words) and words[i].startswith("-"):
            w = words[i]
            if w in UV_RUN_FLAGS:
                as_script, i = as_script or w == "--script", i + 1
            elif w in UV_RUN_VALUED or ("=" in w and w.split("=", 1)[0] in UV_RUN_VALUED):
                value = w.split("=", 1)[1] if "=" in w else (words[i + 1] if i + 1 < len(words) else "")
                if not UV_VERSION.match(value):
                    return None, (f"`{w.split('=', 1)[0]} {value}` does not name a Python version (such as 3.12): the path of "
                                  "an interpreter is not taken, because an interpreter is a program the lock would not bind")
                i += 1 if "=" in w else 2
            else:
                return None, f"`{w}` is not an option `uv run` may take in a plan"
        if i >= len(words):
            return None, "`uv run` is followed by a script file"
        if not as_script and not words[i].endswith(".py"):
            return None, (f"`uv run {words[i]}` would run a program of that name, not a script: `uv run` is followed by "
                          "a script file whose name ends in .py (or by --script and the file)")
        return "uv run", words[i]
    return None, f"`{words[0]}` is not a launcher the study tool knows"


def uses_uv(plan: dict) -> bool:
    return any(launch(argv)[0] == "uv run" for _, argv in Study.commands(plan))


def environment_problems(study: Study, plan: dict, lock: dict) -> list:
    """Virtual environment folders `uv run` would use now that the lock did not record, or recorded with
    another checksum. One the lock recorded that is gone now is not a problem."""
    if not uses_uv(plan):
        return []
    at_lock = lock["data"].get("uv_environments") or {}
    return [f"{key} ({'changed' if key in at_lock else 'new'} since the lock)"
            for key, sha in study.uv_environments().items() if at_lock.get(key) != sha]


def command_problem(argv: list) -> str | None:
    """Why a command cannot be read as a launcher and a script, or None."""
    launcher, script = launch(argv)
    if launcher is None:
        return (f"{script}. A command is {LAUNCHERS}, then the script's own arguments. Put the step in a script and "
                "name the script, so the lock can bind it")
    return None


def is_argv(v) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(w, (str, int, float)) and not isinstance(w, bool) for w in v)


def is_text(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def pair_ok(v) -> bool:
    if isinstance(v, dict):
        return bool(v) and all(isinstance(x, (str, int, float)) and not isinstance(x, bool) and str(x).strip() for x in v.values())
    return isinstance(v, (str, int)) and not isinstance(v, bool) and bool(str(v).strip())


def passes_problems(where: str, step: dict) -> list:
    """`passes_environment`: the names of environment variables a step's commands are given beside the tool's
    own short list. Names only; a PYTHON or SF_ name is never passed."""
    names = step.get("passes_environment")
    if names is None:
        return []
    if not (isinstance(names, list) and names and all(isinstance(n, str) and ENV_NAME.match(n) for n in names)):
        return [f"`{where}.passes_environment`: a list of environment variable names (such as [EARTHDATA_TOKEN]) that "
                "this step's commands are given beside the short list every command gets; names only, never values"]
    bad = [n for n in names if n.upper().startswith(("PYTHON", "SF_"))]
    if bad:
        return [f"`{where}.passes_environment`: {', '.join(bad)} cannot be passed: a name that starts with PYTHON or SF_ "
                "never reaches a command"]
    return []


def unknown_keys(where: str, obj: dict, allowed: tuple) -> list:
    return [f"`{where}{k}`: not a key the study tool knows here (it knows: {', '.join(allowed)})"
            for k in sorted(set(map(str, obj)) - set(allowed))]


def subject_and_window(where: str, spec: dict, required: bool) -> list:
    p = []
    if "pair" in spec or required:
        if not pair_ok(spec.get("pair")):
            p.append(f"`{where}pair`: say what was held out (the subject), as text or as a mapping such as "
                     "{site: \"HARBOUR-1\", sensor: \"B\"}. The record of what has been opened matches "
                     "studies by it, and the tool never uses the study's id in its place")
    if "window" in spec or required:
        if window_of(spec.get("window")) is None:
            p.append(f"`{where}window`: a mapping with exactly `start` and `end`, each a date written YYYY-MM-DD, start "
                     "not after end (for example {start: \"2025-04-28\", end: \"2026-04-27\"}); text such as "
                     "\"2025 through 2026\" cannot be compared with another study's window")
    return p


def check_plan(plan, study: Study | None = None) -> list:
    """The plan check: is the analysis plan complete and well formed enough to be locked? Every message names
    the key and what it accepts."""
    try:
        return _check_plan(plan, study)
    except Refused as r:
        return [str(r)]
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        # a shape none of the checks below foresaw is still a refusal in plain words, never a Python error
        return ["the analysis plan has a value of a kind the plan check could not read; compare it, key by key, "
                "with factory/templates/analysis-plan.yaml"]


def _check_plan(plan, study: Study | None) -> list:
    if not isinstance(plan, dict):
        return ["the analysis plan is a mapping of keys (see factory/templates/analysis-plan.yaml)"]
    p = unknown_keys("", plan, PLAN_KEYS)
    p += [f"missing `{k}`: {PLAN_NEEDS[k]}" for k in PLAN_NEEDS if not plan.get(k)]
    if p:
        return p
    if not is_text(plan["question"]) or not plan["question"].strip().endswith("?"):
        p.append("`question`: the question is not a question (it is one sentence of text ending in a question mark)")
    if plan.get("study_kind", "confirmatory") not in STUDY_KINDS:
        p.append(f"`study_kind`: one of {', '.join(STUDY_KINDS)} (left out, it is confirmatory)")
    shapes = (("data", dict, "a mapping with `working` and `held_out`"), ("tests", dict, "a mapping of test names"),
              ("rules", list, "a list of decision rules"), ("code", list, "a list of file paths"))
    bad = [f"`{k}`: {what}" for k, kind, what in shapes if not isinstance(plan[k], kind)]
    if bad:
        return p + bad
    if not all(isinstance(c, str) and c for c in plan["code"]):
        p.append("`code`: a list of file paths, each as text (a relative path is read from the study directory)")
    roots = plan.get("roots", {})
    if not isinstance(roots, dict) or not all(isinstance(k, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)
                                              and k not in ("study", "python") and isinstance(v, str) for k, v in roots.items()):
        return p + ["`roots`: a mapping from a short name to a path relative to the study directory, such as "
                    "{kit: ../..}; the names `study` and `python` are the tool's own"]

    # what is working data and what is held out
    data = plan["data"]
    p += unknown_keys("data.", data, DATA_KEYS)
    if not data.get("working"):
        p.append("`data.working`: missing; say what was already seen (everything looked at so far is working data)")
    held = data.get("held_out")
    if not isinstance(held, dict):
        return p + ["`data.held_out`: a mapping with `pair`, `window`, `withheld_values` and `path`"]
    p += unknown_keys("data.held_out.", held, HELD_OUT_KEYS)
    p += subject_and_window("data.held_out.", held, required=True)
    if not held.get("withheld_values"):
        p.append("`data.held_out.withheld_values`: missing; list the values nobody reads before the opening")
    if not is_text(held.get("path")):
        p.append("`data.held_out.path`: missing; the path inside the study where the access gate puts the held-out data")

    # openings allowed
    b = plan["openings_allowed"]
    for v in (b.values() if isinstance(b, dict) else [b]):
        if not (isinstance(v, int) and not isinstance(v, bool) and v >= 1):
            p.append("`openings_allowed`: its values are whole numbers of openings, and the only one accepted is 1")
        elif v > 1:
            p.append(f"`openings_allowed`: {v} is refused. Held-out data is opened once: a second opening of the same data "
                     "needs sequential inference, which this tool does not have. Write 1")
    if isinstance(b, dict) and not set(b) <= set(HELD_OUT_TESTS):
        p.append(f"`openings_allowed`: keyed by held-out test, one of {', '.join(HELD_OUT_TESTS)}")

    # the tests
    tests = plan["tests"]
    for t, spec in tests.items():
        if t not in FREE_TESTS + HELD_OUT_TESTS:
            p.append(f"`tests.{t}`: `{t}` is not a test this study tool runs (it runs: {', '.join(FREE_TESTS + HELD_OUT_TESTS)})")
            continue
        if not isinstance(spec, dict):
            p.append(f"`tests.{t}`: test {t} needs a command (argv list) and a receipt path, written as a mapping with "
                     "`command` and `receipt`" + (" and `fetch`" if t in HELD_OUT_TESTS else ""))
            continue
        p += unknown_keys(f"tests.{t}.", spec, TEST_KEYS)
        if not is_argv(spec.get("command")) or not is_text(spec.get("receipt")):
            p.append(f"`tests.{t}`: test {t} needs a command (argv list: a list of words, the program first) and a "
                     "receipt path (`receipt`, a path inside the study)")
        if t in HELD_OUT_TESTS:
            if not is_argv(spec.get("fetch")):
                p.append(f"`tests.{t}.fetch`: test {t} needs a fetch (argv list): the access gate fetches held-out data, nobody else")
            if "data" in spec and not is_text(spec["data"]):
                p.append(f"`tests.{t}.data`: a path inside the study, where this test's fetch puts its data")
            p += subject_and_window(f"tests.{t}.", spec, required=False)
        else:
            if "fetch" in spec:
                p.append(f"`tests.{t}.fetch`: test {t} runs before the lock and fetches nothing")
            for k in ("data", "window", "pair"):
                if k in spec:
                    p.append(f"`tests.{t}.{k}`: belongs only to a test on held-out data; files a test writes for itself "
                             "go in `writes`")
        if "writes" in spec and not (isinstance(spec["writes"], list) and all(is_text(w) for w in spec["writes"])):
            p.append(f"`tests.{t}.writes`: a list of paths inside the study that this test's own commands write")
        p += passes_problems(f"tests.{t}", spec)
    p += [f"`tests.{t}`: test {t} is not in the plan" for t in ("known-answers", "working-data", "held-out") if t not in tests]

    # the rehearsals
    rehearsals = plan.get("rehearsals") or []
    if not isinstance(rehearsals, list):
        return p + ["`rehearsals`: a list; each rehearsal needs an id and steps (a list of argv lists)"]
    seen = set()
    for i, reh in enumerate(rehearsals):
        ok = (isinstance(reh, dict) and is_text(reh.get("id")) and isinstance(reh.get("steps"), list) and reh["steps"]
              and all(is_argv(st) for st in reh["steps"]))
        if not ok:
            p.append(f"`rehearsals[{i}]`: each rehearsal needs an id and steps (a list of argv lists)")
            continue
        p += unknown_keys(f"rehearsals[{reh['id']}].", reh, REHEARSAL_KEYS)
        if reh["id"] in seen:
            p.append(f"`rehearsals[{reh['id']}].id`: two rehearsals share this id")
        seen.add(reh["id"])
        if "receipt" in reh and not is_text(reh["receipt"]):
            p.append(f"`rehearsals[{reh['id']}].receipt`: a path inside the study")
        if "writes" in reh and not (isinstance(reh["writes"], list) and all(is_text(w) for w in reh["writes"])):
            p.append(f"`rehearsals[{reh['id']}].writes`: a list of paths inside the study that this rehearsal's own steps write")
        if "needs" in reh and not (isinstance(reh["needs"], list) and reh["needs"] and all(is_text(w) for w in reh["needs"])):
            p.append(f"`rehearsals[{reh['id']}].needs`: a list of files that must exist for this rehearsal to pass "
                     "(the tool itself looks for them and binds them)")
        p += passes_problems(f"rehearsals[{reh['id']}]", reh)
    if p:
        return p

    # commands: a launcher the tool knows, a script that is a file, and every placeholder defined
    for where, argv in Study.commands(plan):
        why = command_problem(argv)
        if why:
            p.append(f"`{where}`: {why}")
        if study:
            undefined = False
            for w in argv:
                try:
                    study.expand(w, plan)
                except Refused as r:
                    undefined = True
                    p.append(f"`{where}`: {r}")
            if not why and not undefined:
                script = launch(argv)[1]
                if not study.word(script, plan).is_file():
                    p.append(f"`{where}`: its script `{script}` is not a file (the tool looked for {study.word(script, plan)}). "
                             "A command's script has to exist: it is what the lock binds")
    if study:
        for c in plan["code"]:
            try:
                study.expand(c, plan)
            except Refused as r:
                p.append(f"`code`: {r}")
    if study and not p:
        p += output_problems(plan, study)

    # the decision rules
    rules = plan["rules"]
    ids = [r.get("id") if isinstance(r, dict) else None for r in rules]
    if not rules or None in ids or not all(isinstance(i, str) and i for i in ids) or len(set(ids)) != len(ids):
        p.append("`rules`: every rule needs its own id (each rule is a mapping with `id`, `role`, `supported_if`, "
                 "`refuted_if` and `power_evidence`)")
        return p
    for r in rules:
        p += unknown_keys(f"rules[{r['id']}].", r, RULE_KEYS)
        if "role" in r and r["role"] not in ROLES:
            p.append(f"`rules[{r['id']}].role`: one of {', '.join(ROLES)}")
    if not any(r.get("role") == "primary" for r in rules):
        p.append("`rules`: no primary rule (give one rule `role: primary`; the others are `role: secondary`)")
    for r in rules:
        rid = r["id"]
        why = conds_problem(r.get("supported_if"))
        ref = r.get("refuted_if")
        ref_why = None
        if not isinstance(ref, list) or not ref:
            ref_why = "is a list of one or more groups of conditions (any one group refutes)"
        else:
            for i, g in enumerate(ref):
                gw = conds_problem(g)
                if gw:
                    ref_why = f"[{i}] {gw}; each group is itself a list of conditions"
                    break
        if why or ref_why:
            where = f"`rules[{rid}].supported_if` {why}" if why else f"`rules[{rid}].refuted_if` {ref_why}"
            p.append(f"rule {rid}: needs supported_if (conditions, all of which must hold) and refuted_if (a list of "
                     f"condition groups); {CONDITION}. Here {where} (a rule that cannot be refuted is not a rule)")
        p += evidence_problems(rid, r.get("power_evidence"))
    return p


def output_problems(plan: dict, study: Study) -> list:
    """The paths a plan says its steps write: inside the study, each written by one step only, none of them a file
    the tool or people write, and the held-out data path named by its own fetch."""
    p = []
    held = plan["data"]["held_out"]
    claimed = {}

    def claim(rel, where):
        if not study.inside(rel):
            p.append(f"`{rel}` must be a path inside the study (`{where}`)")
            return
        r = (study.d / rel).resolve()
        top = r.relative_to(study.d).parts
        if r.relative_to(study.d).as_posix() in PROTECTED or top[0] in PROTECTED_FOLDERS:
            p.append(f"`{where}`: `{rel}` is a file the study tool or people write (the study log, the plan, the request, "
                     "notes, verdicts, the finding, the scorecard); a step cannot write there")
        elif r in claimed and not (where.endswith(".data") and claimed[r] == "data.held_out.path"):
            p.append("two tests write the same receipt" if where.endswith(".receipt") and claimed[r].endswith(".receipt")
                     else f"`{where}`: `{rel}` is already written by `{claimed[r]}`; each step writes its own files")
        claimed.setdefault(r, where)

    claim(held["path"], "data.held_out.path")
    for t, spec in plan["tests"].items():
        claim(spec["receipt"], f"tests.{t}.receipt")
        if spec.get("data"):
            claim(spec["data"], f"tests.{t}.data")
        for w in spec.get("writes") or []:
            claim(w, f"tests.{t}.writes")
    for reh in plan.get("rehearsals") or []:
        if reh.get("receipt"):
            claim(reh["receipt"], f"rehearsals[{reh['id']}].receipt")
        for w in reh.get("writes") or []:
            claim(w, f"rehearsals[{reh['id']}].writes")
    held_out_paths = [plan["tests"][t].get("data") or held["path"] for t in HELD_OUT_TESTS if t in plan["tests"]]
    if len(held_out_paths) == 2 and (study.d / held_out_paths[0]).resolve() == (study.d / held_out_paths[1]).resolve():
        p.append("`tests.independent-site.data`: the two tests on held-out data would write the same data file; give the "
                 "repeat at an independent site its own `data` path, and name it in its fetch command")
    code = {study.word(c, plan).resolve() for c in plan["code"]}
    scripts = {study.word(launch(argv)[1], plan).resolve(): w for w, argv in Study.commands(plan) if launch(argv)[0]}
    for reh in plan.get("rehearsals") or []:
        for n in reh.get("needs") or []:
            code.add(study.word(n, plan).resolve())
    for r, where in claimed.items():
        if r in code:
            p.append(f"`{where}`: `{r.relative_to(study.d).as_posix()}` is in the `code` list or under `needs`; a file is "
                     "either locked with the code or something a step writes")
        elif r in scripts:
            p.append(f"`{where}`: `{r.relative_to(study.d).as_posix()}` is the script `{scripts[r]}` runs; a script is locked "
                     "with the code, so no step may write it")
    for t in HELD_OUT_TESTS:
        spec = plan["tests"].get(t)
        if not spec:
            continue
        rel = spec.get("data") or held["path"]
        if not study.inside(rel):
            continue
        target = (study.d / rel).resolve()
        named = False
        for w in spec["fetch"]:
            f = study.word(w, plan).resolve()
            if f == target or (f != study.d and f.is_relative_to(study.d) and target.is_relative_to(f)):
                named = True
        if not named:
            p.append(f"`tests.{t}.fetch`: the fetch command does not name `{rel}`, where the plan says the held-out data "
                     "goes, nor the folder it sits in. Write the path (or its folder) into the fetch command, so the "
                     "data cannot land somewhere the tool is not watching")
    return p


def evidence_problems(rid: str, pe) -> list:
    """A rule's power evidence: where the known-answers receipt reports on it, and the criteria it must meet.
    The tool carries four required criteria; a plan leaves one out only by waiving it with a reason."""
    where = f"rules[{rid}].power_evidence"
    if not isinstance(pe, dict):
        return [f"`{where}`: rule {rid} needs power_evidence (where the known-answer tests show the rule failing when the "
                "idea is false): a mapping with `path` (where in the known-answers receipt this rule's rates sit, such "
                f"as rules.{rid}) and `require` (a list of criteria; {CONDITION})"]
    p = unknown_keys(f"{where}.", pe, EVIDENCE_KEYS)
    why = conds_problem(pe.get("require"))
    if not is_text(pe.get("path")) or why:
        p.append(f"`{where}`: rule {rid} needs power_evidence with `path` (text, such as rules.{rid}) and `require` "
                 f"(a list of criteria; {CONDITION})" + (f". Here `require` {why}" if why else ""))
        return p
    waived = pe.get("waived") or []
    ok = isinstance(waived, list) and all(isinstance(w, dict) and set(w) == {"criterion", "reason"}
                                          and w["criterion"] in REQUIRED_CRITERIA and is_text(w["reason"])
                                          and len(w["reason"].strip()) >= 20 for w in waived)
    if not ok:
        p.append(f"`{where}.waived`: a list of {{criterion: one of {', '.join(REQUIRED_CRITERIA)}, reason: a sentence "
                 "saying why this rule cannot be held to it}")
        return p
    waived_names = {w["criterion"] for w in waived}
    for name in sorted(waived_names & set(NEVER_WAIVED)):
        p.append(f"`{where}.waived`: `{name}` cannot be waived. A rule has a refutation, and this criterion is what shows the "
                 "rule can refute when the idea is false; without it the rule has not been shown able to fail. Put it "
                 "under `require` with a value the known-answer tests could miss")
    for c in pe["require"]:
        if cannot_fail(c):
            p.append(f"`{where}.require`: `{c['field']} {c['op']} {c['value']}` is a criterion that cannot fail (every rate "
                     "between 0 and 1 meets it), so it shows nothing; set a value the known-answer tests could miss")
    for name, (direction, meaning) in REQUIRED_CRITERIA.items():
        mine = [c for c in pe["require"] if c["field"] == name]
        if name in waived_names:
            if mine:
                p.append(f"`{where}`: `{name}` is both required and waived; choose one")
            continue
        if not mine:
            p.append(f"`{where}.require`: the required criterion `{name}` is missing ({meaning}; {direction} some value). "
                     "Add it, or waive it under `waived` with a reason")
        elif not any(c["op"] in DIRECTION_OPS[direction] for c in mine):
            p.append(f"`{where}.require`: `{name}` is {meaning}, so its criterion is {direction} a value "
                     f"(op {' or '.join(DIRECTION_OPS[direction])})")
    return p


def subject_key(plan: dict, spec: dict) -> str:
    """What was held out, in a form that matches through spacing and case. It is the plan's `pair`, never
    the study's id: two studies of one subject must meet in the record whatever they are called."""
    key = spec.get("pair") or plan["data"]["held_out"]["pair"]

    def norm(v):
        if isinstance(v, dict):
            return {str(k).strip().casefold(): norm(x) for k, x in v.items()}
        return " ".join(str(v).split()).casefold()
    return json.dumps(norm(key), sort_keys=True)


def window_for(plan: dict, spec: dict) -> dict:
    return window_of(spec.get("window") or plan["data"]["held_out"]["window"])


def windows_overlap(a, b) -> bool:
    """Two windows overlap unless both are dated and apart. A window that cannot be read overlaps everything."""
    a, b = window_of(a), window_of(b)
    if a is None or b is None:
        return True
    return a["start"] <= b["end"] and b["start"] <= a["end"]


def openings_path(study: Study) -> Path:
    return study.d.parent / "openings.jsonl"  # one record of what has been opened, beside the studies, in the same commits


def record_lines(study: Study) -> list:
    """The record of what has been opened, one mapping per line; a line that does not parse is kept as unreadable."""
    rp, out = openings_path(study), []
    if not rp.is_file():
        return out
    for ln in rp.read_text().splitlines():
        if not ln.strip():
            continue
        try:
            e = json.loads(ln)
            out.append(e if isinstance(e, dict) else {"unreadable": ln[:200]})
        except ValueError:
            out.append({"unreadable": ln[:200]})
    return out


def own_line(ev: list, line: dict) -> bool:
    """A line of the record is this study's own only when the fingerprint it carries is that of an
    `opening.started` event in this study's log. The directory's name proves nothing."""
    seq, _, h = str(line.get("started", "")).partition(":")
    return (seq.isdigit() and int(seq) < len(ev) and ev[int(seq)]["hash"] == h
            and ev[int(seq)]["kind"] == "opening.started")


def is_system_trial(plan: dict | None) -> bool:
    return isinstance(plan, dict) and plan.get("study_kind") == "system_trial"


def earlier_openings(study: Study, plan: dict, spec: dict, ev: list) -> list:
    """Openings other studies have already made of this pair and window.
    A window is opened once; whatever a later study finds there is
    exploratory, which is what makes inconclusive a final answer. A
    system trial's data is made at its own opening, so nothing earlier
    can have opened it."""
    if is_system_trial(plan):
        return []
    key, window = subject_key(plan, spec), window_for(plan, spec)
    return [{k: e.get(k) for k in ("study", "dir", "test", "window", "at")} for e in record_lines(study)
            if not own_line(ev, e) and e.get("key") == key and windows_overlap(e.get("window"), window)]


def record_problems(study: Study, ev: list) -> list:
    """Where the record of what has been opened and this study's log disagree."""
    lines, p = record_lines(study), []
    for e in ev:
        if e["kind"] == "opening.started":
            mark = f"{e['seq']}:{e['hash']}"
            if not any(ln.get("started") == mark for ln in lines):
                p.append(f"the record of what has been opened ({openings_path(study).name}, beside the study) has no line for "
                         f"this study's {e['data']['test']} opening (event {e['seq']})")
    tests = sorted({str(ln.get("test")) for ln in lines if ln.get("dir") == study.d.name and not own_line(ev, ln)})
    for t in tests:
        p.append(f"the record of what has been opened holds a {t} opening made from this directory that this study log "
                 "does not contain (the log was cut back, or the directory is being used a second time)")
    return p


def openings_of(ev: list, test: str) -> tuple:
    started = [e for e in ev if e["kind"] == "opening.started" and e["data"]["test"] == test]
    voided = {e["data"]["n"] for e in ev if e["kind"] == "opening.voided" and e["data"]["test"] == test}
    return started, voided


def involved(ev: list) -> set:
    """Everyone who ran, wrote or decided part of the study, by name without regard to case."""
    return {e["actor"].casefold() for e in ev if e["kind"] not in NOT_PART_OF_THE_WORK}


def ran_tests(ev: list) -> set:
    return {e["actor"].casefold() for e in ev if e["kind"] in ("test.run", "rehearsal.run")}


# ---- commands -----------------------------------------------------------
def cmd_start(study: Study, a) -> None:
    if study.log.exists():
        raise Refused("this study is already started")
    if not str(a.question).strip().endswith("?"):
        raise Refused("the question is not a question: `--question` is one sentence ending in a question mark")
    asked_by = getattr(a, "asked_by", None)
    if asked_by and (not ACTOR.fullmatch(asked_by) or not asked_by.startswith("human:") or asked_by.lower() in PLACEHOLDER_ACTORS):
        raise Refused("`--asked-by` names the person who asked, as human:<id>")
    data = {"id": a.id, "question": a.question}
    request = getattr(a, "request", None)
    src = Path(request).resolve() if request else None
    if src is not None and not src.is_file():
        raise Refused(f"the request file {request} does not exist")
    study.d.mkdir(parents=True, exist_ok=True)
    if src is not None:
        if src.is_relative_to(study.d):
            dest = src
        else:
            dest = study.d / "request.md"  # the request the study answers is kept inside the study
            if dest.exists() and sha_file(dest) != sha_file(src):
                raise Refused("the study already holds a different request.md; start with `--request` on that file, or remove it")
            shutil.copyfile(src, dest)
        data["request"] = {"file": dest.relative_to(study.d).as_posix(), "sha": sha_file(dest)}
    if asked_by:
        data["asked_by"] = asked_by
    for sub in ("receipts", "notes", "verdicts", "data"):
        (study.d / sub).mkdir(exist_ok=True)
    study.append(a.by, "study.started", data)
    print(f"started {a.id}" + (f" (request {data['request']['file']}, sha256 {data['request']['sha'][:12]})" if src else ""))


def request_of(ev: list) -> dict | None:
    start = next((e for e in ev if e["kind"] == "study.started"), None)
    return start["data"].get("request") if start else None


def checked_plan(study: Study) -> dict:
    plan = study.plan()
    problems = check_plan(plan, study)
    if problems:
        raise Refused("the analysis plan does not pass its check: " + "; ".join(problems))
    return plan


def cmd_check_plan(study: Study, a) -> None:
    problems = check_plan(study.plan(), study)
    for x in problems:
        print("plan check:", x)
    if problems:
        raise Refused(f"{len(problems)} problem(s) in the analysis plan")
    note_held_out(study, study.plan(), study.events())  # in a started study: what is held out goes on record, or a change is refused
    print("plan check: the analysis plan is complete")


def passed_names(passes=()) -> list:
    """The names of the variables a command is given: the short list and every UV_ variable, where the caller
    has them set, and the names its plan step lists. The three PYTHON settings are added when it runs."""
    names = {k for k in os.environ if k in PASSED_ON or k.startswith("UV_")}
    names |= {k for k in passes or () if k in os.environ}
    return sorted(n for n in names if not n.upper().startswith(("PYTHON", "SF_")))


def given_names(passes=()) -> list:
    """The names of the variables a command of a plan runs under: the fixed list the tool builds for every script
    (tools/fence.py, `minimal_environment`) and the names its plan step lists. Nothing else of the caller's arrives."""
    built = fence.minimal_environment(Path("/"), sys.executable, mark=("SF_INSIDE_A_STEP", "1"))
    return sorted({*built, *(k for k in passes or () if k in os.environ and not k.upper().startswith(("PYTHON", "SF_")))})


def not_set(step: dict) -> list:
    return [n for n in step.get("passes_environment") or [] if n not in os.environ]


NOT_COPIED = ("study-log.jsonl", "scorecard.json", "curation-list.json")  # what a command of a plan is never shown
NOT_COPIED_FOLDERS = ("notes", "verdicts", ".git", "__pycache__")
RUNS = []  # how each command of this process ran, newest last: what the event of its test, rehearsal or opening records


def how_it_ran(since: int = 0) -> dict:
    """What the log records about how the commands of one step ran: whether the kernel fence was applied and
    tried for each, what a command could read and write, and anything it left running."""
    runs = RUNS[since:]
    if not runs:
        return {"commands": 0}
    worst = fence.KERNEL if all(r["confined"] == fence.KERNEL for r in runs) else fence.SCRATCH_ONLY
    return {"commands": len(runs), "confined": worst, "interpreter": runs[-1].get("interpreter"),
            "fence": runs[-1].get("fence"), "processes_ended": sum(r.get("ended", 0) for r in runs),
            "launcher_settings": runs[-1].get("settings") or {}}


def run_argv(study: Study, plan: dict, argv: list, passes=()) -> int:
    """Run one command of the plan the way a look is run (tools/fence.py): in a scratch copy of the study, with an
    interpreter prepared beforehand, an environment the tool builds (a fixed short list and the names the plan
    step lists under `passes_environment`), the kernel fence where the machine has one, and nothing left running
    afterwards. The command can read its scratch copy, the folders of the files the lock binds and the system's
    folders; it can write its scratch copy. It is never shown the study log, the notes or the verdicts, and it
    cannot read the tools. What it wrote is brought back into the study afterwards, except a change to a file the
    tool keeps, which fails the run. There is no input to read."""
    try:
        launcher, script = launch(argv)
        if launcher is None:
            return 126
        at = [str(w) for w in argv].index(script, 1)
        scratch = fence.make_scratch("sf-step-")
    except (ValueError, OSError):
        return 127
    work = scratch / "work" / "study"
    try:
        shutil.copytree(study.d, work, symlinks=True,
                        ignore=lambda folder, names: [n for n in names if (Path(folder) == study.d and (n in NOT_COPIED or n in NOT_COPIED_FOLDERS))
                                                      or n == "__pycache__"])
        before = {}
        for base, dirs, files in os.walk(work):
            for name in files + [d for d in dirs if (Path(base) / d).is_symlink()]:
                q = Path(base) / name
                before[q.relative_to(work).as_posix()] = os.readlink(q) if q.is_symlink() else sha_file(q)
        try:
            ready = fence.prepare_interpreter([str(w) for w in argv[:at]], study.word(script, plan), scratch / "private", cwd=study.d)
        except fence.Cannot as why:
            print(f"this command was not run: {why}", file=sys.stderr)
            return 127
        words = [ready["python"], *[study.expand(t, plan, study_dir=work) for t in argv[at:]]]
        read = list(ready["read"]) + [str(scratch / "private")]
        for key in study.code_hashes(plan):  # what the lock binds is what the command may read: a script's folder, or one file
            if key.startswith("("):
                continue
            f = study.word(key, plan)
            if f.resolve().is_relative_to(study.d):
                continue
            read.append(str(f.resolve().parent if f.suffix in IMPORTABLE else f.resolve()))
        env = fence.minimal_environment(scratch, ready["python"], {k: os.environ[k] for k in passes or () if k in os.environ
                                                                    and not k.upper().startswith(("PYTHON", "SF_"))},
                                        mark=("SF_INSIDE_A_STEP", study.d.name))
        never = [str(p) for p in (study.log, TOOL) if not any(Path(p).resolve().is_relative_to(Path(r).resolve()) for r in read)]
        try:
            ran = fence.run_fenced(words, work, env, scratch, read, [str(scratch / s) for s in ("work", "tmp", "cache", "home")],
                                   never_read=never, never_write=[str(study.d)], inherit=True)
        except fence.Cannot as why:
            print(f"this command was not run: {why}", file=sys.stderr)
            return 127
        code = ran["code"]
        RUNS.append({"confined": ran["confined"], "fence": ran["fence"], "ended": ran["ended"], "interpreter": ready["how"],
                     "settings": ready["settings"]})
        if ran["not_run"]:
            print("this command was not run: this machine has a kernel fence and it could not be put up or did not hold ("
                  + str(ran["fence"].get("why_not")) + ")", file=sys.stderr)
            return code or 120
        if ran["left_alive"]:
            print(f"this command left {ran['left_alive']} process(es) running that could not be ended; the run is a failure", file=sys.stderr)
            code = code or 97
        if ran["fence"].get("tools_changed"):
            print("this command ran without a kernel fence, and what the tools run from changed while it ran ("
                  + ", ".join(ran["fence"]["tools_changed"][:4]) + "); the run is a failure", file=sys.stderr)
            code = code or 98
        kept = []
        after = set()
        for base, dirs, files in os.walk(work):
            dirs.sort()
            for name in sorted(files) + [d for d in dirs if (Path(base) / d).is_symlink()]:
                q = Path(base) / name
                rel = q.relative_to(work).as_posix()
                after.add(rel)
                now = os.readlink(q) if q.is_symlink() else sha_file(q)
                if before.get(rel) == now:
                    continue
                if rel in PROTECTED or rel.split("/")[0] in PROTECTED_FOLDERS + ACT_FOLDERS:
                    kept.append(rel)
                    continue
                dest = study.d / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.is_symlink() or dest.is_file():
                    dest.unlink()
                if q.is_symlink():
                    os.symlink(now, dest)
                else:
                    shutil.copyfile(q, dest)
        for rel in sorted(set(before) - after):  # what the command removed is removed, unless the tool keeps it
            if rel in PROTECTED or rel.split("/")[0] in PROTECTED_FOLDERS + ACT_FOLDERS:
                kept.append(rel)
            else:
                with contextlib.suppress(OSError):
                    (study.d / rel).unlink()
        if kept:
            print("this command changed files the tool keeps (" + ", ".join(kept[:5]) + "); they were left as they stood and the "
                  "run is a failure", file=sys.stderr)
            code = code or 94
        return code
    except OSError as failure:
        print(f"this command was not run: {failure}", file=sys.stderr)
        return 127
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def runnable(study: Study, plan: dict, argv: list) -> bool:
    first = study.expand(argv[0], plan)
    return bool(shutil.which(first) or (study.d / first).is_file())


def early_data(study: Study, plan: dict, ev: list) -> list:
    """Held-out data sitting in the study before its opening: every held-out test's own data path is watched."""
    out = []
    for t in HELD_OUT_TESTS:
        spec = plan["tests"].get(t)
        if spec and not any(e["kind"] == "opening.started" and e["data"]["test"] == t for e in ev):
            rel = spec.get("data") or plan["data"]["held_out"]["path"]
            if study.path(rel).exists():
                out.append(rel)
    return out


def clear_outputs(study: Study, step: dict) -> Path | None:
    """Remove what a step is about to write, so a pass is a receipt this run wrote and nothing left behind
    can steer it."""
    rp = study.path(step["receipt"]) if step.get("receipt") else None
    for f in ([rp] if rp else []) + [study.path(w) for w in step.get("writes") or []]:
        if f.is_file() or f.is_symlink():
            f.unlink()
    return rp


def run_step(study: Study, plan: dict, argvs: list, passes=()) -> tuple:
    """Run the commands of one test or rehearsal, then look at what they did to the code identity:
    (exit code, what went wrong or None, the identity afterwards). A step that leaves behind a file its own
    command names, without the plan declaring it under `writes`, would change the identity every later step is
    held to; so would a step that rewrites something it is tested on. Either fails the run, in words."""
    before = study.code_hashes(plan)
    code = 0
    for argv in argvs:
        code = run_argv(study, plan, argv, passes)
        if code != 0:
            break
    after = study.code_hashes(plan)
    problem = None
    if code == 0:
        new = sorted(k for k in after if k not in before)
        changed = sorted(k for k in before if after.get(k) != before[k])
        if new:
            code, problem = 94, ("this run wrote files that its own command names and the plan does not declare ("
                                 + ", ".join(new) + "): list them under `writes` for this step, and the tool will remove "
                                 "them before each run and keep them out of the locked code")
        elif changed:
            code, problem = 94, ("this run changed files that are locked with the code (" + ", ".join(changed)
                                 + "): a step does not write to what it is tested on")
    return code, problem, after


def cmd_test(study: Study, a) -> None:
    if a.what not in FREE_TESTS:
        raise Refused(f"`{a.what}` is not a test that runs before the lock (known-answers or working-data); "
                      "held-out data is run only by `open-held-out`")
    plan = checked_plan(study)
    if early_data(study, plan, study.events()):
        raise Refused("held-out data is present in the workspace before any opening; testing stops here")
    note_held_out(study, plan, study.events())
    spec = plan["tests"][a.what]
    if not_set(spec):
        raise Refused(f"the plan passes {', '.join(not_set(spec))} to this test (`passes_environment`) and it is not set in "
                      "the environment; set it and run again. Nothing was run")
    passes = spec.get("passes_environment") or ()
    rp = clear_outputs(study, spec)  # a pass is a receipt this run wrote, never one left behind
    mark = len(RUNS)
    code, problem, identity = run_step(study, plan, [spec["command"]], passes)
    if code == 0 and not rp.is_file():
        code = 96  # exit 0 and no receipt is not a pass
    study.append(a.by, "test.run", {"test": a.what, "exit": code, "plan_sha": study.plan_sha(),
                                    "code": identity, "receipt_sha": sha_file(rp), "problem": problem,
                                    "env": env_stamp(study, plan), "env_names": given_names(passes),
                                    "held_out_sha": held_out_block(plan)["sha"], "ran_in": how_it_ran(mark)})
    name = TEST_NAMES.get(a.what, a.what)
    print(f"{name}: {'pass' if code == 0 else 'FAIL'} (exit {code})" + (f"; {problem}" if problem else ""))
    if code != 0:
        raise Refused(f"{name} did not pass" + (f": {problem}" if problem else ""))


def rule_fields(plan: dict) -> list:
    out = []
    for r in plan["rules"]:
        for c in list(r["supported_if"]) + [c for g in r["refuted_if"] for c in g]:
            out.append((r["id"], c["field"]))
    return out


def unresolved(plan: dict, receipt) -> list:
    """Rule fields a receipt does not carry as finite numbers."""
    bad = []
    for rid, field in rule_fields(plan):
        try:
            ok = is_num(dig(receipt, field))
        except (KeyError, TypeError):
            ok = False
        if not ok:
            bad.append(f"{rid}: {field}")
    return bad


def cmd_rehearse(study: Study, a) -> None:
    """A rehearsal on working data of something the opening depends on
    (its fetch path, the form of the finding), so the one opening is not
    spent discovering that it never worked."""
    plan = checked_plan(study)
    reh = next((r for r in plan.get("rehearsals") or [] if r["id"] == a.id), None)
    if not reh:
        raise Refused(f"no rehearsal `{a.id}` is in the plan")
    if early_data(study, plan, study.events()):
        raise Refused("held-out data is present in the workspace before any opening; testing stops here")
    note_held_out(study, plan, study.events())
    if not_set(reh):
        raise Refused(f"the plan passes {', '.join(not_set(reh))} to this rehearsal (`passes_environment`) and it is not set "
                      "in the environment; set it and run again. Nothing was run")
    passes = reh.get("passes_environment") or ()
    rp = clear_outputs(study, reh)
    mark = len(RUNS)
    absent = [str(n) for n in reh.get("needs") or [] if not study.word(n, plan).is_file()]
    if absent:  # what the rehearsal needs is not there: nothing is run, and the attempt is logged as a failure
        code, problem, identity = 93, "the rehearsal needs these files and they do not exist: " + ", ".join(absent), study.code_hashes(plan)
    else:
        code, problem, identity = run_step(study, plan, reh["steps"], passes)
    if code == 0 and rp is not None:
        try:
            missing = unresolved(plan, json.loads(rp.read_text()))
        except (OSError, ValueError):
            missing = ["no readable receipt"]
        if missing:
            code, problem = 95, "the rehearsal receipt lacks rule fields: " + ", ".join(missing)
    study.append(a.by, "rehearsal.run", {"id": a.id, "exit": code, "plan_sha": study.plan_sha(),
                                         "code": identity, "receipt_sha": sha_file(rp) if rp else None,
                                         "problem": problem, "env": env_stamp(study, plan),
                                         "env_names": given_names(passes),
                                         "held_out_sha": held_out_block(plan)["sha"], "ran_in": how_it_ran(mark)})
    print(f"rehearsal {a.id}: {'pass' if code == 0 else 'FAIL'} (exit {code})" + (f"; {problem}" if problem else ""))
    if code != 0:
        raise Refused(f"rehearsal {a.id} did not pass")


def need_person(a, what: str) -> None:
    if not str(a.by).startswith("human:"):
        raise Refused(f"{what} is a person's act; the actor must be human:<id>")
    if str(a.by).lower() in PLACEHOLDER_ACTORS:
        raise Refused(f"`{a.by}` is the placeholder from the documents; give the person's own id, such as human:jdoe")
    if not evidence_ok(a.evidence):
        raise Refused(f"{what} needs --evidence: the https URL of the person's approving review or comment, host name "
                      "and all (https://.../pull/N is a placeholder), because an actor name typed at a prompt proves nothing")


def definition_tool():
    """The validator, loaded from beside this file by its path: it knows how a definition tree is read and
    what its checksum is, so the lock, `status` and the scorecard name a definition the same way it does."""
    if "check_factory" not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_factory", TOOL.parent / "check_factory.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["check_factory"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["check_factory"]


def definition_of(root: Path) -> dict:
    """The root file of a definition tree, read. Refuses a folder that holds none, and a schema this tool does not know."""
    fy = Path(root) / "factory.yaml"
    try:
        spec = yaml.safe_load(fy.read_text())
    except (OSError, yaml.YAMLError):
        spec = None
    if not isinstance(spec, dict) or not isinstance(spec.get("procedure"), dict):
        raise Refused(f"{root} is not a factory's definition: it has no factory.yaml with a `procedure` (the definition is a folder "
                      "rooted at factory.yaml; `tools/check_factory.py` says what is wrong with one)")
    if spec.get("schemaVersion") not in definition_tool().SCHEMAS:
        raise Refused(f"the definition at {root} says schema version `{spec.get('schemaVersion')}`, which this study tool does not know")
    return spec


def definition_stamp(root: Path, lock: dict | None = None) -> dict:
    """Which definition a command read: its folder, the checksum of the whole tree, the version it gives itself,
    whether it is this factory's own (the factory/ folder in the repository the study tool is in), and whether it
    is the one the lock recorded."""
    root = Path(root).resolve()
    spec = definition_of(root)
    tree = definition_tool().tree_checksum(root)
    beside = root == FACTORY.resolve()
    whole = definition_tool().stamp(root)
    out = {"path": "factory/ (this factory's own)" if beside else str(root), "sha256": tree["sha256"], "files": tree["files"],
           "version": str(spec.get("version")), "models": whole["models"], "skills": whole["skills"],
           "this_factorys_own": beside, "remarks": []}
    if not beside:
        out["remarks"].append("this is not this factory's own definition (factory/): what it calls done is its own claim")
    locked = (lock or {}).get("data", {}).get("definition") if lock else None
    if locked:
        out["same_as_locked"] = locked.get("sha256") == out["sha256"]
        if not out["same_as_locked"]:
            out["remarks"].append(f"this is not the definition the lock recorded (the lock recorded version {locked.get('version')}, "
                                  f"sha256 {locked.get('sha256')})")
            for agent in sorted(set(locked.get("models") or {}) | set(out["models"])):
                was, is_ = (locked.get("models") or {}).get(agent), out["models"].get(agent)
                if was != is_:
                    out["remarks"].append(f"the agent `{agent}` declared {was} at the lock and declares {is_} now")
            for skill in sorted(set(locked.get("skills") or {}) | set(out["skills"])):
                if (locked.get("skills") or {}).get(skill) != out["skills"].get(skill):
                    out["remarks"].append(f"the skill `{skill}` is not the skill the lock recorded (its checksum differs, or it was added or removed)")
    return out


def models_report(ev: list, definition: dict) -> dict:
    """The models, both ways: what the definition's agents declare, and what the log's agent events recorded.
    Both are declarations. A recorded model that no agent of the definition declares is remarked on, because
    it means the work was done by something the definition does not describe."""
    declared = definition.get("models") or {}
    recorded = models_recorded(ev)
    known = {m.get("model") for m in declared.values()}
    out = {"declared_by_the_definition": declared, "recorded_in_the_log": recorded,
           "note": "a model is declared by the definition and by whoever calls the tool; nothing proves which model answered", "remarks": []}
    for actor, models in recorded.items():
        for m in models:
            if m not in known:
                out["remarks"].append(f"{actor} wrote under the model `{m}`, which no agent of this definition declares")
    return out


# ---- the held-out block, and every change to it ---------------------------------
def held_out_block(plan: dict) -> dict:
    """What a plan holds out, as one block with a checksum: the window, the subject, the withheld values, where the
    data lands, and the same for each test on held-out data. This is what the per-call check and the reviewers go
    by, so a change to it is an event of its own (`held-out-change`) and is shown at the lock."""
    held = (plan.get("data") or {}).get("held_out") or {}
    block = {"window": held.get("window"), "pair": held.get("pair"), "path": held.get("path"),
             "withheld_values": held.get("withheld_values"),
             "tests": {t: {k: spec[k] for k in ("data", "window", "pair") if isinstance(spec, dict) and spec.get(k) is not None}
                       for t, spec in sorted((plan.get("tests") or {}).items()) if t in HELD_OUT_TESTS}}
    text = json.dumps(block, sort_keys=True, default=str)
    return {"block": json.loads(text), "sha": sha_text(text)}


def held_out_paths(study: Study, block: dict) -> list:
    rels = [block.get("path")] + [t.get("data") for t in (block.get("tests") or {}).values()]
    return sorted({str((study.d / r).resolve()) for r in rels if isinstance(r, str) and r})


def held_out_record(study: Study) -> Path:
    """Beside the studies, like the record of what has been opened: every held-out block a study has declared,
    from the first time a tool saw it. A path once declared stays on it, whatever the plan says later."""
    return study.d.parent / "held-out.jsonl"


def held_out_lines(study: Study) -> list:
    out, f = [], held_out_record(study)
    if f.is_file():
        for ln in f.read_text().splitlines():
            with contextlib.suppress(ValueError):
                e = json.loads(ln)
                if isinstance(e, dict) and e.get("dir") == study.d.name:
                    out.append(e)
    return out


def _record_held_out(study: Study, block: dict, why: str) -> None:
    line = {"dir": study.d.name, "sha": block["sha"], "block": block["block"], "paths": held_out_paths(study, block["block"]),
            "at": now(), "why": why}
    with held_out_record(study).open("a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")


def note_held_out(study: Study, plan: dict, ev: list) -> None:
    """Record the plan's held-out block the first time a tool sees it in a started study, and from then on refuse to
    go on while the block differs from the one on record and no `held-out.changed` event accounts for it."""
    if not study.log.exists():
        return  # a template, or a folder nothing was started in: nothing is recorded beside it
    now_, lines = held_out_block(plan), held_out_lines(study)
    if not lines:
        _record_held_out(study, now_, "first seen")
    elif lines[-1]["sha"] != now_["sha"]:
        if any(e["kind"] == "held-out.changed" and e["data"]["to_sha"] == now_["sha"] and e["data"]["from_sha"] == lines[-1]["sha"] for e in ev):
            _record_held_out(study, now_, "changed, on the record")
        else:
            was, is_ = lines[-1]["block"], now_["block"]
            what = [f"{k}: was {json.dumps(was.get(k))}, is {json.dumps(is_.get(k))}" for k in sorted(set(was) | set(is_)) if was.get(k) != is_.get(k)]
            raise Refused("the plan's held-out block is not the one on record for this study (" + "; ".join(what)[:500] + "). What is "
                          "held out is not changed by editing the plan alone: the coordinating step records the change, with its "
                          "reason, by `sf.py held-out-change --study ... --by ... --reason ...`, and the lock shows every such "
                          "change. Nothing was run")


def held_out_history(study: Study, ev: list, plan: dict | None = None) -> list:
    """Every state of the held-out block this study's log knows, in order, in plain words: the first one a test or a
    rehearsal ran under, each recorded change with who recorded it and why, and any change the log shows without a
    record of it (a test that ran under another block than the one before it)."""
    out, last = [], None
    for e in ev:
        d = e["data"]
        if e["kind"] == "held-out.changed":
            out.append({"at_event": e["seq"], "what": "changed, on the record", "by": e["actor"], "reason": d.get("reason"),
                        "from": d.get("from"), "to": d.get("to"), "sha": d["to_sha"]})
            last = d["to_sha"]
        elif e["kind"] in ("test.run", "rehearsal.run", "lock.requested") and d.get("held_out_sha"):
            if last is None:
                out.append({"at_event": e["seq"], "what": "first recorded in the log", "by": e["actor"], "sha": d["held_out_sha"]})
            elif d["held_out_sha"] != last:
                out.append({"at_event": e["seq"], "what": "CHANGED WITH NO RECORD OF THE CHANGE", "by": e["actor"], "sha": d["held_out_sha"]})
            last = d["held_out_sha"]
    if plan is not None:
        now_ = held_out_block(plan)
        if last is not None and now_["sha"] != last:
            out.append({"at_event": None, "what": "CHANGED WITH NO RECORD OF THE CHANGE (the plan on disk)", "by": None, "sha": now_["sha"]})
    return out


def cmd_held_out_change(study: Study, a) -> None:
    """The coordinating step records that what is held out has changed, and why. The plan on disk already carries
    the new block (a person edits the plan; the per-call check refuses the analysis role that edit)."""
    plan = checked_plan(study)
    ev = study.events()
    if a.by.casefold() in ran_tests(ev):
        raise Refused(f"{a.by} ran this study's tests or rehearsals; a change to what is held out is recorded by the coordinating "
                      "step or a person, not by whoever builds the method")
    if not str(a.reason or "").strip():
        raise Refused("`--reason` says why what is held out changed; the lock shows it")
    if any(e["kind"] == "opening.started" for e in ev):
        raise Refused("held-out data has been opened in this study; what is held out is not changed afterwards")
    now_, lines = held_out_block(plan), held_out_lines(study)
    if not lines:
        _record_held_out(study, now_, "first seen")
        print("the held-out block is now on record for this study; nothing had been recorded before, so nothing changed")
        return
    if lines[-1]["sha"] == now_["sha"]:
        raise Refused("the plan's held-out block is the one on record: nothing changed")
    study.append(a.by, "held-out.changed", {"from_sha": lines[-1]["sha"], "to_sha": now_["sha"], "from": lines[-1]["block"],
                                            "to": now_["block"], "reason": a.reason})
    _record_held_out(study, now_, "changed, on the record")
    print(f"held-out block changed, on the record (was sha256 {lines[-1]['sha'][:12]}, is {now_['sha'][:12]}); the lock will show it. "
          "Tests and rehearsals that passed under the old block still stand in the log; the lock needs them on the plan as it is now")


# ---- the two acts by people: a request, then a merged pull request ------------------
PRACTICE = "practice"            # the act was typed at a command line: for trying things out, the examples and the self-tests
PULL_REQUEST = "pull-request"    # the act was a pull request approved and merged on a protected branch
PRACTICE_WORDS = ("PRACTICE LOCK: this study was locked from a command line, not by an approved pull request. It is a practice "
                  "run and cannot close as a signed finding.")
ROUTES = ("in a real study the {act} is a pull request: `sf.py request-{act}` writes the request into the study, a person approves "
          "and merges it on the protected branch, and the merge is recorded with `sf.py {act} --record-merge` (the workflow in "
          "factory/harnesses/github does that). To try the tools out, `sf.py {act} --local-practice --by human:<id> --evidence URL` "
          "records it from the command line; a study whose {act} was typed says so everywhere and never closes as a signed finding")


def acts_declared(factory: Path) -> dict:
    """The two acts as the definition declares them (factory.yaml, procedure.acts_by_people)."""
    acts = definition_of(Path(factory))["procedure"].get("acts_by_people")
    return acts if isinstance(acts, dict) else {}


def route_of(event: dict | None) -> str | None:
    """How a lock or a signature in the log was made: `practice`, `pull-request`, or None when there is none. An
    event from before the routes had names was typed at a command line, which is what practice means."""
    if not event:
        return None
    return event["data"].get("route") or PRACTICE


def is_act_by_people(e: dict) -> bool:
    """Is a lock, a signature or a void in the log recorded the way an act by people is? Typed: a person's name and
    an https link. From a merge: the platform as the actor, the merge commit, and at least one person who approved."""
    d = e["data"]
    if d.get("route") == PULL_REQUEST:
        merge = d.get("merge") or {}
        return bool(PLATFORM_ACTOR.fullmatch(e["actor"]) and re.fullmatch(r"[0-9a-f]{40,64}", str(merge.get("commit")))
                    and (merge.get("people") or {}).get("approved"))
    return e["actor"].startswith("human:") and evidence_ok(d.get("evidence"))


def repo_of(study: Study) -> Path | None:
    top = git("-C", str(study.d), "rev-parse", "--show-toplevel")
    return Path(top.stdout.strip()).resolve() if top and top.returncode == 0 and top.stdout.strip() else None


def manifest_now(study: Study, plan: dict, ev: list, factory: Path, act: str) -> dict:
    """What a request binds, worked out from the files as they stand: every checksum the act would bind. Two
    manifests are the same exactly when nothing bound has changed."""
    request = request_of(ev)
    definition = definition_stamp(Path(factory))
    out = {"schema": "science-factory/act-request/v1", "act": act, "study": study.d.name,
           "plan_sha": study.plan_sha(), "code": study.code_hashes(plan),
           "request": {"file": request["file"], "sha": sha_file(study.d / request["file"])} if request else None,
           "definition": {k: definition[k] for k in ("sha256", "files", "version", "models", "skills")},
           "held_out": held_out_block(plan), "uv_environments": study.uv_environments() if uses_uv(plan) else {}}
    if act == "lock":
        out["receipts"] = {t: sha_file(study.path(plan["tests"][t]["receipt"])) for t in FREE_TESTS}
        out["receipts"].update({f"rehearsal:{r['id']}": sha_file(study.path(r["receipt"])) for r in plan.get("rehearsals") or [] if r.get("receipt")})
    else:
        att = attached_finding(ev)
        out["finding"] = {"file": att["data"]["file"], "sha": sha_file(study.d / att["data"]["file"])} if att else None
        out["verdicts"] = {e["data"]["file"]: sha_file(study.d / e["data"]["file"]) for e in ev if e["kind"] == "review.verdict"}
        out["decision"] = None  # filled in by the request
    return out


def manifest_difference(asked: dict, now_: dict) -> list:
    """In plain words, what differs between the manifest a request carries and the files as they stand."""
    out = []
    for key in sorted(set(asked) | set(now_)):
        a_, b_ = asked.get(key), now_.get(key)
        if a_ == b_ or key in ("log_head", "prepared", "decision"):
            continue
        if key == "code" and isinstance(a_, dict) and isinstance(b_, dict):
            out += ["a bound file: " + d for d in code_difference(a_, b_)] or ["the study tool itself"]
        elif key == "definition" and isinstance(a_, dict) and isinstance(b_, dict):
            out.append(f"the factory's definition (the request binds version {a_.get('version')}, sha256 {str(a_.get('sha256'))[:16]}; "
                       f"here it is version {b_.get('version')}, sha256 {str(b_.get('sha256'))[:16]})")
        elif isinstance(a_, dict) and isinstance(b_, dict):
            out += [f"{key}: {k}" for k in sorted(set(a_) | set(b_)) if a_.get(k) != b_.get(k)]
        else:
            out.append({"plan_sha": "the analysis plan"}.get(key, key))
    return out


def definition_change_summary(locked: dict, factory: Path) -> list:
    """What changed in the definition since a lock, in the validator's own words when the locked tree can still be
    found in this repository's history; otherwise what the lock's own stamp shows (a model, a skill)."""
    root = Path(factory).resolve()
    stamp = definition_stamp(root, {"data": {"definition": locked}})
    lines = [r for r in stamp["remarks"] if "not the definition the lock recorded" not in r and "not this factory's own" not in r]
    tool = definition_tool()
    top = git("-C", str(root), "rev-parse", "--show-toplevel")
    if top is not None and top.returncode == 0 and top.stdout.strip():
        repo = Path(top.stdout.strip()).resolve()
        rel = root.relative_to(repo).as_posix() if root.is_relative_to(repo) else None
        log = git("-C", str(repo), "log", "--format=%H", "-n", "100", "--", rel) if rel else None
        for commit in (log.stdout.split() if log is not None and log.returncode == 0 else []):
            tmp = Path(tempfile.mkdtemp(prefix="sf-definition-"))
            try:
                done = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", commit, rel], capture_output=True,
                                      env={k: os.environ[k] for k in passed_names()}, stdin=subprocess.DEVNULL)
                if done.returncode != 0:
                    continue
                import io
                import tarfile
                with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
                    tar.extractall(tmp, filter="data")
                if tool.tree_checksum(tmp / rel)["sha256"] == locked.get("sha256"):
                    return [str(x) for x in tool.summary(tmp / rel, root)][:40] + lines
            except (OSError, ValueError, KeyError):
                continue
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
    return lines + ["the locked tree was not found in this repository's history, so the validator's summary of the change could not "
                    "be made here: run `tools/check_factory.py --summary OLD NEW` on the two trees"]


def merge_problems(study: Study, merge: dict, request_folder: str) -> tuple:
    """Check, with git alone and offline, the merge a lock or a signature cites: (problems, the manifest in the
    merge commit or None). The commit exists; it lies on the named branch's own line of commits (its first parents)
    and is reachable from HEAD; it brought the request in or changed it; and the request's manifest is in it.
    git cannot say who approved the pull request, or that the branch is protected: the platform's record says
    that, and the recording job copies it into the log."""
    repo = repo_of(study)
    if repo is None:
        return ["the study is not in a git work tree, so the merge the act cites cannot be checked"], None
    commit, branch = str(merge.get("commit") or ""), str(merge.get("branch") or "")
    if not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        return ["the act cites no merge commit by its full checksum"], None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,200}", branch) or ".." in branch:
        return ["the act names no protected branch"], None
    g = lambda *words: git("-C", str(repo), *words)  # noqa: E731
    ok = lambda done: done is not None and done.returncode == 0  # noqa: E731
    if not ok(g("cat-file", "-e", commit + "^{commit}")):
        return [f"the merge commit {commit[:12]} is not in this repository"], None
    refs = [r for r in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}") if ok(g("rev-parse", "--verify", "--quiet", r))]
    if not refs:
        return [f"this clone has no branch `{branch}` (neither origin/{branch} nor a local one): fetch it"], None
    ref = refs[0]
    problems = []
    line = g("rev-list", "--first-parent", ref)
    if not ok(line) or commit not in line.stdout.split():
        problems.append(f"the commit {commit[:12]} is not on the branch `{branch}` ({ref}): it is not one of that branch's own "
                        "commits (its first parents), so it was not merged there")
    if not ok(g("merge-base", "--is-ancestor", commit, "HEAD")):
        problems.append(f"the merge commit {commit[:12]} is not reachable from what is checked out here (HEAD): check out the "
                        f"protected branch `{branch}` at or after the merge")
    rel = (study.d / request_folder / "manifest.json").relative_to(repo).as_posix()
    shown = g("show", f"{commit}:{rel}")
    if not ok(shown):
        problems.append(f"the merge commit {commit[:12]} does not hold the request's manifest ({rel})")
        return problems, None
    before = g("show", f"{commit}^1:{rel}")
    if ok(before) and before.stdout == shown.stdout:
        problems.append(f"the commit {commit[:12]} did not bring this request in or change it: the manifest was already there, "
                        "unchanged, in the commit before it on the branch")
    try:
        manifest = json.loads(shown.stdout)
    except ValueError:
        problems.append("the manifest in the merge commit is not JSON")
        return problems, None
    return problems, {"manifest": manifest, "sha": sha_text(shown.stdout), "ref": ref}


def platform_record(path, act: str, declared: dict) -> dict:
    """The platform's record of a merged pull request, read from the file the recording job wrote, and held to
    what the definition declares for the act: the pull request was merged, and enough people other than its author
    approved it. The names in it are the platform's, never typed at this tool."""
    try:
        rec = json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError):
        raise Refused("`--platform-record` names the JSON file the recording job wrote from the platform's own record of the "
                      "merged pull request (factory/harnesses/github/record_act.py writes it); it could not be read")
    need = int((declared.get(act) or {}).get("approvals") or 1)
    author, approved = str(rec.get("author") or ""), [str(x.get("login") if isinstance(x, dict) else x) for x in rec.get("approved") or []]
    others = sorted({x for x in approved if x and x.casefold() != author.casefold()})
    if not rec.get("merged") or not re.fullmatch(r"[0-9a-f]{40,64}", str(rec.get("merge_commit") or "")):
        raise Refused("the platform's record does not say the pull request was merged, with its merge commit")
    if not author or len(others) < need:
        raise Refused(f"the platform's record shows {len(others)} approving review(s) by people other than the pull request's author "
                      f"({author or 'unknown'}); the definition asks for {need} for the {act}. An author's own approval does not count")
    if not PLATFORM_ACTOR.fullmatch("platform:" + str(rec.get("platform") or "")):
        raise Refused("the platform's record does not name the platform (such as github)")
    return {"platform": rec["platform"], "pull_request": rec.get("pull_request"), "url": rec.get("url"), "merge_commit": rec["merge_commit"],
            "branch": rec.get("base"), "merged_at": rec.get("merged_at"),
            "people": {"author": author, "approved": others, "merged_by": rec.get("merged_by")},
            "reviews": [x for x in rec.get("approved") or [] if isinstance(x, dict)]}


def practice_declared(factory: Path, act: str) -> bool:
    """Does the definition itself declare this act as practice (`route: practice`)? Then every study made under it
    is a practice study, with no flag needed, and says so."""
    try:
        return (acts_declared(factory).get(act) or {}).get("route") == PRACTICE
    except Refused:
        return False


def refuse_typed_act(a, act: str, factory: Path) -> None:
    if not (getattr(a, "local_practice", False) or Study.default_route == PRACTICE or practice_declared(factory, act)):
        raise Refused(ROUTES.format(act=act))


def write_request(study: Study, folder: str, summary: list, manifest: dict) -> tuple:
    out = study.d / folder
    out.mkdir(exist_ok=True)
    text = "\n".join(summary).rstrip() + "\n"
    (out / "EVIDENCE.md").write_text(text)
    manifest = {**manifest, "evidence_summary_sha": sha_text(text)}
    body = json.dumps(manifest, indent=1, sort_keys=True, default=str) + "\n"
    (out / "manifest.json").write_text(body)
    return sha_text(body), sha_text(text)


def from_the_request(study: Study, ev: list) -> dict:
    """What a request that came from an exploration's hand-over says about the exploring and its review."""
    req = request_of(ev)
    try:
        text = (study.d / req["file"]).read_text() if req else ""
    except OSError:
        text = ""
    pick = lambda label: next((ln.split("**", 2)[2].strip() for ln in text.splitlines() if ln.startswith(f"**{label}.**")), None)  # noqa: E731
    return {"how_it_was_found": pick("How it was found"), "review_of_the_lead": pick("The review of the lead"), "text": text}


def conds_text(conds: list) -> str:
    return " and ".join(f"{c['field']} {c['op']} {c['value']}" for c in conds)


def lock_evidence(study: Study, a) -> dict:
    """Everything the lock checks and everything it shows, without recording anything: the tests and rehearsals
    passed on exactly this plan and code, every rule met its criteria, and what the people locking are shown, as
    lines. The same for a lock typed at a command line and for a request that goes into a pull request."""
    plan = checked_plan(study)
    ev = study.events()
    note_held_out(study, plan, ev)
    lines = []
    say = lines.append
    code, psha = study.code_hashes(plan), study.plan_sha()
    if None in code.values():
        raise Refused("a file the plan names is missing: " + ", ".join(k for k, v in code.items() if v is None))
    bound = {}
    for t in FREE_TESTS:
        e = study.last("test.run", test=t)
        if not e or e["data"]["exit"] != 0:
            raise Refused(f"{TEST_NAMES[t]}: not passed yet")
        if e["data"]["plan_sha"] != psha or e["data"]["code"] != code:
            raise Refused(f"{TEST_NAMES[t]} passed on a different plan or different code; run again")
        if e["data"]["receipt_sha"] != sha_file(study.path(plan["tests"][t]["receipt"])):
            raise Refused(f"the {t} receipt on disk is not the one the study log recorded")
        bound[t] = e["data"]["receipt_sha"]
    for reh in plan.get("rehearsals") or []:
        e = study.last("rehearsal.run", id=reh["id"])
        if not e or e["data"]["exit"] != 0:
            raise Refused(f"rehearsal `{reh['id']}` has not passed ({reh.get('why', 'it is in the plan')})")
        if e["data"]["plan_sha"] != psha or e["data"]["code"] != code:
            raise Refused(f"rehearsal `{reh['id']}` passed on a different plan or different code; run it again")
        bound[f"rehearsal:{reh['id']}"] = e["data"]["receipt_sha"]
    try:
        known = json.loads(study.path(plan["tests"]["known-answers"]["receipt"]).read_text())
        working = json.loads(study.path(plan["tests"]["working-data"]["receipt"]).read_text())
    except ValueError:
        raise Refused("a test receipt is not JSON")
    missing = unresolved(plan, working)
    if missing:
        raise Refused("the working-data receipt does not carry these rule fields as numbers, so the opening "
                      "could not be judged: " + ", ".join(missing))
    shown = []  # what the people locking are shown: each rule, each criterion, and the rate measured beside it
    for r in plan["rules"]:
        pe = r["power_evidence"]
        try:
            block = dig(known, pe["path"])
        except (KeyError, TypeError):
            raise Refused(f"rule {r['id']}: no power evidence at `{pe['path']}` in the known-answers receipt")
        if not isinstance(block, dict) or block.get("tested_rule") != rule_as_tested(r):
            raise Refused(f"rule {r['id']}: the known-answer evidence is not for the rule as planned "
                          "(the receipt must echo the supported_if and refuted_if it exercised)")
        if not holds(pe["require"], block):
            have = {k: v for k, v in block.items() if k != "tested_rule"}
            raise Refused(f"rule {r['id']}: the known-answer tests do not show this rule failing when the idea is false "
                          f"(needs {pe['require']}, has {have})")
        shown.append(f"  {r['id']} ({r.get('role', 'secondary')}): supported if {conds_text(r['supported_if'])}; refuted if "
                     + ", or ".join(conds_text(g) for g in r["refuted_if"]) + "; anything else is inconclusive")
        for c in pe["require"]:
            need = " (required of every rule)" if c["field"] in REQUIRED_CRITERIA else ""
            shown.append(f"    criterion {c['field']} {c['op']} {c['value']}: measured {block.get(c['field'])}{need}")
        for w in pe.get("waived") or []:
            shown.append(f"    WAIVED {w['criterion']}: {w['reason']}")
    request = request_of(ev)
    if request:
        on_disk = sha_file(study.d / request["file"])
        if on_disk is None:
            raise Refused(f"the request the study was started with ({request['file']}) is missing; the lock binds it with the plan")
        request = {"file": request["file"], "sha": on_disk, "changed_since_the_start": on_disk != request["sha"]}
    definition = definition_stamp(Path(getattr(a, "factory", None) or FACTORY))
    after_opening = any(e["kind"] == "opening.started" for e in ev)
    say("What this lock binds.")
    say(f"the analysis plan: sha256 {psha}" + (" (a system trial: its held-out data is made at its own opening, and it can "
                                                  "close only as a system trial, never as a finding)" if is_system_trial(plan) else ""))
    started = next((e for e in ev if e["kind"] == "study.started"), None)
    if started and " ".join(str(started["data"].get("question")).split()) != " ".join(str(plan["question"]).split()):
        say("the question, as the study was started: " + str(started["data"].get("question")))
        say("the question, as the plan has it:       " + " ".join(str(plan["question"]).split()))
    if request:
        say(f"the request: {request['file']}, sha256 {request['sha']}"
              + (" (CHANGED since the study started; this is the text that is bound)" if request["changed_since_the_start"] else ""))
    else:
        say("the request: none was given when the study started, so none is bound")
    say(f"the factory's definition: {definition['path']}, version {definition['version']}, {definition['files']} files, sha256 {definition['sha256']}")
    say("the models its agents declare (declared, not proven): "
          + "; ".join(f"{a} {m['model']} under {m['harness']}" for a, m in sorted(definition["models"].items())))
    say("the skills its agents use, each by sha256: " + "; ".join(f"{s} {h[:16]}" for s, h in sorted(definition["skills"].items())))
    recorded = models_recorded(ev)
    say("the models this study's log records so far: "
          + ("; ".join(f"{a} {', '.join(m)}" for a, m in sorted(recorded.items())) or "no agent has written to it"))
    for remark in models_report(ev, definition)["remarks"]:
        say(f"  {remark}")
    for remark in definition["remarks"]:
        say(f"  {remark}")
    say(f"bound files ({len(code)}), each by sha256; a change to any of them, or anything new that Python could import "
          "beside them, blocks the opening:")
    for k in sorted(code):
        say(f"  {code[k][:16]}  {k}")
    say("commands, each with the script it runs, which is bound above:")
    for where, argv in Study.commands(plan):
        launcher, script = launch(argv)
        say(f"  {where}: {launcher} runs {script} (sha256 {code[script][:16]})")
    for reh in plan.get("rehearsals") or []:
        for n in reh.get("needs") or []:
            say(f"  rehearsals[{reh['id']}].needs: {n} (sha256 {code[str(n)][:16]})")
    environments = study.uv_environments() if uses_uv(plan) else {}
    for key, sha in environments.items():
        say(f"  a virtual environment folder that `uv run` would use: {key} (its pyvenv.cfg and interpreter, sha256 {sha[:16]}; "
              "what else is inside it is not bound)")
    asked = {w: s.get("passes_environment") for w, s in [(f"tests.{k}", v) for k, v in plan["tests"].items()]
             + [(f"rehearsals[{r['id']}]", r) for r in plan.get("rehearsals") or []] if s.get("passes_environment")}
    say("environment a command is given: a short list the tool keeps, every UV_ variable"
          + ("".join(f"; {w} is also given {', '.join(v)}" for w, v in asked.items()) if asked else "; no step asks for more"))
    say("decision rules, each criterion with the rate the known-answer tests measured beside it:")
    for line in shown:
        say(line)
    say("openings allowed: " + ", ".join(f"{t} {study.allowed(plan, t)}" for t in HELD_OUT_TESTS if t in plan["tests"]))
    history = held_out_history(study, ev, plan)
    say("what is held out, and every change to it this study's log knows:")
    say("  now: " + json.dumps(held_out_block(plan)["block"], sort_keys=True))
    for h in history:
        say(f"  {h['what']}" + (f" at event {h['at_event']}" if h["at_event"] is not None else "") + (f" by {h['by']}" if h.get("by") else "")
            + (f": {h['reason']}" if h.get("reason") else "") + f" (sha256 {h['sha'][:16]})")
    if not history:
        say("  no test or rehearsal has recorded it yet")
    on_record = record_lines(study)
    spec = plan["tests"]["held-out"]
    key, window = subject_key(plan, spec), window_for(plan, spec)
    same = [ln for ln in on_record if ln.get("key") == key and windows_overlap(ln.get("window"), window)]
    say(f"openings already on record beside this study: {len(on_record)}, of which {len(same)} are of this subject and an "
        "overlapping window" + ("" if not on_record else " (read them: the record matches subjects by text, a person "
                                                       "matches them by meaning)"))
    for ln in same + [ln for ln in on_record if ln not in same][-20:]:
        say(("  SAME SUBJECT  " if ln in same else "  ") + json.dumps(ln, sort_keys=True))
    data = {"plan_sha": psha, "code": code, "receipts": bound, "after_opening": after_opening, "request": request,
            "uv_environments": environments,
            "definition": {k: definition[k] for k in ("path", "sha256", "files", "version", "models", "skills")},
            "models_recorded": recorded, "held_out": held_out_block(plan), "held_out_history": history}
    return {"plan": plan, "ev": ev, "lines": lines, "data": data, "shown": shown}


def lock_summary(study: Study, got: dict, factory: Path) -> list:
    """The evidence summary of a lock request, in plain words: what a person reads before approving the pull
    request. Generated from the study as it stands; the manifest beside it holds the checksums."""
    plan, ev, d = got["plan"], got["ev"], got["data"]
    started = next((e for e in ev if e["kind"] == "study.started"), None)
    runs = [e for e in ev if e["kind"] in ("test.run", "rehearsal.run")]
    notes = stage_of(study, factory)["open_notes"]
    came = from_the_request(study, ev)
    reviews = [e for e in ev if e["kind"] == "review.verdict"]
    out = [f"# Lock request: {plan['study']}", "",
           "This is a request to lock a study's plan and code together, so that its held-out data can be opened once. Nothing is "
           "locked by this file. The lock is a person's act: approving and merging the pull request that carries this folder, on the "
           "protected branch. Read what follows before you approve; the checksums are in `manifest.json` beside this file, and the "
           "required check on the pull request says whether they still match the files.", "",
           "## The question", "", str(plan["question"]).strip(), ""]
    if started and " ".join(str(started["data"].get("question")).split()) != " ".join(str(plan["question"]).split()):
        out += ["As the study was started, the question read: " + str(started["data"].get("question")), ""]
    out += ["## What would count for and against (the plan's rules)", ""] + ["    " + ln for ln in got["shown"]] + [""]
    out += ["## What is held out, and every change to it", "", "    " + json.dumps(d["held_out"]["block"], sort_keys=True), ""]
    out += [f"- {h['what']}" + (f", at log event {h['at_event']}" if h["at_event"] is not None else "") + (f", by {h['by']}" if h.get("by") else "")
            + (f": {h['reason']}" if h.get("reason") else "") for h in d["held_out_history"]] or ["- nothing recorded yet"]
    out += ["", "## The known-answer tests, working data and rehearsals", "",
            f"{len(runs)} attempts are in the log, of which {sum(1 for e in runs if e['data']['exit'] != 0)} failed. The receipts this lock would bind:", ""]
    out += [f"- {name}: sha256 {sha}" for name, sha in sorted(d["receipts"].items())]
    fenced = sorted({(e["data"].get("ran_in") or {}).get("confined") or "not recorded" for e in runs})
    out += ["", "How the plan's commands ran (the kernel fence, or a scratch folder only): " + ", ".join(fenced) + ".", "",
            "## The code this lock would bind", "", f"{len(d['code'])} files, each by sha256:", ""]
    out += [f"- `{k}` {v[:16] if v else 'MISSING'}" for k, v in sorted(d["code"].items())]
    out += ["", "## The factory that made this study", "",
            f"Definition version {d['definition']['version']}, {d['definition']['files']} files, sha256 {d['definition']['sha256']}. "
            "If the definition changes after the lock, the opening is refused until the study is locked again.", "",
            "Models its agents declare (declared, not proven): " + "; ".join(f"{k} {m['model']} under {m['harness']}" for k, m in sorted(d["definition"]["models"].items())) + ".",
            "Models the log records so far: " + ("; ".join(f"{k} {', '.join(m)}" for k, m in sorted(d["models_recorded"].items())) or "no agent has written to it") + ".", "",
            "## Open notes", ""] + ([f"- {n}" for n in notes] or ["None."])
    out += ["", "## The exploration that led here, and what its reviewer said", ""]
    if came["how_it_was_found"] or came["review_of_the_lead"]:
        out += ["How many things were tried: " + str(came["how_it_was_found"] or "the request does not say."), "",
                "The review of the lead: " + str(came["review_of_the_lead"] or "the request does not say."), ""]
    else:
        out += ["This study's request carries no hand-over from an exploration, so nothing is known here about what was tried before it.", ""]
    out += ["Reviews recorded in this study's own log so far: " + ("; ".join(f"{e['actor']} {e['data']['verdict']}" for e in reviews) or "none (a study is reviewed after its opening)") + ".", "",
            "## Everything the lock prints", "", "```"] + got["lines"] + ["```"]
    return out


def cmd_request_lock(study: Study, a) -> None:
    """Write the lock request into the study: the evidence summary a person reads and the manifest of what the
    lock would bind. An assistant may do this; it records nothing as locked."""
    factory = Path(getattr(a, "factory", None) or FACTORY)
    study.check_actor(a.by)
    got = lock_evidence(study, a)
    manifest = manifest_now(study, got["plan"], got["ev"], factory, "lock")
    head = got["ev"][-1]
    manifest.update(log_head={"seq": head["seq"], "hash": head["hash"]}, prepared={"by": a.by, "at": now()},
                    protected_branch=(acts_declared(factory).get("lock") or {}).get("protected_branch"),
                    after_opening=got["data"]["after_opening"])
    msha, ssha = write_request(study, "lock-request", lock_summary(study, got, factory), manifest)
    study.append(a.by, "lock.requested", {"manifest_sha": msha, "summary_sha": ssha, "plan_sha": manifest["plan_sha"],
                                          "held_out_sha": manifest["held_out"]["sha"]})
    print(f"lock request written: {study.d.name}/lock-request/EVIDENCE.md and manifest.json (manifest sha256 {msha[:16]}). Nothing is "
          "locked. Commit the study, open a pull request against the protected branch, and have it approved and merged by the "
          "people the definition names; the merge is the lock")


def cmd_check_request(study: Study, a) -> None:
    """Does the request in the study still match the files it was made from? The pull request's required check."""
    if a.act not in ("lock", "signature"):
        raise Refused("`--act` is lock or signature")
    problems = request_problems(study, a.act, Path(getattr(a, "factory", None) or FACTORY))
    if problems:
        raise Refused(f"the {a.act} request does not match the files as they stand: " + "; ".join(problems[:8])
                      + f". Prepare it again (`sf.py request-{a.act}`), and have it approved as it then stands")
    print(f"{a.act} request: the manifest matches the files as they stand")


def cmd_lock(study: Study, a) -> None:
    factory = Path(getattr(a, "factory", None) or FACTORY)
    if getattr(a, "record_merge", None):
        record_merged_act(study, a, "lock", factory)
        return
    need_person(a, "the lock")
    refuse_typed_act(a, "lock", factory)
    got = lock_evidence(study, a)
    for line in got["lines"]:
        print(line)
    print("THIS IS A PRACTICE LOCK, typed at a command line: no pull request, no approval the platform recorded. The study says so "
          "in its status, on its scorecard and in its finding, and it cannot close as a signed finding")
    e = study.append(a.by, "lock.recorded", {**got["data"], "evidence": a.evidence, "route": PRACTICE})
    print("The lock: plan and code locked (practice)" + (" (AFTER an opening: this study is now exploratory)" if got["data"]["after_opening"] else ""))
    print(f"post this log fingerprint where the workspace cannot rewrite it: {e['seq']}:{e['hash']}")


def request_problems(study: Study, act: str, factory: Path) -> list:
    """Why a request in the study no longer matches the files it was made from, in plain words; empty when it does."""
    folder = f"{act}-request"
    try:
        asked = json.loads((study.d / folder / "manifest.json").read_text())
        text = (study.d / folder / "EVIDENCE.md").read_text()
    except (OSError, ValueError):
        return [f"the study holds no readable {folder}/manifest.json and EVIDENCE.md: run `sf.py request-{act}`"]
    if asked.get("evidence_summary_sha") != sha_text(text):
        return ["the evidence summary (EVIDENCE.md) is not the one the manifest names: it was edited after the request was prepared"]
    plan = checked_plan(study)
    here = manifest_now(study, plan, study.events(), factory, act)
    return manifest_difference({k: v for k, v in asked.items() if k in here}, here)


def record_merged_act(study: Study, a, act: str, factory: Path) -> None:
    """Record a lock or a signature whose act was a pull request merged on the protected branch. Run by the job
    that follows the merge (factory/harnesses/github), under the platform's name; the people are the platform's
    record, read from a file that job wrote, and nothing typed here names a person."""
    if not PLATFORM_ACTOR.fullmatch(str(a.by)):
        raise Refused(f"a merged {act} is recorded under the platform's name (`--by platform:github`), by the job that follows the merge; "
                      "the people who approved are read from the platform's record, not typed")
    declared = acts_declared(factory)
    rec = platform_record(a.platform_record, act, declared)
    if rec["merge_commit"] != a.record_merge:
        raise Refused("`--record-merge` names another commit than the platform's record of the merged pull request")
    branch = (declared.get(act) or {}).get("protected_branch")
    if rec["branch"] != branch:
        raise Refused(f"the pull request was merged into `{rec['branch']}`; the definition names `{branch}` as the protected branch for the {act}")
    folder = f"{act}-request"
    problems, found = merge_problems(study, {"commit": rec["merge_commit"], "branch": branch}, folder)
    if problems:
        raise Refused(f"the merge does not check out, so no {act} is recorded: " + "; ".join(problems))
    manifest = found["manifest"]
    stale = [str(r.get("login")) for r in rec["reviews"] if r.get("commit_id") and r.get("manifest_sha_at_review") not in (None, found["sha"])]
    if stale:
        raise Refused("the request changed after the approval of " + ", ".join(stale) + ": an approval covers the request as it stood "
                      "when it was given")
    differs = request_problems(study, act, factory)
    if differs:
        raise Refused(f"the files here are not the ones the merged request binds, so no {act} is recorded: " + "; ".join(differs[:8]))
    ev = study.events()
    merge = {"commit": rec["merge_commit"], "branch": branch, "ref_checked": found["ref"], "pull_request": rec["pull_request"],
             "url": rec["url"], "platform": rec["platform"], "merged_at": rec["merged_at"], "people": rec["people"],
             "manifest_sha": found["sha"], "approvals_asked": int((declared.get(act) or {}).get("approvals") or 1)}
    if act == "lock":
        got = lock_evidence(study, a)
        e = study.append(a.by, "lock.recorded", {**got["data"], "evidence": rec["url"], "route": PULL_REQUEST, "merge": merge})
        print(f"The lock: recorded from the merge {rec['merge_commit'][:12]} of pull request {rec['pull_request']} on `{branch}`, approved by "
              + ", ".join(rec["people"]["approved"]) + " (the platform's record)")
    else:
        rep = check_log(study, getattr(a, "anchor", None) or manifest.get("anchors"))
        att = attached_finding(ev)
        decision = manifest.get("decision")
        if decision not in ("signed", "declined"):
            raise Refused("the merged signature request names no decision (signed or declined)")
        if decision == "signed" and (rep["status"] != READY or not att):
            raise Refused(f"only a study whose log check says it is ready is recorded as signed (this one is: {rep['status']})")
        e = study.append(a.by, "signature.recorded", {"decision": decision, "evidence": rec["url"], "route": PULL_REQUEST, "merge": merge,
                                                      "status_at_decision": rep["status"], "comment": getattr(a, "comment", None),
                                                      "finding": {"file": att["data"]["file"], "sha": att["data"]["sha"]} if att else None})
        print(f"the steward's signature: {decision}, recorded from the merge {rec['merge_commit'][:12]} of pull request {rec['pull_request']} "
              f"on `{branch}`, approved by " + ", ".join(rec["people"]["approved"]) + " (the platform's record)")
    print(f"post this log fingerprint where the workspace cannot rewrite it: {e['seq']}:{e['hash']}")


def judge(plan: dict, receipt_path: Path, data_path: Path, exit_code) -> tuple:
    """The locked rules, applied to a receipt: (outcome per rule, why the method declined or None). A receipt
    counts only when the run exited 0 and the receipt names, by checksum, the data that was fetched."""
    receipt = None
    if exit_code == 0 and receipt_path.is_file():
        try:
            receipt = json.loads(receipt_path.read_text())
        except ValueError:
            receipt = None
    # an opening's receipt must name the data it read, by hash; a command that ignored the fetch has no result
    data_sha = sha_file(data_path)
    if not (isinstance(receipt, dict) and isinstance(receipt.get("data"), dict) and data_sha is not None
            and receipt["data"].get("sha256") == data_sha):
        receipt = None
    declined = receipt.get("refused") if isinstance(receipt, dict) else None
    if isinstance(receipt, dict) and not declined and unresolved(plan, receipt):
        receipt = None  # a receipt the rules cannot read is a failed run, never a quiet inconclusive
    outcomes = {}
    for r in plan["rules"]:
        if not isinstance(receipt, dict):
            outcomes[r["id"]] = "run-failed"
        elif declined:
            outcomes[r["id"]] = "inconclusive"  # planned: the locked method declining to estimate is a result
        elif holds(r["supported_if"], receipt):
            outcomes[r["id"]] = "supported"
        elif any(holds(g, receipt) for g in r["refuted_if"]):
            outcomes[r["id"]] = "refuted"
        else:
            outcomes[r["id"]] = "inconclusive"
    return outcomes, (str(declined)[:300] if declined else None)


def start_opening(study: Study, plan: dict, test: str, by: str, f, factory=None, practice_ok: bool = False) -> tuple:
    """Everything that decides whether an opening may start, and the start itself, done while the study log is
    held: two openings asked for at the same moment cannot both pass the allowance."""
    spec = plan["tests"][test]
    ev = study.read_held(f)
    locks = [e for e in ev if e["kind"] == "lock.recorded"]
    if not locks:
        raise Refused("no lock yet: held-out data is opened only after people lock the plan and the code")
    lock = locks[-1]
    if study.plan_sha() != lock["data"]["plan_sha"]:
        raise Refused("the analysis plan changed after the lock")
    locked_definition = lock["data"].get("definition") or {}
    here = definition_tool().tree_checksum(Path(factory or FACTORY).resolve())
    if locked_definition.get("sha256") and locked_definition["sha256"] != here["sha256"]:
        raise Refused("the factory's definition changed after the lock (the lock binds the tree's checksum "
                      f"{locked_definition['sha256'][:16]}, version {locked_definition.get('version')}; the tree here is {here['sha256'][:16]}). "
                      "What changed: " + " | ".join(definition_change_summary(locked_definition, Path(factory or FACTORY)))[:1500]
                      + ". Nothing was opened and the opening is not used up. The remedy is a new lock on the definition as it is now")
    if route_of(lock) == PULL_REQUEST:
        problems, found = merge_problems(study, lock["data"].get("merge") or {}, "lock-request")
        if not problems and found["sha"] != (lock["data"].get("merge") or {}).get("manifest_sha"):
            problems.append("the manifest in the merge commit is not the one the lock recorded")
        if not problems:
            problems += ["what the merged request binds is not what is here: " + d for d in request_problems(study, "lock", Path(factory or FACTORY))]
        if problems:
            raise Refused("the lock's merge does not check out: " + "; ".join(problems[:6]) + ". Nothing was opened and the opening "
                          "is not used up")
    elif not (Study.default_route == PRACTICE or practice_ok or practice_declared(Path(factory or FACTORY), "lock")):
        raise Refused("this study's lock was typed at a command line (a practice lock), and a real study's held-out data is opened only "
                      "after a lock that was a pull request merged on the protected branch. " + ROUTES.format(act="lock")
                      + ". To open the held-out data of a practice study, say so: `open-held-out --local-practice`. Nothing was "
                      "opened and the opening is not used up")
    code = study.code_hashes(plan)
    if code != lock["data"]["code"]:
        diff = code_difference(lock["data"]["code"], code) or ["the study tool itself (run the opening with the tool that was locked)"]
        raise Refused("the code changed after the lock (check out the locked files; a changed neighbour counts, and so does "
                      "anything new that Python could import beside them): " + "; ".join(diff[:6]))
    planted = environment_problems(study, plan, lock)
    if planted:
        raise Refused("a virtual environment folder that `uv run` would use appeared or changed after the lock, and uv runs "
                      "the interpreter inside it: " + "; ".join(planted[:6]) + ". Remove it, or put back the one the lock "
                      "recorded; nothing was opened and the opening is not used up")
    if by.casefold() in ran_tests(ev):
        raise Refused(f"{by} ran this study's tests or rehearsals; the access gate is not the assistant that built the "
                      "method. Open the held-out data as another actor")
    started, voided = openings_of(ev, test)
    used = len(started) - len(voided)
    if used >= study.allowed(plan, test):
        raise Refused(f"the openings allowed for {test} are used up ({used} of {study.allowed(plan, test)})")
    data_rel = spec.get("data") or plan["data"]["held_out"]["path"]
    data, rp = study.path(data_rel), study.path(spec["receipt"])
    if data.exists():
        raise Refused("held-out data is already in the workspace; only the access gate fetches it")
    if rp.exists():
        raise Refused(f"a {test} receipt already exists; an opening writes its own")
    for w in spec.get("writes") or []:
        if study.path(w).exists():
            raise Refused(f"`{w}` already exists; the plan says the opening writes it, so it must not be there beforehand")
    in_git, committed = study.committed_log()
    f.seek(0)
    if committed is not None and not f.read().startswith(committed):
        raise Refused("the study log is not a continuation of the committed study log (rewritten or cut short); "
                      "nothing is opened from a log that lost events")
    if in_git and lock["hash"] not in (committed or ""):
        raise Refused("the lock is not committed: it lands as a commit (the approved pull request) before the held-out data is opened")
    disagree = record_problems(study, ev)
    if disagree:
        raise Refused(disagree[0] + "; nothing is opened until the record and the log agree")
    for argv in (spec["fetch"], spec["command"]):  # refuse, without using the opening, what could never have started
        if not runnable(study, plan, argv):
            raise Refused(f"`{argv[0]}` is not runnable here; nothing was opened and the opening is not used up")
    if not_set(spec):
        raise Refused(f"the plan passes {', '.join(not_set(spec))} to this opening's commands (`passes_environment`) and it "
                      "is not set in the environment; set it and open again. Nothing was opened and the opening is not used up")
    n = len(started) + 1
    prior = earlier_openings(study, plan, spec, ev)
    before = study.listing()
    started_ev = study._append(f, by, "opening.started", {
        "test": test, "n": n, "plan_sha": study.plan_sha(), "code": code, "env": env_stamp(study, plan),
        "lock_route": route_of(lock), "definition_sha": here["sha256"],
        "lock_committed": bool(in_git), "earlier_openings_of_this_window": prior, "listing": sorted(before),
        "uv_environments": study.uv_environments() if uses_uv(plan) else {}})
    key = subject_key(plan, spec)
    line = {"study": plan["study"], "dir": study.d.name, "test": test, "key": key, "window": window_for(plan, spec),
            "at": started_ev["at"], "started": f"{started_ev['seq']}:{started_ev['hash']}"}
    if is_system_trial(plan):  # a blind test case is made at its own opening: each trial is its own subject
        line["study_kind"] = "system_trial"
        line["key"] = json.dumps({"pair": json.loads(key), "sealed at the opening": line["started"]}, sort_keys=True)
    with openings_path(study).open("a") as rec:
        rec.write(json.dumps(line, sort_keys=True) + "\n")
        rec.flush()
        os.fsync(rec.fileno())
    return n, prior, before, data_rel


def cmd_open_held_out(study: Study, a) -> None:
    if a.test not in HELD_OUT_TESTS:
        raise Refused(f"{a.test} is not a test on held-out data")
    study.check_actor(a.by)
    plan = checked_plan(study)
    spec = plan["tests"].get(a.test)
    if not spec:
        raise Refused(f"{a.test} is not in the plan")
    with study.held() as f:
        n, prior, before, data_rel = start_opening(study, plan, a.test, a.by, f, getattr(a, "factory", None),
                                                   bool(getattr(a, "local_practice", False)))
    data, rp = study.path(data_rel), study.path(spec["receipt"])
    passes = spec.get("passes_environment") or ()
    mark = len(RUNS)
    fetch_exit = run_argv(study, plan, spec["fetch"], passes)
    after = study.listing()
    fetch_wrote = sorted(k for k, v in after.items() if before.get(k) != v)  # new or changed during the fetch
    code = run_argv(study, plan, spec["command"], passes) if fetch_exit == 0 and data.is_file() else None
    outcomes, declined = judge(plan, rp, data, code)
    e = study.append(a.by, "opening.finished", {"test": a.test, "n": n, "fetch_exit": fetch_exit, "exit": code,
                                                "receipt": spec["receipt"], "receipt_sha": sha_file(rp), "data": data_rel,
                                                "data_sha": sha_file(data), "fetch_wrote": fetch_wrote,
                                                "wrote": {w: sha_file(study.path(w)) for w in spec.get("writes") or []},
                                                "env_names": given_names(passes), "ran_in": how_it_ran(mark),
                                                "outcomes": outcomes, "method_declined": declined})
    print(f"held-out data opened ({a.test}, opening {n}); outcomes {outcomes}" + (f" (the method declined: {declined})" if declined else ""))
    if prior:
        print(f"this data was already opened by {[x['dir'] for x in prior]}: this study is exploratory")
    print(f"post this log fingerprint where the workspace cannot rewrite it: {e['seq']}:{e['hash']}")


def cmd_void_unread(study: Study, a) -> None:
    """An opening whose fetch failed and left nothing behind may be made
    again, once a person voids it, on the record. The tool has to be able
    to say that nothing was read: it needs the opening's finished event,
    a fetch that failed, and no file new or changed in the study during
    the fetch. An opening that was started and never finished is used up."""
    need_person(a, "voiding an opening")
    if a.test not in HELD_OUT_TESTS:
        raise Refused(f"{a.test} is not a test on held-out data")
    plan = checked_plan(study)
    ev = study.events()
    started, voided = openings_of(ev, a.test)
    if not started:
        raise Refused(f"no {a.test} opening has been started")
    n = started[-1]["data"]["n"]
    if n in voided:
        raise Refused(f"{a.test} opening {n} is already voided")
    finished = [e for e in ev if e["kind"] == "opening.finished" and e["data"]["test"] == a.test and e["data"].get("n") == n]
    used_up = "it is used up and cannot be voided"
    if not finished:
        raise Refused(f"{a.test} opening {n} was started and never finished: the tool cannot say what it read, so {used_up}")
    c = finished[-1]["data"]
    spec = plan["tests"][a.test]
    data = study.path(spec.get("data") or plan["data"]["held_out"]["path"])
    present = [x for x in [data, study.path(spec["receipt"])] + [study.path(w) for w in spec.get("writes") or []] if x.exists()]
    if c.get("data_sha") or c.get("exit") is not None or present:
        raise Refused(f"this opening read data or ran the locked analysis; {used_up}")
    if not isinstance(c.get("fetch_exit"), int) or c["fetch_exit"] == 0:
        raise Refused(f"the fetch of this opening did not fail (exit {c.get('fetch_exit')}): what it fetched may be anywhere, so {used_up}")
    if c.get("fetch_wrote") is None or c["fetch_wrote"]:
        wrote = ", ".join(c.get("fetch_wrote") or ["unknown: the opening did not record it"])
        raise Refused(f"files appeared or changed in the study during the fetch ({wrote}): the tool cannot say nothing was read, so {used_up}")
    study.append(a.by, "opening.voided", {"test": a.test, "n": n, "reason": a.reason, "evidence": a.evidence})
    print(f"{a.test}: opening {n} voided ({a.reason})")


def standing_openings(ev: list) -> list:
    """Openings that were started and not voided, finished or not: each one used the data up."""
    voids = {(e["data"]["test"], e["data"]["n"]) for e in ev if e["kind"] == "opening.voided"}
    return [e for e in ev if e["kind"] == "opening.started" and (e["data"]["test"], e["data"]["n"]) not in voids]


def last_live_opening(ev: list):
    voids = {(e["data"]["test"], e["data"]["n"]) for e in ev if e["kind"] == "opening.voided"}
    live = [e for e in ev if e["kind"] == "opening.finished" and (e["data"]["test"], e["data"].get("n")) not in voids]
    return live[-1] if live else None


def cmd_review(study: Study, a) -> None:
    ev = study.events()
    if a.by.casefold() in involved(ev):
        raise Refused("this actor ran part of the study, wrote its finding or decided on it; a review assistant that did "
                      "none of it reviews it (names are compared without regard to case)")
    if a.verdict not in ("approve", "block"):
        raise Refused("verdict is approve or block")
    if not any(e["kind"] == "opening.finished" for e in ev):
        raise Refused("the held-out data has not been opened yet; there is nothing to review")
    f = Path(a.file).resolve()
    if not f.is_file():
        raise Refused("the verdict file does not exist")
    (study.d / "verdicts").mkdir(exist_ok=True)
    dest = study.d / "verdicts" / f"{len(ev):03d}-{f.name}"  # never overwrites an earlier verdict
    shutil.copyfile(f, dest)
    study.append(a.by, "review.verdict", {"verdict": a.verdict, "file": f"verdicts/{dest.name}", "sha": sha_file(dest)})
    live = last_live_opening(ev)
    attached = any(e["kind"] == "finding.attached" and live and e["seq"] > live["seq"] for e in ev)
    print(f"review: {a.verdict}" + ("" if attached else " (recorded before any finding was attached: the study is ready for the "
                                                       "steward only after a verdict that follows the finding)"))


def cmd_note(study: Study, a) -> None:
    kinds = ("missing", "wrong", "stale", "contradiction", "method", "dead-end")
    if a.kind not in kinds:
        raise Refused(f"kind is one of {kinds}")
    n = sum(1 for e in study.events() if e["kind"] == "note.raised") + 1  # the study log numbers notes, not the folder
    ev = Path(a.evidence).resolve() if a.evidence else None
    shown = str(ev.relative_to(study.d)) if ev and ev.is_relative_to(study.d) else str(ev)
    note = {"id": f"NOTE-{n:03d}", "at": now(), "by": a.by, "kind": a.kind, "about": a.about,
            "text": a.text, "evidence": {"path": shown, "sha256": sha_file(ev)} if ev else None,
            "status": "open"}
    (study.d / "notes").mkdir(exist_ok=True)
    fp = study.d / "notes" / f"{note['id']}.json"
    if fp.exists():
        raise Refused(f"{fp.name} already exists and is not in the study log")
    fp.write_text(json.dumps(note, indent=1))
    try:  # the log keeps the note's words too, so a note file that is lost loses nothing
        study.append(a.by, "note.raised", {"id": note["id"], "kind": a.kind, "about": a.about, "sha": sha_file(fp),
                                           "text": a.text, "evidence": note["evidence"]})
    except Refused:
        fp.unlink(missing_ok=True)
        raise
    print(f"note {note['id']} recorded ({a.kind}: {a.about})")


def cmd_curation_list(study: Study, a) -> None:
    route = {"missing": "draft the concept at status draft and open a concept issue (the ingest loop); a validity "
                        "domain is drafted by the seeder from sources the steward supplies",
             "wrong": "amend the named concept by pull request; a signed concept stays stable and owes a signature "
                      "until the steward re-signs (merge then sign)",
             "stale": "re-verify the named concept against its source and move its stale_after",
             "contradiction": "open a steward review; never resolve by editing either side",
             "method": "amend the recipe or the computation by pull request with the known-answer test evidence "
                       "attached; a signed recipe stays stable and owes a signature",
             "dead-end": "draft a dead-end concept: the attempt, the failure, and what would reopen it"}
    by_subject = {}
    resolved = {e["data"]["id"] for e in study.events() if e["kind"] == "note.resolved"}
    for e in study.events():  # the study log says which notes exist; a file that vanished is still listed
        if e["kind"] != "note.raised" or e["data"]["id"] in resolved:
            continue
        fp = study.d / "notes" / f"{e['data']['id']}.json"
        try:
            f = json.loads(fp.read_text())
        except (OSError, ValueError):
            kept = e["data"].get("text")
            f = {"id": e["data"]["id"], "at": e["at"], "by": e["actor"], "kind": e["data"]["kind"], "about": e["data"]["about"],
                 "status": "open", "evidence": e["data"].get("evidence"),
                 "text": kept if kept is not None else "the note file is missing or unreadable, and this study log was "
                                                        "written before the tool kept a note's words in the log",
                 "restored": "the note file is missing or unreadable; these words are the study log's copy"}
        if f.get("status", "open") == "open":
            by_subject.setdefault(str(f.get("about")), []).append({**f, "route": route.get(f.get("kind"), "steward review")})
    out = {"study": study.d.name, "generated": now(), "open_notes": sum(len(v) for v in by_subject.values()),
           "by_subject": by_subject,
           "contract": "the curating assistant drafts at status draft with its own generated event; "
                       "it never merges and never signs"}
    (study.d / "curation-list.json").write_text(json.dumps(out, indent=1))
    print(f"curation list: {out['open_notes']} open note(s) across {len(by_subject)} subject(s)")


def cmd_attach(study: Study, a) -> None:
    """The drafted finding (or negative result) joins the record, by hash."""
    ev = study.events()
    if not any(e["kind"] == "opening.finished" for e in ev):
        raise Refused("there is no finished opening to write a finding from")
    if any(e["kind"] == "signature.recorded" for e in ev):
        raise Refused("the steward has already decided on this study; nothing is attached after the signature. The "
                      "finding the steward decided on is the one in the signature event; a different finding is a new study")
    f = Path(a.file).resolve()
    if not f.is_file():
        raise Refused("the finding file does not exist")
    if route_of(study.last("lock.recorded")) == PRACTICE and PRACTICE_WORDS not in " ".join(f.read_text(errors="replace").split()):
        raise Refused("this study's lock was typed at a command line (a practice lock), and its finding has to say so. Put this "
                      f"sentence in the finding, word for word, and attach again: {PRACTICE_WORDS}")
    (study.d / "finding").mkdir(exist_ok=True)
    dest = study.d / "finding" / f"{len(ev):03d}-{f.name}"
    shutil.copyfile(f, dest)
    study.append(a.by, "finding.attached", {"file": f"finding/{dest.name}", "sha": sha_file(dest)})
    live = last_live_opening(ev)
    earlier = any(e["kind"] == "review.verdict" and live and e["seq"] > live["seq"] for e in ev)
    print(f"finding attached: finding/{dest.name}" + (" (the reviews recorded before it do not cover it: the review "
                                                        "assistant reads this finding and records a verdict again)" if earlier else ""))


def attached_finding(ev: list):
    """The finding in force: the last one attached since the last opening that stands."""
    live = last_live_opening(ev)
    found = [e for e in ev if e["kind"] == "finding.attached" and live and e["seq"] > live["seq"]]
    return found[-1] if found else None


def cmd_signature(study: Study, a) -> None:
    """The steward's signature, in the study log. The signature itself is
    the steward's verified event on the finding, made with the
    organization's signing tool; this records that it happened, or that the
    steward declined, on which finding (its path and checksum), and where."""
    factory = Path(getattr(a, "factory", None) or FACTORY)
    if getattr(a, "record_merge", None):
        record_merged_act(study, a, "signature", factory)
        return
    if a.decision not in ("signed", "declined"):
        raise Refused("the decision is signed or declined")
    ev = study.events()
    if not standing_openings(ev):
        raise Refused("the steward decides after the held-out data has been opened; to stop a study before that, close it "
                      "with an early exit such as `close --outcome withdrawn --cite ...`")
    rep = check_log(study, a.anchor)
    att = attached_finding(ev)
    if getattr(a, "prepare", False):
        study.check_actor(a.by)
        if a.decision == "signed" and (rep["status"] != READY or not att):
            raise Refused(f"a request to sign is prepared only for a study whose log check says it is ready (this one is: {rep['status']})")
        plan = checked_plan(study)
        manifest = manifest_now(study, plan, ev, factory, "signature")
        manifest.update(decision=a.decision, log_head={"seq": ev[-1]["seq"], "hash": ev[-1]["hash"]}, prepared={"by": a.by, "at": now()},
                        status_at_request=rep["status"], anchors=list(a.anchor or []),
                        protected_branch=(acts_declared(factory).get("signature") or {}).get("protected_branch"))
        msha, ssha = write_request(study, "signature-request", signature_summary(study, plan, ev, rep, att, a.decision), manifest)
        study.append(a.by, "signature.requested", {"manifest_sha": msha, "summary_sha": ssha, "decision": a.decision})
        print(f"signature request written: {study.d.name}/signature-request/EVIDENCE.md and manifest.json (manifest sha256 {msha[:16]}). "
              "Nothing is signed. The steward's approval and merge of the pull request that carries it, on the protected branch, is "
              "the signature")
        return
    need_person(a, "the steward's signature")
    refuse_typed_act(a, "signature", factory)
    if a.decision == "signed":
        if rep["status"] != READY:
            raise Refused(f"only a study whose log check says it is ready is recorded as signed (this one is: {rep['status']})")
        if not att:
            raise Refused("no finding is attached")
        if sha_file(study.d / att["data"]["file"]) != att["data"]["sha"]:
            raise Refused(f"the finding on disk ({att['data']['file']}) is not the one that was attached; the signature names "
                          "a finding by its checksum, so restore the attached text")
    study.append(a.by, "signature.recorded", {"decision": a.decision, "evidence": a.evidence, "route": PRACTICE,
                                              "status_at_decision": rep["status"], "comment": a.comment,
                                              "finding": {"file": att["data"]["file"], "sha": att["data"]["sha"]} if att else None})
    print(f"the steward's signature: {a.decision} (practice: typed at a command line)"
          + (f" (finding {att['data']['file']}, sha256 {att['data']['sha'][:12]})" if att else ""))


def cmd_request_signature(study: Study, a) -> None:
    """Write the signature request into the study: the finding, the review, the outcome under the locked rules and
    what merging the pull request would sign. An assistant may do this; it records nothing as signed."""
    a.prepare = True
    cmd_signature(study, a)


def signature_summary(study: Study, plan: dict, ev: list, rep: dict, att, decision: str) -> list:
    """The evidence summary of a signature request, in plain words: the finding, the verdict of the review, the
    outcome the locked rules gave, and what merging the pull request would sign."""
    lock = [e for e in ev if e["kind"] == "lock.recorded"][-1]
    out = [f"# Signature request: {plan['study']}", "",
           f"This is a request for the steward's decision on a finding: **{decision}**. Nothing is signed by this file. The signature "
           "is the steward's act: approving and merging the pull request that carries this folder, on the protected branch. The "
           "checksums are in `manifest.json` beside this file, and the required check on the pull request says whether they still "
           "match the files.", "",
           "## The question", "", str(plan["question"]).strip(), "",
           "## What the opening showed", "", f"The log check says: {rep['status']}.", ""]
    out += [f"- {t}: " + ", ".join(f"{rule} {o}" for rule, o in sorted(o_.items())) for t, o_ in sorted(rep["outcomes"].items())] or ["- no opening has a result"]
    out += ["", "## The finding that would be signed", ""]
    if att:
        try:
            body = (study.d / att["data"]["file"]).read_text()
        except OSError:
            body = "(the attached finding could not be read)"
        out += [f"`{att['data']['file']}`, sha256 {att['data']['sha']}:", "", "```", *body.rstrip().splitlines(), "```"]
    else:
        out += ["No finding is attached."]
    out += ["", "## The review", ""]
    out += [f"- {who}: {verdict}" for who, verdict in sorted(rep["reviews"].items())] or ["- no review assistant that did none of the study has recorded a verdict on this finding"]
    for e in ev:
        if e["kind"] == "review.verdict" and att and e["seq"] > att["seq"]:
            with contextlib.suppress(OSError):
                out += ["", f"The verdict file of {e['actor']} (`{e['data']['file']}`):", "", "```", *(study.d / e["data"]["file"]).read_text().rstrip().splitlines(), "```"]
    out += ["", "## The lock this rests on", "",
            (f"A pull request merged on `{lock['data']['merge']['branch']}` (merge {lock['data']['merge']['commit'][:12]}), approved by "
             + ", ".join(lock["data"]["merge"]["people"]["approved"]) + " by the platform's record." if route_of(lock) == PULL_REQUEST
             else "A PRACTICE LOCK, typed at a command line. This study cannot close as a signed finding."), "",
            "## Problems and remarks from the log check", ""]
    out += [f"- problem: {p}" for p in rep["problems"]] + [f"- {r}" for r in rep["purity"] + rep["remarks"]] or ["None."]
    return out


def cmd_resolve(study: Study, a) -> None:
    """A note is never deleted: it is accepted, linked to where it went, or declined with a reason."""
    if a.disposition not in ("accepted", "linked", "declined"):
        raise Refused("the disposition is accepted, linked or declined")
    if not any(e["kind"] == "note.raised" and e["data"]["id"] == a.note for e in study.events()):
        raise Refused(f"{a.note} was never raised in this study")
    if a.disposition == "declined" and not a.comment:
        raise Refused("a declined note needs its reason (--comment)")
    if a.disposition != "declined" and not a.ref:
        raise Refused("an accepted or linked note needs where it went (--ref: a pull request, an issue, a concept path)")
    study.append(a.by, "note.resolved", {"id": a.note, "disposition": a.disposition, "ref": a.ref, "comment": a.comment})
    print(f"{a.note}: {a.disposition}")


EARLY_EXITS = ("answered-by-existing-knowledge", "outside-a-signed-domain", "dead-end", "withdrawn")
LATE_EXITS = {"finding-signed": "signed", "negative-result-signed": "signed", "system-trial-accepted": "signed",
              "not-signed": "declined", "system-trial-declined": "declined", "practice-ended": None}
SIGNED_FINDINGS = ("finding-signed", "negative-result-signed")  # never the close of a study whose lock or signature was typed
TRIAL_EXITS = ("system-trial-accepted", "system-trial-declined")


def cmd_close(study: Study, a) -> None:
    ev = study.events()
    if a.outcome in EARLY_EXITS:
        if any(e["kind"] == "opening.started" for e in ev):
            raise Refused("the held-out data has been opened; this study ends in a result, not an early exit")
        if not a.cite:
            raise Refused("an early exit cites what resolved the question (--cite: the finding, domain or dead-end)")
    elif a.outcome in LATE_EXITS:
        sig = study.last("signature.recorded")
        if not sig or (LATE_EXITS[a.outcome] and sig["data"]["decision"] != LATE_EXITS[a.outcome]):
            raise Refused(f"`{a.outcome}` needs the steward's signature recorded" + (f" as {LATE_EXITS[a.outcome]}" if LATE_EXITS[a.outcome] else ""))
        try:
            trial = is_system_trial(study.plan())
        except Refused:
            trial = None
        if trial is not None and trial != (a.outcome in TRIAL_EXITS):
            raise Refused(f"`{a.outcome}` does not fit this study: a system trial closes as {' or '.join(TRIAL_EXITS)}, and "
                          "only a system trial does")
        if a.outcome in SIGNED_FINDINGS:  # a signed finding rests on two acts by people that were merged pull requests
            lock = study.last("lock.recorded")
            typed = [what for what, e in (("lock", lock), ("signature", sig)) if route_of(e) != PULL_REQUEST]
            if typed:
                raise Refused(f"`{a.outcome}` is refused: this study's {' and '.join(typed)} was typed at a command line (practice), "
                              "and a study closes as a signed finding only when its lock and its signature were pull requests merged "
                              "on the protected branch. A practice study closes as `practice-ended`")
            for what, e, folder in (("lock", lock, "lock-request"), ("signature", sig, "signature-request")):
                problems, _found = merge_problems(study, e["data"].get("merge") or {}, folder)
                if problems:
                    raise Refused(f"`{a.outcome}` is refused: the {what}'s merge does not check out: " + "; ".join(problems[:4]))
        if a.outcome == "practice-ended":
            if not any(route_of(e) == PRACTICE for e in ev if e["kind"] in ACTS_BY_PEOPLE):
                raise Refused("`practice-ended` closes a practice study (one whose lock or signature was typed at a command line); "
                              "this one's were merged pull requests")
        # a signed outcome, in practice too, is recorded only on a study that still checks out
        if LATE_EXITS[a.outcome] == "signed" or (a.outcome == "practice-ended" and sig["data"]["decision"] == "signed"):
            rep = check_log(study, getattr(a, "anchor", None))
            if rep["status"] != SIGNED:
                raise Refused(f"`{a.outcome}` needs a study whose log check still says it is signed; this one says: "
                              f"{rep['status']}" + ("".join("; " + x for x in rep["problems"][:3])))
        if a.outcome == "system-trial-accepted":
            verdict = study.last("trial.verdict")
            live = last_live_opening(ev)
            if not verdict:
                raise Refused("`system-trial-accepted` needs the sealed answer revealed and its verdict in the study log: run "
                              "`system_trial.py verdict --study ... --by ...` after the steward has decided")
            if verdict["data"].get("verdict") != "right" or (live and verdict["data"].get("data_sha") != live["data"].get("data_sha")):
                raise Refused(f"the system trial's verdict is `{verdict['data'].get('verdict')}`, not `right`: a trial is accepted "
                              "only when the factory was right. Record the steward's decision as declined and close as "
                              "system-trial-declined; a new trial is a new study")
    else:
        raise Refused(f"the outcome is one of {EARLY_EXITS + tuple(LATE_EXITS)}")
    study.append(a.by, "study.closed", {"outcome": a.outcome, "cite": a.cite, "comment": a.comment})
    print(f"closed: {a.outcome}")


def stage_checks(study: Study) -> tuple:
    """What is true of this study, by name, and for what is not yet true,
    why. The procedure's stages say which of these finish them; nothing
    else decides where a study is."""
    ev = study.events()
    why = {}
    try:
        plan = checked_plan(study)
    except Refused as r:
        plan = None
        why["plan-complete"] = str(r)
    opened = bool(standing_openings(ev))
    psha, code = (study.plan_sha(), study.code_hashes(plan)) if plan else (None, None)

    def passed(name: str, kind: str, **match) -> bool:
        e = study.last(kind, **match)
        if not e:
            reason = "not run yet"
        elif e["data"]["exit"] != 0:
            reason = "its last run did not pass"
        elif e["data"]["plan_sha"] != psha:
            reason = "it passed on a different analysis plan than the one on disk now: run it again"
        elif not same_code(e["data"]["code"], code, tool_too=not opened):
            diff = code_difference(e["data"]["code"], code) or ["the study tool itself"]
            reason = ("it passed on code that is not what is checked out now (" + "; ".join(diff[:4])
                      + ("; and more" if len(diff) > 4 else "") + "): run it again")
        else:
            return True
        why.setdefault(name, []).append(f"{TEST_NAMES.get(match.get('test'), match.get('test') or 'rehearsal ' + str(match.get('id')))}: {reason}")
        return False

    lock = study.last("lock.recorded")
    live_last = last_live_opening(ev)
    voids = {(e["data"]["test"], e["data"]["n"]) for e in ev if e["kind"] == "opening.voided"}
    live = [e for e in ev if e["kind"] == "opening.finished" and (e["data"]["test"], e["data"].get("n")) not in voids]
    doers = involved(ev)
    raised = {e["data"]["id"] for e in ev if e["kind"] == "note.raised"}
    resolved = {e["data"]["id"] for e in ev if e["kind"] == "note.resolved"}
    att = attached_finding(ev)
    last_opening = standing_openings(ev)[-1]["seq"] if opened else None
    tests_pass = bool(plan) and all([passed("tests-pass", "test.run", test=t) for t in FREE_TESTS])
    rehearsals_pass = bool(plan) and all([passed("rehearsals-pass", "rehearsal.run", id=r["id"]) for r in plan.get("rehearsals") or []])
    truth = {
        "started": any(e["kind"] == "study.started" for e in ev),
        "plan-complete": plan is not None,
        "tests-pass": tests_pass,
        "rehearsals-pass": rehearsals_pass,
        "locked": bool(plan and lock and lock["data"]["plan_sha"] == psha
                       and same_code(lock["data"]["code"], code, tool_too=not opened)),
        "openings-complete": bool(plan and live) and all(any(c["data"]["test"] == t for c in live)
                                                         for t in HELD_OUT_TESTS if t in plan["tests"]),
        "finding-attached": att is not None,
        # a verdict counts only when it follows the finding it is about
        "reviewed": att is not None and any(e["kind"] == "review.verdict" and e["seq"] > att["seq"]
                                            and e["actor"].casefold() not in doers for e in ev),
        "steward-decided": last_opening is not None and any(e["kind"] == "signature.recorded" and e["seq"] > last_opening for e in ev),
        "notes-resolved": raised <= resolved,
        "closed": any(e["kind"] == "study.closed" for e in ev),
    }
    if live_last is not None and att is not None and not truth["reviewed"]:
        why["reviewed"] = "no review assistant has recorded a verdict since the finding was attached"
    return truth, why


def stage_of(study: Study, factory: Path) -> dict:
    stamp = definition_stamp(Path(factory), study.last("lock.recorded"))
    stages = definition_of(Path(factory))["procedure"].get("stages")
    if not isinstance(stages, list) or not stages:
        raise Refused("the definition's factory.yaml has no procedure.stages")
    truth, why = stage_checks(study)
    closed = study.last("study.closed")
    done, here = [], None
    for st in stages:
        names = st.get("done_when") or []
        unknown = [n for n in names if n not in truth]
        if unknown or not names:
            raise Refused(f"stage {st.get('id')}: done_when names nothing this study tool can check ({unknown or 'empty'})")
        if all(truth[n] for n in names) and here is None:
            done.append(st["id"])
        elif here is None:
            needs = [n for n in names if not truth[n]]
            here = {"stage": st["id"], "who": st.get("done_by") or "people", "does": st.get("does"), "still_needs": needs}
            if any(n in why for n in needs):
                here["why"] = {n: why[n] for n in needs if n in why}
    if closed:
        here = {"stage": "closed", "outcome": closed["data"]["outcome"], "cite": closed["data"].get("cite")}
    return {"study": study.d.name, "definition": stamp, "models": models_report(study.events(), stamp), "acts": acts_report(study),
            "done": done, **(here or {"stage": "complete"}),
            "open_notes": sorted({e["data"]["id"] for e in study.events() if e["kind"] == "note.raised"}
                                 - {e["data"]["id"] for e in study.events() if e["kind"] == "note.resolved"})}


def acts_report(study: Study) -> dict:
    """How this study's two acts by people were made, for `status`, the scorecard and anyone reading either: by a
    pull request merged on the protected branch, with the people the platform recorded, or typed at a command
    line, which is practice."""
    out = {}
    for name, kind in (("lock", "lock.recorded"), ("signature", "signature.recorded")):
        e = study.last(kind)
        if not e:
            asked = study.last(f"{name}.requested")
            out[name] = "requested, not made: the request waits for a pull request to be approved and merged" if asked else "not made"
        elif route_of(e) == PULL_REQUEST:
            m = e["data"]["merge"]
            out[name] = {"route": PULL_REQUEST, "merge_commit": m["commit"], "branch": m["branch"], "pull_request": m.get("url") or m.get("pull_request"),
                         "approved_by": m["people"]["approved"], "author": m["people"]["author"],
                         "note": "the people are the platform's record, copied by the recording job; git alone shows the merge, not who approved"}
        else:
            out[name] = {"route": PRACTICE, "typed_by": e["actor"],
                         "note": "PRACTICE: typed at a command line, with no approval the platform recorded. This study cannot close as a signed finding"}
    if any(isinstance(v, dict) and v["route"] == PRACTICE for v in out.values()):
        out["practice"] = True
    return out


def cmd_status(study: Study, a) -> None:
    print(json.dumps(stage_of(study, Path(a.factory)), indent=1))


def cmd_fingerprint(study: Study, a) -> None:
    ev = study.events()
    if not ev:
        raise Refused("the study log is empty")
    print(f"{ev[-1]['seq']}:{ev[-1]['hash']}")


def record_sha(rec: dict) -> str:
    return hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()


def change_log_problems(study: Study, ev: list, change_log: Path) -> list:
    """Each `change.recorded` event names its record in the change log by checksum; check them against the file."""
    try:
        records = [json.loads(ln) for ln in Path(change_log).read_text().splitlines() if ln.strip()]
    except (OSError, ValueError):
        return [f"the change log {change_log} is missing or has a line that is not JSON"]
    have = {record_sha(r) for r in records if isinstance(r, dict)}
    p = []
    for e in ev:
        if e["kind"] == "change.recorded" and e["data"].get("record_sha") not in have:
            p.append(f"the change log does not hold the record that event {e['seq']} recorded (the record was changed or removed)")
    mine = {e["seq"]: e for e in ev if e["kind"] == "change.recorded"}
    for r in records:
        ctx = r.get("context") if isinstance(r, dict) and isinstance(r.get("context"), dict) else {}
        if ctx.get("evidence_study") == study.d.name:
            e = mine.get(r.get("log_event"))
            if not e or e["data"].get("record_sha") != record_sha(r):
                p.append(f"the change log holds a record that says this study recorded it (event {r.get('log_event')}), "
                         "and this study log has no such event")
    return p


def check_log(study: Study, posted: list | None = None, change_log=None) -> dict:
    """The log check: the chain, the files the log names, the locked plan
    and code, the record of what has been opened, the outcome the locked
    rules give on the receipt, and the fingerprints posted outside the
    workspace."""
    problems, purity, remarks = [], [], []
    try:
        ev = study.events()
        problems += study._chain(ev)
        unnamed = [e["seq"] for e in ev if str(e["actor"]).startswith("agent:") and not e.get("model")]
        if unnamed:
            problems.append(f"{len(unnamed)} event(s) written by an agent name no model (the first is event {unnamed[0]}): every "
                            "event an agent writes records the model that wrote it")
    except Refused as r:
        ev, problems = [], [str(r)]
    locks = [e for e in ev if e["kind"] == "lock.recorded"]
    started = [e for e in ev if e["kind"] == "opening.started"]
    finished = [e for e in ev if e["kind"] == "opening.finished"]
    voids = {(e["data"]["test"], e["data"]["n"]) for e in ev if e["kind"] == "opening.voided"}
    live = [c for c in finished if (c["data"]["test"], c["data"].get("n")) not in voids]
    standing = [op for op in started if (op["data"]["test"], op["data"]["n"]) not in voids]
    unfinished = [op for op in standing if not any(c["data"]["test"] == op["data"]["test"] and c["data"].get("n") == op["data"]["n"]
                                                   for c in finished)]
    closed = next((e for e in reversed(ev) if e["kind"] == "study.closed"), None)
    plan = None
    if study.plan_path.is_file():
        try:
            plan = study.plan()
            bad = check_plan(plan, study)
            if bad:
                problems.append("the analysis plan on disk is not well formed: " + bad[0]
                                + (f" (and {len(bad) - 1} more; run check-plan)" if len(bad) > 1 else ""))
                plan = None
        except Refused as r:
            plan = None
            problems.append(str(r))
    elif locks:
        # once people have locked, a plan that is missing or unreadable is a problem: nothing is skipped for want of it
        problems.append("the study log holds a lock and the analysis plan (analysis-plan.yaml) is missing: restore the locked "
                        "plan, because nothing can be checked against the lock without it")
    for mark in posted or []:
        seq, _, h = str(mark).partition(":")
        if not seq.isdigit() or int(seq) >= len(ev) or ev[int(seq)]["hash"] != h:
            problems.append(f"the study log does not contain the posted fingerprint {str(mark)[:20]} (rewritten or cut short)")
    covered = {int(str(x).partition(":")[0]) for x in posted or [] if str(x).partition(":")[0].isdigit()}
    in_git, committed = study.committed_log()
    if committed is not None and not (study.log.read_text() if study.log.exists() else "").startswith(committed):
        problems.append("the study log is not a continuation of the committed study log (rewritten or cut short)")
    if not in_git:
        remarks.append("not in a git work tree: only posted fingerprints guard against a rewritten study log here")
    for e in ev:
        if e["kind"] in ("lock.recorded", "signature.recorded", "opening.voided"):
            if not is_act_by_people(e):
                problems.append(f"{e['kind']} at event {e['seq']} was not recorded by a person with evidence")
            elif e["data"].get("route") == PULL_REQUEST:
                bad, found = merge_problems(study, e["data"]["merge"], "lock-request" if e["kind"] == "lock.recorded" else "signature-request")
                if not bad and found["sha"] != e["data"]["merge"].get("manifest_sha"):
                    bad = ["the manifest in the merge commit is not the one the log recorded"]
                problems += [f"{e['kind']} at event {e['seq']}: {b}" for b in bad]
            elif e["kind"] != "opening.voided":
                remarks.append(f"{e['kind']} at event {e['seq']} was typed at a command line by {e['actor']} (practice): this study "
                               "cannot close as a signed finding")
            if e["kind"] == "opening.voided":
                remarks.append(f"{e['data']['test']} opening {e['data']['n']} was voided by {e['actor']}: {e['data'].get('reason')}")
    start = next((e for e in ev if e["kind"] == "study.started"), None)
    if not locks:
        remarks.append("not locked: no lock yet")
        req = request_of(ev)
        if req and sha_file(study.d / req["file"]) != req["sha"]:
            remarks.append(f"the request ({req['file']}) changed since the study started; the lock binds whatever it says then")
    else:
        lock = locks[-1]
        if study.plan_path.is_file() and study.plan_sha() != lock["data"]["plan_sha"]:
            problems.append("the analysis plan on disk is not the locked plan")
        if plan:
            here = study.code_hashes(plan)
            diff = code_difference(lock["data"]["code"], here)
            tool_then, tool_now = lock["data"]["code"].get("(the study tool)"), here.get("(the study tool)")
            if diff:
                problems.append("the code on disk is not the locked code: " + "; ".join(diff[:6]) + ("; and more" if len(diff) > 6 else ""))
            elif tool_then != tool_now and not standing:
                problems.append(f"the code on disk is not the locked code: the study tool itself changed since the lock (locked "
                                f"sha256 {tool_then}, on disk sha256 {tool_now}); open with the locked tool, or lock again")
            elif tool_then != tool_now:
                remarks.append(f"the study tool on disk (sha256 {tool_now}) is not the one the lock recorded (sha256 {tool_then}); "
                               "the opening ran with the locked tool, and this check was made by the one on disk")
        req = lock["data"].get("request")
        if req and sha_file(study.d / req["file"]) != req["sha"]:
            problems.append(f"the request ({req['file']}) changed after the lock, or is missing: the lock binds the request with the plan")
        first_lock = locks[0]["seq"]
        for op in started:
            if op["seq"] < first_lock:
                problems.append("an opening started before any lock")
            l_before = [g for g in locks if g["seq"] < op["seq"]]
            if l_before and (op["data"]["plan_sha"] != l_before[-1]["data"]["plan_sha"]
                             or op["data"]["code"] != l_before[-1]["data"]["code"]):
                problems.append("an opening ran on a plan or code that was not the locked pair")
        if any(g["data"].get("after_opening") for g in locks) or (started and locks[-1]["seq"] > started[0]["seq"]):
            purity.append("the plan was locked again after an opening")
    if start and plan and " ".join(str(start["data"].get("question")).split()) != " ".join(str(plan["question"]).split()):
        remarks.append("the question the study was started with and the question in the plan are worded differently; "
                       "the plan's is the one that is locked")
    no_commit = 0
    for op in started:
        if op["data"].get("earlier_openings_of_this_window"):
            purity.append("this pair and window were already opened by "
                          + ", ".join(sorted({str(x.get("dir")) for x in op["data"]["earlier_openings_of_this_window"]})))
        if not op["data"].get("lock_committed"):
            l_before = [g for g in locks if g["seq"] < op["seq"]]
            if l_before and l_before[-1]["actor"] == HARNESS_PERSON:
                remarks.append(f"the lock was not in a commit when the {op['data']['test']} opening started; it was recorded by the "
                               "blind test harness, which works in throwaway directories (the one named exception)")
            else:
                no_commit += 1
                remarks.append(f"the lock was not in a commit when the {op['data']['test']} opening started (event {op['seq']}): "
                               "outside a git work tree nothing but a posted fingerprint shows that the lock came first")
    problems += record_problems(study, ev)
    for e in ev:
        if e["kind"] == "finding.attached" and sha_file(study.d / e["data"]["file"]) != e["data"]["sha"]:
            problems.append(f"the attached finding {e['data']['file']} changed after it was attached, or is missing")
    for t in HELD_OUT_TESTS:
        n = sum(1 for op in standing if op["data"]["test"] == t)
        if n > study.allowed(plan, t):
            problems.append(f"{t}: {n} openings against {study.allowed(plan, t)} allowed")
    pending = [t for t in HELD_OUT_TESTS if plan and t in plan["tests"] and not any(op["data"]["test"] == t for op in standing)]
    last_by_test = {c["data"]["test"]: c for c in live}
    locked_plan = bool(plan and locks and study.plan_sha() == locks[-1]["data"]["plan_sha"])
    for t, c in last_by_test.items():
        rel = c["data"].get("receipt") or (((plan or {}).get("tests") or {}).get(t) or {}).get("receipt")
        rpath = study.path(rel) if rel else None
        same_receipt = rpath is not None and sha_file(rpath) == c["data"]["receipt_sha"]
        if not same_receipt:
            problems.append(f"the {t} receipt on disk is not the one the opening wrote")
        dpath = study.path(c["data"]["data"])
        same_data = not c["data"].get("data_sha") or sha_file(dpath) == c["data"]["data_sha"]
        if not same_data:
            problems.append(f"the {t} data on disk is not what the opening read")
        for rel, was in (c["data"].get("wrote") or {}).items():  # the other files the plan said the opening writes
            if sha_file(study.path(rel)) != was:
                problems.append(f"`{rel}`, which the {t} opening wrote, changed after the opening or is missing")
        if locked_plan and same_receipt and same_data:
            again, _ = judge(plan, rpath, dpath, c["data"].get("exit"))
            if again != c["data"]["outcomes"]:  # the log is not taken at its word: the locked rules are applied again
                problems.append(f"the {t} receipt on disk gives {again} under the locked rules, and the study log says "
                                f"{c['data']['outcomes']}")
    if plan and early_data(study, plan, ev):
        problems.append("held-out data is present with no opening in the study log")
    for op in unfinished:
        remarks.append(f"the {op['data']['test']} opening (event {op['seq']}) was started and not finished: it is used up, "
                       "and it cannot be voided because nothing says what it read")
    for e in ev:
        if e["kind"] == "note.raised":
            fp = study.d / "notes" / f"{e['data']['id']}.json"
            if sha_file(fp) != e["data"]["sha"]:
                remarks.append(f"{e['data']['id']} was edited or removed after it was raised"
                               + (" (the study log keeps its words)" if e["data"].get("text") is not None else ""))
        if e["kind"] == "review.verdict" and sha_file(study.d / e["data"]["file"]) != e["data"]["sha"]:
            problems.append("a review verdict file was edited after it was recorded")
    if change_log:
        problems += change_log_problems(study, ev, Path(change_log))
    elif any(e["kind"] == "change.recorded" for e in ev):
        remarks.append("this study recorded changes to the procedure; pass --change-log to check them against the change log")
    outcomes = {c["data"]["test"]: c["data"]["outcomes"] for c in live}
    failed = [t for t, o in outcomes.items() if "run-failed" in o.values()]
    failed += [op["data"]["test"] for op in unfinished if op["data"]["test"] not in failed]
    doers = involved(ev)
    att = attached_finding(ev)
    verdicts = {}  # each independent review assistant's latest word on the finding in force
    if att:
        for e in ev:
            if e["kind"] == "review.verdict" and e["seq"] > att["seq"] and e["actor"].casefold() not in doers:
                verdicts[e["actor"]] = e["data"]["verdict"]
    sig = None
    if standing:
        sig = next((e for e in reversed(ev) if e["kind"] == "signature.recorded" and e["seq"] > standing[-1]["seq"]), None)
    ending = f"; closed as {closed['data']['outcome']}" if closed else ""
    if problems:
        status = INVALID
    elif not locks or not standing:
        status = f"closed before any opening ({closed['data']['outcome']})" if closed else "in progress"
    elif purity:
        status = EXPLORATORY
    elif sig and sig["data"]["decision"] == "signed":
        status = SIGNED + ending
    elif sig:
        status = DECLINED + ending
    elif failed:
        status = f"confirmatory study, held-out data opened without a result ({', '.join(failed)})"
    elif pending:
        status = f"confirmatory study, a planned opening remains ({', '.join(pending)})"
    elif not att:
        status = NO_FINDING
    elif not verdicts:
        status = NO_REVIEW
    elif "block" in verdicts.values():
        status = "confirmatory study, blocked by review"
    elif not ({locks[-1]["seq"]} | {c["seq"] for c in live}) <= covered:
        status = "confirmatory study, log fingerprints missing (pass --anchor for the lock and for each finished opening)"
    else:
        status = READY
    return {"study": study.d.name, "status": status, "problems": problems, "purity": purity,
            "remarks": remarks, "outcomes": outcomes, "reviews": verdicts,
            "finding": att["data"]["file"] if att else None,
            "signature": sig["data"]["decision"] if sig else None,
            "closed": closed["data"]["outcome"] if closed else None,
            "openings_without_a_committed_lock": no_commit,
            "posted_fingerprints_checked": len(posted or []),
            "log_fingerprint": f"{ev[-1]['seq']}:{ev[-1]['hash']}" if ev else None, "events": len(ev)}


def cmd_check_log(study: Study, a) -> None:
    rep = check_log(study, a.anchor, getattr(a, "change_log", None))
    print(json.dumps(rep, indent=1))
    if rep["status"] == INVALID:
        raise Refused("the log check failed")


def cmd_scorecard(study: Study, a) -> None:
    ev = study.events()
    runs = [e for e in ev if e["kind"] == "test.run"]
    by_test = {}
    for e in runs:
        t = by_test.setdefault(e["data"]["test"], {"attempts": 0, "failures": 0})
        t["attempts"] += 1
        t["failures"] += e["data"]["exit"] != 0
    t0 = dt.datetime.fromisoformat(ev[0]["at"].rstrip("Z")) if ev else None
    t1 = dt.datetime.fromisoformat(ev[-1]["at"].rstrip("Z")) if ev else None
    try:
        planned = [t for t in HELD_OUT_TESTS if t in (study.plan().get("tests") or {})]
    except (Refused, AttributeError):
        planned = None  # no readable plan: the scorecard says so and does not guess
    rep = check_log(study, a.anchor)
    status = rep["status"]
    card = {"study": study.d.name, "status": status, "acts": acts_report(study),
            "definition": definition_stamp(Path(a.factory), study.last("lock.recorded")),
            "models": models_report(ev, definition_stamp(Path(a.factory), study.last("lock.recorded"))),
            "finished": status.startswith("confirmatory study") or status == EXPLORATORY,
            "closed": rep["closed"],
            "elapsed_seconds": int((t1 - t0).total_seconds()) if ev else 0,
            "tests": by_test,
            "defects_caught_before_any_opening": sum(v["failures"] for v in by_test.values()),
            "openings_used": {t: len(openings_of(ev, t)[0]) - len(openings_of(ev, t)[1])
                              for t in HELD_OUT_TESTS if planned is None or t in planned or openings_of(ev, t)[0]},
            "openings_allowed": {t: study.allowed(None, t) for t in planned} if planned is not None else None,
            "notes_raised": sum(1 for e in ev if e["kind"] == "note.raised"),
            "acts_by_people": sum(1 for e in ev if e["actor"].startswith(("human:", "platform:"))),
            "acts_by_assistants": sum(1 for e in ev if e["actor"].startswith("agent:")),
            "checks": run_checks(study, Path(a.factory), a.anchor)}
    (study.d / "scorecard.json").write_text(json.dumps(card, indent=1))
    print(json.dumps(card, indent=1))


def deterministic_scorers(factory: Path) -> list:
    """The definition's deterministic scorers, as (name, check), in the order of their names: every
    scorers/<name>/scorer.md whose front matter says `type: deterministic`. A judge is not evaluated here."""
    fd, out = definition_tool(), []
    for f in sorted((Path(factory) / "scorers").glob("*/scorer.md")):
        try:
            fm = fd.front_matter(f.read_text())[0]
        except (OSError, ValueError, yaml.YAMLError):
            raise Refused(f"the scorer {f.parent.name} has no front matter that parses")
        if fm.get("type") == "deterministic":
            out.append((f.parent.name, fm.get("check")))
    if not out:
        raise Refused(f"the definition at {factory} has no deterministic scorer (scorers/<name>/scorer.md)")
    return out


def run_checks(study: Study, factory: Path, posted: list | None = None) -> dict:
    """Evaluate the definition's deterministic scorers against one study. A check
    that cannot be judged yet says `pending`, never `pass`."""
    ev, rep = study.events(), check_log(study, posted)
    finished = [e for e in ev if e["kind"] == "opening.finished"]
    started = [e for e in ev if e["kind"] == "opening.started"]
    listed = set()
    lf = study.d / "curation-list.json"
    if lf.is_file():
        try:
            listed = {f["id"] for fl in json.loads(lf.read_text())["by_subject"].values() for f in fl}
        except (ValueError, KeyError, TypeError, AttributeError):
            listed = set()
    raised = {e["data"]["id"] for e in ev if e["kind"] == "note.raised"}
    opened = None if not finished else True
    kinds = {
        "log-checks-out": rep["status"] != INVALID,
        "not-exploratory": opened and rep["status"] != EXPLORATORY,
        "openings-within-allowed": opened and all(len(openings_of(ev, t)[0]) - len(openings_of(ev, t)[1]) <= study.allowed(None, t)
                                                  for t in HELD_OUT_TESTS),
        "no-failed-opening": opened and all("run-failed" not in c["data"]["outcomes"].values() for c in finished),
        "lock-committed-before-opening": (rep["openings_without_a_committed_lock"] == 0) if started else None,
        "review-recorded": opened and bool(rep["reviews"]),
        "acts-recorded-by-people": all(is_act_by_people(e) for e in ev if e["kind"] in ACTS_BY_PEOPLE) and (
            True if any(e["kind"] in ACTS_BY_PEOPLE for e in ev) else None),
        "notes-on-curation-list": (raised - {e["data"]["id"] for e in ev if e["kind"] == "note.resolved"}) <= listed,
    }
    out = {}
    for name, check in deterministic_scorers(factory):
        if check not in kinds:
            raise Refused(f"scorer {name}: the check `{check}` is not one this study tool evaluates")
        v = kinds[check]
        out[name] = "pending" if v is None else ("pass" if v else "fail")
    return out


def not_a_change_log(log: Path) -> str | None:
    """Why an existing file cannot be the change log, or None. The change log holds change records and nothing else."""
    if not log.exists():
        return None
    try:
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
    except OSError:
        return "it cannot be read"
    for ln in lines:
        try:
            rec = json.loads(ln)
        except ValueError:
            return "it has a line that is not JSON"
        if not isinstance(rec, dict) or not {"problem_class", "change", "predicted"} <= set(rec):
            if isinstance(rec, dict) and {"seq", "kind", "prev", "hash"} <= set(rec):
                return "it is a study log (by its content, whatever it is called)"
            return "it holds lines that are not change records"
    return None


def cmd_log_change(study: Study, a) -> None:
    """Append one record to the change log: what was changed in the
    procedure, why, what it was predicted to do, and (later) what it did.
    The record is written first and the event that names it by checksum
    second, so the study log never points at a record that does not exist."""
    log = Path(a.log).resolve()
    if log.suffix != ".jsonl" or log.name == "study-log.jsonl":
        raise Refused("the change log is its own .jsonl file, never a study log")
    if log.name == "openings.jsonl":
        raise Refused("the change log is its own .jsonl file, never the record of what has been opened")
    why = not_a_change_log(log)
    if why:
        raise Refused(f"{log} cannot be the change log: {why}. The change log is its own file, such as factory/change-log.jsonl")
    study.check_actor(a.by)
    try:
        definition = definition_stamp(Path(a.factory))
    except Refused as r:
        raise Refused(f"{r}; a change record names the definition it was made under")
    with study.held() as f:
        ev = study.read_held(f)
        rec = {"at": now(), "by": a.by, "problem_class": a.problem, "change": a.change,
               "rationale": a.rationale, "predicted": a.predicted, "observed": a.observed,
               "context": {"model": a.model, "definition_sha": definition["sha256"], "definition_version": definition["version"],
                           "evidence_study": study.d.name, "log_fingerprint": ev[-1]["hash"] if ev else None},
               "log_event": len(ev)}
        try:
            with log.open("a") as out:
                out.write(json.dumps(rec, sort_keys=True) + "\n")
        except OSError as e:
            raise Refused(f"the change log could not be written at {log} ({e.strerror}); nothing was recorded")
        study._append(f, a.by, "change.recorded", {"problem_class": a.problem, "change": a.change,
                                                  "change_log": log.name, "record_sha": record_sha(rec)})
    print(f"change recorded under `{a.problem}`" + ("" if a.observed else " (the observed outcome is still to be recorded)"))


# ---- selftest: the happy path and the attacks ---------------------------
TOY = '''import hashlib, json, os, sys
from pathlib import Path
mode, out = sys.argv[1], sys.argv[2]
here = Path(__file__).resolve().parent
if mode == "known-answers":
    import yaml
    rule = yaml.safe_load((here / "analysis-plan.yaml").read_text())["rules"][0]
    tested = TESTED or {"supported_if": rule["supported_if"], "refuted_if": rule["refuted_if"]}
    json.dump({"rules": {"r": {"power_to_refute_when_false": POWER, "false_confirm_when_false": 0.0,
                               "false_confirm_at_edge_max": 0.04, "false_refute_at_edge_max": 0.04,
                               "coverage_when_true": 0.93, "tested_rule": tested}}}, open(out, "w"))
elif mode == "fetch":
    if (here / "fetch-is-down").exists():
        sys.exit(7)
    json.dump({"value": 1.02}, open(out, "w"))
elif mode == "fetch-elsewhere":  # exits 0 and writes a file name the plan does not expect
    json.dump({"value": 1.02}, open(os.path.join(out, "held-out-y1.json"), "w"))
elif mode == "fetch-fails-after-writing":
    json.dump({"value": 1.02}, open(os.path.join(out, "partial.json"), "w"))
    sys.exit(7)
elif mode == "fetch-with-token":  # a provider that wants a token
    if not os.environ.get("EARTHDATA_TOKEN"):
        sys.exit(7)
    json.dump({"value": 1.02}, open(out, "w"))
elif mode == "silent":  # exits 0 and writes nothing at all
    pass
elif mode == "environment":  # what a command the tool runs can see
    token = os.environ.get("EARTHDATA_TOKEN")
    json.dump({"gain": {"ci_low": 0.96, "ci_high": 1.04},
               "seen": sorted(k for k in os.environ if k.startswith(("PYTHON", "SF_"))),
               "names": sorted(os.environ), "token_sha": hashlib.sha256(token.encode()).hexdigest() if token else None,
               "data": {"sha256": hashlib.sha256(open(sys.argv[3], "rb").read()).hexdigest()} if len(sys.argv) > 3 else None},
              open(out, "w"))
elif mode == "scribble":  # writes a file its command names and the plan does not declare
    json.dump({"note": "left behind"}, open(sys.argv[3], "w"))
    json.dump({"gain": {"ci_low": 0.96, "ci_high": 1.04}}, open(out, "w"))
elif mode == "blind":  # a method that looks for the answer in what it was given
    text = open(sys.argv[3]).read()
    json.dump({"gain": {"ci_low": 0.99, "ci_high": 1.01}, "answer_seen": "put_in" in text or '"gain"' in text,
               "data": {"sha256": hashlib.sha256(text.encode()).hexdigest()}}, open(out, "w"))
elif mode == "decline":
    json.dump({"refused": "too few pairs", "data": {"sha256": hashlib.sha256(open(sys.argv[3], "rb").read()).hexdigest()}}, open(out, "w"))
else:
    src = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {"value": 1.0}
    read = {"sha256": hashlib.sha256(open(sys.argv[3], "rb").read()).hexdigest()} if len(sys.argv) > 3 and mode != "deaf" else None
    json.dump({"gain": {"ci_low": src["value"] - 0.04, "ci_high": src["value"] + 0.04}, "data": read}, open(out, "w"))
'''
PLAN = {
    "study": "STUDY-TEST", "question": "Is the gain within ten percent of one?",
    "quantity_estimated": "gain", "independence": "synthetic", "overturn": "an interval outside the band",
    "limitations": ["toy"], "openings_allowed": 1, "code": ["{study}/toy.py"],
    "data": {"working": "toy", "held_out": {"window": {"start": "2031-01-01", "end": "2031-12-31"},
                                            "withheld_values": ["value"], "path": "data/held-out.json"}},
    "tests": {"known-answers": {"command": ["{python}", "{study}/toy.py", "known-answers", "{study}/receipts/known-answers.json"],
                                "receipt": "receipts/known-answers.json"},
              "working-data": {"command": ["{python}", "{study}/toy.py", "working-data", "{study}/receipts/working-data.json"],
                               "receipt": "receipts/working-data.json"},
              "held-out": {"fetch": ["{python}", "{study}/toy.py", "fetch", "{study}/data/held-out.json"],
                           "command": ["{python}", "{study}/toy.py", "held-out", "{study}/receipts/held-out.json",
                                       "{study}/data/held-out.json"],
                           "receipt": "receipts/held-out.json"}},
    "rules": [{"id": "r", "role": "primary",
               "supported_if": [{"field": "gain.ci_low", "op": ">=", "value": 0.9}, {"field": "gain.ci_high", "op": "<=", "value": 1.1}],
               "refuted_if": [[{"field": "gain.ci_high", "op": "<", "value": 0.9}], [{"field": "gain.ci_low", "op": ">", "value": 1.1}]],
               "power_evidence": {"path": "rules.r", "require": [{"field": "power_to_refute_when_false", "op": ">=", "value": 0.8},
                                                                    {"field": "false_confirm_when_false", "op": "<=", "value": 0.05},
                                                                    {"field": "false_confirm_at_edge_max", "op": "<=", "value": 0.05},
                                                                    {"field": "false_refute_at_edge_max", "op": "<=", "value": 0.05},
                                                                    {"field": "coverage_when_true", "op": ">=", "value": 0.9}]}}],
}
URL = "https://example.invalid/review/1"


class A:  # a tiny argparse stand-in for the selftest
    def __init__(self, **k):
        self.__dict__.update(k)


def _fresh(tmp: Path, name: str, power: float = 0.9, tested: str = "None", plan: dict | None = None, start: A | None = None) -> Study:
    study = Study(tmp / name)
    cmd_start(study, start or A(id="STUDY-TEST", question=PLAN["question"], by="human:tester"))
    (study.d / "toy.py").write_text(TOY.replace("POWER", str(power)).replace("TESTED", tested))
    plan = json.loads(json.dumps(plan or PLAN))
    if isinstance(plan.get("data"), dict) and isinstance(plan["data"].get("held_out"), dict):
        plan["data"]["held_out"].setdefault("pair", name)  # each toy study has its own subject unless a test shares one
    study.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    return study


def _fresh_tested(tmp: Path, name: str) -> Study:
    study = _fresh(tmp, name)
    cmd_test(study, A(what="known-answers", by="agent:b"))
    cmd_test(study, A(what="working-data", by="agent:b"))
    return study


def _to_lock(study: Study, by: str = "human:tester") -> None:
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    cmd_test(study, A(what="working-data", by="agent:analysis"))
    cmd_lock(study, A(by=by, evidence=URL))


def _posted(study: Study) -> list:
    """What a steward would have posted on the tracking issue: the log fingerprint at the lock and after each opening."""
    return [f"{e['seq']}:{e['hash']}" for e in study.events() if e["kind"] in ("lock.recorded", "opening.finished")]


def _refuses(fn, *args) -> bool:
    try:
        fn(*args)
    except Refused:
        return True
    return False


def _refusal(fn, *args) -> str:
    """The words of a refusal, or nothing when the call went through."""
    try:
        fn(*args)
    except Refused as r:
        return str(r)
    return ""


def _selftest_fence_and_acts(tmp: Path, check) -> None:
    """The second independent attack on the tools, made here against the study tool, and the two acts by people as
    pull requests. Every study is in a throwaway folder; the only person's name typed is the placeholder."""
    import copy
    import time
    person = "human:throwaway-placeholder"
    kernel = bool(fence.landlock())
    have_git = bool(shutil.which("git"))

    def plan_with(change) -> dict:
        plan = copy.deepcopy(PLAN)
        change(plan)
        return plan

    def receipt(study: Study, name: str = "working-data") -> dict:
        return json.loads((study.d / "receipts" / f"{name}.json").read_text())
    probe = plan_with(lambda p: p["tests"]["working-data"].update(
        command=["{python}", "{study}/probe.py", "{study}/receipts/working-data.json"]))
    outside = tmp / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("held out\n")

    # ---- a command of a plan is fenced like a look (finding N5, and N1 to N3 as they bear on the study tool)
    study = _fresh(tmp, "f-fenced", plan=probe)
    (study.d / "probe.py").write_text(f'''import json, os, sys
tried = {{}}
def attempt(name, fn):
    try:
        fn()
        tried[name] = "done"
    except Exception as e:
        tried[name] = type(e).__name__
attempt("read the study log", lambda: open({str(study.log)!r}).read())
attempt("read the study tool", lambda: open({str(TOOL)!r}).read())
attempt("read a file outside", lambda: open({str(outside / "secret.txt")!r}).read())
attempt("read through a certificate variable", lambda: open(os.path.join(os.environ.get("SSL_CERT_DIR", "/nonexistent"), "secret.txt")).read())
attempt("write into the real study", lambda: open({str(study.d / "planted.txt")!r}, "w").write("x"))
attempt("write beside the study tool", lambda: open({str(TOOL.parent / "planted-by-a-step.py")!r}, "w").write("x"))
attempt("write into the tool's own environment", lambda: open(os.path.join({str(fence.own_environment())!r}, "planted-by-a-step.pth"), "w").write("x"))
json.dump({{"gain": {{"ci_low": 0.96, "ci_high": 1.04}}, "tried": tried, "cwd": os.getcwd(), "names": sorted(os.environ),
           "log_in_my_copy": os.path.exists("study-log.jsonl")}}, open(sys.argv[1], "w"))
''')
    kept = {k: os.environ.get(k) for k in ("SSL_CERT_DIR", "UV_KNOB", "UV_ENV_FILE")}
    os.environ.update(SSL_CERT_DIR=str(outside), UV_KNOB="5", UV_ENV_FILE=str(outside / "secret.txt"))
    try:
        cmd_test(study, A(what="working-data", by="agent:analysis"))
    finally:
        for k, v in kept.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    got, ran_in = receipt(study), study.last("test.run")["data"]["ran_in"]
    stray = [p for p in (study.d / "planted.txt", TOOL.parent / "planted-by-a-step.py", fence.own_environment() / "planted-by-a-step.pth") if p.exists()]
    for p in stray:
        p.unlink()
    check("a command of a plan runs in a scratch copy of the study that holds no study log, under a fixed environment: no UV_ "
          "variable and no certificate setting of the caller's arrives",
          got["cwd"] != str(study.d) and "sf-step-" in got["cwd"] and got["log_in_my_copy"] is False
          and not {"SSL_CERT_DIR", "UV_KNOB", "UV_ENV_FILE"} & set(got["names"]) and "SF_INSIDE_A_STEP" in got["names"])
    if kernel:
        check("with the kernel fence, a command of a plan cannot read the study log, the study tool, a file outside, or what a "
              "certificate variable of the caller's names, and cannot write into the real study, beside the tools or into the "
              "tool's own environment",
              set(got["tried"].values()) <= {"PermissionError", "FileNotFoundError"} and got["tried"]["read the study log"] == "PermissionError"
              and got["tried"]["write into the tool's own environment"] == "PermissionError" and not stray)
        check("the event of a test says the kernel fence was applied and tried, with what was tried and what the command could read",
              ran_in["confined"] == fence.KERNEL and ran_in["fence"]["applied"] is True
              and any("kept-out.txt" in x for x in ran_in["fence"]["tried_and_kept_out"])
              and any(x.startswith("write ") for x in ran_in["fence"]["tried_and_kept_out"]) and isinstance(ran_in["fence"]["could_read"], list))
    else:
        check("without a kernel fence the event of a test says so, and says why", ran_in["confined"] == fence.SCRATCH_ONLY and ran_in["fence"]["why_not"])

    # a fence that does not hold is a refusal, never a quiet fall-back (N2): here the canary is put inside what may be read
    if kernel:
        scratch = fence.make_scratch("sf-selftest-")
        try:
            (scratch / "work" / "run.py").write_text(f"open({str(tmp / 'ran-unfenced')!r}, 'w').write('x')\n")
            env = fence.minimal_environment(scratch, sys.executable)
            leaky = fence.run_fenced([sys.executable, "run.py"], scratch / "work", env, scratch, [*fence.interpreter_places(sys.executable), str(scratch)],
                                     [str(scratch / "work"), str(tmp)])
            check("on a machine with a kernel fence, a fence that does not keep its own canary out is a refusal: the script is not run, "
                  "and the report says what leaked",
                  leaky["not_run"] and leaky["confined"] == fence.SCRATCH_ONLY and "could read" in str(leaky["fence"]["why_not"])
                  and not (tmp / "ran-unfenced").exists())
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    try:
        fence.run_fenced([sys.executable, "-c", "pass"], tmp, {}, tmp, [], [str(TOOL.parent.parent)])
        refused = ""
    except fence.Cannot as why:
        refused = str(why)
    check("a script is never given a place to write that holds what the tools run from", "holds what the tool itself runs from" in refused)

    # the delayed job of N5: a step leaves a process behind that waits, then calls the lock under a person's name
    late = plan_with(lambda p: p["tests"]["working-data"].update(
        command=["{python}", "{study}/after.py", "{study}/receipts/working-data.json"]))
    study = _fresh(tmp, "f-delayed", plan=late)
    marker = tmp / "the-delayed-job-ran"
    (study.d / "after.py").write_text(f'''import json, os, subprocess, sys
json.dump({{"gain": {{"ci_low": 0.96, "ci_high": 1.04}}}}, open(sys.argv[1], "w"))
env = {{k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "SF_"))}}
job = "import time, subprocess, sys; time.sleep(2); open({str(marker)!r}, 'w').write('x'); " \\
      "subprocess.run([sys.executable, {str(TOOL)!r}, 'lock', '--study', {str(study.d)!r}, '--by', '{person}', " \\
      "'--evidence', 'https://example.org/pull/1', '--local-practice'])"
subprocess.Popen([sys.executable, "-c", job], env=env, start_new_session=True, stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
''')
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    cmd_test(study, A(what="working-data", by="agent:analysis"))
    ended = study.last("test.run")["data"]["ran_in"]["processes_ended"]
    time.sleep(3.5)
    if sys.platform.startswith("linux"):
        check("a job a step leaves behind to call the lock later under a person's name is ended with the step: it never runs, "
              "and no lock is in the log",
              not marker.exists() and not study.last("lock.recorded") and ended >= 0)
    # a step that calls the study tool directly, with its marks taken off: refused by its ancestry, with no kernel fence at all
    scratch = fence.make_scratch("sf-selftest-")
    try:
        (scratch / "work" / "call.py").write_text(
            "import os, subprocess, sys\n"
            "env = {k: v for k, v in os.environ.items() if not k.startswith(('PYTHON', 'SF_'))}\n"
            f"r = subprocess.run([sys.executable, '-X', 'utf8', {str(TOOL)!r}, 'lock', '--study', {str(study.d)!r}, '--by', '{person}', "
            "'--evidence', 'https://example.org/pull/1', '--local-practice'], env=env, capture_output=True, text=True)\n"
            "print(r.returncode, r.stderr)\n")
        called = fence.run_fenced([sys.executable, "call.py"], scratch / "work", fence.minimal_environment(scratch, sys.executable), scratch,
                                  [], [str(scratch / "work")], kernel=False)
        check("the study tool refuses the lock, and every other command, when a step of a plan is anywhere above it, even with the "
              "marks taken out of the environment, an interpreter option with a value in front, and no kernel fence",
              called["out"].startswith("2 ") and "started from inside a look or a step of a plan" in called["out"]
              and "fence.py --inside" in called["out"] and not study.last("lock.recorded") and called["confined"] == fence.SCRATCH_ONLY)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    kept_mark = os.environ.pop("SF_INSIDE_A_STEP", None)
    try:
        os.environ["SF_INSIDE_A_STEP"] = "S"
        check("the mark a step's environment carries is enough on its own to refuse", "SF_INSIDE_A_STEP" in _refusal(refuse_inside_a_look))
    finally:
        os.environ.pop("SF_INSIDE_A_STEP", None)
        if kept_mark is not None:
            os.environ["SF_INSIDE_A_STEP"] = kept_mark
    # a step that tries to change what the tool keeps, in its own copy
    meddle = plan_with(lambda p: p["tests"]["working-data"].update(command=["{python}", "{study}/meddle.py", "{study}/receipts/working-data.json"]))
    study = _fresh(tmp, "f-meddle", plan=meddle)
    (study.d / "meddle.py").write_text('import json, sys\njson.dump({"gain": {"ci_low": 0.96, "ci_high": 1.04}}, open(sys.argv[1], "w"))\n'
                                       'open("analysis-plan.yaml", "a").write("\\n# widened\\n")\nopen("study-log.jsonl", "w").write("{}")\n')
    plan_before = study.plan_sha()
    refusal = _refusal(cmd_test, study, A(what="working-data", by="agent:analysis"))
    check("a step that rewrites the analysis plan or writes a study log in its scratch copy changes neither: the run fails, and the "
          "plan and the log are as they stood",
          "did not pass" in refusal and study.plan_sha() == plan_before and not study.chain_problems()
          and study.last("test.run")["data"]["exit"] == 94)

    # ---- N14: a name with a line break after it is not a name
    check("an actor with a line break after the name is refused, for --by and for --asked-by",
          _refuses(Study.check_actor, "agent:a\n") and _refuses(Study.check_actor, person + "\n")
          and _refuses(cmd_start, Study(tmp / "f-newline"), A(id="S", question="Is it so?", by="agent:coordinating", asked_by=person + "\n")))

    # ---- N6: the held-out block is on record from the first time a tool sees it, and a change to it is an event
    study = _fresh(tmp, "h-block")
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    first = held_out_block(study.plan())
    check("the first time a tool sees a started study's plan, its held-out block goes on record beside the studies, with the paths it holds out",
          [ln["sha"] for ln in held_out_lines(study)] == [first["sha"]]
          and held_out_lines(study)[0]["paths"] == [str(study.d / "data" / "held-out.json")])
    moved = study.plan_path.read_text().replace("data/held-out.json", "data/other.json")
    study.plan_path.write_text(moved)
    check("after that, a plan whose held-out block differs is refused by the plan check, the tests and the request for a lock, in words that say what changed",
          "not the one on record" in _refusal(cmd_check_plan, study, A()) and "data/other.json" in _refusal(cmd_test, study, A(what="working-data", by="agent:analysis"))
          and "not the one on record" in _refusal(cmd_request_lock, study, A(by="agent:coordinating")))
    check("whoever ran the tests cannot record the change; it needs a reason",
          "ran this study's tests" in _refusal(cmd_held_out_change, study, A(by="agent:analysis", reason="x"))
          and "--reason" in _refusal(cmd_held_out_change, study, A(by="agent:coordinating", reason=" ")))
    cmd_held_out_change(study, A(by="agent:coordinating", reason="the provider moved the file"))
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    cmd_test(study, A(what="working-data", by="agent:analysis"))
    shown = "\n".join(lock_evidence(study, A(by=person))["lines"])
    check("the coordinating step records the change, the tests run again, and what the lock shows lists the change with who and why",
          "changed, on the record at event" in shown and "by agent:coordinating: the provider moved the file" in shown and "data/other.json" in shown)
    held_out_record(study).unlink()
    study.plan_path.write_text(study.plan_path.read_text().replace("data/other.json", "data/third.json"))
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    cmd_test(study, A(what="working-data", by="agent:analysis"))
    shown = "\n".join(lock_evidence(study, A(by=person))["lines"])
    check("with the record beside the studies deleted, a later change still shows at the lock, from the log: changed with no record of the change",
          "CHANGED WITH NO RECORD OF THE CHANGE" in shown)
    template = tmp / "h-template"
    template.mkdir()
    (template / "toy.py").write_text(TOY.replace("POWER", "0.9").replace("TESTED", "None"))
    (template / "analysis-plan.yaml").write_text(yaml.safe_dump(plan_with(lambda p: p["data"]["held_out"].update(pair="t")), sort_keys=False))
    cmd_check_plan(Study(template), A())
    check("the plan check of a folder nothing was started in records nothing beside it", not (tmp / "held-out.jsonl").exists() or
          not any(json.loads(ln).get("dir") == "h-template" for ln in (tmp / "held-out.jsonl").read_text().splitlines()))

    # ---- the definition is bound by the lock, and a changed definition blocks the opening
    definition = tmp / "factory-copy"
    shutil.copytree(FACTORY, definition)
    study = _fresh(tmp, "d-definition")
    cmd_test(study, A(what="known-answers", by="agent:analysis"))
    cmd_test(study, A(what="working-data", by="agent:analysis"))
    cmd_lock(study, A(by=person, evidence=URL, factory=str(definition), local_practice=True))
    agent = definition / "agents" / "review" / "agent.md"
    was = agent.read_text()
    model = study.last("lock.recorded")["data"]["definition"]["models"]["review"]["model"]
    agent.write_text(was.replace(f"model: {model}", "model: some-other-model-1"))
    refusal = _refusal(cmd_open_held_out, study, A(test="held-out", by="agent:coordinating", factory=str(definition), local_practice=True))
    check("a definition changed between the lock and the opening blocks the opening, says what changed, uses no opening up, and names the remedy",
          "the factory's definition changed after the lock" in refusal and "the agent `review` declared" in refusal and "some-other-model-1" in refusal
          and "a new lock" in refusal and not study.last("opening.started"))
    (definition / "skills" / "read-what-is-known" / "SKILL.md").write_text((definition / "skills" / "read-what-is-known" / "SKILL.md").read_text() + "\nA typo fixed.\n")
    agent.write_text(was)
    refusal = _refusal(cmd_open_held_out, study, A(test="held-out", by="agent:coordinating", factory=str(definition), local_practice=True))
    check("a one-line change to a skill blocks it too, and is named", "definition changed after the lock" in refusal and "read-what-is-known" in refusal)
    cmd_lock(study, A(by=person, evidence=URL, factory=str(definition), local_practice=True))
    cmd_open_held_out(study, A(test="held-out", by="agent:coordinating", factory=str(definition), local_practice=True))
    check("locked again on the definition as it is now, the study opens", study.last("opening.finished") is not None)

    # ---- practice: a typed lock is practice, by name, and says so everywhere
    route = Study.default_route
    Study.default_route = None  # as a command line has it: nothing is practice unless it says so
    try:
        study = _fresh(tmp, "p-practice")
        cmd_test(study, A(what="known-answers", by="agent:analysis"))
        cmd_test(study, A(what="working-data", by="agent:analysis"))
        typed = _refusal(cmd_lock, study, A(by=person, evidence=URL))
        check("a lock typed at a command line with no word of practice is refused, and the refusal names both routes",
              "the lock is a pull request" in typed and "request-lock" in typed and "--local-practice" in typed and not study.last("lock.recorded"))
        cmd_lock(study, A(by=person, evidence=URL, local_practice=True))
        status = stage_of(study, FACTORY)
        check("a practice lock is recorded as practice, and `status` says so in plain words",
              study.last("lock.recorded")["data"]["route"] == PRACTICE and status["acts"]["practice"] is True
              and "PRACTICE" in status["acts"]["lock"]["note"] and "cannot close as a signed finding" in status["acts"]["lock"]["note"])
        check("the held-out data of a practice study is not opened unless the caller says practice too",
              "practice lock" in _refusal(cmd_open_held_out, study, A(test="held-out", by="agent:coordinating"))
              and not study.last("opening.started"))
        cmd_open_held_out(study, A(test="held-out", by="agent:coordinating", local_practice=True))
        (tmp / "bare-finding.md").write_text("SUPPORTED, from the receipts\n")
        (tmp / "practice-finding.md").write_text("SUPPORTED, from the receipts\n\n" + PRACTICE_WORDS + "\n")
        check("the finding of a practice study is refused until it says, word for word, that the lock was practice",
              "has to say so" in _refusal(cmd_attach, study, A(by="agent:analysis", file=str(tmp / "bare-finding.md"))))
        cmd_attach(study, A(by="agent:analysis", file=str(tmp / "practice-finding.md")))
        (tmp / "ok.md").write_text("APPROVE")
        cmd_review(study, A(by="agent:review", verdict="approve", file=str(tmp / "ok.md")))
        posted = _posted(study)
        cmd_scorecard(study, A(factory=str(FACTORY), anchor=posted))
        card = json.loads((study.d / "scorecard.json").read_text())
        check("the scorecard of a practice study says practice", card["acts"]["practice"] is True and card["acts"]["lock"]["route"] == PRACTICE)
        check("a signature typed with no word of practice is refused",
              "the signature is a pull request" in _refusal(cmd_signature, study, A(by=person, evidence=URL, decision="signed", anchor=posted, comment=None)))
        cmd_signature(study, A(by=person, evidence=URL, decision="signed", anchor=posted, comment=None, local_practice=True))
        check("a practice study never closes as a signed finding; it closes as the practice study it is",
              "typed at a command line" in _refusal(cmd_close, study, A(by="agent:coordinating", outcome="finding-signed", cite=None, comment=None, anchor=posted))
              and "typed at a command line" in _refusal(cmd_close, study, A(by="agent:coordinating", outcome="negative-result-signed", cite=None, comment=None, anchor=posted)))
        cmd_close(study, A(by="agent:coordinating", outcome="practice-ended", cite=None, comment=None, anchor=posted))
        check("an actor `platform:<host>` writes nothing but a merged act", "records one thing only" in _refusal(
            cmd_note, _fresh(tmp, "p-platform"), A(kind="method", about="a", text="b", evidence=None, by="platform:github")))

        # ---- the lock as a pull request, checked with git alone
        if have_git:
            repo = tmp / "acts-repo"
            (repo / "studies").mkdir(parents=True)
            g = lambda *w: git("-C", str(repo), "-c", "user.name=selftest", "-c", "user.email=s@example.invalid", "-c", "commit.gpgsign=false", *w)  # noqa: E731
            sha = lambda ref="HEAD": g("rev-parse", ref).stdout.strip()  # noqa: E731
            g("init", "-q", "-b", "main")
            (repo / "README.md").write_text("throwaway\n")
            g("add", "-A"), g("commit", "-q", "-m", "start")
            g("checkout", "-q", "-b", "lock/R1")
            study = _fresh(repo / "studies", "R1", start=A(id="STUDY-TEST", question=PLAN["question"], by="agent:coordinating"))
            cmd_test(study, A(what="known-answers", by="agent:analysis"))
            cmd_test(study, A(what="working-data", by="agent:analysis"))
            cmd_request_lock(study, A(by="agent:coordinating"))
            summary = (study.d / "lock-request" / "EVIDENCE.md").read_text()
            manifest = json.loads((study.d / "lock-request" / "manifest.json").read_text())
            check("a lock request is an evidence summary in plain words and a manifest of checksums, and records nothing as locked",
                  all(h in summary for h in ("## The question", "## What would count for and against", "## What is held out, and every change to it",
                                             "## The known-answer tests", "## The code this lock would bind", "## The factory that made this study",
                                             "## Open notes", "## The exploration that led here"))
                  and manifest["plan_sha"] == study.plan_sha() and manifest["definition"]["sha256"] == definition_tool().tree_checksum(FACTORY)["sha256"]
                  and manifest["code"] == study.code_hashes(study.plan()) and not study.last("lock.recorded")
                  and study.last("lock.requested")["actor"] == "agent:coordinating")
            check("with a request and no merge, there is no lock: the opening is refused", "no lock yet" in _refusal(
                cmd_open_held_out, study, A(test="held-out", by="agent:coordinating")))
            check("the request checks out against the files it was made from", not request_problems(study, "lock", FACTORY))
            g("add", "-A"), g("commit", "-q", "-m", "lock request")
            on_branch = sha()
            rec = tmp / "platform-record.json"

            def platform(commit: str, **more) -> A:
                rec.write_text(json.dumps({"platform": "github", "pull_request": 7, "url": "https://github.example/o/r/pull/7", "author": "octo-author",
                                           "merged": True, "merge_commit": commit, "base": "main", "merged_by": "octo-steward",
                                           "approved": [{"login": "octo-steward", "commit_id": on_branch}], **more}))
                return A(by="platform:github", record_merge=commit, platform_record=str(rec), evidence=None)
            check("no merge: a commit that is not on the protected branch is not a lock",
                  "is not on the branch `main`" in _refusal(cmd_lock, study, platform(on_branch)) and not study.last("lock.recorded"))
            g("checkout", "-q", "-b", "elsewhere", "main")
            g("merge", "-q", "--no-ff", "-m", "merged somewhere else", "lock/R1")
            wrong = sha()
            check("wrong branch: a merge of the request into another branch is not a lock, whatever the record is told",
                  "is not on the branch `main`" in _refusal(cmd_lock, study, platform(wrong))
                  and "merged into `elsewhere`" in _refusal(cmd_lock, study, platform(wrong, base="elsewhere")))
            g("checkout", "-q", "main")
            g("merge", "-q", "--no-ff", "-m", "Merge the lock request", "lock/R1")
            merge = sha()
            check("a merged request is recorded only under the platform's name, never under a typed person's",
                  "under the platform's name" in _refusal(cmd_lock, study, A(by=person, record_merge=merge, platform_record=str(rec), evidence=URL)))
            check("a merge its author alone approved is not a lock", "An author's own approval does not count" in _refusal(
                cmd_lock, study, platform(merge, approved=[{"login": "octo-author", "commit_id": on_branch}])))
            (study.d / "toy.py").write_text((study.d / "toy.py").read_text() + "\n# changed after the merge\n")
            check("manifest changed after the merge: with a bound file edited, the merge is not recorded as a lock",
                  "not the ones the merged request binds" in _refusal(cmd_lock, study, platform(merge)))
            g("checkout", "-q", "--", "studies/R1/toy.py")
            cmd_lock(study, platform(merge))
            lock = study.last("lock.recorded")
            check("the merge is the lock: recorded under the platform's name with the merge commit, the branch and the people the record names",
                  lock["actor"] == "platform:github" and route_of(lock) == PULL_REQUEST and lock["data"]["merge"]["commit"] == merge
                  and lock["data"]["merge"]["people"]["approved"] == ["octo-steward"] and stage_of(study, FACTORY)["acts"]["lock"]["route"] == PULL_REQUEST)
            check("until the recorded lock is committed, nothing is opened", "the lock is not committed" in _refusal(
                cmd_open_held_out, study, A(test="held-out", by="agent:coordinating")))
            g("add", "-A"), g("commit", "-q", "-m", "Record the act merged in " + merge)
            (study.d / "toy.py").write_text((study.d / "toy.py").read_text() + "\n# changed after the lock\n")
            check("manifest changed after the lock: the opening is refused and not used up",
                  "what the merged request binds is not what is here: a bound file: {study}/toy.py" in _refusal(
                      cmd_open_held_out, study, A(test="held-out", by="agent:coordinating"))
                  and not study.last("opening.started"))
            g("checkout", "-q", "--", "studies/R1/toy.py")
            g("checkout", "-q", "--detach", f"{merge}^1")
            g("checkout", "-q", "main", "--", "studies")  # the files of the locked study, with a history that does not hold the merge
            away = _refusal(cmd_open_held_out, study, A(test="held-out", by="agent:coordinating"))
            g("checkout", "-q", "-f", "main")
            check("a checkout whose history does not hold the merge cannot open: the merge is not reachable from HEAD",
                  "not reachable from what is checked out here" in away and not study.last("opening.started"))
            # a practice lock presented as a real one: a typed event that claims the pull request route
            forged = _fresh(repo / "studies", "R2")
            cmd_test(forged, A(what="known-answers", by="agent:analysis"))
            cmd_test(forged, A(what="working-data", by="agent:analysis"))
            cmd_request_lock(forged, A(by="agent:coordinating"))
            got = lock_evidence(forged, A(by=person))
            forged.append(person, "lock.recorded", {**got["data"], "evidence": URL, "route": PULL_REQUEST,
                                                    "merge": {"commit": merge, "branch": "main", "people": {"approved": ["somebody"], "author": "x"}}})
            g("add", "-A"), g("commit", "-q", "-m", "a typed lock that claims a merge")
            check("a practice lock presented as a real one is refused at the opening and fails the log check: the merge it cites did not "
                  "bring its request in, and it was not recorded by the platform",
                  "the lock's merge does not check out" in _refusal(cmd_open_held_out, forged, A(test="held-out", by="agent:coordinating"))
                  and check_log(forged)["status"] == INVALID and not forged.last("opening.started"))
            cmd_open_held_out(study, A(test="held-out", by="agent:coordinating"))
            check("a lock that is a merge on the protected branch, reachable from HEAD, with a manifest that matches, opens the held-out data",
                  study.last("opening.finished") is not None and study.last("opening.started")["data"]["lock_route"] == PULL_REQUEST
                  and check_log(study)["status"] != INVALID)
    finally:
        Study.default_route = route


def selftest() -> int:
    import copy
    import importlib.util
    import io
    import marshal
    import struct
    import time
    results = []
    Study.default_model = "selftest-model"  # every agent event of this self-test is written under this name, except where a check says otherwise
    Study.default_route = PRACTICE  # the self-test types its locks and signatures: practice, in throwaway folders; the pull request route is tested by name

    def check(name: str, ok: bool) -> None:
        results.append((name, bool(ok)))

    with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
        tmp = Path(t).resolve()
        (tmp / "v.md").write_text("APPROVE")
        (tmp / "b.md").write_text("BLOCK")
        (tmp / "finding.md").write_text("a finding drafted from receipts\n\n" + PRACTICE_WORDS + "\n")
        approve = lambda who: A(by=who, verdict="approve", file=str(tmp / "v.md"))  # noqa: E731
        block = lambda who: A(by=who, verdict="block", file=str(tmp / "b.md"))  # noqa: E731
        finding = lambda who="agent:analysis": A(by=who, file=str(tmp / "finding.md"))  # noqa: E731
        opening = lambda who="agent:x": A(test="held-out", by=who)  # noqa: E731
        lock = lambda who="human:tester": A(by=who, evidence=URL)  # noqa: E731
        sign = lambda study, decision="signed": A(by="human:tester", evidence=URL, decision=decision,  # noqa: E731
                                                  anchor=_posted(study), comment=None)
        close = lambda outcome: A(by="agent:coordinating", outcome=outcome, cite=None, comment=None)  # noqa: E731
        void = lambda: A(test="held-out", by="human:tester", evidence=URL, reason="the provider was down")  # noqa: E731
        have_git = bool(shutil.which("git"))

        def said(fn, *args) -> str:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                fn(*args)
            return buf.getvalue()

        def tool(*args, env=None):  # the tool as a command, the way a person runs it
            return subprocess.run([sys.executable, str(TOOL), *args], env={**os.environ, **(env or {})},
                                  capture_output=True, text=True, stdin=subprocess.DEVNULL)

        def git_in(repo: Path):
            def run(*args):
                return git("-C", str(repo), "-c", "user.name=selftest", "-c", "user.email=s@example.invalid",
                           "-c", "commit.gpgsign=false", *args)
            return run

        def tests(study: Study, by: str = "agent:b") -> None:
            cmd_test(study, A(what="known-answers", by=by)), cmd_test(study, A(what="working-data", by=by))

        def open_and_review(study: Study) -> None:
            cmd_open_held_out(study, opening())
            cmd_attach(study, finding())
            cmd_review(study, approve("agent:review"))

        def with_plan(change) -> dict:
            plan = copy.deepcopy(PLAN)
            change(plan)
            return plan

        def plan_problems(tmp_name: str, change) -> list:
            return check_plan(_fresh(tmp, tmp_name, plan=with_plan(change)).plan(), Study(tmp / tmp_name))

        # ---- the happy path, in a git work tree when git is here, so the lock is a commit as the procedure asks
        home = tmp / "happy-repo"
        home.mkdir()
        if have_git:
            git_in(home)("init", "-q")
        study = _fresh(home, "happy")
        check("the procedure places a new study at the test stage, waiting on the tests",
              stage_of(study, FACTORY)["stage"] == "test" and "tests-pass" in stage_of(study, FACTORY)["still_needs"])
        _to_lock(study)
        check("after the lock the procedure places it at the open stage", stage_of(study, FACTORY)["stage"] == "open")
        lock_fp = f"{study.events()[-1]['seq']}:{study.events()[-1]['hash']}"
        if have_git:
            git_in(home)("add", "-A"), git_in(home)("commit", "-q", "-m", "lock")
        check("a review before any opening has finished is refused", _refuses(cmd_review, study, approve("agent:review")))
        cmd_open_held_out(study, opening("agent:coordinating"))
        cmd_attach(study, finding())
        cmd_review(study, approve("agent:review"))
        cmd_note(study, A(kind="method", about="recipes/x.md", text="n", evidence=None, by="agent:coordinating"))
        cmd_curation_list(study, A())
        check("without the posted log fingerprints the study is not ready",
              check_log(study)["status"].startswith("confirmatory study, log fingerprints missing"))
        rep = check_log(study, _posted(study))
        check("the happy path reaches ready for the steward's signature with the rule supported",
              rep["status"] == READY and rep["outcomes"]["held-out"] == {"r": "supported"})
        sc = run_checks(study, FACTORY, _posted(study))
        check("the checks a definition may name, for a stage and for a deterministic scorer, are exactly the ones this tool evaluates",
              set(stage_checks(study)[0]) == set(definition_tool().STAGE_CHECKS)
              and {c for _, c in deterministic_scorers(FACTORY)} == set(definition_tool().SCORER_CHECKS) and len(sc) == 8)
        check("every process check in the procedure passes on the happy path",
              set(sc.values()) == {"pass"} if have_git else {k: v for k, v in sc.items() if v != "pass"} == {"lock-committed": "fail"})
        cmd_log_change(study, A(by="agent:curating", log=str(tmp / "changes.jsonl"), factory=str(FACTORY), problem="toy",
                                change="pr/1", rationale="r", predicted="p", observed=None, model="m"))
        check("a change record lands in the change log and in the study log",
              json.loads((tmp / "changes.jsonl").read_text())["predicted"] == "p" and study.last("change.recorded") is not None)
        check("the change log cannot be pointed at a study log",
              _refuses(cmd_log_change, study, A(by="agent:curating", log=str(study.log), factory=str(FACTORY), problem="toy",
                                                change="c", rationale="r", predicted="p", observed=None, model="m")))
        check("the steward's signature recorded by an assistant is refused",
              _refuses(cmd_signature, study, A(by="agent:analysis", evidence=URL, decision="signed", anchor=_posted(study), comment=None)))
        check("a signature recorded as signed without the posted log fingerprints is refused",
              _refuses(cmd_signature, study, A(by="human:tester", evidence=URL, decision="signed", anchor=None, comment=None)))
        check("closing as signed before the steward's signature is refused",
              _refuses(cmd_close, study, close("finding-signed")) and _refuses(cmd_close, study, close("practice-ended")))
        cmd_review(study, block("agent:second-review"))
        cmd_review(study, approve("agent:third-review"))
        check("one review assistant's block is not cleared by another's approval",
              check_log(study, _posted(study))["status"] == "confirmatory study, blocked by review")
        cmd_review(study, approve("agent:second-review"))
        check("and is cleared when the review assistant that blocked approves",
              check_log(study, _posted(study))["status"] == READY)
        cmd_signature(study, sign(study))
        check("with the signature recorded the procedure waits on the note's disposition",
              stage_of(study, FACTORY)["stage"] == "learn" and stage_of(study, FACTORY)["open_notes"] == ["NOTE-001"])
        check("the signature records the path and checksum of the finding it signs",
              study.last("signature.recorded")["data"]["finding"] == study.last("finding.attached")["data"]
              and study.last("signature.recorded")["data"]["finding"]["sha"] == sha_file(tmp / "finding.md"))
        check("a finding attached after the signature is refused", _refuses(cmd_attach, study, finding()))
        check("after the signature the log check says signed, not ready",
              check_log(study)["status"] == SIGNED and check_log(study)["signature"] == "signed")
        check("a declined note needs its reason",
              _refuses(cmd_resolve, study, A(by="agent:curating", note="NOTE-001", disposition="declined", ref=None, comment=None)))
        cmd_resolve(study, A(by="agent:curating", note="NOTE-001", disposition="linked", ref="https://example.invalid/pr/9", comment=None))
        check("a study that is not a system trial cannot close as one",
              "only a system trial does" in _refusal(cmd_close, study, close("system-trial-accepted")))
        check("a study whose lock and signature were typed at a command line cannot close as a signed finding, of either kind",
              "typed at a command line" in _refusal(cmd_close, study, close("finding-signed"))
              and "typed at a command line" in _refusal(cmd_close, study, close("negative-result-signed"))
              and not any(e["kind"] == "study.closed" for e in study.events()))
        cmd_close(study, close("practice-ended"))
        check("the study closes, as the practice study it is, and takes nothing more",
              stage_of(study, FACTORY)["stage"] == "closed"
              and _refuses(cmd_note, study, A(kind="method", about="x", text="n", evidence=None, by="agent:x")))
        check("and after the close the log check says so", check_log(study)["status"] == SIGNED + "; closed as practice-ended")
        rep = check_log(study, change_log=tmp / "changes.jsonl")
        (tmp / "changes.jsonl").write_text((tmp / "changes.jsonl").read_text().replace('"predicted": "p"', '"predicted": "another"'))
        check("the log check, given the change log, catches a change record edited afterwards",
              rep["status"] != INVALID and check_log(study, change_log=tmp / "changes.jsonl")["status"] == INVALID)
        lines = study.log.read_text().splitlines()
        cut = study.d / "study-log.jsonl"
        cut.write_text("\n".join(lines[:int(lock_fp.split(":")[0])]) + "\n")  # drop the lock and everything after
        rep = check_log(study, [lock_fp])
        check("a study log cut short checks out on its own and is caught by the posted fingerprint",
              not study.chain_problems() and rep["status"] == INVALID and any("posted fingerprint" in p for p in rep["problems"]))

        study = _fresh(tmp, "a1")
        tests(study)
        check("an opening before the lock is refused", _refuses(cmd_open_held_out, study, opening()))
        check("a test run of the held-out data is refused", _refuses(cmd_test, study, A(what="held-out", by="agent:b")))
        check("the lock recorded by an assistant is refused", _refuses(cmd_lock, study, A(by="agent:b", evidence=URL)))
        check("the lock with no evidence of a person's approval is refused", _refuses(cmd_lock, study, A(by="human:tester", evidence=None)))
        check("process checks that cannot be judged yet say pending, not pass",
              run_checks(study, FACTORY)["independent-review"] == "pending")
        check("an evidence link with no host name, and the placeholders from the documents, are refused",
              _refuses(cmd_lock, study, A(by="human:tester", evidence="https://"))
              and _refuses(cmd_lock, study, A(by="human:tester", evidence="https://.../pull/N"))
              and _refuses(cmd_lock, study, A(by="human:YOU", evidence=URL))
              and not study.last("lock.recorded"))
        check("a signature recorded as declined before any opening is refused",
              _refuses(cmd_signature, study, sign(study, "declined")) and not stage_checks(study)[0]["steward-decided"])

        study = _fresh(tmp, "a2")
        _to_lock(study)
        plan = dict(study.plan(), overturn="edited after the lock")
        study.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
        check("an opening after the analysis plan changed is refused", _refuses(cmd_open_held_out, study, opening()))

        study = _fresh(tmp, "a3")
        _to_lock(study)
        (study.d / "toy.py").write_text((study.d / "toy.py").read_text() + "\n# tuned after the lock\n")
        check("an opening after the code changed is refused", _refuses(cmd_open_held_out, study, opening()))

        study = _fresh(tmp, "a3b")
        (study.d / "helper.py").write_text("x = 1\n")
        _to_lock(study)
        (study.d / "helper.py").write_text("x = 2\n")
        check("an opening after a neighbour module the plan does not list changed is refused",
              _refuses(cmd_open_held_out, study, opening()))

        study = _fresh(tmp, "a4")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        check("a second opening beyond the openings allowed is refused", _refuses(cmd_open_held_out, study, opening()))
        check("an opening that obtained its data cannot be voided",
              _refuses(cmd_void_unread, study, A(test="held-out", by="human:tester", evidence=URL, reason="want another")))
        (study.d / "receipts" / "held-out.json").write_text('{"gain": {"ci_low": 0.99, "ci_high": 1.01}}')
        check("a receipt edited after the opening fails the log check", check_log(study)["status"] == INVALID)

        study = _fresh(tmp, "a5")
        _to_lock(study)
        lines = study.log.read_text().splitlines()
        lines[1] = lines[1].replace('"exit": 0', '"exit": 1') if '"exit": 0' in lines[1] else lines[1].replace("agent:analysis", "agent:other")
        study.log.write_text("\n".join(lines) + "\n")
        check("a rewritten study log line fails the log check", check_log(study)["status"] == INVALID)
        check("and nothing more can be appended to it", _refuses(cmd_open_held_out, study, opening()))

        study = _fresh(tmp, "a6")
        _to_lock(study)
        (study.d / "data" / "held-out.json").write_text('{"value": 1.0}')
        check("held-out data present before the opening is refused", _refuses(cmd_open_held_out, study, opening()))
        check("and the log check calls it out", check_log(study)["status"] == INVALID)

        study = _fresh(tmp, "a6b")
        _to_lock(study)
        (study.d / "receipts" / "held-out.json").write_text('{"gain": {"ci_low": 0.99, "ci_high": 1.01}}')
        check("a held-out receipt put in place before the opening is refused",
              _refuses(cmd_open_held_out, study, opening()))

        study = _fresh(tmp, "a7")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        check("a review by an assistant that ran the work is refused", _refuses(cmd_review, study, approve("agent:x")))

        study = _fresh(tmp, "a8", power=0.3)
        tests(study)
        check("a rule that cannot fail when the idea is false cannot be locked", _refuses(cmd_lock, study, lock()))

        study = _fresh(tmp, "a8b", tested='{"supported_if": [], "refuted_if": []}')
        tests(study)
        check("power evidence for a rule other than the planned one cannot be locked", _refuses(cmd_lock, study, lock()))

        study = _fresh(tmp, "a9")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        cmd_lock(study, lock())
        check("locking again after an opening makes the study exploratory", check_log(study)["status"] == EXPLORATORY)
        check("and the plan-adherence check fails on it", run_checks(study, FACTORY)["plan-adherence"] == "fail")

        study = _fresh(tmp, "a10")
        tests(study)
        plan = dict(study.plan(), limitations=["toy", "edited after the tests ran"])
        study.plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
        check("the lock on a plan the known-answer tests and working data never ran against is refused",
              _refuses(cmd_lock, study, lock()))

        silent = copy.deepcopy(PLAN)
        silent["tests"]["working-data"]["command"] = ["{python}", "{study}/toy.py", "silent", "x"]
        study = _fresh(tmp, "a11", plan=silent)
        cmd_test(study, A(what="known-answers", by="agent:b"))
        (study.d / "receipts" / "working-data.json").write_text("{}")
        check("a test that exits 0 without writing its receipt does not pass (a stale receipt is removed)",
              _refuses(cmd_test, study, A(what="working-data", by="agent:b")))

        study = _fresh(tmp, "a12")
        _to_lock(study)
        (study.d / "fetch-is-down").write_text("")
        cmd_open_held_out(study, opening())
        check("an opening whose fetch failed is used up", _refuses(cmd_open_held_out, study, opening()))
        check("and reads as held-out data opened without a result",
              check_log(study)["status"].startswith("confirmatory study, held-out data opened without a result"))
        check("an assistant cannot void it",
              _refuses(cmd_void_unread, study, A(test="held-out", by="agent:x", evidence=URL, reason="network")))
        cmd_void_unread(study, A(test="held-out", by="human:tester", evidence=URL, reason="the provider was down; no data was written"))
        (study.d / "fetch-is-down").unlink()
        open_and_review(study)
        rep = check_log(study, _posted(study))
        check("a person can void an opening that never obtained data, on the record, and the opening then runs once",
              rep["status"] == READY and any("voided" in n for n in rep["remarks"])
              and _refuses(cmd_open_held_out, study, opening()))

        two = copy.deepcopy(PLAN)
        two["openings_allowed"] = {"held-out": 1, "independent-site": 1}
        two["data"]["held_out"]["path"] = "data/held-out.json"
        two["tests"]["independent-site"] = {
            "fetch": ["{python}", "{study}/toy.py", "fetch", "{study}/data/independent-site.json"], "data": "data/independent-site.json",
            "command": ["{python}", "{study}/toy.py", "independent-site", "{study}/receipts/independent-site.json",
                        "{study}/data/independent-site.json"],
            "receipt": "receipts/independent-site.json"}
        study = _fresh(tmp, "a13", plan=two)
        _to_lock(study)
        open_and_review(study)
        check("a planned repeat at an independent site that has not been run keeps the study from ready",
              check_log(study)["status"] == "confirmatory study, a planned opening remains (independent-site)")
        cmd_scorecard(study, A(factory=str(FACTORY), anchor=None))
        both = json.loads((study.d / "scorecard.json").read_text())["openings_allowed"]

        deaf = copy.deepcopy(PLAN)
        deaf["tests"]["held-out"]["command"][2] = "deaf"
        study = _fresh(tmp, "a16", plan=deaf)
        _to_lock(study)
        cmd_open_held_out(study, opening())
        check("an opening whose receipt does not name the fetched data by hash has no result",
              check_log(study)["outcomes"]["held-out"] == {"r": "run-failed"})
        nofetch = copy.deepcopy(PLAN)
        del nofetch["tests"]["held-out"]["fetch"]
        study = _fresh(tmp, "a17", plan=nofetch)
        check("a held-out test with no fetch fails the plan check", _refuses(cmd_check_plan, study, A()))

        if have_git:
            repo = tmp / "repo"
            repo.mkdir()
            g = git_in(repo)
            g("init", "-q")
            (repo / "readme.txt").write_text("a repository for the selftest\n")
            g("add", "-A"), g("commit", "-q", "-m", "first")
            rooted = with_plan(lambda p: p.update(roots={"here": ".."}))
            study = _fresh(repo, "study", plan=rooted)
            _to_lock(study)
            env = study.last("test.run")["data"]["env"]
            check("the environment stamp of a test records the host, the user, and each root's commit and whether its work tree was clean",
                  {"host", "user", "python", "platform", "roots"} <= set(env) and re.fullmatch(r"[0-9a-f]{40}", env["roots"]["here"]["commit"] or "")
                  and env["roots"]["here"]["clean"] is False and "(the study)" in env["roots"])
            check("in a git work tree, an opening before the lock is committed is refused",
                  _refuses(cmd_open_held_out, study, opening()))
            os.environ["GIT_DIR"] = str(tmp / "no-such-repository")
            try:
                check("with GIT_DIR pointing nowhere, an opening before the lock is committed is still refused",
                      "not committed" in _refusal(cmd_open_held_out, study, opening()))
            finally:
                del os.environ["GIT_DIR"]
            g("add", "-A"), g("commit", "-q", "-m", "lock")
            cmd_open_held_out(study, opening())
            g("add", "-A"), g("commit", "-q", "-m", "opening")
            kept = [ln for ln in study.log.read_text().splitlines() if '"opening.' not in ln]
            study.log.write_text("\n".join(kept) + "\n")
            (study.d / "data" / "held-out.json").unlink(), (study.d / "receipts" / "held-out.json").unlink()
            check("and a study log cut back behind its last commit fails the log check and takes no second opening",
                  check_log(study)["status"] == INVALID and not study.chain_problems()
                  and "continuation" in _refusal(cmd_open_held_out, study, opening())
                  and not any(e["kind"].startswith("opening.") for e in study.events()))

        reh = copy.deepcopy(PLAN)
        reh["rehearsals"] = [{"id": "opening-path", "why": "the fetch and the command have run once on working data",
                              "steps": [["{python}", "{study}/toy.py", "fetch", "{study}/data/rehearsal.json"],
                                        ["{python}", "{study}/toy.py", "held-out", "{study}/receipts/rehearsal.json",
                                         "{study}/data/rehearsal.json"]],
                              "receipt": "receipts/rehearsal.json", "writes": ["data/rehearsal.json"]}]
        study = _fresh(tmp, "a18", plan=reh)
        tests(study)
        check("the lock is refused while a planned rehearsal has not passed", _refuses(cmd_lock, study, lock()))
        cmd_rehearse(study, A(id="opening-path", by="agent:b"))
        cmd_lock(study, lock())
        check("and is recorded once the rehearsal has passed on the same plan and code", study.last("lock.recorded") is not None)

        typo = copy.deepcopy(PLAN)
        typo["rules"][0]["supported_if"][0]["field"] = "gain.ci_lo"
        study = _fresh(tmp, "a19", plan=typo)
        tests(study)
        check("a rule that reads a field the working-data receipt does not carry cannot be locked", _refuses(cmd_lock, study, lock()))

        dec = copy.deepcopy(PLAN)
        dec["tests"]["held-out"]["command"][2] = "decline"
        study = _fresh(tmp, "a20", plan=dec)
        _to_lock(study)
        cmd_open_held_out(study, opening())
        check("the locked method declining to estimate is recorded as inconclusive, with its reason",
              check_log(study)["outcomes"]["held-out"] == {"r": "inconclusive"}
              and study.last("opening.finished")["data"]["method_declined"] == "too few pairs")

        same = copy.deepcopy(PLAN)
        same["data"]["held_out"]["pair"] = "one river, one year"
        first, second = _fresh(tmp, "a21", plan=same), _fresh(tmp, "a22", plan=same)
        for o in (first, second):
            _to_lock(o)
            open_and_review(o)
        check("a second study opening the same pair and window is exploratory, the first is not",
              check_log(second, _posted(second))["status"] == EXPLORATORY
              and check_log(first, _posted(first))["status"] == READY)

        study = _fresh(tmp, "a24")
        dirty = tool("test", "known-answers", "--study", str(study.d), "--by", "agent:b", "--model", "selftest-model", env={"PYTHONPATH": str(tmp)})
        check("a test run with an injected Python path visible is refused (a hook that hides itself is a stated limit)",
              dirty.returncode == 2 and "PYTHONPATH" in dirty.stderr and not study.last("test.run"))
        others = [tool(c, "--study", str(study.d), env={"PYTHONPATH": str(tmp)}) for c in ("status", "scorecard", "check-plan", "fingerprint")]
        check("status, scorecard, check-plan and fingerprint are refused too while PYTHONPATH is set",
              all(r.returncode == 2 and "PYTHONPATH" in r.stderr for r in others) and not (study.d / "scorecard.json").exists())
        prefix = tool("test", "known-answers", "--study", str(study.d), "--by", "agent:b", "--model", "selftest-model", env={"PYTHONPYCACHEPREFIX": str(tmp / "planted")})
        check("an inherited PYTHONPYCACHEPREFIX is refused before anything runs",
              prefix.returncode == 2 and "PYTHONPYCACHEPREFIX" in prefix.stderr and not study.last("test.run"))

        inner = copy.deepcopy(PLAN)
        inner["code"] = ["{study}/toy.py"]
        inner["tests"]["held-out"]["command"] = ["{python}", "{study}/runner.py", "held-out", "{study}/receipts/held-out.json",
                                                 "{study}/data/held-out.json"]
        study = _fresh(tmp, "a25", plan=inner)
        (study.d / "runner.py").write_text((study.d / "toy.py").read_text())
        _to_lock(study)
        (study.d / "runner.py").write_text((study.d / "toy.py").read_text() + "\n# edited after the lock\n")
        check("a script inside the study that a command names is locked even when the code list omits it",
              _refuses(cmd_open_held_out, study, opening()))

        spaced = copy.deepcopy(PLAN)
        spaced["data"]["held_out"]["pair"] = "One  River, one year "
        third = _fresh(tmp, "a26", plan=spaced)
        _to_lock(third)
        cmd_open_held_out(third, opening())
        check("the record of what has been opened matches a subject through spacing and case",
              check_log(third)["status"] == EXPLORATORY)

        study = _fresh(tmp, "a23")
        check("an early exit must cite what answered the question",
              _refuses(cmd_close, study, A(by="agent:analysis", outcome="answered-by-existing-knowledge", cite=None, comment=None)))
        cmd_close(study, A(by="agent:analysis", outcome="answered-by-existing-knowledge", cite="findings/x.md", comment=None))
        check("a study closed by an early exit runs nothing further", _refuses(cmd_test, study, A(what="known-answers", by="agent:b")))

        for bad, why in ((dict(PLAN, openings_allowed="many"), "an openings-allowed value that is not a number"),
                         (dict(PLAN, openings_allowed=True), "an openings-allowed value that is a boolean"),
                         (dict(PLAN, rules=[dict(PLAN["rules"][0], supported_if=[{"field": "gain.ci_low", "op": ">=", "value": float("nan")}])]),
                          "a rule threshold that is not a finite number")):
            study = _fresh(tmp, "bad" + str(len(results)), plan=bad)
            check(f"{why} fails the plan check", _refuses(cmd_check_plan, study, A()))
        esc = copy.deepcopy(PLAN)
        esc["tests"]["held-out"]["receipt"] = "../outside.json"
        study = _fresh(tmp, "a14", plan=esc)
        check("a receipt path that leaves the study fails the plan check", _refuses(cmd_check_plan, study, A()))
        study = _fresh(tmp, "a15")
        study.plan_path.write_text("rules: [unclosed\n")
        check("an analysis plan that does not parse is refused, not a crash", _refuses(cmd_check_plan, study, A()))
        check("an actor that is neither human:<id> nor agent:<id> is refused",
              _refuses(cmd_note, study, A(kind="method", about="x", text="n", evidence=None, by="steward")))

        # ---- the third review round: each scenario below is an attack a reviewer carried through
        # the plan goes missing after a lock
        study = _fresh(tmp, "n-plan-gone")
        _to_lock(study)
        open_and_review(study)
        (study.d / "receipts" / "held-out.json").write_text('{"gain": {"ci_low": 0.999, "ci_high": 1.001}, "data": {"sha256": "x"}}')
        study.plan_path.rename(tmp / "plan-moved-aside.yaml")
        rep = check_log(study, _posted(study))
        check("once the log holds a lock, a missing analysis plan fails the log check, and a receipt edited meanwhile is still caught",
              rep["status"] == INVALID and any("analysis plan" in p and "missing" in p for p in rep["problems"])
              and any("receipt on disk" in p for p in rep["problems"]))
        check("and neither the signature nor the scorecard's chain of custody passes while the plan is missing",
              _refuses(cmd_signature, study, sign(study)) and run_checks(study, FACTORY, _posted(study))["chain-of-custody"] == "fail")

        # what the lock binds: every file a command names, read from the study directory
        relative = with_plan(lambda p: p["tests"]["held-out"].update(
            command=["{python}", "analysis/run.py", "held-out", "receipts/held-out.json", "data/held-out.json"]))
        study = _fresh(tmp, "n-relative", plan=relative)
        (study.d / "analysis").mkdir()
        (study.d / "analysis" / "run.py").write_text((study.d / "toy.py").read_text())
        tests(study)
        printed = said(cmd_lock, study, lock())
        check("the lock prints the list of bound files", "bound files" in printed and "  analysis/run.py" in printed and "{study}/toy.py" in printed)
        (study.d / "analysis" / "run.py").write_text("import sys\n")
        check("a script the opening runs by a relative path is locked: changed after the lock, the opening is refused",
              "analysis/run.py" in _refusal(cmd_open_held_out, study, opening()))
        study = _fresh(tmp, "n-any-directory")
        plan = checked_plan(study)
        elsewhere, was = tmp / "elsewhere", os.getcwd()
        elsewhere.mkdir()
        (elsewhere / "fetch").write_text("an unrelated file whose name is a word of a command\n")
        os.chdir(elsewhere)
        try:
            from_elsewhere = study.code_hashes(plan)
        finally:
            os.chdir(was)
        check("the code identity is the same from whatever directory the tool is called",
              from_elsewhere == study.code_hashes(plan) and "fetch" not in from_elsewhere)
        check("a command that names its script with -m or -c fails the plan check",
              any("-m or -c" in x for x in plan_problems("n-dash-m", lambda p: p["tests"]["held-out"].update(
                  command=["{python}", "-m", "runner", "{study}/receipts/held-out.json", "{study}/data/held-out.json"])))
              and any("-m or -c" in x for x in plan_problems("n-dash-c", lambda p: p["tests"]["working-data"].update(
                  command=["{python}", "-Ic", "print(1)", "{study}/receipts/working-data.json"]))))

        # a command is a launcher the tool knows and a script the lock binds; nothing else is run
        def refused_command(name: str, argv: list, *words, key: str = "command", test: str = "held-out") -> bool:
            if key == "steps":
                found = plan_problems(name, lambda p: p.update(rehearsals=[{"id": "x", "why": "w", "steps": [argv]}]))
            else:
                found = plan_problems(name, lambda p: p["tests"][test].update({key: argv}))
            return any(all(w in x for w in words) for x in found)
        outs = ["{study}/receipts/held-out.json", "{study}/data/held-out.json"]
        named, moved = "is not a launcher the study tool knows", "Put the step in a script and name the script"
        check("a command whose program is a shell fails the plan check: the script inside its text would never be locked",
              refused_command("v1-bash", ["bash", "-lc", 'exec python3 analysis.py "$0" "$1"', *outs], "`bash` " + named, moved))
        check("so do env, sh -c and perl -e in front of a script: no list of bad programs, only the launchers the tool knows",
              refused_command("v1-env", ["env", "python3", "{study}/toy.py", "held-out", *outs], "`env` " + named, moved)
              and refused_command("v1-sh", ["sh", "-c", "python3 toy.py held-out receipts/held-out.json data/held-out.json"], "`sh` " + named, moved)
              and refused_command("v1-perl", ["perl", "-e", 'exec "python3", "toy.py", @ARGV', "held-out", *outs], "`perl` " + named, moved)
              and refused_command("v1-python3", ["python3", "{study}/toy.py", "held-out", *outs], "`python3` " + named, moved))
        check("a uv run that ends in python -c, or takes an option the tool does not know, fails the plan check",
              refused_command("v1-uv-c", ["uv", "run", "python", "-c", "print(1)", *outs], "`uv run python` would run a program", moved)
              and refused_command("v1-uv-with", ["uv", "run", "--with", "x", "{study}/toy.py", "held-out", *outs],
                                  "`--with` is not an option `uv run` may take", moved)
              and refused_command("v1-uv-module", ["uv", "run", "-m", "runner", *outs], "`-m` is not an option", moved)
              and refused_command("v1-uv-bare", ["uv", "run", "--script"], "`uv run` is followed by a script file", moved))
        check("a fetch and a rehearsal step are held to the same rule as a test command",
              refused_command("v1-fetch", ["bash", "-c", "python3 toy.py fetch data/held-out.json", "{study}/data/held-out.json"],
                              "`tests.held-out.fetch`", named, key="fetch")
              and refused_command("v1-step", ["sh", "-c", "true"], "`rehearsals[x].steps[0]`", named, key="steps")
              and refused_command("v1-known", ["make", "known-answers"], "`tests.known-answers.command`", named, test="known-answers"))
        check("a command whose script is not a file fails the plan check, with the path the tool looked for",
              refused_command("v1-absent", ["{python}", "{study}/absent.py", "held-out", *outs],
                              "its script `{study}/absent.py` is not a file", str(tmp / "v1-absent" / "absent.py"))
              and refused_command("v1-uv-absent", ["uv", "run", "--script", "tools/absent", "held-out", *outs], "its script `tools/absent` is not a file"))
        study = _fresh(tmp, "v1-written", plan=with_plan(lambda p: (
            p["tests"]["working-data"].update(command=["{python}", "{study}/second.py", "working-data", "{study}/receipts/working-data.json"]),
            p["tests"]["known-answers"].update(writes=["second.py"]))))
        (study.d / "second.py").write_text((study.d / "toy.py").read_text())
        check("the script a command runs cannot also be a file a step writes",
              any("`second.py` is the script `tests.working-data.command` runs" in x for x in check_plan(study.plan(), study)))
        launchers = with_plan(lambda p: (p["tests"]["held-out"].update(
            command=["uv", "run", "--no-project", "--script", "analysis/run.py", "held-out", "receipts/held-out.json", "data/held-out.json"]),
            p.update(rehearsals=[{"id": "form", "why": "the form the finding takes is on file", "needs": ["{study}/form.md"],
                                  "steps": [["{python}", "{study}/toy.py", "working-data", "{study}/receipts/form.json"]],
                                  "writes": ["receipts/form.json"]}])))
        study = _fresh(tmp, "v1-lock-prints", plan=launchers)
        (study.d / "analysis").mkdir()
        (study.d / "analysis" / "run.py").write_text((study.d / "toy.py").read_text())
        tests(study)
        absent = _refusal(cmd_rehearse, study, A(id="form", by="agent:b"))
        failed = study.last("rehearsal.run")["data"]
        check("a rehearsal that needs a file that is not there fails without running its steps, and says which file",
              "did not pass" in absent and failed["exit"] == 93 and "{study}/form.md" in failed["problem"]
              and not (study.d / "receipts" / "form.json").exists()
              and "a file the plan names is missing: {study}/form.md" in _refusal(cmd_lock, study, lock()))
        (study.d / "form.md").write_text("the form of the finding\n")
        tests(study)
        cmd_rehearse(study, A(id="form", by="agent:b"))
        printed = said(cmd_lock, study, lock())
        bound = study.last("lock.recorded")["data"]["code"]
        check("the lock prints, for each command, the launcher and the script it bound, and each file a rehearsal needs",
              f"  tests.held-out.command: uv run runs analysis/run.py (sha256 {bound['analysis/run.py'][:16]})" in printed
              and f"  tests.held-out.fetch: {{python}} runs {{study}}/toy.py (sha256 {bound['{study}/toy.py'][:16]})" in printed
              and f"  rehearsals[form].steps[0]: {{python}} runs {{study}}/toy.py (sha256 {bound['{study}/toy.py'][:16]})" in printed
              and f"  rehearsals[form].needs: {{study}}/form.md (sha256 {bound['{study}/form.md'][:16]})" in printed)
        (study.d / "form.md").write_text("another form\n")
        check("a file a rehearsal needs is locked: changed after the lock, the opening is refused",
              "{study}/form.md" in _refusal(cmd_open_held_out, study, opening()))
        shipped = [f for f in (REPO / "examples" / "stand-alone" / "system-trial" / "analysis-plan.yaml",
                               REPO / "examples" / "baton-rouge" / "system-trial" / "analysis-plan.yaml",
                               REPO / "factory" / "templates" / "analysis-plan.yaml") if f.is_file()]
        check("every command of the plans that ship with the tool is a launcher the tool knows and a script",
              all(command_problem(argv) is None for f in shipped for _, argv in Study.commands(load_plan_text(f.read_text())))
              and all(len(Study.commands(load_plan_text(f.read_text()))) >= 3 for f in shipped))
        check("an interpreter given to uv run by its path fails the plan check; a version is taken",
              refused_command("v1-uv-python-path", ["uv", "run", "--python", "/tmp/planted/python3", "{study}/toy.py", "held-out", *outs],
                              "does not name a Python version", moved)
              and refused_command("v1-uv-python-equals", ["uv", "run", "-p=./python", "{study}/toy.py", "held-out", *outs],
                                  "does not name a Python version")
              and plan_problems("v1-uv-python-version", lambda p: p["tests"]["held-out"].update(
                  command=["uv", "run", "--python", "3.12", "--script", "{study}/toy.py", "held-out", *outs])) == [])
        # what uv picks up from the study's folders is bound when a command runs through uv
        uv_fetch = with_plan(lambda p: p["tests"]["held-out"].update(
            fetch=["uv", "run", "--script", "{study}/toy.py", "fetch", "{study}/data/held-out.json"]))
        study = _fresh(tmp / "uv-folders", "S", plan=uv_fetch)
        _to_lock(study)
        (study.d / ".venv" / "bin").mkdir(parents=True)
        (study.d / ".venv" / "bin" / "python3").write_text("#!/bin/sh\n")
        planted_environment = _refusal(cmd_open_held_out, study, opening())
        shutil.rmtree(study.d / ".venv")
        (study.d.parent / "uv.toml").write_text("offline = true\n")
        planted_settings = _refusal(cmd_open_held_out, study, opening())
        check("a virtual environment folder or a uv settings file planted in the study's folders after the lock blocks the opening, "
              "when the plan runs a command through uv",
              "{study}/.venv (new since the lock)" in planted_environment and "virtual environment" in planted_environment
              and "{study}/../uv.toml (new since the lock)" in planted_settings and not study.last("opening.started"))
        beside = _fresh(tmp / "uv-beside", "S", plan=uv_fetch)  # a developer's environment in the folder above, there at the lock
        (beside.d.parent / ".venv" / "bin").mkdir(parents=True)
        (beside.d.parent / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n")
        (beside.d.parent / ".venv" / "bin" / "python3").write_text("the interpreter\n")
        tests(beside)
        printed = said(cmd_lock, beside, lock())
        at_lock = beside.last("lock.recorded")
        unchanged = environment_problems(beside, beside.plan(), at_lock)
        (beside.d.parent / ".venv" / "bin" / "python3").write_text("another interpreter\n")
        swapped = _refusal(cmd_open_held_out, beside, opening())
        shutil.rmtree(beside.d.parent / ".venv")
        check("a virtual environment folder that was there at the lock is recorded and printed by it; unchanged or gone it is no "
              "problem at the opening, changed it blocks the opening",
              "a virtual environment folder that `uv run` would use: {study}/../.venv" in printed
              and list(at_lock["data"]["uv_environments"]) == ["{study}/../.venv"] and unchanged == []
              and "{study}/../.venv (changed since the lock)" in swapped
              and environment_problems(beside, beside.plan(), at_lock) == [] and not beside.last("opening.started"))
        plain = _fresh(tmp / "uv-folders", "T")  # beside a uv.toml, with a pyproject.toml and an environment of its own
        (plain.d / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        (plain.d / ".venv").mkdir()
        _to_lock(plain)
        check("a plan whose commands all run through {python} does not bind those files: uv never reads them for it",
              not any(k.endswith(("uv.toml", "pyproject.toml", ".venv")) for k in plain.last("lock.recorded")["data"]["code"])
              and plain.last("lock.recorded")["data"]["uv_environments"] == {}
              and environment_problems(plain, plain.plan(), plain.last("lock.recorded")) == [])
        if shutil.which("uv"):
            through_uv = with_plan(lambda p: p["tests"]["working-data"].update(
                command=["uv", "run", "--no-project", "--offline", "--script", "{study}/toy.py", "working-data", "{study}/receipts/working-data.json"]))
            study = _fresh(tmp, "v1-uv-runs", plan=through_uv)
            tests(study)
            check("a uv run of a script runs under the environment the tool builds, and its test passes",
                  study.last("test.run", test="working-data")["data"]["exit"] == 0
                  and "PATH" in study.last("test.run", test="working-data")["data"]["env_names"])
        params = with_plan(lambda p: p["tests"]["held-out"].update(
            command=["{python}", "{study}/toy.py", "held-out", "{study}/receipts/held-out.json", "{study}/data/held-out.json",
                     "--params={study}/params.json"]))
        study = _fresh(tmp, "n-params", plan=params)
        (study.d / "params.json").write_text('{"half_width": 0.30}')
        _to_lock(study)
        (study.d / "params.json").write_text('{"half_width": 0.01}')
        check("a parameter file inside the study that a command names is locked: changed after the lock, the opening is refused",
              "params.json" in _refusal(cmd_open_held_out, study, opening()))
        scribble = with_plan(lambda p: p["tests"]["working-data"].update(
            command=["{python}", "{study}/toy.py", "scribble", "{study}/receipts/working-data.json", "{study}/scratch.json"]))
        study = _fresh(tmp, "n-scribble", plan=scribble)
        why = _refusal(cmd_test, study, A(what="working-data", by="agent:b"))
        check("a test that writes a file its command names and the plan does not declare fails, and says which file",
              "scratch.json" in (study.last("test.run")["data"].get("problem") or "") and study.last("test.run")["data"]["exit"] == 94
              and "did not pass" in why)
        declared = with_plan(lambda p: p["tests"]["working-data"].update(
            command=["{python}", "{study}/toy.py", "scribble", "{study}/receipts/working-data.json", "{study}/scratch.json"],
            writes=["scratch.json"]))
        study = _fresh(tmp, "n-declared", plan=declared)
        (study.d / "scratch.json").write_text("left by an earlier run")
        tests(study)
        check("and passes once the plan declares it under writes, which also keeps it out of the locked code",
              study.last("test.run")["data"]["exit"] == 0 and not any("scratch" in k for k in study.last("test.run")["data"]["code"])
              and json.loads((study.d / "scratch.json").read_text()) == {"note": "left behind"})

        # what Python loads must be what was hashed
        runner = ("import hashlib, json, sys\nimport helper\nsrc = json.load(open(sys.argv[3]))\n"
                  "json.dump({'gain': {'ci_low': src['value'] - helper.HALF, 'ci_high': src['value'] + helper.HALF},\n"
                  "           'data': {'sha256': hashlib.sha256(open(sys.argv[3], 'rb').read()).hexdigest()}}, open(sys.argv[2], 'w'))\n")
        imports = with_plan(lambda p: p["tests"]["held-out"].update(
            command=["{python}", "{study}/run.py", "held-out", "{study}/receipts/held-out.json", "{study}/data/held-out.json"]))

        def with_helper(name: str) -> Study:
            s = _fresh(tmp, name, plan=imports)
            (s.d / "run.py").write_text(runner)
            (s.d / "helper.py").write_text("HALF = 0.30\n")  # 1.02 give or take 0.30: inconclusive
            _to_lock(s)
            return s

        study = with_helper("n-planted-bytecode")
        other = compile("HALF = 0.01\n", str(study.d / "helper.py"), "exec")  # would turn inconclusive into supported
        (study.d / "__pycache__").mkdir()
        (study.d / "__pycache__" / f"helper.{sys.implementation.cache_tag}.pyc").write_bytes(
            importlib.util.MAGIC_NUMBER + struct.pack("<I", 1) + b"\0" * 8 + marshal.dumps(other))  # hash-based, never checked
        cmd_open_held_out(study, opening())
        check("bytecode planted beside a locked source after the lock is never loaded: the result is the source's",
              study.last("opening.finished")["data"]["outcomes"] == {"r": "inconclusive"})
        study = with_helper("n-sourceless-bytecode")
        (study.d / "extra.pyc").write_bytes(importlib.util.MAGIC_NUMBER + struct.pack("<I", 1) + b"\0" * 8 + marshal.dumps(other))
        check("a sourceless .pyc added beside a locked source after the lock blocks the opening",
              "extra.pyc (new since the lock)" in _refusal(cmd_open_held_out, study, opening()))
        study = with_helper("n-shadow-package")
        (study.d / "json").mkdir()
        (study.d / "json" / "__init__.py").write_text("raise SystemExit('the planted json package was imported')\n")
        check("a new package folder named json beside a locked source after the lock blocks the opening",
              "json/__init__.py (new since the lock)" in _refusal(cmd_open_held_out, study, opening()))
        seen = with_plan(lambda p: p["tests"]["working-data"].update(
            command=["{python}", "{study}/toy.py", "environment", "{study}/receipts/working-data.json"]))
        study = _fresh(tmp, "n-environment", plan=seen)
        os.environ["SF_SYSTEM_TRIAL_SEAL"], os.environ["SF_ANYTHING"] = "5:0.9", "1"
        try:
            cmd_test(study, A(what="working-data", by="agent:b"))
        finally:
            del os.environ["SF_SYSTEM_TRIAL_SEAL"], os.environ["SF_ANYTHING"]
        check("a command the tool runs sees no SF_ variable and no PYTHON variable but the three the tool sets",
              json.loads((study.d / "receipts" / "working-data.json").read_text())["seen"]
              == ["PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "PYTHONPYCACHEPREFIX", "SF_INSIDE_A_STEP"])  # the last is the tool's own mark
        planted = {"EARTHDATA_TOKEN": "secret-value-123", "AWS_SECRET_ACCESS_KEY": "another-secret", "LD_LIBRARY_PATH": str(tmp / "planted-libs"),
                   "BASH_ENV": str(tmp / "planted.sh"), "UV_NO_PROGRESS": "1"}
        token_sha = hashlib.sha256(planted["EARTHDATA_TOKEN"].encode()).hexdigest()
        kept = {k: os.environ.get(k) for k in planted}

        def with_planted(fn, *args):
            os.environ.update(planted)
            try:
                return fn(*args)
            finally:
                for k, v in kept.items():
                    os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        study = _fresh(tmp, "e-short-list", plan=seen)
        with_planted(cmd_test, study, A(what="working-data", by="agent:b"))
        got = json.loads((study.d / "receipts" / "working-data.json").read_text())
        recorded = study.last("test.run")["data"]["env_names"]
        allowed = lambda n: n in given_names()  # noqa: E731  (the fixed list the tool builds: no UV_ variable is on it any longer)
        check("a command the tool runs is given a short list of variables and nothing else: a token, a secret key and a library path "
              "in the caller's environment do not arrive",
              all(allowed(n) for n in got["names"]) and got["token_sha"] is None and "PATH" in got["names"]
              and not {"EARTHDATA_TOKEN", "AWS_SECRET_ACCESS_KEY", "LD_LIBRARY_PATH", "BASH_ENV", "UV_NO_PROGRESS"} & set(got["names"]))
        check("the event of a test records the names its command was given, and they are the names the command saw",
              set(recorded) - {"LC_CTYPE"} == set(got["names"]) - {"LC_CTYPE"} and "EARTHDATA_TOKEN" not in recorded)
        passing = with_plan(lambda p: p["tests"]["working-data"].update(
            command=["{python}", "{study}/toy.py", "environment", "{study}/receipts/working-data.json"], passes_environment=["EARTHDATA_TOKEN"]))
        study = _fresh(tmp, "e-passes", plan=passing)
        with_planted(cmd_test, study, A(what="working-data", by="agent:b"))
        got = json.loads((study.d / "receipts" / "working-data.json").read_text())
        check("a name the plan lists under passes_environment reaches that step's command; the event records the name and never the value",
              got["token_sha"] == token_sha and "EARTHDATA_TOKEN" in study.last("test.run")["data"]["env_names"]
              and "AWS_SECRET_ACCESS_KEY" not in got["names"] and planted["EARTHDATA_TOKEN"] not in study.log.read_text())
        unset = _fresh(tmp, "e-not-set", plan=passing)
        os.environ.pop("EARTHDATA_TOKEN", None)
        why = _refusal(cmd_test, unset, A(what="working-data", by="agent:b"))
        check("a step whose plan passes a name that is not set is refused before anything runs",
              "EARTHDATA_TOKEN" in why and "Nothing was run" in why and not unset.last("test.run")
              and not (unset.d / "receipts" / "working-data.json").exists())
        check("passes_environment is a list of names, and never a PYTHON or SF_ name",
              any("`tests.working-data.passes_environment`" in x and "names only" in x for x in plan_problems(
                  "e-shape", lambda p: p["tests"]["working-data"].update(passes_environment="EARTHDATA_TOKEN")))
              and any("names only" in x for x in plan_problems(
                  "e-value", lambda p: p["tests"]["working-data"].update(passes_environment=["EARTHDATA_TOKEN=secret"])))
              and any("PYTHONPATH cannot be passed" in x for x in plan_problems(
                  "e-python", lambda p: p["tests"]["working-data"].update(passes_environment=["PYTHONPATH"])))
              and any("SF_SEAL cannot be passed" in x for x in plan_problems(
                  "e-sf", lambda p: p.update(rehearsals=[{"id": "x", "why": "w", "passes_environment": ["SF_SEAL"],
                                                          "steps": [["{python}", "{study}/toy.py", "silent", "x"]]}]))))
        token_fetch = lambda passes: with_plan(lambda p: p["tests"]["held-out"].update(  # noqa: E731
            fetch=["{python}", "{study}/toy.py", "fetch-with-token", "{study}/data/held-out.json"],
            command=["{python}", "{study}/toy.py", "environment", "{study}/receipts/held-out.json", "{study}/data/held-out.json"],
            **({"passes_environment": ["EARTHDATA_TOKEN"]} if passes else {})))
        study = _fresh(tmp, "e-opening", plan=token_fetch(True))
        _to_lock(study)
        why = _refusal(cmd_open_held_out, study, opening())
        check("an opening whose plan passes a name that is not set is refused, and the opening is not used up",
              "EARTHDATA_TOKEN" in why and "not used up" in why and not study.last("opening.started"))
        printed = with_planted(said, cmd_open_held_out, study, opening())
        done = study.last("opening.finished")["data"]
        check("at an opening the names the plan passes reach the fetch, and the opening's event records them",
              done["fetch_exit"] == 0 and done["outcomes"] == {"r": "supported"} and "EARTHDATA_TOKEN" in done["env_names"]
              and "AWS_SECRET_ACCESS_KEY" not in done["env_names"]
              and json.loads((study.d / "receipts" / "held-out.json").read_text())["token_sha"] == token_sha)
        study = _fresh(tmp, "e-opening-unlisted", plan=token_fetch(False))
        _to_lock(study)
        with_planted(cmd_open_held_out, study, opening())
        check("and a fetch whose plan does not list the token never sees it, though the caller has it set",
              study.last("opening.finished")["data"]["fetch_exit"] == 7 and "EARTHDATA_TOKEN" not in study.last("opening.finished")["data"]["env_names"])
        study = _fresh(tmp, "e-lock-prints", plan=passing)
        with_planted(tests, study)
        check("the lock prints which steps are given which extra names",
              "tests.working-data is also given EARTHDATA_TOKEN" in said(cmd_lock, study, lock())
              and "no step asks for more" in said(cmd_lock, _fresh_tested(tmp, "e-lock-prints-none"), lock()))
        os.environ["GIT_DIR"], os.environ["LD_LIBRARY_PATH_FOR_GIT"] = str(tmp / "no-such-repository"), "x"
        try:
            names_git_sees = git("-c", "alias.names=!env", "names")
        finally:
            del os.environ["GIT_DIR"], os.environ["LD_LIBRARY_PATH_FOR_GIT"]
        if have_git:
            check("git, the tool's other child, is given the same short list",
                  names_git_sees is not None and "PATH=" in names_git_sees.stdout
                  and not any(ln.startswith(("LD_LIBRARY_PATH_FOR_GIT=", "GIT_DIR=" + str(tmp))) for ln in names_git_sees.stdout.splitlines()))
        beside = tmp / "tool-copy"
        beside.mkdir()
        shutil.copyfile(TOOL, beside / "sf.py")
        shutil.copyfile(TOOL.parent / "fence.py", beside / "fence.py")  # the one file the study tool loads from beside it, by path
        for name in ("json", "argparse", "hashlib", "ctypes", "signal"):
            (beside / f"{name}.py").write_text(f"open({str(beside / 'imported')!r}, 'a').write('{name} ')\nraise SystemExit(3)\n")
        ran = subprocess.run([sys.executable, str(beside / "sf.py"), "fingerprint", "--study", str(tmp / "nowhere")],
                             capture_output=True, text=True, env=dict(os.environ), stdin=subprocess.DEVNULL)
        check("a file named like a standard module beside the study tool is not imported by it",
              ran.returncode == 2 and "the study log is empty" in ran.stderr and not (beside / "imported").exists())

        # the subject, the window and the record of what has been opened
        check("a plan with no pair fails the plan check: the study's id never stands in for the subject",
              any("data.held_out.pair" in x for x in check_plan(with_plan(lambda p: None), None))
              and any("data.held_out.pair" in x for x in plan_problems("n-pairs", lambda p: p["data"]["held_out"].update(pairs="x"))))
        check("a window written as text, or with other keys than start and end, fails the plan check",
              any("data.held_out.window" in x for x in plan_problems("n-text-window", lambda p: p["data"]["held_out"].update(
                  window="2025 through 2026")))
              and any("data.held_out.window" in x for x in plan_problems("n-from-to", lambda p: p["data"]["held_out"].update(
                  window={"from": "2025-04-28", "to": "2026-04-27"}))))
        (tmp / "real-study").mkdir()
        os.symlink(tmp / "real-study", tmp / "linked-study")
        check("a study directory reached through a symlink is refused", "symlink" in _refusal(Study, tmp / "linked-study"))
        used = _fresh(tmp / "reuse", "STUDY-A")
        _to_lock(used)
        cmd_open_held_out(used, opening())
        used.d.rename(used.d.parent / "STUDY-A-inconclusive")
        again = _fresh(tmp / "reuse", "STUDY-A")
        _to_lock(again)
        check("a directory used again after its first study opened takes no opening: the record's line is not this log's own",
              "does not contain" in _refusal(cmd_open_held_out, again, opening()) and check_log(again)["status"] == INVALID
              and check_log(Study(tmp / "reuse" / "STUDY-A-inconclusive"))["status"] != INVALID)
        study = _fresh(tmp / "cut-back", "study")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        study.log.write_text("\n".join(ln for ln in study.log.read_text().splitlines() if '"opening.' not in ln) + "\n")
        (study.d / "data" / "held-out.json").unlink(), (study.d / "receipts" / "held-out.json").unlink()
        check("outside git too, a log cut back behind its opening takes no second opening: the record still holds the first",
              not study.chain_problems() and "does not contain" in _refusal(cmd_open_held_out, study, opening())
              and check_log(study)["status"] == INVALID)
        study = _fresh(tmp / "no-record", "study")
        _to_lock(study)
        open_and_review(study)
        ready = check_log(study, _posted(study))["status"]
        openings_path(study).unlink()
        rep = check_log(study, _posted(study))
        check("an opening with no line in the record of what has been opened fails the log check",
              ready == READY and rep["status"] == INVALID and any("has no line" in p for p in rep["problems"]))

        # an opening is voided only when the tool can say that nothing was read
        study = _fresh(tmp, "n-killed")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        study.log.write_text("\n".join(study.log.read_text().splitlines()[:-1]) + "\n")  # as if killed before it finished
        (study.d / "data" / "held-out.json").unlink(), (study.d / "receipts" / "held-out.json").unlink()
        check("an opening that was started and never finished cannot be voided, and reads as opened without a result",
              "never finished" in _refusal(cmd_void_unread, study, void())
              and check_log(study)["status"].startswith("confirmatory study, held-out data opened without a result"))
        elsewhere_plan = with_plan(lambda p: p["tests"]["held-out"].update(fetch=["{python}", "{study}/toy.py", "fetch-elsewhere", "{study}/data"]))
        study = _fresh(tmp, "n-fetched-elsewhere", plan=elsewhere_plan)
        _to_lock(study)
        cmd_open_held_out(study, opening())
        done = study.last("opening.finished")["data"]
        check("an opening whose fetch exited 0 and wrote a file under another name cannot be voided",
              done["fetch_exit"] == 0 and done["fetch_wrote"] == ["data/held-out-y1.json"] and _refuses(cmd_void_unread, study, void()))
        nothing_plan = with_plan(lambda p: p["tests"]["held-out"].update(fetch=["{python}", "{study}/toy.py", "silent", "{study}/data/held-out.json"]))
        study = _fresh(tmp, "n-fetched-nothing", plan=nothing_plan)
        _to_lock(study)
        cmd_open_held_out(study, opening())
        done = study.last("opening.finished")["data"]
        why = _refusal(cmd_void_unread, study, void())
        check("an opening whose fetch exited 0 without delivering the planned file cannot be voided",
              done["fetch_exit"] == 0 and done["fetch_wrote"] == [] and done["data_sha"] is None and done["receipt_sha"] is None
              and "did not fail (exit 0)" in why and not study.last("opening.voided")
              and "used up" in _refusal(cmd_open_held_out, study, opening()))
        partial = with_plan(lambda p: p["tests"]["held-out"].update(
            fetch=["{python}", "{study}/toy.py", "fetch-fails-after-writing", "{study}/data"]))
        study = _fresh(tmp, "n-partial", plan=partial)
        _to_lock(study)
        cmd_open_held_out(study, opening())
        check("an opening whose fetch failed after writing a file into the study cannot be voided",
              study.last("opening.finished")["data"]["fetch_exit"] == 7 and "data/partial.json" in _refusal(cmd_void_unread, study, void()))
        check("a fetch command that names neither the planned data path nor its folder fails the plan check",
              any("tests.held-out.fetch" in x for x in plan_problems("n-fetch-names", lambda p: p["tests"]["held-out"].update(
                  fetch=["{python}", "{study}/toy.py", "fetch", "{study}/elsewhere/held-out.json"]))))
        def same_data(p):
            p["openings_allowed"] = {"held-out": 1, "independent-site": 1}
            p["tests"]["independent-site"] = {
                "fetch": ["{python}", "{study}/toy.py", "fetch", "{study}/data/held-out.json"],
                "command": ["{python}", "{study}/toy.py", "independent-site", "{study}/receipts/independent-site.json", "{study}/data/held-out.json"],
                "receipt": "receipts/independent-site.json", "pair": "another site"}
        check("two tests on held-out data that would write the same data file fail the plan check",
              any("would write the same data file" in x for x in plan_problems("n-same-data", same_data)))
        check("an allowance of more than one opening fails the plan check",
              any("openings_allowed" in x for x in plan_problems("n-two", lambda p: p.update(openings_allowed={"held-out": 2})))
              and any("openings_allowed" in x for x in plan_problems("n-five", lambda p: p.update(openings_allowed=5))))

        # an opening outside a commit
        study = _fresh(tmp, "n-no-commit")
        _to_lock(study)
        open_and_review(study)
        rep = check_log(study, _posted(study))
        harness = _fresh(tmp, "n-harness")
        _to_lock(harness, by=HARNESS_PERSON)
        open_and_review(harness)
        check("outside a git work tree an opening is a remark in the log check and a failed lock-committed check, the blind test harness apart",
              rep["status"] == READY and any("not in a commit" in r for r in rep["remarks"])
              and run_checks(study, FACTORY, _posted(study))["lock-committed"] == "fail"
              and run_checks(harness, FACTORY, _posted(harness))["lock-committed"] == "pass")
        check("the scorecard's check for failed openings is named no-failed-opening",
              "no-failed-opening" in run_checks(study, FACTORY) and "clean-opening" not in run_checks(study, FACTORY))

        # a plan that does not say what it appears to say
        study = _fresh(tmp, "n-twice")
        study.plan_path.write_text(study.plan_path.read_text() + "openings_allowed: 1\n")
        check("a plan that gives a key twice is refused", "twice" in _refusal(cmd_check_plan, study, A()))
        unknown = (("anything_at_all", lambda p: p.update(anything_at_all={"a": 1})),
                   ("data.held_out.Pair", lambda p: p["data"]["held_out"].update(Pair="x")),
                   ("tests.held-out.feth", lambda p: p["tests"]["held-out"].update(feth=["x"])),
                   ("rules[r].primary", lambda p: p["rules"][0].update(primary=True)),
                   ("rehearsals[x].recipt", lambda p: p.update(rehearsals=[{"id": "x", "steps": [["true"]], "recipt": "r.json"}])))
        check("unknown keys at the top level, in data.held_out, in a test, in a rule and in a rehearsal each fail the plan check",
              all(any(f"`{key}`" in x for x in plan_problems(f"n-unknown-{i}", change)) for i, (key, change) in enumerate(unknown)))
        study = _fresh(tmp, "n-lock-prints")
        tests(study)
        printed = said(cmd_lock, study, lock())
        check("the lock prints each rule, each criterion with the measured rate beside it, and the openings allowed",
              "supported if gain.ci_low >= 0.9 and gain.ci_high <= 1.1" in printed
              and "criterion power_to_refute_when_false >= 0.8: measured 0.9" in printed
              and "criterion coverage_when_true >= 0.9: measured 0.93" in printed and "openings allowed: held-out 1" in printed)

        def without(name):
            def change(p):
                pe = p["rules"][0]["power_evidence"]
                pe["require"] = [c for c in pe["require"] if c["field"] != name]
            return change

        def waived(p):
            without("coverage_when_true")(p)
            p["rules"][0]["power_evidence"]["waived"] = [{"criterion": "coverage_when_true",
                                                          "reason": "the rule is on a rate with no interval to cover"}]
        check("a rule that leaves out a required criterion fails the plan check",
              all(any(f"required criterion `{n}`" in x for x in plan_problems(f"n-without-{i}", without(n)))
                  for i, n in enumerate(REQUIRED_CRITERIA)))
        study = _fresh(tmp, "n-waived", plan=with_plan(waived))
        tests(study)
        check("and passes when the criterion is waived with a reason, which the lock prints",
              "WAIVED coverage_when_true: the rule is on a rate" in said(cmd_lock, study, lock()))

        def waive(name):
            def change(p):
                without(name)(p)
                p["rules"][0]["power_evidence"]["waived"] = [{"criterion": name, "reason": "this rule cannot be held to it, for a stated reason"}]
            return change
        never = plan_problems("n-waive-power", waive("power_to_refute_when_false"))
        check("the power to refute when the idea is false cannot be waived: it is what shows a rule able to fail",
              any("`power_to_refute_when_false` cannot be waived" in x and "rules[r].power_evidence.waived" in x for x in never))
        check("the other three required criteria can each still be waived with a stated reason",
              NEVER_WAIVED == ("power_to_refute_when_false",)
              and all(plan_problems(f"n-waive-{i}", waive(n)) == []
                      for i, n in enumerate(c for c in REQUIRED_CRITERIA if c not in NEVER_WAIVED)))

        def vacuous(field, op, value):
            def change(p):
                req = p["rules"][0]["power_evidence"]["require"]
                req[:] = [c for c in req if c["field"] != field] + [{"field": field, "op": op, "value": value}]
            return change
        check("a criterion that cannot fail (power at least 0, a rate at most 1) fails the plan check",
              any("cannot fail" in x for x in plan_problems("n-vacuous-power", vacuous("power_to_refute_when_false", ">=", 0.0)))
              and any("cannot fail" in x for x in plan_problems("n-vacuous-rate", vacuous("false_confirm_at_edge_max", "<=", 1)))
              and any("at most" in x for x in plan_problems("n-wrong-way", vacuous("false_confirm_at_edge_max", ">=", 0.5))))

        # the procedure a command read
        doctored = tmp / "doctored-definition"
        shutil.copytree(FACTORY, doctored, ignore=shutil.ignore_patterns("__pycache__"))
        (doctored / "factory.yaml").write_text(re.sub(r"done_when: \[[^\]]*\]", "done_when: [started]", (FACTORY / "factory.yaml").read_text()))
        tree_sha = lambda d: definition_tool().tree_checksum(d)["sha256"]  # noqa: E731
        where = stage_of(study, doctored)
        check("the lock records the definition's checksum, and status says so when it is given another definition",
              study.last("lock.recorded")["data"]["definition"]["sha256"] == tree_sha(FACTORY)
              and where["stage"] == "complete" and where["definition"]["sha256"] == tree_sha(doctored)
              and not where["definition"]["this_factorys_own"] and where["definition"]["same_as_locked"] is False
              and len(where["definition"]["remarks"]) == 2 and stage_of(study, FACTORY)["definition"]["remarks"] == [])
        cmd_scorecard(study, A(factory=str(doctored), anchor=None))
        card = json.loads((study.d / "scorecard.json").read_text())
        check("the scorecard file names the definition it was made with, by path and checksum",
              card["definition"]["path"] == str(doctored) and card["definition"]["sha256"] == tree_sha(doctored)
              and card["definition"]["remarks"])
        check("the scorecard lists openings allowed only for the tests the plan has",
              card["openings_allowed"] == {"held-out": 1} and both == {"held-out": 1, "independent-site": 1})
        before = len(study.events())
        check("a change record on a definition that does not exist is refused",
              _refuses(cmd_log_change, study, A(by="agent:curating", log=str(tmp / "changes-2.jsonl"), factory=str(tmp / "nope"),
                                                problem="p", change="c", rationale="r", predicted="p", observed=None, model=None))
              and len(study.events()) == before and not (tmp / "changes-2.jsonl").exists())

        # the model that wrote each event, and which factory made the study
        study = _fresh(tmp, "n-models")
        Study.default_model = None
        try:
            check("an event an agent writes with no model named is refused, and nothing is written",
                  "names the model that wrote it" in _refusal(cmd_test, study, A(what="known-answers", by="agent:analysis"))
                  and [e["kind"] for e in study.events()] == ["study.started"])
            study.model = "auto"
            check("a router or a stand-in is not a model: `auto` is refused, and so is a name with a space in it",
                  "not a concrete model" in _refusal(cmd_note, study, A(kind="method", about="a", text="b", evidence=None, by="agent:analysis"))
                  and (setattr(study, "model", "some model") or "not a model's name" in _refusal(
                      cmd_note, study, A(kind="method", about="a", text="b", evidence=None, by="agent:analysis"))))
            study.model = None
            cmd_note(study, A(kind="method", about="a", text="a person's note", evidence=None, by="human:tester"))
            check("a person's event needs no model and carries none", "model" not in study.events()[-1])
            study.model = "claude-sonnet-5-5"
            cmd_test(study, A(what="known-answers", by="agent:analysis"))
            cmd_test(study, A(what="working-data", by="agent:analysis"))
            written = study.events()[-1]
            check("an agent's event records the model its caller declared", written["model"] == "claude-sonnet-5-5" and written["actor"] == "agent:analysis")
            forged = study.log.read_text().replace('"model": "claude-sonnet-5-5"', '"model": "claude-opus-5-5"', 1)
            check("the model is under the log's hash: changing it in the file breaks the chain",
                  forged != study.log.read_text() and Study._chain(study, Study._parse(forged)) != [] and study.chain_problems() == [])
            study.model = "a-model-nobody-declared"
            cmd_note(study, A(kind="method", about="b", text="from somewhere else", evidence=None, by="agent:visitor"))
            study.model = None
            cmd_lock(study, A(by="human:tester", evidence=URL))
            bound = study.last("lock.recorded")["data"]
            stamp = definition_tool().stamp(FACTORY)
            check("the lock binds the checksum of the definition tree, the model each agent declares and each skill used by checksum",
                  bound["definition"]["sha256"] == stamp["sha256"] and bound["definition"]["models"] == stamp["models"]
                  and bound["definition"]["skills"] == stamp["skills"] and len(stamp["skills"]) >= 5 and len(stamp["models"]) == 4
                  and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in stamp["skills"].values()))
            check("the lock records which models the log's agent events were written under",
                  bound["models_recorded"] == {"agent:analysis": ["claude-sonnet-5-5"], "agent:visitor": ["a-model-nobody-declared"]})
            where = stage_of(study, FACTORY)
            check("status shows the models the definition declares beside the ones the log recorded, and says they are declared, not proven",
                  where["models"]["declared_by_the_definition"]["review"]["model"] == stamp["models"]["review"]["model"]
                  and where["models"]["recorded_in_the_log"]["agent:analysis"] == ["claude-sonnet-5-5"] and "nothing proves" in where["models"]["note"])
            check("status remarks on an agent that wrote under a model no agent of the definition declares, and on no other",
                  where["models"]["remarks"] == ["agent:visitor wrote under the model `a-model-nobody-declared`, which no agent of this definition declares"])
            cmd_scorecard(study, A(factory=str(FACTORY), anchor=None))
            card = json.loads((study.d / "scorecard.json").read_text())
            check("the scorecard shows the definition's checksum, its declared models, its skills and the models recorded",
                  card["definition"]["sha256"] == stamp["sha256"] and card["definition"]["skills"] == stamp["skills"]
                  and card["models"]["recorded_in_the_log"]["agent:visitor"] == ["a-model-nobody-declared"] and card["definition"]["same_as_locked"] is True)
            other = tmp / "another-definition"
            shutil.copytree(FACTORY, other, ignore=shutil.ignore_patterns("__pycache__"))
            agent_file = other / "agents" / "review" / "agent.md"
            agent_file.write_text(re.sub(r"(?m)^model: .*$", "model: claude-haiku-5-5", agent_file.read_text(), count=1))
            skill_file = other / "skills" / "read-what-is-known" / "SKILL.md"
            skill_file.write_text(skill_file.read_text() + "\nOne more line.\n")
            moved = stage_of(study, other)["definition"]["remarks"]
            check("status says which agent's model and which skill are not what the lock recorded",
                  any("the agent `review` declared" in r and "claude-haiku-5-5" in r for r in moved)
                  and any("the skill `read-what-is-known` is not the skill the lock recorded" in r for r in moved)
                  and not any("the agent `analysis`" in r for r in moved))
            # an agent event with no model, added by hand with the right hash: the chain holds and the log check says so
            ev = study.events()
            body = {"seq": len(ev), "at": now(), "actor": "agent:quiet", "kind": "remark.added", "data": {"text": "written by hand"}}
            with study.log.open("a") as f:
                f.write(json.dumps({**body, "prev": ev[-1]["hash"], "hash": Study._digest(ev[-1]["hash"], body)}, sort_keys=True) + "\n")
            check("an agent event with no model, added by hand with the right hash, fails the log check",
                  study.chain_problems() == [] and any("name no model" in q for q in check_log(study)["problems"])
                  and models_recorded(study.events())["agent:quiet"] == ["none recorded"])
        finally:
            Study.default_model = "selftest-model"
        named = subprocess.run([sys.executable, str(TOOL), "note", "--study", str(tmp / "n-cli-model"), "--by", "agent:x", "--kind", "method",
                                "--about", "a", "--text", "b"], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        check("on the command line an agent with no --model is refused before anything is written",
              named.returncode == 2 and "names the model that wrote it" in named.stderr and not (tmp / "n-cli-model").exists())

        # the finding, the review and the signature
        study = _fresh(tmp, "n-finding")
        _to_lock(study)
        cmd_open_held_out(study, opening())
        cmd_review(study, approve("agent:review"))
        early = check_log(study, _posted(study))["status"]
        cmd_attach(study, finding())
        check("a verdict recorded before the finding does not make the study ready",
              early == NO_FINDING and check_log(study, _posted(study))["status"] == NO_REVIEW
              and not stage_checks(study)[0]["reviewed"] and _refuses(cmd_signature, study, sign(study)))
        cmd_review(study, approve("agent:review"))
        attached = study.d / study.last("finding.attached")["data"]["file"]
        attached.write_text("SUPPORTED: something the receipts do not say")
        rep = check_log(study, _posted(study))
        check("a finding edited after it was attached fails the log check",
              rep["status"] == INVALID and any("finding" in p and "changed" in p for p in rep["problems"]))
        attached.write_text((tmp / "finding.md").read_text())
        cmd_signature(study, sign(study))
        (study.d / "receipts" / "held-out.json").write_text("{}")
        check("closing as signed runs the log check again: a receipt edited after the signature blocks the close",
              "still says it is signed" in _refusal(cmd_close, study, close("practice-ended")))

        # the log is not taken at its word
        study = _fresh(tmp / "by-hand", "study")
        _to_lock(study)
        locked = study.last("lock.recorded")["data"]
        (study.d / "data" / "held-out.json").write_text('{"value": 1.5}')
        (study.d / "receipts" / "held-out.json").write_text(json.dumps(
            {"gain": {"ci_low": 1.46, "ci_high": 1.54}, "data": {"sha256": sha_file(study.d / "data" / "held-out.json")}}))
        op = study.append("agent:x", "opening.started", {"test": "held-out", "n": 1, "plan_sha": locked["plan_sha"], "code": locked["code"],
                                                         "env": {}, "lock_committed": True, "earlier_openings_of_this_window": []})
        openings_path(study).write_text(json.dumps({"dir": study.d.name, "test": "held-out", "started": f"{op['seq']}:{op['hash']}"}) + "\n")
        study.append("agent:x", "opening.finished", {
            "test": "held-out", "n": 1, "fetch_exit": 0, "exit": 0, "receipt": "receipts/held-out.json",
            "receipt_sha": sha_file(study.d / "receipts" / "held-out.json"), "data": "data/held-out.json",
            "data_sha": sha_file(study.d / "data" / "held-out.json"), "fetch_wrote": [], "outcomes": {"r": "supported"},
            "method_declined": None})
        rep = check_log(study)
        check("an opening added to the log by hand, whose receipt the locked rules judge otherwise, fails the log check",
              rep["status"] == INVALID and len(rep["problems"]) == 1 and "under the locked rules" in rep["problems"][0])

        # a system trial
        trial = with_plan(lambda p: (p.update(study_kind="system_trial"), p["data"]["held_out"].update(pair="a blind test case")))
        first, second = _fresh(tmp / "trials", "TRIAL-1", plan=trial), _fresh(tmp / "trials", "TRIAL-2", plan=trial)
        for o in (first, second):
            _to_lock(o)
            open_and_review(o)
        check("a second system trial with the same pair and window beside the first is not exploratory",
              check_log(first, _posted(first))["status"] == READY and check_log(second, _posted(second))["status"] == READY)
        cmd_signature(second, sign(second))
        no_verdict = _refusal(cmd_close, second, close("system-trial-accepted"))
        opened = second.last("opening.finished")["data"]
        second.append("human:tester", "trial.verdict", {"verdict": "WRONG", "data_sha": opened["data_sha"]})
        wrong = _refusal(cmd_close, second, close("system-trial-accepted"))
        check("a system trial cannot close as a finding", "a system trial closes as" in _refusal(cmd_close, second, close("finding-signed")))
        second.append("human:tester", "trial.verdict", {"verdict": "right", "data_sha": "0" * 64})
        check("a verdict of right given on other data than the opening read does not accept the trial",
              _refuses(cmd_close, second, close("system-trial-accepted")) and not second.last("study.closed"))
        second.append("human:tester", "trial.verdict", {"verdict": "right", "data_sha": opened["data_sha"]})
        cmd_close(second, close("system-trial-accepted"))
        check("a system trial closes as accepted only with a verdict in the study log that says the factory was right",
              "verdict" in no_verdict and "not `right`" in wrong and second.last("study.closed")["data"]["outcome"] == "system-trial-accepted")

        # the request
        (tmp / "n-request").mkdir()
        (tmp / "n-request" / "request.md").write_text("If it cannot tell: say so and wait for the next year.\n")
        study = _fresh(tmp, "n-request", start=A(id="STUDY-TEST", question=PLAN["question"], by="agent:coordinating",
                                                 request=str(tmp / "n-request" / "request.md"), asked_by="human:tester"))
        begun = study.events()[0]["data"]
        _to_lock(study)
        open_and_review(study)
        ready = check_log(study, _posted(study))["status"]
        (study.d / "request.md").write_text("If it cannot tell: treat it as supported.\n")
        rep = check_log(study, _posted(study))
        check("start binds the request by checksum, the lock binds it with the plan, and a request changed after the lock fails the log check",
              begun["request"]["file"] == "request.md" and begun["asked_by"] == "human:tester"
              and study.last("lock.recorded")["data"]["request"]["sha"] == begun["request"]["sha"]
              and ready == READY and rep["status"] == INVALID and any("request" in p for p in rep["problems"]))
        check("a study is not started on a question that is not a question",
              _refuses(cmd_start, Study(tmp / "n-not-a-question"), A(id="S", question="no question mark here", by="agent:coordinating")))

        # the plan check speaks in keys, never in Python errors
        guesses = (("rules[r].primary", lambda p: (p["rules"][0].pop("role"), p["rules"][0].update(primary=True))),
                   ("rules[r].power_evidence", lambda p: p["rules"][0].update(power_evidence="receipts/known-answers.json")),
                   ("unknown key `number`", lambda p: p["rules"][0]["supported_if"].__setitem__(
                       0, {"field": "gain.ci_low", "op": ">=", "number": 0.9})),
                   ("`rules`", lambda p: p.update(rules={"r": p["rules"][0]})),
                   ("`tests.held-out`", lambda p: p["tests"].update({"held-out": "toy.py"})),
                   ("{wo}/toy.py", lambda p: p["tests"]["known-answers"]["command"].__setitem__(1, "{wo}/toy.py")))
        answers = [plan_problems(f"n-guess-{i}", change) for i, (_, change) in enumerate(guesses)]
        check("the plan check names the key and what it accepts for a natural wrong guess, and never shows a Python error",
              all(any(key in x for x in got) for (key, _), got in zip(guesses, answers))
              and not any("Error" in x or "object has no attribute" in x for got in answers for x in got))
        study = _fresh(tmp, "n-bare-names", plan=with_plan(lambda p: p.update(code=["toy.py"])))
        os.chdir(elsewhere)
        try:
            _to_lock(study)
        finally:
            os.chdir(was)
        check("code listed by bare file name is read from the study directory, so the lock finds it wherever the tool is called from",
              study.last("lock.recorded")["data"]["code"]["toy.py"] == sha_file(study.d / "toy.py"))
        template = REPO / "factory" / "templates" / "analysis-plan.yaml"
        if template.is_file():
            study = Study(tmp / "n-template")
            cmd_start(study, A(id="STUDY-0002", question="Is it?", by="agent:coordinating"))
            shutil.copyfile(template, study.plan_path)
            before_scripts = check_plan(study.plan(), study)
            for _, argv in Study.commands(study.plan()):  # the scripts the template names are the scientist's to write
                script = study.word(launch(argv)[1], study.plan())
                script.parent.mkdir(parents=True, exist_ok=True)
                script.write_text("")
            check("the analysis-plan template passes the plan check as written", check_plan(study.plan(), study) == [])
            check("and before its scripts are written, the only problems the plan check finds in the template are the scripts that are not files yet",
                  len(before_scripts) == len(Study.commands(study.plan())) and all("is not a file" in x for x in before_scripts))

        # paths a plan may not write to, and where the change log may live
        check("a receipt path that names the study log, the plan or a note fails the plan check",
              all(any("cannot write there" in x for x in plan_problems(
                  f"n-protected-{i}", lambda p, r=r: p["tests"]["working-data"].update(receipt=r)))
                  for i, r in enumerate(("study-log.jsonl", "analysis-plan.yaml", "notes/NOTE-001.json"))))
        study = _fresh(tmp, "n-change-log")
        innocent = tmp / "innocent.jsonl"
        shutil.copyfile(_fresh(tmp, "n-other-study").log, innocent)

        def change_to(path):
            return A(by="agent:curating", log=str(path), factory=str(FACTORY), problem="p", change="c", rationale="r",
                     predicted="p", observed=None, model=None)
        (tmp / "a-new-record").mkdir()
        (tmp / "a-new-record" / "openings.jsonl").touch()  # empty, so only its name says what it is
        check("the change log cannot be the record of what has been opened, nor a study log under another name",
              _refuses(cmd_log_change, study, change_to(tmp / "openings.jsonl"))
              and "record of what has been opened" in _refusal(cmd_log_change, study, change_to(tmp / "a-new-record" / "openings.jsonl"))
              and (tmp / "a-new-record" / "openings.jsonl").read_text() == ""
              and "study log" in _refusal(cmd_log_change, study, change_to(innocent))
              and len(innocent.read_text().splitlines()) == 1)
        check("a change log that cannot be written leaves no event in the study log",
              "could not be written" in _refusal(cmd_log_change, study, change_to(tmp / "no-such-folder" / "changes.jsonl"))
              and not study.last("change.recorded"))

        # two openings at once
        study = _fresh(tmp, "n-at-once")
        _to_lock(study)
        plan = checked_plan(study)
        with study.held() as f:
            other = subprocess.Popen([sys.executable, str(TOOL), "open-held-out", "--study", str(study.d), "--by", "agent:second", "--model", "selftest-model"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, stdin=subprocess.DEVNULL)
            time.sleep(1.5)
            waiting = other.poll() is None and not any(e["kind"] == "opening.started" for e in study.events())
            start_opening(study, plan, "held-out", "agent:first", f)
        _, err = other.communicate(timeout=120)
        check("two openings asked for at the same moment: the second waits for the study log and finds the opening used up",
              waiting and other.returncode == 2 and "used up" in err
              and sum(e["kind"] == "opening.started" for e in study.events()) == 1)

        # the study tool itself changes
        study = _fresh(tmp, "n-tool-changed")
        _to_lock(study)
        changed = tmp / "sf-with-a-comment.py"
        changed.write_text(TOOL.read_text() + "\n# a comment\n")
        real = TOOL
        globals()["TOOL"] = changed
        try:
            refused_before = _refuses(cmd_open_held_out, study, opening()) and check_log(study)["status"] == INVALID
        finally:
            globals()["TOOL"] = real
        open_and_review(study)
        globals()["TOOL"] = changed
        try:
            rep = check_log(study, _posted(study))
        finally:
            globals()["TOOL"] = real
        check("before an opening a changed study tool blocks it; after the opening the log check gives a remark naming both checksums",
              refused_before and rep["status"] == READY
              and any(sha_file(changed) in r and sha_file(real) in r for r in rep["remarks"]))

        # smaller things from the same review
        real_data = with_plan(lambda p: p["tests"]["held-out"].update(
            data="data/real.json", fetch=["{python}", "{study}/toy.py", "fetch", "{study}/data/real.json"],
            command=["{python}", "{study}/toy.py", "held-out", "{study}/receipts/held-out.json", "{study}/data/real.json"]))
        study = _fresh(tmp, "n-early-data", plan=real_data)
        (study.d / "data" / "real.json").write_text('{"value": 1.0}')
        check("held-out data sitting at a test's own data path before its opening stops the tests",
              "before any opening" in _refusal(cmd_test, study, A(what="known-answers", by="agent:b")))
        study = _fresh(tmp, "n-actors")
        tests(study, by="agent:runner")
        cmd_lock(study, lock())
        unnamed = _fresh(tmp, "n-unnamed-opener")
        _to_lock(unnamed)
        check("an opening asked for under a name that is neither human:<id> nor agent:<id> is refused before anything is opened",
              "the actor is" in _refusal(cmd_open_held_out, unnamed, A(test="held-out", by="nobody"))
              and not unnamed.last("opening.started") and not (unnamed.d / "data" / "held-out.json").exists())
        check("the assistant that ran the tests cannot open the held-out data, whatever the case of its name",
              "access gate" in _refusal(cmd_open_held_out, study, opening("agent:runner"))
              and _refuses(cmd_open_held_out, study, opening("agent:Runner")))
        cmd_open_held_out(study, opening("agent:opener"))
        cmd_attach(study, finding("agent:writer"))
        check("an actor differing only in case from one that ran the tests cannot review, nor can the one who attached the finding",
              _refuses(cmd_review, study, approve("agent:Runner")) and _refuses(cmd_review, study, approve("agent:writer"))
              and _refuses(cmd_review, study, approve("human:tester")) and not _refuses(cmd_review, study, approve("agent:review")))
        cmd_note(study, A(kind="method", about="recipes/x.md", text="the words of the note", evidence=None, by="agent:review"))
        (study.d / "notes" / "NOTE-001.json").unlink()
        cmd_curation_list(study, A())
        listed = json.loads((study.d / "curation-list.json").read_text())["by_subject"]["recipes/x.md"][0]
        check("a note whose file is deleted keeps its words: the curation list restores them from the study log",
              listed["text"] == "the words of the note" and "restored" in listed
              and any("NOTE-001" in r and "keeps its words" in r for r in check_log(study)["remarks"]))

        # the system trial's own pieces, when the gain method ships with the tool
        kit = REPO / "methods" / "gain"
        if (kit / "system_trial.py").is_file() and (kit / "test_cases.py").is_file():
            sealed = subprocess.run([sys.executable, str(kit / "system_trial.py"), "seal", "--out", str(tmp / "seal" / "case.json"),
                                     "--answer", str(tmp / "seal" / "answer.json")], capture_output=True, text=True,
                                    env={**os.environ, "SF_SYSTEM_TRIAL_SEAL": "5:0.9", "BLIND_TEST_SEAL": "5:0.9"})
            case_text = (tmp / "seal" / "case.json").read_text() if sealed.returncode == 0 else "{}"
            case = json.loads(case_text)
            answer = json.loads((tmp / "seal" / "answer.json").read_text()) if sealed.returncode == 0 else {}
            check("the seal ignores a seed and a gain passed through the environment unless its command carries --harness",
                  sealed.returncode == 0 and answer.get("sealed", {}).get("by") == "operating-system entropy at the opening"
                  and answer.get("put_in", {}).get("seed") != 5)
            check("a sealed blind test case holds no trace of what was put in; the answer is a separate file tied to it by checksum",
                  "put_in" not in case_text and '"gain"' not in case_text and '"seed"' not in case_text
                  and case.get("sealed", {}).get("answer_sha256") == sha_file(tmp / "seal" / "answer.json")
                  and "gain" in answer.get("put_in", {}))
            blind = with_plan(lambda p: (p.update(study_kind="system_trial", roots={"kit": str(kit)}), p["tests"].update({"held-out": {
                "fetch": ["{python}", "{kit}/system_trial.py", "seal", "--harness", "--out", "{study}/data/held-out.json",
                          "--answer", "{study}/sealed/answer.json"],
                "command": ["{python}", "{study}/toy.py", "blind", "{study}/receipts/held-out.json", "{study}/data/held-out.json"],
                "receipt": "receipts/held-out.json", "writes": ["sealed/answer.json"],
                "passes_environment": ["BLIND_TEST_SEAL"]}})))
            study = _fresh(tmp / "blind", "TRIAL", plan=blind)
            _to_lock(study)
            os.environ["BLIND_TEST_SEAL"] = "5:0.9"
            try:
                open_and_review(study)
            finally:
                del os.environ["BLIND_TEST_SEAL"]
            receipt = json.loads((study.d / "receipts" / "held-out.json").read_text())
            check("a method that looks for the answer in what it is given finds nothing",
                  receipt["answer_seen"] is False and study.last("opening.finished")["data"]["outcomes"] == {"r": "supported"}
                  and json.loads((study.d / "sealed" / "answer.json").read_text())["put_in"]["gain"] == 0.9)
            cmd_signature(study, sign(study))
            answer_file = study.d / "sealed" / "answer.json"
            kept_answer = answer_file.read_text()
            answer_file.write_text(kept_answer.replace('"gain": 0.9', '"gain": 1.0'))
            edited = check_log(study, _posted(study))
            answer_file.write_text(kept_answer)
            check("the sealed answer is bound by the opening too: changed afterwards, the log check fails",
                  kept_answer != answer_file.read_text().replace('"gain": 0.9', '"gain": 1.0') and edited["status"] == INVALID
                  and any("sealed/answer.json" in x for x in edited["problems"]) and check_log(study)["status"] == SIGNED)
            verdict = [sys.executable, str(kit / "system_trial.py"), "verdict", "--study", str(study.d), "--by", "human:tester"]
            one = subprocess.run(verdict, capture_output=True, text=True, env=dict(os.environ))
            event = study.last("trial.verdict")
            data = study.d / "data" / "held-out.json"
            data.write_text(data.read_text().replace("the blind test harness", "operating-system entropy at the opening"))
            two = subprocess.run(verdict, capture_output=True, text=True, env=dict(os.environ))
            check("system_trial.py verdict writes its verdict to the study log, and refuses once the sealed data is edited",
                  one.returncode == 1 and event is not None and event["data"]["verdict"].startswith("void")
                  and two.returncode == 2 and "REFUSED" in two.stderr
                  and sum(e["kind"] == "trial.verdict" for e in study.events()) == 1)

        # the known-answer tests' own check, when the gain method ships with the tool
        if (kit / "known_answer_tests.py").is_file() and (kit / "confront.py").is_file() and (kit / "test_cases.py").is_file():
            own = subprocess.run([sys.executable, str(kit / "known_answer_tests.py"), "--selftest"], capture_output=True, text=True,
                                 env=dict(os.environ), stdin=subprocess.DEVNULL)
            check("the known-answer tests run the method in a process of its own that is given only the data: a method that searches "
                  "its process for the answer finds nothing, and an input that carries the answer is refused "
                  "(known_answer_tests.py --selftest)",
                  own.returncode == 0 and "PASS  a method that looks for the answer in its own process finds nothing" in own.stdout
                  and "PASS  the same search, run in this process where the truth is kept, finds" in own.stdout
                  and "PASS  the method refuses an input that carries what was put in" in own.stdout
                  and "FAIL" not in own.stdout)

    def parses(words: list) -> bool:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                build_parser().parse_args(words)
        except SystemExit:
            return False
        return True

    check("an option is taken only when it is spelled out: `--b` is not `--by` and `--stud` is not `--study`, so a check that "
          "reads a command before it runs sees the options the tool will",
          parses(["note", "--study", "s", "--by", "agent:x", "--kind", "missing", "--about", "a", "--text", "b"])
          and not parses(["note", "--study", "s", "--b", "human:someone", "--kind", "missing", "--about", "a", "--text", "b"])
          and not parses(["note", "--study", "s", "--b=human:someone", "--kind", "missing", "--about", "a", "--text", "b"])
          and not parses(["status", "--stud", "s"]) and not parses(["lock", "--study", "s", "--by", "human:x", "--evid", URL]))
    with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
        _selftest_fence_and_acts(Path(t).resolve(), check)
    kept = os.environ.pop("SF_INSIDE_A_LOOK", None)
    try:
        outside = started_from_a_look() is None and not _refuses(refuse_inside_a_look)
        os.environ["SF_INSIDE_A_LOOK"] = "EXPLORATION-T"
        check("a command started from inside a look is refused, and one started outside a look is not",
              outside and "inside a look" in _refusal(refuse_inside_a_look))
    finally:
        os.environ.pop("SF_INSIDE_A_LOOK", None)
        if kept is not None:
            os.environ["SF_INSIDE_A_LOOK"] = kept
    Study.default_model = None
    for name, ok in results:
        print(("PASS  " if ok else "FAIL  ") + name)
    good = all(ok for _, ok in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
    return 0 if good else 1


def started_from_a_look() -> str | None:
    """What says this process was started by a script the tools ran (a look, or a command of a plan: a test, a
    rehearsal step, a fetch, the opening's analysis), or None. Such a script runs on data and nothing else: one
    that could call a tool of this package would act under any name it liked, a review of its own lead or a lock
    included. The reading is in tools/fence.py (`started_under`): a mark in the environment, which a script can
    take off, and the process's ancestry, which it cannot."""
    return fence.started_under()


def refuse_inside_a_look() -> None:
    why = started_from_a_look()
    if why:
        raise Refused(f"this command was started from inside a look or a step of a plan ({why}). A script the tools run works on "
                      "data; it does not call the tools of this package, and nothing it leaves running does either. Each tool is "
                      "called by a role, under its own name, outside any look and any step")


def build_parser() -> argparse.ArgumentParser:
    """Every command and every option, spelled out. No abbreviation is taken (`--b` is not `--by`): a check that
    reads a command before it runs must see the same options the tool will."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *args):
        p = sub.add_parser(name, allow_abbrev=False)
        p.add_argument("--study", required=True, help="the study directory")
        if by in args and not any(names == ["--model"] for names, _ in args):
            args = (*args, model)
        for names, kw in args:
            p.add_argument(*names, **kw)
        p.set_defaults(fn=fn)

    by = (["--by"], {"required": True, "help": "who acts: human:<id> or agent:<id>"})
    model = (["--model"], {"default": None, "help": "the model that acts, when an agent does: required with --by agent:<id>, declared "
                                                    "by the caller and recorded in the event; a person's event needs none"})
    anchor = (["--anchor"], {"action": "append", "default": None,
                             "help": "SEQ:HASH, a log fingerprint posted outside the workspace; repeatable"})
    evidence = (["--evidence"], {"default": None, "help": "https URL, host name and all, of the person's approving review or comment"})
    proc = (["--factory"], {"default": str(FACTORY), "help": "the factory's definition, a folder rooted at factory.yaml (default: factory/, this factory's own)"})
    comment = (["--comment"], {"default": None, "help": "free text kept with the event"})
    held_out = (["--test"], {"default": "held-out", "help": "which test on held-out data (default: held-out)"})
    add("start", cmd_start, (["--id"], {"required": True}), (["--question"], {"required": True}), by,
        (["--request"], {"default": None, "help": "the request this study answers; bound by checksum, and by the lock with the plan"}),
        (["--asked-by"], {"default": None, "dest": "asked_by", "help": "the person who asked, as human:<id>"}))
    add("check-plan", cmd_check_plan)
    add("test", cmd_test, (["what"], {"help": "known-answers or working-data"}), by)
    add("rehearse", cmd_rehearse, (["--id"], {"required": True}), by)
    practice = (["--local-practice"], {"action": "store_true", "dest": "local_practice",
                                       "help": "practice mode: record this act from the command line, with no pull request. For trying "
                                               "the tools out; the study says so everywhere and never closes as a signed finding"})
    record_merge = (["--record-merge"], {"default": None, "dest": "record_merge", "metavar": "COMMIT",
                                         "help": "record this act from the merge commit of its approved pull request (run by the job that follows the merge)"})
    platform_rec = (["--platform-record"], {"default": None, "dest": "platform_record",
                                            "help": "the JSON file the recording job wrote from the platform's record of the pull request"})
    add("request-lock", cmd_request_lock, by, proc)
    add("request-signature", cmd_request_signature, by, proc, anchor, (["--decision"], {"required": True, "help": "signed or declined"}))
    add("check-request", cmd_check_request, proc, (["--act"], {"required": True, "help": "lock or signature"}))
    add("lock", cmd_lock, by, evidence, proc, practice, record_merge, platform_rec)
    add("open-held-out", cmd_open_held_out, held_out, by, proc, practice)
    add("held-out-change", cmd_held_out_change, by, (["--reason"], {"required": True, "help": "why what is held out changed; the lock shows it"}))
    add("void-unread", cmd_void_unread, held_out, by, evidence, (["--reason"], {"required": True}))
    add("review", cmd_review, by, (["--verdict"], {"required": True}), (["--file"], {"required": True}))
    add("attach", cmd_attach, by, (["--file"], {"required": True}))
    add("signature", cmd_signature, by, evidence, anchor, comment, proc, practice, record_merge, platform_rec,
        (["--decision"], {"default": None, "help": "signed or declined; a recorded merge takes it from the merged request"}))
    add("note", cmd_note, by, (["--kind"], {"required": True}), (["--about"], {"required": True}),
        (["--text"], {"required": True}), (["--evidence"], {"default": None}))
    add("curation-list", cmd_curation_list)
    add("resolve", cmd_resolve, by, comment, (["--note"], {"required": True, "help": "the note's id, such as NOTE-001"}),
        (["--disposition"], {"required": True}), (["--ref"], {"default": None}))
    add("close", cmd_close, by, comment, anchor, (["--outcome"], {"required": True}), (["--cite"], {"default": None}))
    add("status", cmd_status, proc)
    add("fingerprint", cmd_fingerprint)
    add("check-log", cmd_check_log, anchor,
        (["--change-log"], {"default": None, "dest": "change_log", "help": "the change log, to check this study's change records against"}))
    add("scorecard", cmd_scorecard, proc, anchor)
    add("log-change", cmd_log_change, by, proc, (["--log"], {"required": True, "help": "the path of the change log"}),
        (["--problem"], {"required": True}), (["--change"], {"required": True}), (["--rationale"], {"required": True}),
        (["--predicted"], {"required": True}), (["--observed"], {"default": None}), (["--model"], {"default": None}))
    sub.add_parser("selftest", allow_abbrev=False)
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        refuse_dirty_environment()  # every command, the selftest included
        refuse_inside_a_look()
        if a.cmd == "selftest":
            return selftest()
        study = Study(a.study)
        study.model = getattr(a, "model", None)
        if str(getattr(a, "by", "")).startswith("agent:") and not study.model:
            raise Refused(NO_MODEL)  # said before anything is run or written
        a.fn(study, a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, AttributeError, OSError) as e:  # malformed files are refusals, not crashes
        print("REFUSED: a file in the study is malformed or missing, and the tool could not read it. Run check-plan, then "
              f"check-log, to find which (for whoever maintains the tool: {type(e).__name__}: {e})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
