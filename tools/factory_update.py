#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""factory_update: bring a study repository's copy of the factory up to a newer one.

A scientist copies `factory/` and `tools/` of the science factory into the
repository where their science lives (docs/CREATE-A-FACTORY.md), then edits
it: the repository's name under both acts, a local version, their own
settings. Without this tool that copy never receives a fix. With it, the copy
carries a pin, and an update is a pull request a person reviews.

The pin is `factory-pin.yaml` at the top of the study repository: the source
repository, the version of the definition copied, the commit it came from,
the checksum of that definition tree (as `check_factory.py --checksum`
gives it, the change log apart) and of `tools/`, and any study a person chose
to carry on its old definition. This tool writes it; nobody edits it by hand.

  pin       write the pin for a repository whose factory/ and tools/ were
            copied from the source at a commit (`--at`, default HEAD)
  status    compare, and write nothing: has the source moved, what would
            change, what is kept, what conflicts, which studies are locked
  update    write the newer definition and tools into the study repository on
            a new branch, keeping this repository's own edits, bump the pin,
            add a record to the change log, commit, and write the pull
            request's description (`--body-out`)
  selftest  the tool tests itself, in throwaway git repositories

How an update merges, file by file, against the definition at the pinned
commit (the base): a file changed only upstream is taken; a file changed only
here is kept; a file changed on both sides is merged line by line and refused
if the lines meet. `factory.yaml` is merged field by field: a field changed on
both sides to different values is refused, by name, with the three values,
and the merged text must say exactly what the merged fields say. The field
`version` is the tool's: the update gives the definition upstream's version,
or, where this repository's edits are kept, `<upstream version>+local.<n>`, a
version no upstream record can use. The change log is this repository's own,
with upstream's new records after it and one record of the update (its
prediction; what it did is recorded after the merge). `tools/` is taken from
upstream, and a tool edited here and changed upstream is refused. Nothing in
`methods/` or `examples/` is touched.

A locked study is bound to its definition: the lock binds the tree's
checksum, its version and `tools/`, and a changed definition blocks its
opening. So an update is refused while any study is locked and not closed,
unless a person carries that study on its old version
(`--carry-on-old-version studies/NAME`): the pin then records it with the
commit before the update, and its opening is made from a checkout of that
commit (`tools/waiting.py` says so).

Usage:
  factory_update.py pin    --repo DIR --source CLONE [--at REF]
  factory_update.py status --repo DIR --source CLONE [--to REF|PATH] [--json]
  factory_update.py update --repo DIR --source CLONE [--to REF|PATH] --by ACTOR [--model MODEL]
                           [--branch NAME] [--carry-on-old-version studies/NAME ...] [--body-out FILE]
                           [--git-identity "NAME <EMAIL>"] [--json]
  factory_update.py selftest

CLONE is a git clone of the science factory. REF is a commit, branch or tag in
it (default HEAD); PATH is a clean checkout holding factory/ and tools/.
ACTOR is human:<id>, agent:<id> (with --model) or platform:<host> for the
workflow (factory/harnesses/github/update.workflow.yml).

The JSON (`--json`), schema `science-factory/factory-update/v1`:
  {"schema", "repository", "pin", "from": {"version", "commit", "definition_sha256"},
   "to": {"version", "commit", "definition_sha256"}, "moved", "update_needed",
   "factory": {"from_upstream": [path], "kept_here": [path], "merged": [path],
               "fields_kept_here": [{"field", "value"}],
               "conflicts": [{"file", "field"?, "base", "here", "upstream", "why"}]},
   "tools": {"from_upstream": [path], "kept_here": [path], "conflicts": [...]},
   "change_log": {"upstream_records": [{"version", "change", "predicted", "observed", "at"}]},
   "locked_studies": [{"study", "version", "definition_sha256", "carried"}],
   "refused": [reason], "version_after", "branch", "commit", "check", "body", "says"}
`refused` empty means the update can be made (status) or was made (update).
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
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import contextlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import tarfile  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402


class _SourceOnly(importlib.machinery.SourceFileLoader):
    """A module of this factory is loaded from its source text, compiled here, and never from cached bytecode beside it."""

    def get_code(self, fullname):
        return compile(self.get_data(self.path), self.path, "exec", dont_inherit=True)


HERE = Path(__file__).resolve().parent


def neighbour(name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py", loader=_SourceOnly(name, str(HERE / f"{name}.py")))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


sf = neighbour("sf")
cf = sf.definition_tool()  # check_factory.py: how a tree's checksum is made
Refused = sf.Refused
SCHEMA = "science-factory/factory-update/v1"
PIN = "factory-pin.yaml"
LOG = "change-log.jsonl"
ABSENT = "(absent)"
VERSION = re.compile(r"(?m)^version:[ \t]*(\S+)")
SAYS = ("A locked study is bound to its definition: the lock binds the definition tree's checksum, its version and tools/, and a "
        "changed definition blocks its opening. An update is a change to the definition, reviewed as a pull request like any other.")


# ---------------------------------------------------------------- git and trees
def run_git(*args, cwd: Path, identity: str | None = None, check: bool = True, data: bytes | None = None) -> subprocess.CompletedProcess:
    """git, with nothing of the caller's environment that would point it at another repository."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and not (k.startswith("PYTHON") and k not in sf.KEPT_PYTHON)}
    pre = []
    if identity:
        m = re.fullmatch(r"\s*(.+?)\s*<([^<>\s]+)>\s*", identity)
        if not m:
            raise Refused("--git-identity is `NAME <EMAIL>`")
        pre = ["-c", f"user.name={m.group(1)}", "-c", f"user.email={m.group(2)}"]
    done = subprocess.run(["git", "-c", "commit.gpgsign=false", *pre, *args], cwd=cwd, capture_output=True, env=env, input=data)
    if check and done.returncode != 0:
        raise Refused(f"git {' '.join(args[:3])} in {cwd} failed: {done.stderr.decode(errors='replace').strip()[:300]}")
    return done


def commit_of(clone: Path, ref: str) -> str:
    done = run_git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=clone, check=False)
    if done.returncode != 0:
        raise Refused(f"{ref} is not a commit in {clone}: fetch it first (the pin names a commit of the source repository)")
    return done.stdout.decode().strip()


def tree_at(clone: Path, commit: str, out: Path) -> Path:
    """factory/ and tools/ of the source at a commit, taken out of git into a folder."""
    done = run_git("archive", "--format=tar", commit, "factory", "tools", cwd=clone, check=False)
    if done.returncode != 0:
        raise Refused(f"the commit {commit[:12]} of {clone} has no factory/ and tools/ to update from")
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        tar.extractall(out, filter="data")
    return out


def files(root: Path) -> dict:
    """{path: (bytes, executable)} for every file under a folder."""
    if not root.is_dir():
        return {}
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise Refused(f"{p} is a symlink: a definition and its tools are files themselves")
        if p.is_file():
            out[p.relative_to(root).as_posix()] = (p.read_bytes(), bool(p.stat().st_mode & stat.S_IXUSR))
    return out


def write_files(root: Path, got: dict) -> None:
    if root.exists():
        shutil.rmtree(root)
    for rel, (data, exe) in got.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        if exe:
            p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def source_name(clone: Path) -> str:
    done = run_git("remote", "get-url", "origin", cwd=clone, check=False)
    url = done.stdout.decode().strip() if done.returncode == 0 else ""
    return url or str(clone.resolve())


# ---------------------------------------------------------------- the pin
def read_pin(repo: Path) -> dict:
    f = repo / PIN
    if not f.is_file():
        raise Refused(f"{repo} has no {PIN}: write it once with `factory_update.py pin --repo {repo} --source CLONE --at COMMIT`, naming the "
                      "commit of the science factory its factory/ and tools/ were copied from")
    try:
        pin = yaml.safe_load(f.read_text())
    except yaml.YAMLError as e:
        raise Refused(f"{f} is not YAML ({e})")
    need = ("source", "version", "commit", "definition_sha256", "tools_sha256")
    if not isinstance(pin, dict) or any(not pin.get(k) for k in need) or not re.fullmatch(r"[0-9a-f]{40,64}", str(pin.get("commit"))):
        raise Refused(f"{f} names the source, the version, the commit (its full checksum), definition_sha256 and tools_sha256")
    return pin


def pin_text(pin: dict) -> str:
    head = ("# Where this repository's factory came from. tools/factory_update.py writes this file; nobody edits it by hand.\n"
            "# source: the science factory's repository; version and commit: what factory/ and tools/ were copied or last updated\n"
            "# from; definition_sha256 and tools_sha256: the checksums of those trees there (the change log apart), so the base of\n"
            "# the next update can be checked; carried_on_old_version: studies a person chose to keep on the definition they\n"
            "# were locked to, each opened from a checkout of the commit before the update.\n")
    return head + yaml.safe_dump(pin, sort_keys=False)


def checksums(tree: Path) -> dict:
    spec = yaml.safe_load((tree / "factory" / "factory.yaml").read_text())
    return {"version": str(spec.get("version")), "definition_sha256": cf.tree_checksum(tree / "factory")["sha256"],
            "tools_sha256": cf.tools_checksum(tree / "tools")["sha256"]}


def cmd_pin(a) -> dict:
    repo, clone = Path(a.repo).resolve(), Path(a.source).resolve()
    if (repo / PIN).exists():
        raise Refused(f"{repo / PIN} exists: the pin is moved by `update`, never written again by hand")
    commit = commit_of(clone, a.at or "HEAD")
    with tempfile.TemporaryDirectory() as t:
        up = tree_at(clone, commit, Path(t) / "up")
        sums = checksums(up)
        differ = sorted(k for k in set(files(up / "tools")) | set(files(repo / "tools")) if files(up / "tools").get(k) != files(repo / "tools").get(k))
    pin = {"source": source_name(clone), "version": sums["version"], "commit": commit, "definition_sha256": sums["definition_sha256"],
           "tools_sha256": sums["tools_sha256"], "pinned_at": sf.now(), "carried_on_old_version": []}
    (repo / PIN).write_text(pin_text(pin))
    return {"schema": SCHEMA, "repository": str(repo), "pin": pin, "tools_differ_here": differ,
            "says": f"pinned to version {pin['version']} at {commit[:12]} of {pin['source']}"
                    + (f"; tools/ here differs from that commit in {', '.join(differ[:5])}: those count as edits made here" if differ else "")}


# ---------------------------------------------------------------- merging
def flat(obj, at=()) -> dict:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            out.update(flat(v, at + (str(k),)))
        return out if out or not at else {at: {}}
    return {at: obj}


def field(p: tuple) -> str:
    return ".".join(p)


def shown(v) -> str:
    return ABSENT if v is ABSENT else json.dumps(v, default=str)


def merge_lines(here: bytes, base: bytes, up: bytes) -> tuple:
    """(merged bytes, number of places the lines meet), by git's three-way merge of one file."""
    with tempfile.TemporaryDirectory() as t:
        paths = []
        for name, data in (("here", here), ("base", base), ("upstream", up)):
            (Path(t) / name).write_bytes(data)
            paths.append(str(Path(t) / name))
        done = run_git("merge-file", "-p", "--quiet", *paths, cwd=Path(t), check=False)
    if done.returncode < 0 or done.returncode > 127:
        raise Refused("git merge-file could not merge a file")
    return done.stdout, done.returncode


def set_version(text: str, v: str) -> str:
    return VERSION.sub(lambda m: m.group(0).replace(m.group(1), v), text, count=1)


def scalar_spans(text: str) -> dict:
    """{field: (start, end)} of every scalar value under mappings, by its place in the text, comments and all left where they are."""
    out = {}

    def walk(node, at=()):
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                walk(v, at + (str(k.value),))
        elif isinstance(node, yaml.ScalarNode) and at:
            out[at] = (node.start_mark.index, node.end_mark.index)
    walk(yaml.compose(text))
    return out


def upstream_with_these(up: str, here: str, fields: list) -> str | None:
    """Upstream's text with this repository's value of each field put in place of upstream's, scalar by scalar, so that every
    comment and every line upstream wrote stays as upstream wrote it; None when a field is not a scalar on both sides."""
    try:
        su, sh = scalar_spans(up), scalar_spans(here)
    except yaml.YAMLError:
        return None
    if any(k not in su or k not in sh for k in fields):
        return None
    for k in sorted(fields, key=lambda k: su[k][0], reverse=True):
        a, b = su[k]
        up = up[:a] + here[sh[k][0]:sh[k][1]] + up[b:]
    return up


def merge_factory_yaml(here: bytes, base: bytes, up: bytes) -> tuple:
    """(merged text with upstream's version, fields kept from here, conflicts). Field by field; `version` is the tool's."""
    try:
        B, H, U = (yaml.safe_load(x.decode("utf-8")) or {} for x in (base, here, up))
    except (yaml.YAMLError, UnicodeDecodeError) as e:
        return None, [], [{"file": "factory.yaml", "why": f"it does not parse as YAML ({e})"}]
    fb, fh, fu = flat(B), flat(H), flat(U)
    keys = set(fb) | set(fh) | set(fu)
    get = lambda d, k: d.get(k, ABSENT)  # noqa: E731
    mine = {k for k in keys if get(fh, k) != get(fb, k) and k[:1] != ("version",)}
    theirs = {k for k in keys if get(fu, k) != get(fb, k) and k[:1] != ("version",)}
    conflicts = [{"file": "factory.yaml", "field": field(k), "base": shown(get(fb, k)), "here": shown(get(fh, k)), "upstream": shown(get(fu, k)),
                  "why": "both sides changed this field, to different values"}
                 for k in sorted(mine & theirs) if get(fh, k) != get(fu, k)]
    kept = [{"field": field(k), "value": shown(get(fh, k))} for k in sorted(mine - theirs)]
    if conflicts:
        return None, kept, conflicts
    uv = str(U.get("version"))
    want = dict(fb)
    for k in mine:
        want[k] = get(fh, k)
    for k in theirs:
        want[k] = get(fu, k)
    want = {k: v for k, v in want.items() if v is not ABSENT and k[:1] != ("version",)}

    def says(text) -> bool:
        try:
            return text is not None and {k: v for k, v in flat(yaml.safe_load(text) or {}).items() if k[:1] != ("version",)} == want
        except yaml.YAMLError:
            return False
    # first, upstream's text with this repository's values put in, scalar by scalar; then git's line merge
    text = upstream_with_these(up.decode(), here.decode(), sorted(mine - theirs))
    if says(text):
        return text, kept, []
    merged, clashes = merge_lines(set_version(here.decode(), uv).encode(), set_version(base.decode(), uv).encode(), up)
    if clashes:
        return None, kept, [{"file": "factory.yaml", "why": "the fields do not clash, but edits made here and upstream sit on lines next to each "
                                                           "other, and the text cannot be merged without choosing between them: "
                                                           + ", ".join(sorted({field(k) for k in mine})[:6])}]
    if not says(merged.decode()):
        return None, kept, [{"file": "factory.yaml", "why": "the merged text does not say what the merged fields say; merge it by hand"}]
    return merged.decode(), kept, []


def merge_tree(base: dict, here: dict, up: dict, yaml_file: str | None, mergeable: bool) -> dict:
    """Three trees of files, merged. {files, from_upstream, kept_here, merged, conflicts, fields_kept_here}."""
    out = {"files": {}, "from_upstream": [], "kept_here": [], "merged": [], "conflicts": [], "fields_kept_here": []}
    for rel in sorted(set(base) | set(here) | set(up)):
        b, h, u = base.get(rel), here.get(rel), up.get(rel)
        if h == u:
            got = h
        elif h == b:
            got = u
            out["from_upstream"].append(rel)
        elif u == b:
            got = h
            out["kept_here"].append(rel)
        elif rel == yaml_file and h and u and b:
            text, kept, clash = merge_factory_yaml(h[0], b[0], u[0])
            out["fields_kept_here"] += kept
            if clash:
                out["conflicts"] += clash
                continue
            got = (text.encode(), u[1])
            out["merged"].append(rel)
        elif mergeable and h and u and b:
            data, clashes = merge_lines(h[0], b[0], u[0])
            if clashes:
                out["conflicts"].append({"file": rel, "why": f"edited here and upstream, and the edits meet in {clashes} place(s)"})
                continue
            got = (data, u[1] if h[1] == b[1] else h[1])
            out["merged"].append(rel)
        else:
            out["conflicts"].append({"file": rel, "why": ("edited here and changed upstream: a tool is not edited here" if not mergeable else
                                                          "removed on one side and changed on the other")
                                     + f" (base {'present' if b else ABSENT}, here {'present' if h else ABSENT}, upstream {'present' if u else ABSENT})"})
            continue
        if got is not None:
            out["files"][rel] = got
    return out


def log_lines(data: bytes | None) -> list:
    return [ln for ln in (data or b"").decode().splitlines() if ln.strip()]


def plain(rec: dict) -> dict:
    return {"version": (rec.get("context") or {}).get("definition_version"), "change": rec.get("change"), "predicted": rec.get("predicted"),
            "observed": rec.get("observed"), "at": rec.get("at")}


def locked_studies(repo: Path) -> list:
    out = []
    for log in sorted((repo / "studies").glob("*/study-log.jsonl")) if (repo / "studies").is_dir() else []:
        try:
            ev = sf.Study(log.parent).events()
        except Refused:
            continue
        lock = next((e for e in reversed(ev) if e["kind"] == "lock.recorded"), None)
        if lock and not any(e["kind"] == "study.closed" for e in ev):
            d = lock["data"].get("definition") or {}
            out.append({"study": log.parent.relative_to(repo).as_posix(), "version": d.get("version"), "definition_sha256": d.get("sha256")})
    return out


def next_local_version(upstream_version: str, lines: list) -> str:
    n = 0
    pat = re.compile(re.escape(upstream_version) + r"\+local\.(\d+)$")
    for ln in lines:
        with contextlib.suppress(ValueError, TypeError, AttributeError):
            m = pat.match(str((json.loads(ln).get("context") or {}).get("definition_version")))
            if m:
                n = max(n, int(m.group(1)))
    return f"{upstream_version}+local.{n + 1}"


def target(a, clone: Path, t: Path) -> tuple:
    """(the newer tree as a folder, its commit)."""
    to = a.to or "HEAD"
    p = Path(to)
    if p.is_dir() and (p / "factory" / "factory.yaml").is_file():
        dirty = run_git("status", "--porcelain", "--", "factory", "tools", cwd=p, check=False)
        if dirty.returncode != 0 or dirty.stdout.strip():
            raise Refused(f"{p} is not a clean git checkout of factory/ and tools/: an update names the commit it came from, so commit first")
        commit = commit_of(p, "HEAD")
        return tree_at(p, commit, t / "to"), commit
    commit = commit_of(clone, to)
    return tree_at(clone, commit, t / "to"), commit


def plan_update(a, t: Path) -> dict:
    repo, clone = Path(a.repo).resolve(), Path(a.source).resolve()
    pin = read_pin(repo)
    base_tree = tree_at(clone, commit_of(clone, pin["commit"]), t / "base")
    sums = checksums(base_tree)
    refused = []
    if sums["definition_sha256"] != pin["definition_sha256"] or sums["tools_sha256"] != pin["tools_sha256"]:
        refused.append(f"the definition or the tools at the pinned commit {pin['commit'][:12]} are not the trees the pin names by checksum: "
                       "the source is not the repository the pin came from, or the pin was edited")
    up_tree, up_commit = target(a, clone, t)
    to = {**checksums(up_tree), "commit": up_commit}
    frm = {"version": pin["version"], "commit": pin["commit"], "definition_sha256": pin["definition_sha256"], "tools_sha256": pin["tools_sha256"]}
    fb, fh, fu = files(base_tree / "factory"), files(repo / "factory"), files(up_tree / "factory")
    lb, lh, lu = (log_lines((x.get(LOG) or (b"", False))[0]) for x in (fb, fh, fu))
    for x in (fb, fh, fu):
        x.pop(LOG, None)
    fac = merge_tree(fb, fh, fu, "factory.yaml", True)
    tools = merge_tree(files(base_tree / "tools"), files(repo / "tools"), files(up_tree / "tools"), None, False)
    if lh[:len(lb)] != lb:
        refused.append("the change log here does not begin with the change log at the pinned commit: a change log is only added to")
    if lu[:len(lb)] != lb:
        refused.append("upstream's change log does not begin with the change log at the pinned commit: it was rewritten upstream")
    new_up = lu[len(lb):]
    records = []
    for ln in new_up:
        with contextlib.suppress(ValueError):
            records.append(plain(json.loads(ln)))
    locked = locked_studies(repo)
    carried = {str(c).strip("/") for c in a.carry_on_old_version or []}
    for s in locked:
        s["carried"] = s["study"] in carried
        if not s["carried"]:
            refused.append(f"{s['study']} is locked and not closed. A locked study is bound to its definition (version {s['version']}, "
                           f"sha256 {str(s['definition_sha256'])[:16]}): the lock binds the tree, its version and tools/, and an update would "
                           "block its opening. Close it first, or carry it on its old version (`--carry-on-old-version "
                           f"{s['study']}`), and open it from a checkout of the commit before the update")
    unknown = sorted(carried - {s["study"] for s in locked})
    if unknown:
        refused.append(f"--carry-on-old-version names {', '.join(unknown)}, which is not a locked study that is still open here")
    conflicts = fac["conflicts"] + tools["conflicts"]
    if conflicts:
        refused.append(f"{len(conflicts)} conflict(s): both sides changed the same " + ("field or lines" if fac["conflicts"] else "tool")
                       + ", and the update does not choose between them. To take upstream's, make this repository's the same as upstream's "
                       "on a branch and update again; to keep yours, take upstream's in the update and make your change again after it, "
                       "recorded with `sf.py log-change`")
    local = bool(fac["kept_here"] or fac["merged"] or tools["kept_here"])
    after = next_local_version(to["version"], lh + new_up) if local else to["version"]
    moved = pin["commit"] != up_commit
    return {"schema": SCHEMA, "repository": str(repo), "pin": pin, "from": frm, "to": to, "moved": moved,
            "update_needed": moved and (sums["definition_sha256"] != to["definition_sha256"] or sums["tools_sha256"] != to["tools_sha256"] or bool(new_up)),
            "factory": {k: fac[k] for k in ("from_upstream", "kept_here", "merged", "fields_kept_here", "conflicts")},
            "tools": {k: tools[k] for k in ("from_upstream", "kept_here", "conflicts")},
            "change_log": {"upstream_records": records}, "locked_studies": locked, "refused": refused, "version_after": after,
            "branch": None, "commit": None, "check": None, "body": None, "says": SAYS, "_merged": (fac["files"], tools["files"], lh, new_up, up_tree)}


def tool_env() -> dict:
    return {k: v for k, v in os.environ.items() if not (k.startswith("PYTHON") and k not in sf.KEPT_PYTHON)}


def run_check(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(repo / "tools" / "check_factory.py"), *args], cwd=repo, capture_output=True, text=True,
                          env=tool_env(), stdin=subprocess.DEVNULL)


def body_of(p: dict, summary: str, check: dict) -> str:
    frm, to = p["from"], p["to"]
    lines = [f"# Update the factory from {frm['version']} to {to['version']}", "",
             f"This pull request brings the definition and the tools of the science factory from version {frm['version']} (commit "
             f"{frm['commit'][:12]}) to version {to['version']} (commit {to['commit'][:12]}) of {p['pin']['source']}, as version "
             f"{p['version_after']} here. Merging it changes the definition every new study is locked to; it is reviewed like any change to "
             "`factory/`. Nothing in it opens, locks or signs anything.", "",
             "## What this change does to the definition", "", "From `check_factory.py --summary` of the definition here against the one this "
             "pull request writes:", "", summary.strip() or "(no summary was written)", "",
             "## The change-log records between the two versions", ""]
    recs = p["change_log"]["upstream_records"]
    if not recs:
        lines.append("Upstream recorded no change between the two commits.")
    def said(x) -> str:
        x = " ".join(str(x or "").split())
        return x if x.endswith((".", "!", "?")) else x + "."
    for r in recs:
        lines.append(f"- **{r['version']}** ({r['at']}): {said(r['change'])} Predicted: {said(r['predicted'])} "
                     + (f"Observed: {said(r['observed'])}" if r.get("observed") else "Observed: not recorded."))
    lines += ["", "## What is kept from this repository", ""]
    kept = p["factory"]["fields_kept_here"]
    lines += [f"- `factory.yaml`: `{k['field']}` stays {k['value']}." for k in kept]
    lines += [f"- `factory/{f}`: edited here, unchanged upstream, kept." for f in p["factory"]["kept_here"]]
    lines += [f"- `factory/{f}`: edited on both sides, in lines that do not meet: merged." for f in p["factory"]["merged"] if f != "factory.yaml"]
    lines += [f"- `tools/{f}`: edited here, unchanged upstream, kept. TAKE NOTE: a tool is not meant to be edited here." for f in p["tools"]["kept_here"]]
    if not (kept or p["factory"]["kept_here"] or p["tools"]["kept_here"]):
        lines.append("Nothing: this repository had not edited its copy.")
    lines += ["", "## Tools", "", (f"{len(p['tools']['from_upstream'])} file(s) of `tools/` come from upstream: "
                                    + ", ".join(p["tools"]["from_upstream"][:12]) + ".") if p["tools"]["from_upstream"] else "No tool changes.",
              "", "## Studies", ""]
    carried = [s for s in p["locked_studies"] if s["carried"]]
    lines.append("No study here is locked and still open." if not carried else "")
    for s in carried:
        lines.append(f"- `{s['study']}` is locked to version {s['version']} (sha256 {str(s['definition_sha256'])[:16]}) and a person carried it on that "
                     f"version: its opening is made from a checkout of {p['pin_after']['carried_on_old_version'][-1]['commit_before_update'][:12]}, the "
                     "commit before this update. A locked study is bound to its definition.")
    lines += ["", "## The check", "", f"`check_factory.py` on the definition this pull request writes: **{check['result']}** (its last line: `{check['last_line']}`).", "",
              "After merging, record what the update did: `uv run tools/sf.py log-change --study studies/SETUP --by human:YOUR-ID --log "
              "factory/change-log.jsonl --problem \"the factory here is behind the science factory it was copied from\" --change \"...\" "
              "--rationale \"...\" --predicted \"...\" --observed \"what it did\"`.", ""]
    return "\n".join(x for x in lines if x is not None) + "\n"


def cmd_status(a) -> dict:
    with tempfile.TemporaryDirectory() as t:
        p = plan_update(a, Path(t))
    p.pop("_merged")
    return p


def cmd_update(a) -> dict:
    repo = Path(a.repo).resolve()
    if sf.PLATFORM_ACTOR.fullmatch(str(a.by or "")):
        pass
    else:
        sf.Study.check_actor(a.by)
        if str(a.by).startswith("agent:") and not a.model:
            raise Refused(sf.NO_MODEL)
    if run_git("status", "--porcelain", cwd=repo).stdout.strip():
        raise Refused(f"{repo} has changes not committed: an update is made on a new branch from a clean work tree")
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        p = plan_update(a, t)
        merged, tools, lh, new_up, up_tree = p.pop("_merged")
        if not p["moved"]:
            p["refused"].append(f"the source has not moved: the pin is at {p['from']['commit'][:12]}, which is {p['to']['commit'][:12]}")
        if p["refused"]:
            return p
        before = run_git("rev-parse", "HEAD", cwd=repo).stdout.decode().strip()
        branch = a.branch or f"factory-update/{p['to']['version']}"
        if run_git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=repo, check=False).returncode == 0:
            p["refused"].append(f"the branch {branch} exists: an update for this version is already on a branch")
            return p
        old = t / "old-factory"
        shutil.copytree(repo / "factory", old)
        run_git("switch", "-q", "-c", branch, cwd=repo)
        text = merged.get("factory.yaml")
        if text is None:
            raise Refused("the merged definition has no factory.yaml")
        merged["factory.yaml"] = (set_version(text[0].decode(), p["version_after"]).encode(), text[1])
        write_files(repo / "tools", tools)
        log_now = lh + new_up
        write_files(repo / "factory", {**merged, LOG: ("".join(x + "\n" for x in log_now).encode(), False)})
        spec = yaml.safe_load(merged["factory.yaml"][0].decode())
        rec = {"at": sf.now(), "by": a.by, "problem_class": "the factory here is behind the science factory it was copied from",
               "change": f"Update from upstream {p['from']['version']} ({p['from']['commit'][:12]}) to {p['to']['version']} ({p['to']['commit'][:12]}), "
                         f"as version {p['version_after']}: {len(p['factory']['from_upstream'])} definition file(s) from upstream, "
                         f"{len(p['factory']['kept_here'])} kept from here, {len(p['factory']['merged'])} merged, {len(tools)} tool file(s).",
               "rationale": "a copy of the factory that is never updated never receives a fix; tools/factory_update.py keeps this repository's own edits",
               "predicted": "check_factory.py says VALID on the merged definition, and no locked study's opening is blocked except one carried on its old version",
               "observed": None,
               "context": {"model": a.model, "definition_sha": cf.tree_checksum(repo / "factory")["sha256"], "definition_version": p["version_after"],
                           "acts_sha256": cf.acts_sha256(spec), "evidence_study": None, "log_fingerprint": None,
                           "update": {"from": p["from"], "to": {k: p["to"][k] for k in ("version", "commit", "definition_sha256", "tools_sha256")}}},
               "log_event": None}
        with (repo / "factory" / LOG).open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        pin = {k: v for k, v in p["pin"].items() if k != "carried_on_old_version"}
        pin.update(version=p["to"]["version"], commit=p["to"]["commit"], definition_sha256=p["to"]["definition_sha256"],
                   tools_sha256=p["to"]["tools_sha256"], pinned_at=sf.now(),
                   carried_on_old_version=list(p["pin"].get("carried_on_old_version") or [])
                   + [{"study": s["study"], "version": s["version"], "definition_sha256": s["definition_sha256"], "commit_before_update": before}
                      for s in p["locked_studies"] if s["carried"]])
        (repo / PIN).write_text(pin_text(pin))
        p["pin_after"] = pin
        checked = run_check(repo)
        last = (checked.stdout.strip().splitlines() or ["(nothing printed)"])[-1]
        p["check"] = {"result": {0: "valid", 1: "invalid", 2: "not validated"}.get(checked.returncode, f"exit {checked.returncode}"),
                      "exit": checked.returncode, "last_line": last.replace("check-factory: ", "")}
        summary = "\n".join(run_check(repo, "--summary", str(old), str(repo / "factory")).stdout.splitlines()[1:])
        body = body_of(p, summary, p["check"])
        run_git("add", "-A", "--", "factory", "tools", PIN, cwd=repo)
        run_git("commit", "-q", "-m", f"Update the factory from {p['from']['version']} to {p['to']['version']}, as {p['version_after']}",
                cwd=repo, identity=a.git_identity)
        p.update(branch=branch, commit=run_git("rev-parse", "HEAD", cwd=repo).stdout.decode().strip())
        out = Path(a.body_out) if a.body_out else None
        if out:
            out.write_text(body)
        p["body"] = body
    return p


def in_words(p: dict) -> str:
    if "pin" in p and "from" not in p:
        return p["says"] + "\n"
    lines = [f"factory update: {p['repository']}",
             f"  pinned: version {p['from']['version']} at {p['from']['commit'][:12]}; upstream: version {p['to']['version']} at {p['to']['commit'][:12]}"
             + ("" if p["moved"] else " (the source has not moved)")]
    f, t = p["factory"], p["tools"]
    lines.append(f"  definition: {len(f['from_upstream'])} file(s) from upstream, {len(f['kept_here'])} kept from here, {len(f['merged'])} merged; "
                 f"tools: {len(t['from_upstream'])} from upstream, {len(t['kept_here'])} kept from here")
    for k in f["fields_kept_here"]:
        lines.append(f"  kept from here: factory.yaml `{k['field']}` = {k['value']}")
    for c in f["conflicts"] + t["conflicts"]:
        lines.append(f"  CONFLICT: {c['file']}" + (f" `{c['field']}`: at the pin {c['base']}, here {c['here']}, upstream {c['upstream']}" if c.get("field") else "")
                     + f" ({c['why']})")
    for s in p["locked_studies"]:
        lines.append(f"  locked and not closed: {s['study']} (version {s['version']})" + (", carried on its old version" if s["carried"] else ""))
    lines.append(f"  {len(p['change_log']['upstream_records'])} upstream change-log record(s) between the two; the version here after the update: {p['version_after']}")
    for r in p["refused"]:
        lines.append(f"  REFUSED: {r}")
    if p.get("branch"):
        lines.append(f"  written on the branch {p['branch']} (commit {p['commit'][:12]}); check_factory: {p['check']['result']}")
    elif not p["refused"]:
        lines.append("  the update can be made" if p["update_needed"] else "  nothing to update")
    lines.append(f"  {SAYS}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    results = []

    def check(name: str, ok) -> None:
        results.append((name, bool(ok)))

    root = HERE.parent
    with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
        t = Path(t).resolve()
        ident = "selftest <s@example.invalid>"
        g = lambda repo, *w: run_git(*w, cwd=repo, identity=ident)  # noqa: E731

        def commit(repo: Path, msg: str) -> str:
            g(repo, "add", "-A")
            g(repo, "commit", "-q", "-m", msg)
            return g(repo, "rev-parse", "HEAD").stdout.decode().strip()

        def edit(p: Path, old: str, new: str) -> None:
            s = p.read_text()
            assert old in s, (p, old)
            p.write_text(s.replace(old, new, 1))

        def record(log: Path, version: str, change: str, acts_of: Path | None = None) -> None:
            spec = yaml.safe_load((acts_of or log.parent / "factory.yaml").read_text())
            with log.open("a") as f:
                f.write(json.dumps({"at": sf.now(), "by": "agent:coordinating", "problem_class": "a test", "change": change, "rationale": "x",
                                    "predicted": "it is valid", "observed": None,
                                    "context": {"definition_version": version, "acts_sha256": cf.acts_sha256(spec)}}) + "\n")

        # upstream: a throwaway repository holding this factory, the tools, the methods and the system trial's plan
        up = t / "upstream"
        for part in ("factory", "tools", "methods"):
            shutil.copytree(root / part, up / part, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(root / "examples" / "stand-alone" / "system-trial", up / "examples" / "stand-alone" / "system-trial")
        g(up, "init", "-q", "-b", "main")
        commit(up, "upstream at its current version")

        def study_repo(name: str, local: bool = True) -> Path:
            """A study repository made the way docs/FIRST-STUDY.md says: a copy, its repository named, a local version, recorded, pinned."""
            r = t / name
            here_version = str(yaml.safe_load((up / "factory" / "factory.yaml").read_text())["version"])
            for part in ("factory", "tools", "methods"):
                shutil.copytree(up / part, r / part)
            shutil.copytree(up / "examples", r / "examples")
            g(r, "init", "-q", "-b", "main")
            if local:
                fy = r / "factory" / "factory.yaml"
                fy.write_text(fy.read_text().replace("example-org/example-studies", "owner/my-science"))
                edit(fy, f"version: {here_version} ", f"version: {here_version}+local.1 ")
                record(r / "factory" / LOG, f"{here_version}+local.1", "the repository is named")
            head = g(up, "rev-parse", "HEAD").stdout.decode().strip()
            got = cmd_pin(argparse.Namespace(repo=str(r), source=str(up), at=None))
            check(f"{name}: the pin names the source, the version, the commit and both checksums", got["pin"]["commit"] == head and got["pin"]["version"] == here_version
                  and len(got["pin"]["definition_sha256"]) == 64 and not got["tools_differ_here"])
            commit(r, "the factory, copied and pinned")
            return r

        def upstream_moves(new_version: str, change) -> str:
            fy = up / "factory" / "factory.yaml"
            was = str(yaml.safe_load(fy.read_text())["version"])
            edit(fy, f"version: {was} ", f"version: {new_version} ")
            change()
            record(up / "factory" / LOG, new_version, f"Definition {new_version}: a change upstream.")
            return commit(up, f"upstream {new_version}")

        def args(r: Path, **k) -> argparse.Namespace:
            return argparse.Namespace(**{"repo": str(r), "source": str(up), "to": None, "by": "human:throwaway-placeholder", "model": None, "branch": None,
                                         "carry_on_old_version": None, "body_out": None, "git_identity": ident, **k})

        # 1. no conflict: upstream changed an agent's file; this repository named itself
        plain_repo = study_repo("plain")
        check("before upstream moves, status says the source has not moved and nothing is to update",
              (lambda s: not s["moved"] and not s["update_needed"])(cmd_status(args(plain_repo))))
        review = up / "factory" / "agents" / "review" / "agent.md"
        v1 = upstream_moves("0.90.0", lambda: review.write_text(review.read_text() + "\nA sentence added upstream.\n"))
        s = cmd_status(args(plain_repo))
        check("status: the source has moved, the agent's file comes from upstream, the repository's name is kept, and nothing conflicts",
              s["moved"] and s["update_needed"] and "agents/review/agent.md" in s["factory"]["from_upstream"] and not s["refused"]
              and {"field": "procedure.acts_by_people.lock.repository", "value": '"owner/my-science"'} in s["factory"]["fields_kept_here"]
              and s["version_after"] == "0.90.0+local.1" and [r["version"] for r in s["change_log"]["upstream_records"]] == ["0.90.0"])
        done = cmd_update(args(plain_repo))
        fy = yaml.safe_load((plain_repo / "factory" / "factory.yaml").read_text())
        pin = yaml.safe_load((plain_repo / PIN).read_text())
        check("update with no conflict: on a new branch, the agent's file is upstream's, the acts name this repository, the version is local "
              "to upstream's, and the pin moved", not done["refused"] and done["branch"] == "factory-update/0.90.0"
              and (plain_repo / "factory" / "agents" / "review" / "agent.md").read_bytes() == review.read_bytes()
              and fy["procedure"]["acts_by_people"]["lock"]["repository"] == "owner/my-science" and fy["version"] == "0.90.0+local.1"
              and pin["commit"] == v1 and pin["version"] == "0.90.0"
              and g(plain_repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.decode().strip() == "factory-update/0.90.0")
        check("the merged definition is valid, said by its own tools", done["check"]["result"] == "valid")
        logged = log_lines((plain_repo / "factory" / LOG).read_bytes())
        check("the change log is this repository's, then upstream's new record, then the update's own, which predicts and leaves the outcome for after",
              logged[:len(log_lines(g(plain_repo, "show", f"main:factory/{LOG}").stdout))] == log_lines(g(plain_repo, "show", f"main:factory/{LOG}").stdout)
              and json.loads(logged[-2])["context"]["definition_version"] == "0.90.0" and json.loads(logged[-1])["observed"] is None
              and json.loads(logged[-1])["context"]["definition_version"] == "0.90.0+local.1")
        body = done["body"]
        check("the description is the summary of old against new and the change-log records between the two, in plain words",
              "## What this change does to the definition" in body and "The definition's version goes from" in body
              and "agents/review/agent.md" in body and "**0.90.0**" in body and "Definition 0.90.0: a change upstream." in body
              and "`procedure.acts_by_people.lock.repository` stays \"owner/my-science\"" in body and "**valid**" in body)
        check("the work tree is clean after the update: everything is in one commit on the branch", not g(plain_repo, "status", "--porcelain").stdout.strip())
        g(plain_repo, "switch", "-q", "main")
        check("an update is not made twice for the same version", any("exists" in r for r in cmd_update(args(plain_repo))["refused"]))

        # 2. a local edit kept: this repository edited a skill; upstream changed something else
        kept_repo = study_repo("kept")
        skill = kept_repo / "factory" / "skills" / "read-what-is-known" / "SKILL.md"
        skill.write_text(skill.read_text() + "\nA local sentence of this repository.\n")
        commit(kept_repo, "a local edit to a skill")
        tmpl = up / "factory" / "templates" / "request.md"
        v2 = upstream_moves("0.91.0", lambda: tmpl.write_text(tmpl.read_text() + "\nA line added upstream.\n"))
        done = cmd_update(args(kept_repo))
        check("update with a local edit kept: the skill keeps this repository's sentence, the template is upstream's, and both are said",
              not done["refused"] and "A local sentence of this repository." in skill.read_text()
              and (kept_repo / "factory" / "templates" / "request.md").read_bytes() == tmpl.read_bytes()
              and "skills/read-what-is-known/SKILL.md" in done["factory"]["kept_here"] and "edited here, unchanged upstream, kept" in done["body"]
              and done["check"]["result"] == "valid" and done["to"]["commit"] == v2)

        # 3. a conflict refused: both sides changed the number of approvals the lock needs
        clash_repo = study_repo("clash")
        cfy = clash_repo / "factory" / "factory.yaml"
        edit(cfy, "approvals: 1 ", "approvals: 2 ")
        commit(clash_repo, "two approvals here")
        v3 = upstream_moves("0.92.0", lambda: edit(up / "factory" / "factory.yaml", "approvals: 1 ", "approvals: 3 "))
        was = cfy.read_bytes()
        done = cmd_update(args(clash_repo))
        c = [x for x in done["factory"]["conflicts"] if x.get("field") == "procedure.acts_by_people.lock.approvals"]
        check("update with a conflict is refused, naming the field and its three values, and writes nothing and makes no branch",
              done["refused"] and len(c) == 1 and (c[0]["base"], c[0]["here"], c[0]["upstream"]) == ("1", "2", "3") and done["branch"] is None
              and cfy.read_bytes() == was and g(clash_repo, "branch", "--list", "factory-update/*").stdout.strip() == b"")
        check("in plain words the conflict says where the field stood at the pin, here and upstream", "at the pin 1, here 2, upstream 3" in in_words(done))
        edit(cfy, "approvals: 2 ", "approvals: 3 ")
        commit(clash_repo, "take upstream's number")
        done = cmd_update(args(clash_repo))
        check("made the same as upstream's, the field no longer conflicts and the update goes through, every comment of upstream's text kept",
              not done["refused"] and done["to"]["commit"] == v3 and "approvals: 3 " in cfy.read_text()
              and [ln for ln in cfy.read_text().splitlines() if ln.lstrip().startswith("#")]
              == [ln for ln in (up / "factory" / "factory.yaml").read_text().splitlines() if ln.lstrip().startswith("#")])

        # 4. refused because a study is locked and not closed
        locked_repo = study_repo("locked")
        sf.Study.default_model, sf.Study.default_route, sf.PLATFORM_CALL = "selftest-model", sf.PRACTICE, sf._dead_platform
        study = sf._fresh(locked_repo / "studies", "S1", start=sf.A(id="S1", question=sf.PLAN["question"], by="agent:coordinating"))
        sf.cmd_test(study, sf.A(what="known-answers", by="agent:analysis"))
        sf.cmd_test(study, sf.A(what="working-data", by="agent:analysis"))
        sf.cmd_lock(study, sf.A(by="human:throwaway-placeholder", evidence=sf.URL, local_practice=True))
        commit(locked_repo, "a study, locked")
        v4 = upstream_moves("0.93.0", lambda: review.write_text(review.read_text() + "\nAnother sentence.\n"))
        done = cmd_update(args(locked_repo))
        check("update refused because a study is locked and not closed, saying that a locked study is bound to its definition",
              done["refused"] and any("studies/S1 is locked and not closed" in r and "bound to its definition" in r for r in done["refused"])
              and done["branch"] is None)
        before = g(locked_repo, "rev-parse", "HEAD").stdout.decode().strip()
        done = cmd_update(args(locked_repo, carry_on_old_version=["studies/S1"]))
        pin = yaml.safe_load((locked_repo / PIN).read_text())
        check("carried on its old version by a person's explicit choice, the update goes through and the pin names the study and the commit before",
              not done["refused"] and pin["carried_on_old_version"] == [{"study": "studies/S1", "version": study.last("lock.recorded")["data"]["definition"]["version"],
                                                                        "definition_sha256": study.last("lock.recorded")["data"]["definition"]["sha256"],
                                                                        "commit_before_update": before}]
              and "a person carried it on that version" in done["body"] and done["to"]["commit"] == v4)
        check("an unknown study cannot be carried", any("not a locked study" in r for r in cmd_status(args(locked_repo, carry_on_old_version=["studies/NOPE"]))["refused"]))

        # 5. what the description says, and a tool edited here
        tool_repo = study_repo("tools")
        (tool_repo / "tools" / "fence.py").write_text((tool_repo / "tools" / "fence.py").read_text() + "\n# a local edit\n")
        commit(tool_repo, "a tool edited here")
        upstream_moves("0.94.0", lambda: (up / "tools" / "fence.py").write_text((up / "tools" / "fence.py").read_text() + "\n# upstream\n"))
        s = cmd_status(args(tool_repo))
        check("a tool edited here and changed upstream is a conflict: a tool is not edited in a study repository",
              any(c["file"] == "fence.py" and "a tool is not edited here" in c["why"] for c in s["tools"]["conflicts"]) and s["refused"])
        none = study_repo("unedited", local=False)
        v6 = upstream_moves("0.95.0", lambda: tmpl.write_text(tmpl.read_text() + "\nOne more line.\n"))
        done = cmd_update(args(none, to=v6))
        check("a repository with no edits of its own takes upstream's version as it is, and says nothing was kept",
              not done["refused"] and yaml.safe_load((none / "factory" / "factory.yaml").read_text())["version"] == "0.95.0"
              and "Nothing: this repository had not edited its copy." in done["body"])
        tampered = study_repo("tampered")
        p_ = yaml.safe_load((tampered / PIN).read_text())
        p_["definition_sha256"] = "0" * 64
        (tampered / PIN).write_text(pin_text(p_))
        check("a pin whose checksum is not the tree at its commit is refused", any("not the trees the pin names" in r for r in cmd_status(args(tampered))["refused"]))
        check("the JSON keys are the ones the docstring documents", set(cmd_status(args(tampered))) == {
            "schema", "repository", "pin", "from", "to", "moved", "update_needed", "factory", "tools", "change_log", "locked_studies", "refused",
            "version_after", "branch", "commit", "check", "body", "says"})
        cli = subprocess.run([sys.executable, str(Path(__file__).resolve()), "status", "--repo", str(none), "--source", str(up), "--json"],
                             capture_output=True, text=True, env=tool_env())
        check("the command prints the JSON, and says the source has not moved since the update", cli.returncode == 0
              and json.loads(cli.stdout)["schema"] == SCHEMA and json.loads(cli.stdout)["moved"] is False)
    failed = [n for n, ok in results if not ok]
    for n, ok in results:
        print(("PASS  " if ok else "FAIL  ") + n)
    print(f"selftest: {'PASS' if not failed else 'FAIL'} ({len(results) - len(failed)} of {len(results)})")
    return 0 if not failed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    repo = (["--repo"], {"required": True, "help": "the study repository (a git work tree with factory/, tools/ and the pin)"})
    source = (["--source"], {"required": True, "help": "a git clone of the science factory"})
    to = (["--to"], {"default": None, "help": "a commit, branch or tag of the source, or a clean checkout's path (default HEAD of the source)"})
    js = (["--json"], {"action": "store_true", "help": "print the JSON this docstring documents"})

    def add(name, *opts):
        p = sub.add_parser(name, allow_abbrev=False)
        for names, kw in opts:
            p.add_argument(*names, **kw)
        return p
    add("pin", repo, source, (["--at"], {"default": None, "help": "the commit factory/ and tools/ were copied from (default HEAD)"}), js)
    add("status", repo, source, to, (["--carry-on-old-version"], {"action": "append", "default": None, "dest": "carry_on_old_version"}), js)
    add("update", repo, source, to, js, (["--by"], {"required": True, "help": "human:<id>, agent:<id> (with --model), or platform:<host>"}),
        (["--model"], {"default": None}), (["--branch"], {"default": None}),
        (["--carry-on-old-version"], {"action": "append", "default": None, "dest": "carry_on_old_version",
                                      "help": "studies/NAME: a locked study a person keeps on its old definition; repeatable"}),
        (["--body-out"], {"default": None, "help": "where the pull request's description is written"}),
        (["--git-identity"], {"default": None, "help": "NAME <EMAIL> for the commit, when git has none"}))
    sub.add_parser("selftest", allow_abbrev=False)
    a = ap.parse_args()
    try:
        sf.refuse_dirty_environment()
        sf.refuse_inside_a_look()
        if a.cmd == "selftest":
            return selftest()
        got = {"pin": cmd_pin, "status": cmd_status, "update": cmd_update}[a.cmd](a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    print(json.dumps(got, indent=1) if a.json else in_words(got), end="" if not a.json else "\n")
    return 2 if got.get("refused") else 0


if __name__ == "__main__":
    sys.exit(main())
