#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""check_factory: is this folder a science factory's definition, and what
did a change to it change?

A science factory is defined as code: a folder of YAML and Markdown files
rooted at `factory.yaml`. This tool reads such a folder and gives one of
three results. It runs no language model and it edits nothing.

  valid          exit 0   every rule below holds
  invalid        exit 1   at least one rule is broken; each is printed
  not validated  exit 2   the tool could not tell: the folder or a file in
                          it cannot be read, the schema version is one this
                          tool does not know, a git ref a benchmark names
                          cannot be looked up here. This is never a pass.

The tree it reads (the path is the name: a resource is called what its
folder or file is called, and nothing inside a file can rename it):

  factory.yaml                        identity, defaults, the procedure, the two acts by people
  agents/<name>/agent.md              one agent: settings and permissions in front matter, instructions in the body
  agents/<name>/skills/<skill>/       a skill that agent alone uses
  skills/<skill>/SKILL.md             a skill two or more agents use
  harnesses/<name>/harness.yaml       what starts an agent, and the models it can start
  runners/<name>.yaml                 where a job computes
  scorers/<name>/scorer.md            one check: deterministic (the tool works it out) or a judge (a rubric for a model)
  benchmarks/<suite>/suite.yaml       a blind test suite; its cases in cases/<case>.yaml
  automations/<name>/automation.md    what would start work without a person (declared; no trigger is built)
  templates/, checkers.yaml, change-log.jsonl

The rules, by name (the name is printed with each broken rule):

  form        the schema version is known; every key is a key this schema
              has (an unknown key is refused, and so is a key given twice);
              every file sits at a path of the tree above; names are lower
              case words joined by hyphens; nothing is a symlink
  references  everything named resolves to a file: an agent's harness,
              model (one the harness lists; a concrete model, never a
              router and never `auto`) and runner; the coordinator; who
              does each stage; each stage's checks and each deterministic
              scorer's check (names the study tool can evaluate); a
              scorer's agents and a judge's model; a benchmark's
              configurations and cases; a runner's contract (the twelve
              keys factory.yaml lists); a pinned checker's checksum
  roles       the agent files, the procedure's `agents` block and the
              skills say the same thing (every rule of check_roles.py)
  acts        the acts by people are exactly the stages people do, and no
              agent may call them
  skills      a skill's name is used once; a skill in an agent's own
              folder is named by that agent; a shared skill is named by
              two agents or more
  firewall    every scorer declares what it reads, from a fixed list of
              kinds of material; a judge reads nothing written after an
              opening of held-out data; no scorer that reads such material
              may carry `selfImprovement: true`; a benchmark case is a
              planted truth on synthetic data or on observation metadata,
              never real held-out data
  acceptance  an acceptance suite keeps no case and no seed in the
              definition, shares no case with a design suite, and every
              agent's `must_never_see` lists what the suite says must
              never be seen
  automations an automation is marked not wired and starts only a stage
              that agents do before the lock

What it cannot check is printed with every result: who really merged a
lock, which model really answered (a model is declared, by the definition
and by whoever calls the tools, and nothing proves it), whether a person
read a finding and then edited a prompt by hand, and whether the files a
harness rendered are up to date (that harness's own `--check` says).

Usage:
  check_factory.py [ROOT] [--repository DIR]     validate (ROOT defaults to the `factory/` folder beside tools/)
  check_factory.py --summary OLD NEW             what changed between two definition trees, in plain words;
                                                 a tree is a folder, or git:<ref>:<path> for a folder at a git ref
  check_factory.py --checksum [ROOT]             the checksum of the definition tree, as the lock binds it
  check_factory.py --selftest                    every rule, with a definition that breaks it
"""
import sys

sys.dont_write_bytecode = True  # the tool loads check_roles.py from beside it and leaves no bytecode folder
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tarfile  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCHEMAS = ("science-factory/v1alpha1",)
NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{1,99}$")
NOT_A_MODEL = ("auto", "router", "routers/", "inherit", "default", "none", "unknown", "model", "any")
SHA = re.compile(r"^[0-9a-f]{64}$")

# What a stage's `done_when` may name, and the checks a deterministic scorer may name: the study tool evaluates
# exactly these (sf.py tests that the two lists and its own are the same).
STAGE_CHECKS = ("started", "plan-complete", "tests-pass", "rehearsals-pass", "locked", "openings-complete", "finding-attached",
                "reviewed", "steward-decided", "notes-resolved", "closed")
SCORER_CHECKS = ("log-checks-out", "not-exploratory", "openings-within-allowed", "no-failed-opening", "lock-committed-before-opening",
                 "review-recorded", "acts-recorded-by-people", "notes-on-curation-list")
BEFORE_THE_LOCK = ("started", "plan-complete", "tests-pass", "rehearsals-pass")  # the checks of the stages an automation may start

# The firewall's fixed list: the kinds of material a scorer may say it reads. The line between the two halves is
# the first opening of held-out data in a study: what was written before it, and what was written from it on.
MATERIAL = {
    "request": "the scientist's request, as bound when the study or exploration started",
    "plan": "the analysis plan, as the lock bound it (or as it stands, in a study nothing has been opened in)",
    "known-answer-tests": "the receipts of the known-answer tests, the working data and the rehearsals, as run before any opening",
    "pre-lock-log": "the study log up to the first opening of held-out data: the start, the tests, the rehearsals, the lock",
    "exploration-log": "an exploration's log: what was set aside, every look, every choice",
    "lead": "an exploration's lead, as recorded",
    "review-before-opening": "a review recorded before any opening: of a lead, or of a plan",
    "transcript-before-opening": "what an agent was asked and answered, kept by a harness, finished before any opening",
}
POST_OPENING = {
    "opening-outcome": "what an opening of held-out data produced: its receipt and how each rule came out",
    "finding": "the written finding",
    "post-opening-log": "the study log from the first opening on: openings, the finding, reviews, the signature, the close",
    "review-after-opening": "a review recorded after an opening",
    "transcript-after-opening": "what an agent was asked and answered after an opening",
}
CANNOT_CHECK = (
    "who really merged a lock or signed: names are typed, and the repository's own rules say who merged",
    "which model really answered: a model is declared by the definition and by whoever calls the tools, never proven",
    "whether a person or an agent read a finding and then changed a prompt by hand: the firewall covers scorers, judges and what feeds a proposal",
    "whether an agent can reach the acceptance set by another road: `must_never_see` is instruction, and a harness's per-call check when a platform calls it",
    "whether the files a harness rendered are up to date: run that harness's own check (factory/harnesses/claude-code/render.py --check)",
)


class NotValidated(Exception):
    """The tool could not tell. Never a pass."""


# ---------------------------------------------------------------- reading
class _NoDuplicateKeys(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    seen = set()
    for k, _ in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in seen:
            raise yaml.YAMLError(f"the key `{key}` is given twice")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_NoDuplicateKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_yaml(text: str):
    return yaml.load(text, Loader=_NoDuplicateKeys)


def front_matter(text: str) -> tuple:
    """(front matter as a mapping, body). Raises ValueError when there is none that parses."""
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end < 0:
        raise ValueError("no front matter (the file begins with `---`, the settings, then `---`)")
    fm = load_yaml(text[4:end])
    if not isinstance(fm, dict):
        raise ValueError("the front matter is not a mapping")
    return fm, text[end + 5:]


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def files_of(root: Path) -> list:
    """Every file of the tree, as paths from the root, sorted. Bytecode folders are no part of a definition."""
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if (p.is_file() or p.is_symlink()) and "__pycache__" not in p.parts and p.suffix != ".pyc")


def tree_checksum(root: Path) -> dict:
    """The checksum of a definition tree: every file by path and sha256, except the change log, which is a record
    about the definition and grows after each change is tried."""
    root = Path(root).resolve()
    listed = [(rel, sha_bytes((root / rel).read_bytes())) for rel in files_of(root) if rel != "change-log.jsonl"]
    return {"sha256": sha_bytes(json.dumps(listed, separators=(",", ":")).encode()), "files": len(listed)}


def skill_dirs(root: Path) -> dict:
    """{skill name: (scope, folder)}; scope is `shared` or the agent whose own skill it is. A name used twice keeps
    the first and is reported by the validator."""
    out = {}
    for scope, base in [("shared", root / "skills")] + [(a.name, a / "skills") for a in sorted((root / "agents").glob("*")) if a.is_dir()]:
        if base.is_dir():
            for d in sorted(q for q in base.iterdir() if q.is_dir()):
                out.setdefault(d.name, (scope, d))
    return out


def skill_checksums(root: Path) -> dict:
    """Each skill of the tree by the checksum of everything in its folder, with whose it is."""
    root = Path(root).resolve()
    out = {}
    for name, (scope, d) in skill_dirs(root).items():
        listed = [(rel, sha_bytes((d / rel).read_bytes())) for rel in files_of(d)]
        out[name] = {"scope": scope, "sha256": sha_bytes(json.dumps(listed, separators=(",", ":")).encode())}
    return out


def agents_of(root: Path) -> dict:
    """{agent: front matter} for every agent file that parses."""
    out = {}
    for f in sorted((Path(root) / "agents").glob("*/agent.md")):
        try:
            out[f.parent.name] = front_matter(f.read_text(encoding="utf-8"))[0]
        except (ValueError, yaml.YAMLError, OSError):
            continue
    return out


def declared_models(root: Path) -> dict:
    """What each agent's definition declares: its harness, its model and its runner, after the defaults. Declared,
    never proven."""
    root = Path(root).resolve()
    try:
        defaults = load_yaml((root / "factory.yaml").read_text(encoding="utf-8")).get("agentDefaults") or {}
    except (OSError, yaml.YAMLError, AttributeError):
        defaults = {}
    out = {}
    for name, fm in agents_of(root).items():
        out[name] = {k: fm.get(k, defaults.get(k)) for k in ("harness", "model", "runner")}
        out[name]["skills"] = sorted(str(c)[6:] for c in fm.get("may_call") or [] if str(c).startswith("skill:"))
    return out


def stamp(root: Path) -> dict:
    """Which factory this is, for a lock or a status line: the tree's checksum, the version it gives itself, the
    models its agents declare and the skills they use by checksum."""
    root = Path(root).resolve()
    try:
        spec = load_yaml((root / "factory.yaml").read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise NotValidated(f"the definition at {root} has no factory.yaml that can be read ({e})")
    if not isinstance(spec, dict):
        raise NotValidated(f"{root / 'factory.yaml'} is not a mapping")
    tree = tree_checksum(root)
    models = declared_models(root)
    used = sorted({s for m in models.values() for s in m["skills"]})
    sums = skill_checksums(root)
    return {"sha256": tree["sha256"], "files": tree["files"], "name": spec.get("name"), "version": spec.get("version"),
            "schemaVersion": spec.get("schemaVersion"),
            "models": {a: {k: m[k] for k in ("harness", "model")} for a, m in models.items()},
            "skills": {s: sums[s]["sha256"] for s in used if s in sums}}


# ---------------------------------------------------------------- the schema
# A spec is a type, a list of one spec, ("one", values), ("map", spec) for a mapping with free keys, or a mapping
# of keys to specs, where a key ending in `!` is required. Unknown keys are refused.
TEXT, NUMBER, WHOLE, FLAG, ANY = "text", "number", "whole number", "true or false", "anything"
STRINGS = [TEXT]
FACTORY = {
    "schemaVersion!": TEXT, "name!": TEXT, "version!": TEXT, "description!": TEXT, "alias": TEXT, "product": TEXT, "by_products": STRINGS,
    "capability": {"name!": TEXT, "repositories!": STRINGS, "borrows": [ANY], "stewards": TEXT, "holds": ("map", TEXT),
                   "shared_across_factories": STRINGS, "not_yet_shared": TEXT},
    "agentDefaults!": {"harness!": TEXT, "model!": TEXT, "runner!": TEXT},
    "procedure!": {
        "coordinator!": TEXT, "study_kinds": ("map", TEXT),
        "request": {"fields": STRINGS, "questions_back": TEXT, "ways_to_hold_data_out": STRINGS},
        "people": ("map", TEXT),
        "agents!": ("map", {"does!": TEXT, "may_not": TEXT, "must": TEXT, "never_sees": STRINGS, "runs": TEXT}),
        "separations": ("map", {"rule!": TEXT, "held_by!": TEXT, "not_held_by_the_tool": TEXT}),
        "stages!": [{"id!": TEXT, "done_by!": ANY, "done_when!": STRINGS, "does!": TEXT, "ends_early_when": STRINGS}],
        "acts_by_people!": ("map", {"who!": STRINGS, "command!": TEXT, "evidence!": TEXT, "not_held_by_the_tool": TEXT}),
        "rules_for_people": STRINGS},
    "where_it_runs": {"default!": TEXT, "tests": TEXT, "opening_held_out_data": TEXT},
    "runner_contract!": {"keys!": ("map", TEXT), "rules_for_every_runner": STRINGS},
    "measure": {"scorecard": TEXT, "judges": TEXT, "blind_test_of_the_system": TEXT,
                "improving_the_procedure": {"rule": TEXT, "change_log": TEXT, "firewall": TEXT, "later": TEXT}},
}
AGENT = {"description!": TEXT, "harness": TEXT, "model": TEXT, "runner": TEXT, "may_call!": STRINGS, "must_never_see!": STRINGS,
         "reads!": STRINGS, "writes!": STRINGS, "hands_on!": [{"what!": TEXT, "to!": TEXT}]}
HARNESS = {"description!": TEXT, "starts!": TEXT, "models!": ANY, "status!": ("one", ("built", "built, not exercised", "specified")),
           "holds": STRINGS, "by_instruction_only": STRINGS}
RUNNER = {"description!": TEXT, "platform": {"os!": TEXT, "arch!": TEXT, "linux": {"dockerImage!": TEXT}},
          "status!": ("one", ("built", "specified")), "basis!": TEXT, "for!": STRINGS, "contract!": ("map", TEXT), "open_questions!": STRINGS}
SCORER = {"description!": TEXT, "type!": ("one", ("deterministic", "judge")), "check": TEXT, "reads!": STRINGS, "selfImprovement!": FLAG,
          "agents": STRINGS, "labels": [{"value!": TEXT, "score!": NUMBER, "description": TEXT}], "passingScore": NUMBER,
          "samplingRate": NUMBER, "model": TEXT, "harness": TEXT, "applies_to": ("one", ("study", "exploration"))}
DEFINITION_REF = {"path": TEXT, "ref": TEXT}
SUITE = {
    "name!": TEXT, "description!": TEXT, "set!": ("one", ("design", "acceptance")),
    "target!": {"procedure!": ("one", ("confirming",)), "method!": TEXT, "plan!": TEXT},
    "configurations!": [{"name!": TEXT, "definition!": DEFINITION_REF}], "repetitions!": WHOLE, "known_answer_cases": WHOLE,
    "cases": STRINGS,
    "generated": {"count!": WHOLE, "truths!": [NUMBER], "seed!": {"env!": TEXT}, "kept": TEXT},
    "must_never_see": STRINGS,
    "comparison!": {"stated!": TEXT, "baseline!": TEXT, "candidate!": TEXT, "primary!": ("one", ("wrong_verdicts", "false_support_rate", "missed_true_rate")),
                    "margin!": NUMBER, "alpha!": NUMBER, "must_not_be_worse!": [("one", ("wrong_verdicts", "false_support_rate", "missed_true_rate"))],
                    "noise": TEXT},
}
CASE = {"title!": TEXT,
        "sampling!": {"kind!": TEXT, "generator!": TEXT, "seed!": WHOLE, "from": TEXT},
        "truth!": {"quantity!": TEXT, "planted!": NUMBER, "planted_by!": TEXT, "the_idea_is_true!": FLAG},
        "seal!": {"where!": TEXT, "opened_by!": TEXT},
        "tags": STRINGS}
AUTOMATION = {"description!": TEXT, "wired!": FLAG, "stage!": TEXT, "agent": TEXT,
              "triggers!": [{"provider!": ("one", ("schedule", "github", "webhook", "factory")), "event!": TEXT, "filter": ("map", ANY),
                             "schedule": {"name!": TEXT, "cron!": TEXT}}],
              "idempotency": STRINGS}
CHECKERS = {"checkers!": [{"name!": TEXT, "what!": TEXT, "from": TEXT, "path": TEXT, "sha256!": TEXT}]}


def conforms(obj, spec, where: str) -> list:
    """Every way `obj` does not have the form `spec` says, in words."""
    if spec == ANY:
        return []
    if spec == TEXT:
        return [] if isinstance(obj, str) and obj.strip() else [f"{where}: is text, and not empty"]
    if spec == NUMBER:
        return [] if isinstance(obj, (int, float)) and not isinstance(obj, bool) else [f"{where}: is a number"]
    if spec == WHOLE:
        return [] if isinstance(obj, int) and not isinstance(obj, bool) and obj >= 1 else [f"{where}: is a whole number, one or more"]
    if spec == FLAG:
        return [] if isinstance(obj, bool) else [f"{where}: is true or false"]
    if isinstance(spec, list):
        if not isinstance(obj, list):
            return [f"{where}: is a list"]
        return [q for i, x in enumerate(obj) for q in conforms(x, spec[0], f"{where}[{i}]")]
    if isinstance(spec, tuple) and spec[0] == "one":
        return [] if obj in spec[1] else [f"{where}: is one of {', '.join(map(str, spec[1]))} (it is `{obj}`)"]
    if isinstance(spec, tuple) and spec[0] == "map":
        if not isinstance(obj, dict):
            return [f"{where}: is a mapping"]
        return [q for k, v in obj.items() for q in conforms(v, spec[1], f"{where}.{k}")]
    if not isinstance(obj, dict):
        return [f"{where}: is a mapping"]
    known = {k.rstrip("!"): (k.endswith("!"), v) for k, v in spec.items()}
    p = [f"{where}: the key `{k}` is not one this schema has (known here: {', '.join(sorted(known))})" for k in obj if k not in known]
    p += [f"{where}: the key `{k}` is required" for k, (need, _) in known.items() if need and k not in obj]
    for k, (_, sub) in known.items():
        if k in obj:
            p += conforms(obj[k], sub, f"{where}.{k}" if where else k)
    return p


def model_problem(model) -> str | None:
    """Why a value is not a concrete model, or None."""
    m = str(model or "")
    if not MODEL.match(m):
        return "it is not a model's name"
    if m.casefold() in NOT_A_MODEL or m.casefold().startswith(("auto-", "auto:", "router:", "routers/")):
        return ("it is a router or a stand-in, not a concrete model: which model runs a stage has to be knowable before it "
                "runs, so that a lock can bind it")
    return None


# ---------------------------------------------------------------- the rules
def allowed_path(rel: str) -> bool:
    """Is this a place the definition tree has for a file?"""
    parts = rel.split("/")
    if rel in ("factory.yaml", "checkers.yaml", "change-log.jsonl", "README.md", "harnesses/README.md"):
        return True
    top = parts[0]
    if top == "templates" and len(parts) >= 2:
        return True
    if top == "skills" and len(parts) >= 3:
        return True
    if top == "agents" and len(parts) == 3 and parts[2] == "agent.md":
        return True
    if top == "agents" and len(parts) >= 5 and parts[2] == "skills":
        return True
    if top == "harnesses" and len(parts) >= 3:
        return True
    if top == "runners" and len(parts) == 2 and rel.endswith(".yaml"):
        return True
    if top == "scorers" and len(parts) == 3 and parts[2] == "scorer.md":
        return True
    if top == "automations" and len(parts) == 3 and parts[2] == "automation.md":
        return True
    if top == "benchmarks" and len(parts) == 3 and parts[2] in ("suite.yaml", "README.md"):
        return True
    if top == "benchmarks" and len(parts) == 4 and parts[2] == "cases" and rel.endswith(".yaml"):
        return True
    return False


def names_in(rel: str) -> list:
    """The names a path gives its resources: the folder or file each is called by."""
    parts = rel.split("/")
    if parts[0] in ("agents", "harnesses", "scorers", "automations", "benchmarks") and len(parts) >= 3:
        out = [parts[1]]
        if parts[0] == "agents" and len(parts) >= 4 and parts[2] == "skills":
            out.append(parts[3])
        if parts[0] == "benchmarks" and len(parts) == 4:
            out.append(parts[3].removesuffix(".yaml"))
        return out
    if parts[0] == "skills" and len(parts) >= 2:
        return [parts[1]]
    if parts[0] == "runners" and len(parts) == 2:
        return [parts[1].removesuffix(".yaml")]
    return []


def check_roles_module():
    spec = importlib.util.spec_from_file_location("check_roles", HERE / "check_roles.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git_has(ref: str, cwd: Path) -> bool | None:
    """Does this commit exist? None when git cannot say here."""
    try:
        done = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return None
    if done.returncode == 0:
        return True
    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd, capture_output=True, text=True)
    return False if inside.returncode == 0 and inside.stdout.strip() == "true" else None


def validate(root: Path, repository: Path | None = None) -> tuple:
    """(problems, not_validated): two lists of sentences, each beginning with the rule's name. An empty pair is
    `valid`; anything in the second is `not validated`, whatever is in the first."""
    root = Path(root)
    p, nv = [], []

    def bad(rule: str, text: str) -> None:
        p.append(f"{rule}: {text}")

    if root.is_symlink() or not root.is_dir():
        return [], [f"form: {root} is not a folder, so there is no definition to read"]
    root = root.resolve()
    repository = (Path(repository) if repository else root.parent).resolve()
    fy = root / "factory.yaml"
    if not fy.is_file():
        return [], [f"form: {root} has no factory.yaml: a definition is rooted at that file"]
    try:
        spec = load_yaml(fy.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        return [], [f"form: factory.yaml cannot be read ({e})"]
    except yaml.YAMLError as e:
        return [f"form: factory.yaml does not parse ({' '.join(str(e).split())[:200]})"], []
    if not isinstance(spec, dict):
        return ["form: factory.yaml is not a mapping"], []
    version = spec.get("schemaVersion")
    if version is None:
        return ["form: factory.yaml carries no `schemaVersion`, so nothing says which form these files are in"], []
    if version not in SCHEMAS:
        return [], [f"form: the schema version `{version}` is not one this tool knows ({', '.join(SCHEMAS)}); it cannot say whether "
                    "the definition is valid, and does not guess"]
    for q in conforms(spec, FACTORY, ""):
        bad("form", "factory.yaml" + (": " if not q.startswith(":") else "") + q.lstrip(": "))

    # ---- form: every file has a place, every name is a name, nothing is a link
    rels = files_of(root)
    for rel in rels:
        f = root / rel
        if f.is_symlink() or any(q.is_symlink() for q in f.parents if root in q.parents or q == root):
            bad("form", f"{rel} is a symlink (or sits under one): a definition is the files themselves, so that its checksum covers what is read")
            continue
        if not allowed_path(rel):
            bad("form", f"{rel} is at no place the definition tree has for a file (the tree is listed in this tool's help)")
        for n in names_in(rel):
            if not NAME.match(n):
                bad("form", f"{rel}: `{n}` is not a name (lower case words joined by hyphens): the path is the name")

    def read(rel: str, schema: dict, markdown: bool):
        """A resource file, checked for form; None when it does not parse (which is reported)."""
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            nv.append(f"form: {rel} cannot be read ({e})")
            return None
        try:
            obj = front_matter(text)[0] if markdown else load_yaml(text)
        except (ValueError, yaml.YAMLError) as e:
            bad("form", f"{rel}: {' '.join(str(e).split())[:200]}")
            return None
        if "name" in (obj if isinstance(obj, dict) else {}) and schema is not SUITE:
            bad("form", f"{rel}: carries a `name`; the name of this resource is its path, and nothing in the file can change it")
            obj = {k: v for k, v in obj.items() if k != "name"}
        found = conforms(obj, schema, "")
        for q in found:
            bad("form", f"{rel}{'' if q.startswith(':') else ': '}{q}")
        return obj if isinstance(obj, dict) else None

    agents = {rel.split("/")[1]: read(rel, AGENT, True) for rel in rels if re.fullmatch(r"agents/[^/]+/agent\.md", rel)}
    harnesses = {rel.split("/")[1]: read(rel, HARNESS, False) for rel in rels if re.fullmatch(r"harnesses/[^/]+/harness\.yaml", rel)}
    runners = {rel.split("/")[1].removesuffix(".yaml"): read(rel, RUNNER, False) for rel in rels if re.fullmatch(r"runners/[^/]+\.yaml", rel)}
    scorers = {rel.split("/")[1]: read(rel, SCORER, True) for rel in rels if re.fullmatch(r"scorers/[^/]+/scorer\.md", rel)}
    automations = {rel.split("/")[1]: read(rel, AUTOMATION, True) for rel in rels if re.fullmatch(r"automations/[^/]+/automation\.md", rel)}
    suites = {rel.split("/")[1]: read(rel, SUITE, False) for rel in rels if re.fullmatch(r"benchmarks/[^/]+/suite\.yaml", rel)}
    cases = {(rel.split("/")[1], rel.split("/")[3].removesuffix(".yaml")): read(rel, CASE, False)
             for rel in rels if re.fullmatch(r"benchmarks/[^/]+/cases/[^/]+\.yaml", rel)}
    for h in sorted({rel.split("/")[1] for rel in rels if rel.startswith("harnesses/") and rel.count("/") >= 2} - set(harnesses)):
        bad("form", f"harnesses/{h}/ has no harness.yaml: a harness says what it starts and which models it can start")
    for s in sorted({rel.split("/")[1] for rel in rels if rel.startswith("benchmarks/") and rel.count("/") >= 2} - set(suites)):
        bad("form", f"benchmarks/{s}/ has no suite.yaml")
    if not agents:
        bad("form", "the definition has no agent (agents/<name>/agent.md)")

    # ---- references
    proc = spec.get("procedure") if isinstance(spec.get("procedure"), dict) else {}
    stages = [s for s in proc.get("stages") or [] if isinstance(s, dict)]
    defaults = spec.get("agentDefaults") if isinstance(spec.get("agentDefaults"), dict) else {}

    def models_of(harness: str):
        h = harnesses.get(harness) or {}
        return h.get("models")

    def execution(where: str, harness, model, runner) -> None:
        if harness not in harnesses:
            bad("references", f"{where}: the harness `{harness}` is not a folder in harnesses/")
        why = model_problem(model)
        if why:
            bad("references", f"{where}: the model `{model}`: {why}")
        elif harness in harnesses:
            listed = models_of(harness)
            if listed != "any" and (not isinstance(listed, list) or model not in listed):
                bad("references", f"{where}: the model `{model}` is not one the harness `{harness}` lists (harnesses/{harness}/harness.yaml, `models`)")
        if runner is not None and runner not in runners:
            bad("references", f"{where}: the runner `{runner}` is not a file in runners/")

    for name, h in harnesses.items():
        m = (h or {}).get("models")
        if h is not None and m != "any" and not (isinstance(m, list) and m and all(isinstance(x, str) and not model_problem(x) for x in m)):
            bad("form", f"harnesses/{name}/harness.yaml: `models` is the word any, or a list of concrete models")
    execution("factory.yaml, agentDefaults", defaults.get("harness"), defaults.get("model"), defaults.get("runner"))
    for name, fm in agents.items():
        if fm is not None:
            execution(f"agents/{name}/agent.md", fm.get("harness", defaults.get("harness")), fm.get("model", defaults.get("model")),
                      fm.get("runner", defaults.get("runner")))
    if proc.get("coordinator") not in agents:
        bad("references", f"factory.yaml: the coordinator `{proc.get('coordinator')}` is not an agent (agents/<name>/agent.md)")
    seen_ids = set()
    for st in stages:
        sid = st.get("id")
        if sid in seen_ids:
            bad("form", f"factory.yaml: the stage `{sid}` is given twice")
        seen_ids.add(sid)
        who = st.get("done_by")
        if who != "people" and not (isinstance(who, list) and who and all(isinstance(x, str) for x in who)):
            bad("form", f"factory.yaml: stage {sid}: `done_by` is the word people, or a list of agents")
        elif who != "people":
            for a in who:
                if a not in agents:
                    bad("references", f"factory.yaml: stage {sid} is done by `{a}`, which is not an agent")
        names = st.get("done_when") if isinstance(st.get("done_when"), list) else []
        if not names:
            bad("references", f"factory.yaml: stage {sid}: `done_when` names nothing, so nothing would say the stage is finished")
        for n in names:
            if n not in STAGE_CHECKS:
                bad("references", f"factory.yaml: stage {sid}: `done_when` names `{n}`, which the study tool cannot check "
                                  f"(it can check: {', '.join(STAGE_CHECKS)})")
    where = spec.get("where_it_runs") if isinstance(spec.get("where_it_runs"), dict) else {}
    for k in ("default", "tests"):
        if k in where and where[k] not in runners:
            bad("references", f"factory.yaml: where_it_runs.{k} names `{where[k]}`, which is not a file in runners/")
    contract = (spec.get("runner_contract") or {}).get("keys") if isinstance(spec.get("runner_contract"), dict) else None
    for name, r in runners.items():
        if r is not None and isinstance(contract, dict) and isinstance(r.get("contract"), dict) and set(r["contract"]) != set(contract):
            odd = sorted(set(r["contract"]) ^ set(contract))
            bad("references", f"runners/{name}.yaml: its contract table does not have exactly the keys factory.yaml lists under "
                              f"runner_contract.keys (differs in: {', '.join(odd)})")
    ck = root / "checkers.yaml"
    if ck.is_file():
        try:
            listed = load_yaml(ck.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as e:
            listed = None
            bad("form", f"checkers.yaml does not parse ({' '.join(str(e).split())[:160]})")
        if listed is not None:
            for q in conforms(listed, CHECKERS, ""):
                bad("form", f"checkers.yaml{'' if q.startswith(':') else ': '}{q}")
            for c in (listed.get("checkers") or []) if isinstance(listed, dict) else []:
                if not isinstance(c, dict):
                    continue
                if not SHA.match(str(c.get("sha256") or "")):
                    bad("references", f"checkers.yaml: the checker `{c.get('name')}` is not pinned by a sha256 of 64 hex digits")
                elif c.get("path"):
                    f = (repository / str(c["path"]))
                    if not f.is_file():
                        bad("references", f"checkers.yaml: the checker `{c.get('name')}` names the file {c['path']}, which is not there")
                    elif sha_bytes(f.read_bytes()) != c["sha256"]:
                        bad("references", f"checkers.yaml: the file {c['path']} is not the bytes that are pinned (its checksum differs)")

    # ---- roles: the agent files, the procedure's block and the skills agree
    if (repository / "tools").is_dir():
        try:
            for q in check_roles_module().problems(repository, root):
                bad("roles", q)
        except (OSError, yaml.YAMLError, KeyError, TypeError, AttributeError) as e:
            nv.append(f"roles: the role check could not run ({type(e).__name__}: {e})")
    else:
        nv.append(f"roles: {repository} has no tools/ folder, so the commands the agents may call cannot be looked up; name the "
                  "repository the tools are in with --repository")

    # ---- acts: exactly the stages people do, and no agent may call them
    acts = proc.get("acts_by_people") if isinstance(proc.get("acts_by_people"), dict) else {}
    by_people = {st.get("id") for st in stages if st.get("done_by") == "people"}
    if set(acts) != by_people:
        bad("acts", f"factory.yaml: `acts_by_people` names {sorted(acts)}, and the stages people do are {sorted(by_people)}; an act "
                    "by a person is a stage only people do, and the two lists are the same")
    for act, a in acts.items():
        cmd = (a or {}).get("command") if isinstance(a, dict) else None
        for name, fm in agents.items():
            if fm and cmd and cmd in [str(c) for c in fm.get("may_call") or []]:
                bad("acts", f"agents/{name}/agent.md: may_call holds `{cmd}`, which is the {act}: an act of people, and no agent may call it")

    # ---- skills: one name, one scope, and the scope is true
    seen = {}
    for rel in rels:
        m = re.fullmatch(r"(skills|agents/([^/]+)/skills)/([^/]+)/SKILL\.md", rel)
        if m:
            seen.setdefault(m.group(3), []).append(m.group(2) or "shared")
    for d in sorted({"/".join(rel.split("/")[:2]) for rel in rels if rel.startswith("skills/") and rel.count("/") >= 2}
                    | {"/".join(rel.split("/")[:4]) for rel in rels if re.match(r"agents/[^/]+/skills/[^/]+/", rel)}):
        if d.split("/")[-1] not in seen:
            bad("skills", f"{d}/ has no SKILL.md")
    users = {}
    for name, fm in agents.items():
        for c in (fm or {}).get("may_call") or []:
            if str(c).startswith("skill:"):
                users.setdefault(str(c)[6:], set()).add(name)
    for skill, scopes in seen.items():
        if len(scopes) > 1:
            bad("skills", f"the skill `{skill}` is defined {len(scopes)} times ({', '.join(scopes)}): a skill's name is used once, "
                          "because a harness keeps them in one folder")
            continue
        scope, by = scopes[0], users.get(skill, set())
        if scope == "shared" and len(by) < 2:
            bad("skills", f"skills/{skill}/ is shared and {('only ' + next(iter(by))) if by else 'no agent'} names it: a skill one agent "
                          f"alone uses belongs in that agent's own folder (agents/<name>/skills/{skill}/)")
        if scope != "shared" and by != {scope}:
            bad("skills", f"agents/{scope}/skills/{skill}/ is that agent's own skill, and may_call names it for: "
                          f"{', '.join(sorted(by)) or 'no agent'}")

    # ---- the firewall: scorers
    kinds = {**MATERIAL, **POST_OPENING}
    for name, s in scorers.items():
        if s is None:
            continue
        where = f"scorers/{name}/scorer.md"
        reads = [str(x) for x in s.get("reads") or []] if isinstance(s.get("reads"), list) else []
        if not reads:
            bad("firewall", f"{where}: `reads` is empty; every scorer declares what it reads")
        for r in reads:
            if r not in kinds:
                bad("firewall", f"{where}: `reads` names `{r}`, which is not a kind of material (the kinds: {', '.join(kinds)})")
        after = [r for r in reads if r in POST_OPENING]
        if s.get("selfImprovement") is True and after:
            bad("firewall", f"{where}: `selfImprovement: true` on a scorer that reads {', '.join(after)}: what was written after an "
                            "opening of held-out data never feeds a proposal to change the factory")
        if s.get("type") == "deterministic":
            if s.get("check") not in SCORER_CHECKS:
                bad("references", f"{where}: the check `{s.get('check')}` is not one the study tool evaluates ({', '.join(SCORER_CHECKS)})")
            extra = [k for k in ("labels", "passingScore", "samplingRate", "model", "agents", "harness") if k in s]
            if extra:
                bad("form", f"{where}: a deterministic scorer has no {', '.join(extra)}: the tool works it out and no model is asked")
        elif s.get("type") == "judge":
            if after:
                bad("firewall", f"{where}: a judge that reads {', '.join(after)}: a model judge never reads anything written after an "
                                "opening of held-out data, so that what an opening showed cannot colour what is judged sound")
            if "check" in s:
                bad("form", f"{where}: a judge has no `check`; its rubric is the body of the file")
            missing = [k for k in ("agents", "labels", "passingScore", "samplingRate", "model") if k not in s]
            if missing:
                bad("form", f"{where}: a judge needs {', '.join(missing)}")
                continue
            for a in s.get("agents") or []:
                if a not in agents:
                    bad("references", f"{where}: it scores the agent `{a}`, which is not an agent")
            harness = s.get("harness", defaults.get("harness"))
            if harness not in harnesses:
                bad("references", f"{where}: the harness `{harness}` is not a folder in harnesses/")
            why = model_problem(s.get("model"))
            if why:
                bad("references", f"{where}: the model `{s.get('model')}`: {why}")
            elif harness in harnesses and models_of(harness) != "any" and s.get("model") not in (models_of(harness) or []):
                bad("references", f"{where}: the model `{s.get('model')}` is not one the harness `{harness}` lists")
            labels = [x for x in s.get("labels") or [] if isinstance(x, dict)]
            scores = [x.get("score") for x in labels if isinstance(x.get("score"), (int, float))]
            passing = s.get("passingScore")
            if not 1 <= len(labels) <= 20 or len({x.get("value") for x in labels}) != len(labels):
                bad("form", f"{where}: `labels` is one to twenty labels, each value used once")
            if any(not 0 <= x <= 1 for x in scores) or not isinstance(passing, (int, float)) or not 0 <= passing <= 1:
                bad("form", f"{where}: every score, and the passing score, lies between 0 and 1")
            elif scores and (all(x >= passing for x in scores) or all(x < passing for x in scores)):
                bad("form", f"{where}: at least one label passes and at least one fails; here every label falls on one side of {passing}")
            rate = s.get("samplingRate")
            if not isinstance(rate, (int, float)) or isinstance(rate, bool) or not 0 <= rate <= 100:
                bad("form", f"{where}: `samplingRate` is a percentage between 0 and 100")
            try:
                body = front_matter((root / where).read_text(encoding="utf-8"))[1]
            except (ValueError, yaml.YAMLError, OSError):
                body = ""
            if len(body.split()) < 20:
                bad("form", f"{where}: a judge's rubric is the body of the file, and this one has next to none")

    # ---- benchmarks, and the firewall's rule for cases
    sets = {}
    for name, s in suites.items():
        if s is None:
            continue
        where = f"benchmarks/{name}/suite.yaml"
        configs = [c for c in s.get("configurations") or [] if isinstance(c, dict)]
        names = [c.get("name") for c in configs]
        if len(set(names)) != len(names) or not 1 <= len(configs) <= 6:
            bad("form", f"{where}: one to six configurations, each name used once")
        for c in configs:
            d = c.get("definition") if isinstance(c.get("definition"), dict) else {}
            if ("path" in d) == ("ref" in d):
                bad("form", f"{where}: configuration `{c.get('name')}`: its definition is a `path` or a git `ref`, one of the two")
            elif "path" in d:
                target = (root / str(d["path"])).resolve()
                if not (target / "factory.yaml").is_file():
                    bad("references", f"{where}: configuration `{c.get('name')}` names the definition at `{d['path']}` (read from this "
                                      "definition's own folder), and no factory.yaml is there")
            else:
                has = git_has(str(d["ref"]), root)
                if has is None:
                    nv.append(f"references: {where}: configuration `{c.get('name')}` names the git ref `{d['ref']}`, and git cannot be asked here")
                elif not has:
                    nv.append(f"references: {where}: configuration `{c.get('name')}` names the git ref `{d['ref']}`, which this checkout "
                              "does not have (a shallow clone has only its own commit); whether it resolves cannot be told here")
        comp = s.get("comparison") if isinstance(s.get("comparison"), dict) else {}
        for k in ("baseline", "candidate"):
            if comp.get(k) not in names:
                bad("references", f"{where}: the comparison's {k} `{comp.get(k)}` is not one of its configurations")
        if isinstance(comp.get("alpha"), (int, float)) and not 0 < comp["alpha"] < 1:
            bad("form", f"{where}: comparison.alpha lies between 0 and 1")
        target = s.get("target") if isinstance(s.get("target"), dict) else {}
        if target.get("plan") and not (repository / str(target["plan"]) / "analysis-plan.yaml").is_file():
            bad("references", f"{where}: target.plan names `{target.get('plan')}` (read from the repository that holds the definition), "
                              "and no analysis-plan.yaml is there")
        on_disk = sorted(c for (suite, c) in cases if suite == name)
        if s.get("set") == "design":
            listed = [str(c) for c in s.get("cases") or []]
            if "generated" in s or not listed:
                bad("form", f"{where}: a design suite lists its cases, which are files in cases/")
            for c in listed:
                if c not in on_disk:
                    bad("references", f"{where}: it lists the case `{c}`, and cases/{c}.yaml does not exist")
            for c in on_disk:
                if c not in listed:
                    bad("references", f"benchmarks/{name}/cases/{c}.yaml is a case the suite does not list")
            sets.setdefault("design", set()).update(listed)
        elif s.get("set") == "acceptance":
            if "cases" in s or on_disk:
                bad("acceptance", f"{where}: an acceptance suite keeps no case in the definition (found: {', '.join(on_disk) or 'a `cases` list'}): "
                                  "its cases are generated from a seed kept outside, so that no agent proposing changes can read them")
            if "generated" not in s:
                bad("acceptance", f"{where}: an acceptance suite says how its cases are generated (`generated`: count, truths, and the "
                                  "environment variable the seed is read from)")
            never = [str(x) for x in s.get("must_never_see") or []]
            if not any(x.startswith("path:") for x in never):
                bad("acceptance", f"{where}: an acceptance suite lists, under `must_never_see`, the places no agent may read "
                                  "(at least one `path:<pattern>`)")
            for a, fm in agents.items():
                have = [str(x) for x in (fm or {}).get("must_never_see") or []]
                for x in never:
                    if x not in have:
                        bad("acceptance", f"agents/{a}/agent.md: `must_never_see` does not list `{x}`, which the acceptance suite "
                                          f"`{name}` says no agent may see; every agent lists it, with no exception")
            sets.setdefault("acceptance", set()).update(on_disk)
    both = sets.get("design", set()) & sets.get("acceptance", set())
    if both:
        bad("acceptance", f"the cases {', '.join(sorted(both))} are in a design suite and in an acceptance suite; the two sets share no case")
    for (suite, case), c in cases.items():
        if c is None:
            continue
        where = f"benchmarks/{suite}/cases/{case}.yaml"
        kind = (c.get("sampling") or {}).get("kind") if isinstance(c.get("sampling"), dict) else None
        if kind not in ("synthetic", "observation-metadata"):
            bad("firewall", f"{where}: sampling.kind is `{kind}`. A benchmark case is a truth planted by hand on synthetic data, or "
                            "on the observation metadata of a real record (its times, places and flags, never its values): real "
                            "held-out data is never a benchmark case, because a factory tuned on opened data has been fitted to the answer")
        if isinstance(c.get("truth"), dict) and str(c["truth"].get("planted_by", "")).strip().casefold() in ("", "nobody", "the data", "nature"):
            bad("firewall", f"{where}: truth.planted_by says nobody planted it; a benchmark case has a planted truth, sealed until the opening is over")

    # ---- automations: declared, not wired, and only before the lock
    startable = {st.get("id") for st in stages if st.get("done_by") != "people"
                 and isinstance(st.get("done_when"), list) and set(st["done_when"]) <= set(BEFORE_THE_LOCK)}
    for name, a in automations.items():
        if a is None:
            continue
        where = f"automations/{name}/automation.md"
        if a.get("wired") is not False:
            bad("automations", f"{where}: `wired` is not false. No trigger is built: an automation here is a declaration, and says so")
        if a.get("stage") not in startable:
            bad("automations", f"{where}: it would start the stage `{a.get('stage')}`. An automation may start only a stage that agents "
                               f"do before the lock ({', '.join(sorted(startable))}); it never locks, opens or signs")
        if "agent" in a and a["agent"] not in agents:
            bad("references", f"{where}: the agent `{a['agent']}` is not an agent")
        for t in a.get("triggers") or []:
            if isinstance(t, dict) and t.get("provider") == "schedule" and "schedule" not in t:
                bad("form", f"{where}: a schedule trigger carries `schedule` (a name and a cron line)")
    return p, nv


def result(root: Path, repository: Path | None = None) -> tuple:
    """(the word, the exit code, the problems, what could not be validated)."""
    try:
        p, nv = validate(root, repository)
    except NotValidated as e:
        p, nv = [], [str(e)]
    except (OSError, UnicodeDecodeError) as e:
        p, nv = [], [f"form: a file of the definition cannot be read ({e})"]
    if nv:
        return "not validated", 2, p, nv
    return ("invalid", 1, p, nv) if p else ("valid", 0, p, nv)


# ---------------------------------------------------------------- the summary of a change
def materialise(name: str, tmp: Path) -> Path | None:
    """A tree named on the command line, as a folder: itself, or `git:<ref>:<path>` taken out of git. None when
    that ref has no such folder."""
    if not name.startswith("git:"):
        return Path(name)
    _, ref, sub = (name.split(":", 2) + ["factory"])[:3]
    done = subprocess.run(["git", "archive", "--format=tar", ref, sub], capture_output=True)
    if done.returncode != 0:
        return None
    out = tmp / re.sub(r"[^A-Za-z0-9]+", "-", ref)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        tar.extractall(out, filter="data")
    return out / sub


def describe(root: Path) -> dict:
    """What a reviewer of a change wants named, read without judging it."""
    root = Path(root).resolve()
    try:
        spec = load_yaml((root / "factory.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        spec = {}
    proc = spec.get("procedure") if isinstance(spec.get("procedure"), dict) else {}
    defaults = spec.get("agentDefaults") if isinstance(spec.get("agentDefaults"), dict) else {}
    scorers = {}
    for f in sorted((root / "scorers").glob("*/scorer.md")):
        try:
            scorers[f.parent.name] = front_matter(f.read_text(encoding="utf-8"))[0]
        except (ValueError, yaml.YAMLError, OSError):
            scorers[f.parent.name] = {}
    automations = {}
    for f in sorted((root / "automations").glob("*/automation.md")):
        try:
            automations[f.parent.name] = front_matter(f.read_text(encoding="utf-8"))[0]
        except (ValueError, yaml.YAMLError, OSError):
            automations[f.parent.name] = {}
    suites = {}
    for f in sorted((root / "benchmarks").glob("*/suite.yaml")):
        try:
            suites[f.parent.name] = load_yaml(f.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            suites[f.parent.name] = {}
    return {"version": spec.get("version"), "schemaVersion": spec.get("schemaVersion"),
            "stages": {s.get("id"): s for s in proc.get("stages") or [] if isinstance(s, dict)},
            "stage_order": [s.get("id") for s in proc.get("stages") or [] if isinstance(s, dict)],
            "acts": proc.get("acts_by_people") if isinstance(proc.get("acts_by_people"), dict) else {},
            "agents": {a: {**{k: fm.get(k, defaults.get(k)) for k in ("harness", "model", "runner")},
                           **{k: [str(x) for x in fm.get(k) or []] for k in ("may_call", "must_never_see", "writes")}}
                       for a, fm in agents_of(root).items()},
            "scorers": scorers, "automations": automations, "suites": suites,
            "files": {rel: sha_bytes((root / rel).read_bytes()) for rel in files_of(root) if not (root / rel).is_symlink()},
            "checksum": tree_checksum(root)["sha256"]}


def summary(old: Path | None, new: Path) -> list:
    """What changed between two definition trees, in plain words. What touches the acts by people, what an agent
    may call or must never see, what a scorer reads and what may feed improvement comes first, marked."""
    b = describe(new)
    if old is None or not (Path(old) / "factory.yaml").is_file():
        return ["The earlier tree has no definition this tool can read (no factory.yaml), so everything is new.",
                f"The new definition: version {b['version']}, {len(b['stage_order'])} stages, {len(b['agents'])} agents, "
                f"{len(b['scorers'])} scorers, {len(b['suites'])} benchmark suites, {len(b['automations'])} automations, {len(b['files'])} files."]
    a = describe(old)
    first, rest = [], []

    def added_removed(label: str, x: dict, y: dict, out: list) -> None:
        for k in sorted(set(y) - set(x)):
            out.append(f"{label} `{k}` is added.")
        for k in sorted(set(x) - set(y)):
            out.append(f"{label} `{k}` is removed.")

    if a["checksum"] == b["checksum"]:
        return ["Nothing changed: the two trees have the same checksum."]
    if a["version"] != b["version"]:
        rest.append(f"The definition's version goes from {a['version']} to {b['version']}.")
    else:
        first.append(f"TAKE NOTE: the definition changed and its version did not ({b['version']}): a change to the definition is "
                     "recorded in the change log under a new version.")
    if a["schemaVersion"] != b["schemaVersion"]:
        first.append(f"TAKE NOTE: the schema version goes from {a['schemaVersion']} to {b['schemaVersion']}.")
    if a["acts"] != b["acts"]:
        first.append(f"TAKE NOTE: the acts by people change: they were {sorted(a['acts'])} and are {sorted(b['acts'])}"
                     + ("" if set(a["acts"]) != set(b["acts"]) else " (the same acts, with who, the command or the evidence reworded)") + ".")
    added_removed("The stage", a["stages"], b["stages"], first)
    if a["stage_order"] != b["stage_order"] and set(a["stage_order"]) == set(b["stage_order"]):
        first.append(f"TAKE NOTE: the stages are in another order: {', '.join(map(str, b['stage_order']))}.")
    for sid in sorted(set(a["stages"]) & set(b["stages"]), key=str):
        x, y = a["stages"][sid], b["stages"][sid]
        if x.get("done_by") != y.get("done_by"):
            first.append(f"TAKE NOTE: the stage `{sid}` was done by {x.get('done_by')} and is now done by {y.get('done_by')}.")
        if x.get("done_when") != y.get("done_when"):
            first.append(f"TAKE NOTE: the stage `{sid}` was finished by {x.get('done_when')} and is now finished by {y.get('done_when')}.")
        if x.get("does") != y.get("does"):
            rest.append(f"The stage `{sid}` is described in other words.")
    added_removed("TAKE NOTE: the agent", a["agents"], b["agents"], first)
    for name in sorted(set(a["agents"]) & set(b["agents"])):
        x, y = a["agents"][name], b["agents"][name]
        for key, what in (("may_call", "may now call"), ("must_never_see", "must now never see"), ("writes", "may now write")):
            gained, lost = sorted(set(y[key]) - set(x[key])), sorted(set(x[key]) - set(y[key]))
            if gained:
                first.append(f"TAKE NOTE: the agent `{name}` {what}: {'; '.join(gained)}.")
            if lost:
                first.append(f"TAKE NOTE: the agent `{name}` no longer has, under `{key}`: {'; '.join(lost)}.")
        for key in ("model", "harness", "runner"):
            if x[key] != y[key]:
                first.append(f"TAKE NOTE: the agent `{name}` declares the {key} {y[key]} (it was {x[key]}).")
    added_removed("The scorer", a["scorers"], b["scorers"], first)
    for name in sorted(set(a["scorers"]) & set(b["scorers"])):
        x, y = a["scorers"][name], b["scorers"][name]
        for key in ("reads", "selfImprovement", "type", "check", "model", "samplingRate", "passingScore", "labels", "agents"):
            if x.get(key) != y.get(key):
                first.append(f"TAKE NOTE: the scorer `{name}`: `{key}` was {x.get(key)} and is {y.get(key)}.")
    for name in sorted(set(b["scorers"])):
        y = b["scorers"][name]
        if y.get("selfImprovement") is True and (name not in a["scorers"] or a["scorers"][name].get("selfImprovement") is not True):
            first.append(f"TAKE NOTE: the scorer `{name}` may now feed proposals to change the factory (it reads: {y.get('reads')}).")
    added_removed("The automation", a["automations"], b["automations"], first)
    for name in sorted(set(a["automations"]) & set(b["automations"])):
        if a["automations"][name] != b["automations"][name]:
            first.append(f"TAKE NOTE: the automation `{name}` changed (its stage is `{b['automations'][name].get('stage')}`, wired: "
                         f"{b['automations'][name].get('wired')}).")
    added_removed("The benchmark suite", a["suites"], b["suites"], rest)
    for name in sorted(set(a["suites"]) & set(b["suites"])):
        if a["suites"][name].get("comparison") != b["suites"][name].get("comparison"):
            first.append(f"TAKE NOTE: the benchmark suite `{name}` compares by another rule than before; a comparison is stated in "
                         "advance, and changing it after a run is choosing the answer.")
        elif a["suites"][name] != b["suites"][name]:
            rest.append(f"The benchmark suite `{name}` changed (its cases, configurations or repetitions).")
    new_files = sorted(set(b["files"]) - set(a["files"]))
    gone = sorted(set(a["files"]) - set(b["files"]))
    changed = sorted(k for k in set(a["files"]) & set(b["files"]) if a["files"][k] != b["files"][k])
    rest.append(f"Files: {len(new_files)} added, {len(gone)} removed, {len(changed)} changed.")
    for label, names in (("added", new_files), ("removed", gone), ("changed", changed)):
        if names:
            rest.append(f"  {label}: {', '.join(names[:40])}" + (f", and {len(names) - 40} more" if len(names) > 40 else ""))
    return first + rest


# ---------------------------------------------------------------- the self-test
def selftest() -> int:
    results = []
    tmp = Path(tempfile.mkdtemp(prefix="check-factory-")).resolve()
    try:
        def copy(name: str) -> Path:
            d = tmp / name
            shutil.copytree(REPO / "factory", d / "factory", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(REPO / "tools", d / "tools", ignore=shutil.ignore_patterns("__pycache__"))
            for plan in (REPO / "examples").glob("*/system-trial/analysis-plan.yaml"):
                (d / plan.parent.relative_to(REPO)).mkdir(parents=True)
                shutil.copyfile(plan, d / plan.relative_to(REPO))
            return d / "factory"

        def edit(d: Path, rel: str, old: str, new: str) -> None:
            f = d / rel
            text = f.read_text()
            assert old in text, (rel, old)
            f.write_text(text.replace(old, new, 1))

        def write(d: Path, rel: str, text: str) -> None:
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text(text)

        def case(name: str, change, expect: str, word: str = "invalid") -> None:
            d = copy(f"case-{len(results)}")
            change(d)
            got = result(d)
            results.append((name, got[0] == word and any(expect in q for q in got[2] + got[3])))

        own = result(copy("clean"))
        results.append(("this repository's own definition is valid", own[0] == "valid" and own[1] == 0))
        # the three results
        results.append(("a folder with no factory.yaml is not validated, which is not a pass",
                        result(tmp)[0:2] == ("not validated", 2) and result(tmp / "nowhere")[0:2] == ("not validated", 2)))
        case("a schema version this tool does not know is not validated", lambda d: edit(d, "factory.yaml", "science-factory/v1alpha1", "science-factory/v9"),
             "is not one this tool knows", "not validated")
        case("a definition with no schema version is invalid", lambda d: edit(d, "factory.yaml", "schemaVersion: science-factory/v1alpha1", "schemaTag: x"),
             "carries no `schemaVersion`")
        case("a file that cannot be read as text is not validated", lambda d: (d / "runners/local.yaml").write_bytes(b"\xff\xfe\x00bad"),
             "cannot be read", "not validated")
        case("a git ref a benchmark names that cannot be looked up is not validated",
             lambda d: edit(d, "benchmarks/built-in-gain/suite.yaml", 'definition: {path: "."}', 'definition: {ref: "no-such-ref-anywhere"}'),
             "names the git ref", "not validated")
        # form
        case("an unknown key in factory.yaml is refused", lambda d: edit(d, "factory.yaml", "alias: built-in-example", "alias: built-in-example\nnickname: x"),
             "the key `nickname` is not one this schema has")
        case("a key given twice is refused", lambda d: edit(d, "factory.yaml", "alias: built-in-example", "alias: built-in-example\nalias: another"),
             "given twice")
        case("an unknown key in an agent file is refused", lambda d: edit(d, "agents/review/agent.md", "runner: local", "runner: local\nsecrets: [X]"),
             "the key `secrets` is not one this schema has")
        case("a required key that is missing is reported", lambda d: edit(d, "runners/local.yaml", "\nstatus: built", "\nstate: built"), "the key `status` is required")
        case("a file at a place the tree has none for is refused", lambda d: write(d, "agents/notes.txt", "x"), "at no place the definition tree has")
        case("a name inside a file is refused: the path is the name", lambda d: edit(d, "agents/review/agent.md", "runner: local", "runner: local\nname: reviewer"),
             "the name of this resource is its path")
        case("a folder whose name is not a name is refused", lambda d: (d / "scorers/chain-of-custody").rename(d / "scorers/Chain_Of_Custody"),
             "is not a name")
        case("a symlink in the tree is refused", lambda d: (d / "runners/other.yaml").symlink_to(d / "runners/local.yaml"), "is a symlink")
        case("a stage given twice is refused", lambda d: edit(d, "factory.yaml", "    - id: plan\n", "    - id: ask\n"), "the stage `ask` is given twice")
        # references
        case("an agent whose harness is not a folder", lambda d: edit(d, "agents/review/agent.md", "harness: claude-code", "harness: codex"),
             "the harness `codex` is not a folder in harnesses/")
        case("an agent whose model the harness does not list", lambda d: edit(d, "agents/review/agent.md", "model: claude-opus-5-5", "model: gpt-unlisted"),
             "is not one the harness `claude-code` lists")
        case("an agent whose model is a router", lambda d: edit(d, "agents/analysis/agent.md", "model: claude-sonnet-5-5", "model: auto"),
             "a router or a stand-in, not a concrete model")
        case("an agent whose runner is not a file", lambda d: edit(d, "agents/curating/agent.md", "runner: local", "runner: cluster"),
             "the runner `cluster` is not a file in runners/")
        case("the default model is not one the default harness lists", lambda d: edit(d, "factory.yaml", "  model: claude-sonnet-5-5 ", "  model: some-other-model "),
             "factory.yaml, agentDefaults: the model")
        case("a coordinator that is not an agent", lambda d: edit(d, "factory.yaml", "coordinator: coordinating", "coordinator: foreman"),
             "the coordinator `foreman` is not an agent")
        case("a stage done by something that is not an agent", lambda d: edit(d, "factory.yaml", "      done_by: [curating]", "      done_by: [librarian]"),
             "is done by `librarian`, which is not an agent")
        case("a stage finished by a check the tool does not have", lambda d: edit(d, "factory.yaml", "done_when: [plan-complete]", "done_when: [looks-fine]"),
             "which the study tool cannot check")
        case("a deterministic scorer naming a check the tool does not have",
             lambda d: edit(d, "scorers/notes-curated/scorer.md", "check: notes-on-curation-list", "check: notes-look-tidy"), "is not one the study tool evaluates")
        case("a judge that scores an agent that does not exist",
             lambda d: edit(d, "scorers/plan-is-clear/scorer.md", "agents: [analysis]", "agents: [planner]"), "which is not an agent")
        case("a judge whose model is not concrete", lambda d: edit(d, "scorers/plan-is-clear/scorer.md", "model: claude-opus-5-5", "model: auto"),
             "a router or a stand-in")
        case("a benchmark configuration that points at no definition",
             lambda d: edit(d, "benchmarks/built-in-gain/suite.yaml", 'definition: {path: "."}', 'definition: {path: "../elsewhere"}'), "no factory.yaml is there")
        case("a benchmark that lists a case with no file",
             lambda d: (d / "benchmarks/built-in-gain/cases/no-gain.yaml").unlink(), "cases/no-gain.yaml does not exist")
        case("a case file the suite does not list",
             lambda d: shutil.copyfile(d / "benchmarks/built-in-gain/cases/no-gain.yaml", d / "benchmarks/built-in-gain/cases/stray.yaml"),
             "is a case the suite does not list")
        case("a comparison that names a configuration the suite does not have",
             lambda d: edit(d, "benchmarks/built-in-gain/suite.yaml", "candidate: same-again", "candidate: the-new-one"), "is not one of its configurations")
        case("a benchmark whose plan is not there",
             lambda d: edit(d, "benchmarks/built-in-gain/suite.yaml", "plan: examples/stand-alone/system-trial", "plan: examples/nowhere"), "no analysis-plan.yaml is there")
        case("a runner whose contract has other keys than the twelve", lambda d: edit(d, "runners/maap.yaml", "  cancel:", "  stop:"),
             "does not have exactly the keys")
        case("where_it_runs names a runner that is not a file", lambda d: edit(d, "factory.yaml", "  tests: local", "  tests: laptop"),
             "where_it_runs.tests names `laptop`")
        case("a checker that is not pinned by a checksum", lambda d: edit(d, "checkers.yaml", "sha256: cc11ab5f", "sha256: latest-cc11ab5f"),
             "is not pinned by a sha256")

        def unpinned(d: Path) -> None:
            write(d.parent, "tools/a_checker.py", "print('ok')\n")
            edit(d, "checkers.yaml", "checkers:\n", "checkers:\n  - {name: a_checker.py, what: a local checker, path: tools/a_checker.py, sha256: \"" + "0" * 64 + "\"}\n")
        case("a pinned checker whose file is not the bytes that are pinned", unpinned, "is not the bytes that are pinned")
        # roles (check_roles.py, called)
        case("the role check's rules are part of the result: an agent may not call the lock",
             lambda d: edit(d, "agents/coordinating/agent.md", '  - "tools/sf.py close"', '  - "tools/sf.py close"\n  - "tools/sf.py lock"'), "roles:")
        case("an agent file and a skill that give different orders",
             lambda d: edit(d, "agents/review/skills/review-work/SKILL.md", "Your account for the coordinating assistant goes in `record/review/`", "Your account goes beside the author's"),
             "do not say the same thing")
        nv = copy("no-tools")
        shutil.rmtree(nv.parent / "tools")
        results.append(("without the tools the agents' commands cannot be looked up: not validated", result(nv)[0] == "not validated"))
        # acts
        case("an act by people that is not a stage people do", lambda d: edit(d, "factory.yaml", "      done_by: people\n      done_when: [steward-decided]", "      done_by: [curating]\n      done_when: [steward-decided]"),
             "acts:")
        case("an agent may call the signature, named as an act", lambda d: edit(d, "agents/curating/agent.md", '  - "tools/sf.py resolve"', '  - "tools/sf.py resolve"\n  - "tools/sf.py signature"'),
             "acts: agents/curating/agent.md")
        # skills
        case("a skill defined twice", lambda d: shutil.copytree(d / "skills/read-what-is-known", d / "agents/review/skills/read-what-is-known"),
             "a skill's name is used once")
        case("a shared skill that one agent alone uses", lambda d: (d / "agents/review/skills/review-work").rename(d / "skills/review-work"),
             "belongs in that agent's own folder")
        case("a skill folder with no SKILL.md", lambda d: (d / "skills/read-what-is-known/SKILL.md").rename(d / "skills/read-what-is-known/skill.txt"),
             "has no SKILL.md")
        # the firewall
        case("a scorer that does not say what it reads", lambda d: edit(d, "scorers/notes-curated/scorer.md", "reads: [pre-lock-log, post-opening-log]", "reads: []"),
             "every scorer declares what it reads")
        case("a scorer that reads a kind of material that is not on the list",
             lambda d: edit(d, "scorers/notes-curated/scorer.md", "reads: [pre-lock-log, post-opening-log]", "reads: [everything]"), "is not a kind of material")
        case("a judge that reads the finding", lambda d: edit(d, "scorers/plan-is-clear/scorer.md", "reads: [request, plan, known-answer-tests]", "reads: [request, plan, finding]"),
             "a judge that reads finding")
        case("a judge that reads the opening's outcome",
             lambda d: edit(d, "scorers/review-finds-holes/scorer.md", "reads: [exploration-log, lead, review-before-opening]", "reads: [lead, review-before-opening, opening-outcome]"),
             "a model judge never reads anything written after an opening")
        case("a judge that reads the log after the opening",
             lambda d: edit(d, "scorers/exploration-owns-its-count/scorer.md", "reads: [exploration-log, lead]", "reads: [exploration-log, lead, post-opening-log]"),
             "a judge that reads post-opening-log")
        case("selfImprovement on a deterministic scorer that reads post-opening material",
             lambda d: edit(d, "scorers/independent-review/scorer.md", "selfImprovement: false", "selfImprovement: true"),
             "never feeds a proposal to change the factory")
        case("selfImprovement on a scorer that reads the opening's outcome",
             lambda d: edit(d, "scorers/no-failed-opening/scorer.md", "selfImprovement: false", "selfImprovement: true"), "`selfImprovement: true` on a scorer that reads opening-outcome")
        case("a judge with no rubric", lambda d: write(d, "scorers/plan-is-clear/scorer.md", (d / "scorers/plan-is-clear/scorer.md").read_text().split("\n---\n")[0] + "\n---\n\nJudge it.\n"),
             "has next to none")
        case("a judge whose labels all pass", lambda d: edit(d, "scorers/plan-is-clear/scorer.md", "passingScore: 1", "passingScore: 0"),
             "at least one label passes and at least one fails")
        case("a judge with a sampling rate that is no percentage", lambda d: edit(d, "scorers/plan-is-clear/scorer.md", "samplingRate: 100", "samplingRate: 250"),
             "a percentage between 0 and 100")
        case("a deterministic scorer dressed as a judge", lambda d: edit(d, "scorers/notes-curated/scorer.md", "selfImprovement: false", "selfImprovement: false\nmodel: claude-opus-5-5"),
             "a deterministic scorer has no model")
        case("a benchmark case that is real held-out data",
             lambda d: edit(d, "benchmarks/built-in-gain/cases/no-gain.yaml", "kind: synthetic", "kind: held-out-data"), "real held-out data is never a benchmark case")
        case("a benchmark case nobody planted a truth in",
             lambda d: edit(d, "benchmarks/built-in-gain/cases/no-gain.yaml", "planted_by: the benchmark harness", "planted_by: nature"), "a benchmark case has a planted truth")
        # the acceptance set
        case("an agent whose must_never_see does not list the acceptance set",
             lambda d: edit(d, "agents/curating/agent.md", '  - "path:acceptance-cases/*"\n', ""), "which the acceptance suite `acceptance` says no agent may see")
        case("an acceptance suite that keeps a case in the definition",
             lambda d: write(d, "benchmarks/acceptance/cases/leaked.yaml", (d / "benchmarks/built-in-gain/cases/no-gain.yaml").read_text()),
             "keeps no case in the definition")
        case("an acceptance suite that names no place agents must not read",
             lambda d: write(d, "benchmarks/acceptance/suite.yaml", re.sub(r"must_never_see:.*\n(  - .*\n)+", "must_never_see: []\n", (d / "benchmarks/acceptance/suite.yaml").read_text())),
             "the places no agent may read")
        # automations
        case("an automation that would start the lock", lambda d: edit(d, "automations/new-data-release/automation.md", "stage: ask", "stage: lock"),
             "it never locks, opens or signs")
        case("an automation that would start the opening", lambda d: edit(d, "automations/new-data-release/automation.md", "stage: ask", "stage: open"),
             "An automation may start only a stage that agents do before the lock")
        case("an automation marked wired, when no trigger is built", lambda d: edit(d, "automations/finding-expires/automation.md", "wired: false", "wired: true"),
             "No trigger is built")
        case("an automation with a provider this schema does not have",
             lambda d: edit(d, "automations/new-data-release/automation.md", "provider: github", "provider: carrier-pigeon"), "is one of schedule, github, webhook, factory")
        # the checksum and the summary
        a, b = copy("sum-a"), copy("sum-b")
        results.append(("two copies of one definition have one checksum, and the summary says nothing changed",
                        tree_checksum(a) == tree_checksum(b) and summary(a, b) == ["Nothing changed: the two trees have the same checksum."]))
        (b / "change-log.jsonl").write_text((b / "change-log.jsonl").read_text() + "{}\n")
        results.append(("the change log is no part of the checksum: it is a record about the definition", tree_checksum(a) == tree_checksum(b)))
        edit(b, "agents/review/agent.md", '  - "tools/sf.py note"', '  - "tools/sf.py note"\n  - "tools/sf.py attach"')
        edit(b, "agents/review/agent.md", '  - "path:record/analysis/*"\n', "")
        edit(b, "agents/analysis/agent.md", "model: claude-sonnet-5-5", "model: claude-opus-5-5")
        edit(b, "scorers/plan-is-clear/scorer.md", "samplingRate: 100", "samplingRate: 10")
        edit(b, "factory.yaml", "      done_when: [tests-pass, rehearsals-pass]", "      done_when: [tests-pass]")
        (b / "automations/finding-expires/automation.md").unlink()
        said = "\n".join(summary(a, b))
        results.append(("a change to the tree changes its checksum", tree_checksum(a) != tree_checksum(b)))
        results.append(("the summary names, first and marked, what an agent may newly call and no longer must never see",
                        "TAKE NOTE: the agent `review` may now call: tools/sf.py attach." in said
                        and "no longer has, under `must_never_see`: path:record/analysis/*" in said and said.index("TAKE NOTE") < said.index("Files:")))
        results.append(("the summary names a changed model, a changed scorer, a changed stage and a removed automation",
                        "the agent `analysis` declares the model claude-opus-5-5 (it was claude-sonnet-5-5)" in said
                        and "the scorer `plan-is-clear`: `samplingRate` was 100 and is 10" in said
                        and "the stage `test` was finished by ['tests-pass', 'rehearsals-pass'] and is now finished by ['tests-pass']" in said
                        and "The automation `finding-expires` is removed." in said))
        results.append(("the summary says so when the definition changed and its version did not", "its version did not" in said))
        edit(b, "scorers/exploration-owns-its-count/scorer.md", "selfImprovement: true", "selfImprovement: false")
        results.append(("the summary names a scorer that may newly feed improvement",
                        "the scorer `exploration-owns-its-count` may now feed proposals" in "\n".join(summary(b, a))))
        results.append(("the summary of a tree against nothing says everything is new", "everything is new" in summary(tmp / "nowhere", a)[0]))
        st = stamp(a)
        results.append(("the stamp of a definition carries its checksum, the model each agent declares and each skill used by checksum",
                        st["sha256"] == tree_checksum(a)["sha256"] and st["models"]["review"] == {"harness": "claude-code", "model": "claude-opus-5-5"}
                        and set(st["skills"]) == {"read-what-is-known", "explore-a-record", "write-up-a-lead", "review-work", "draft-a-knowledge-page"}
                        and all(SHA.match(v) for v in st["skills"].values())))
        results.append(("the checks a stage and a scorer may name are known here", len(STAGE_CHECKS) == 11 and len(SCORER_CHECKS) == 8))
        results.append(("the self-test leaves no bytecode folder beside the tools", not (HERE / "__pycache__").exists()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = [n for n, good in results if not good]
    for n in failed:
        print("FAIL:", n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("root", nargs="?", type=Path, default=REPO / "factory", help="the definition tree (default: factory/ beside tools/)")
    ap.add_argument("--repository", type=Path, default=None, help="the repository the tools are in (default: the folder the tree is in)")
    ap.add_argument("--summary", nargs=2, metavar=("OLD", "NEW"), default=None, help="what changed between two trees; a tree is a folder or git:<ref>:<path>")
    ap.add_argument("--checksum", action="store_true", help="print the tree's checksum, as the lock binds it")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.summary:
        with tempfile.TemporaryDirectory() as tmp:
            old, new = (materialise(x, Path(tmp)) for x in a.summary)
            if new is None or not (new / "factory.yaml").is_file():
                print(f"check-factory --summary: NOT VALIDATED: the new tree ({a.summary[1]}) has no factory.yaml to read")
                return 2
            print(f"What this change does to the definition ({a.summary[0]} -> {a.summary[1]}):")
            for line in summary(old, new):
                print(("" if line.startswith("  ") else "- ") + line)
        return 0
    if a.checksum:
        try:
            print(json.dumps(stamp(a.root), indent=1))
        except NotValidated as e:
            print(f"check-factory: NOT VALIDATED: {e}")
            return 2
        return 0
    word, code, problems, nv = result(a.root, a.repository)
    for q in problems:
        print("check-factory:", q)
    for q in nv:
        print("check-factory: could not be validated:", q)
    print("check-factory: what this tool cannot check, whatever the result:")
    for q in CANNOT_CHECK:
        print(f"  {q}")
    if code == 0:
        t = tree_checksum(a.root)
        print(f"check-factory: VALID ({t['files']} files; sha256 {t['sha256']})")
    elif code == 1:
        print(f"check-factory: INVALID ({len(problems)} broken rule(s))")
    else:
        print(f"check-factory: NOT VALIDATED ({len(nv)} thing(s) could not be told; this is never a pass)")
    return code


if __name__ == "__main__":
    sys.exit(main())
