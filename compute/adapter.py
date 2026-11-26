#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""adapter: the science factory's compute contract, the one runner
that is built, the conformance test any runner must pass, and the test of
that test.

A known-answer test, a run on working data, a rehearsal and an opening of
the held-out data are each to be one JOB, and a runner is anything
that can do four things with a job. Nothing in the study tool calls this
yet: sf.py still runs its own commands. This file is the contract and its
proof, ready for that wiring.

THE JOB SPEC  (JSON; a field not listed here is refused)

  job        A name for people. It identifies nothing.
  key        The idempotency key: what this job is. For an opening it is
             exactly study, test, opening and lock: the study id, the
             test, the opening number and the lock's fingerprint
             (SEQ:HASH). Any other job gives study, test and whatever
             else names the run. The job id is the first 16 hex digits of
             the sha256 of the key, so it is known before submit and is
             the same from every checkout and every process. Sixteen hex
             digits are 64 bits: safe against accident, not evidence by
             themselves. The run log carries the whole key and the sha256
             of the whole spec.
  argv       The command, as unexpanded tokens. An argument that starts
             with {name} is expanded by the runner: {python} is the
             runner's interpreter and {work} the job's working directory;
             a runner may define more (the local runner takes
             --token kit=DIR). An unknown token is refused. A spec that
             spells out a path of its own is tied to one machine.
  outputs    The files the job will write, as relative paths under its
             working directory. An absolute path, a path with `..` and
             the name run-log.json are refused.
  inputs_manifest
             Optional. Files that must be what the lock says before the
             job may start: {file: "sha256:<64 hex>"}, each file named by
             a token or an absolute path. The runner hashes each one from
             inside the job's environment and does not start the argv
             when one differs.
  environment
             Optional. What the job expects of its surroundings (a
             commit, an image, a lockfile). Carried, not checked: it
             comes back as declared_environment.
  resources  Optional. A runner honours a resource or refuses the spec.
             The local runner honours walltime_seconds and no other.
  env        Optional. Names of environment variables the job needs
             beyond the short list below. No name may start with PYTHON.

THE FOUR VERBS

  submit   Checks the spec, then starts the job. The same key with the
           same spec is the same job: the same id comes back with
           already_submitted true and nothing starts, while the job runs
           and for ever after it ended. The same key with a different
           spec is refused. A submit that died before its record was
           written leaves no job and can be made again; one that died
           after the record and before the job was released leaves a
           failed job that never started.
  status   The phase, the exit code, the reason when there is one, and
           the markers. The phases:
             queued     accepted; the argv has not started
             running    the argv has started and its supervisor is alive
             done       the argv ended by itself; exit is its own code
             failed     it did not: killed by a signal, over its time
                        limit, could not be run, held back by a manifest
                        that did not match, or its supervisor died
             cancelled  stopped by cancel, and gone
             lost       this runner has no record of that id
  collect  Refused until the job is done, failed or cancelled, which is
           when nothing about it can change. Brings back the declared
           outputs that exist, under their relative paths, and
           run-log.json, and nothing else. An output must be a regular
           file inside the working directory, reached without following
           a symlink; any other is left behind and named in the run log.
           Collecting twice gives the same answer.
  cancel   SIGTERM, a wait, SIGKILL; cancelled is reported only when the
           job's processes are gone. A job that had already ended stays
           what it was, and one that ends by itself with an exit code
           while being asked to stop is done, with that code.

MARKERS

  fetch.started  decides whether an opening is used up, and it is written
           by the runner, never by the method: after the manifest matched
           and before the job can reach any data (before the argv starts;
           on a runner that holds a credential or a network route back,
           before it is released). A job that has the marker has used its
           opening up, however it ended. A job without it never started,
           and a person may void it.
  job_markers  are files named marker.<name> that the job writes in its
           working directory to say how far it got. They are for reading
           and are never the grounds for a void.

THE RUN LOG  (returned by collect and written beside the outputs)

  what       job, key, job_id, spec_sha256, argv (as given) and
             argv_started (as expanded; null if it never started)
  where      runner, host, user, platform, and, found from inside the
             job's environment, program (the file argv[0] resolved to,
             with its sha256) and interpreter (its path and version,
             asked of the program itself when it is a Python interpreter;
             null when it is not)
  with what  inputs (for each manifest entry the declared and the
             observed sha256), env_names (names, never values),
             resources (honoured), declared_environment (not checked)
  when       submitted_at, started_at, ended_at
  result     phase, exit, reason, markers, job_markers, outputs (the
             sha256 of each, taken when the job ended; null if absent),
             outputs_refused, log_sha256 and log_bytes (what the job
             printed stays at the runner; only its hash comes back)

THE JOB'S ENVIRONMENT

  Built, not inherited: PATH, HOME, LANG, LC_ALL, TZ, TMPDIR, USER and
  LOGNAME, plus the names the spec lists under env. Every variable whose
  name starts with PYTHON is dropped, and then three are set:
  PYTHONPYCACHEPREFIX to a new empty temporary directory for each job (so
  bytecode planted beside a source file is never read), PYTHONNOUSERSITE=1
  and PYTHONDONTWRITEBYTECODE=1. The runner adds SF_PLACE_JOB, a tag it
  uses to find what a job left running. (A Python job may also see
  LC_CTYPE: its own interpreter adds that when the locale is plain C.)

WHAT IS LEFT TO THE STUDY TOOL, AND WHAT IS NOT BUILT

  One opening. A runner refuses a second spec under a used key and never
  runs a key twice, but it knows only its own jobs: a second runner, or
  the next opening number, is a new job. The study log is what limits
  openings to one. It writes the opening before it submits (the id is
  known beforehand), and it decides whether a job without fetch.started
  may be voided.
  The locked code. A runner checks the files the manifest names and no
  others. Which files those are, and a module or a folder planted beside
  them under another name, is the study tool's to bind.
  Who may ask for what. The runner records the names a job asked for under
  env; which job may be given a credential is for the analysis plan.
  Not built: removing a job (what a job wrote stays at the runner until a
  person deletes it), a bound on the size of outputs, any resource but a
  time limit, and steps with a check between them (a job is one argv).

THE LOCAL RUNNER

  LocalRunner keeps its own records in <root>/state/<job id>/ and runs the
  job in <root>/work/<job id>/, so a job that writes only where it was
  put cannot touch them. One supervisor process for each job holds a file
  lock while it lives (which is how status tells a dead job from a
  running one), is handed the argv through a pipe from submit and never
  reads it back from disk, stops the job and everything it left running,
  then hashes the outputs and copies them into the runner's own keep. It
  is not the runner for an opening: the job runs as the same user on the
  same machine as whoever built the method, so a job that goes looking
  can read and rewrite the runner's records, a job that leaves its session
  and drops its tag can outlive a cancel, and the interpreter is the one
  on that machine. Its run log is evidence, not proof.

CONFORMANCE

  `conformance --runner REF` runs against any runner, using only the four
  verbs and what collect brings back: the interpreter is the runner's
  ({python}) and the waits are the runner's (settle_seconds,
  grace_seconds). A runner is built when it passes. `conformance
  --self-check` tests the test: it runs it against the deliberately wrong
  runners kept at the end of this file and passes only if every one of
  them fails on the checks written for its defect, the honest runners
  pass, every check is failed by some wrong runner, and the local runner's
  own records stand up to a hand on its disk.

Usage:
  adapter.py submit  --root DIR --spec SPEC.json [--token NAME=PATH ...] [--runner REF]
  adapter.py status  --root DIR --job ID [--runner REF]
  adapter.py collect --root DIR --job ID --into DIR [--runner REF]
  adapter.py cancel  --root DIR --job ID [--runner REF]
  adapter.py conformance [--runner REF]
  adapter.py conformance --self-check

REF is a class in this file, module:Class, or path/to/file.py:Class; the
class is made with one argument, the directory it may keep its records in.
"""
import argparse
import contextlib
import datetime as dt
import errno
import fcntl
import getpass
import hashlib
import importlib
import importlib.util
import json
import marshal
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SELF = Path(__file__).resolve()
SPEC_FIELDS = ("job", "key", "argv", "outputs", "inputs_manifest", "environment", "resources", "env")
REQUIRED = ("job", "key", "argv", "outputs")
OPENING_KEY = ["lock", "opening", "study", "test"]
PASSED_ON = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR", "USER", "LOGNAME")
SET_BY_THE_PLACE = {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}  # and PYTHONPYCACHEPREFIX, new for each job
TAG = "SF_PLACE_JOB"            # set in a job's environment so the runner can find what the job left running
MARKERS = ("fetch.started",)    # written by the runner, never by the job
FINAL = ("done", "failed", "cancelled")
STATUS_KEYS = ("job_id", "phase", "exit", "reason", "markers", "job_markers")
RUN_LOG_KEYS = ("job_id", "job", "key", "runner", "spec_sha256", "argv", "argv_started", "phase", "exit", "reason", "markers",
                "job_markers", "outputs", "outputs_refused", "inputs", "declared_environment", "resources", "env_names", "host",
                "user", "platform", "interpreter", "program", "submitted_at", "started_at", "ended_at", "log_sha256", "log_bytes")
ID = re.compile(r"[0-9a-f]{16}")
TOKEN = re.compile(r"\{([a-z][a-z0-9_]*)\}")
SHA = re.compile(r"sha256:[0-9a-f]{64}")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
MARKER = re.compile(r"marker\.([a-z0-9][a-z0-9._-]{0,63})")
STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


class Refused(ValueError):
    """The contract says no. Nothing was started and nothing was changed."""


# ---------------------------------------------------------------- the contract's own arithmetic

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path) -> str | None:
    """sha256 of a regular file (a symlink to one is followed); None for anything else."""
    try:
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK), "rb") as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                return None
            h = hashlib.sha256()
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
            return h.hexdigest()
    except OSError:
        return None


def spec_sha256(spec: dict) -> str:
    return sha_bytes(canonical(spec))


def job_id_of(key: dict) -> str:
    """The job id anyone can work out from the idempotency key: 64 bits of its sha256."""
    return sha_bytes(canonical(key))[:16]


def expand(arg: str, tokens: dict) -> str:
    """Put the runner's value for a leading {name}; leave anything else as it is."""
    m = TOKEN.match(arg)
    return tokens[m[1]] + arg[m.end():] if m else arg


def output_problem(name) -> str | None:
    """Why a name cannot be an output, or None. An output is a relative path that stays inside the working directory."""
    if not isinstance(name, str) or not name or "\0" in name:
        return "is not a file name"
    if name.startswith("/"):
        return "is an absolute path"
    if any(part in ("", ".", "..") for part in name.split("/")):
        return "does not stay inside the working directory"
    if name == "run-log.json":
        return "is the run log's own name"
    return None


def check_spec(spec, tokens, resources, strict_outputs: bool = True) -> dict:
    """The shape every runner checks at submit. `tokens` are the names the
    runner expands and `resources` the ones it honours."""
    def no(why):
        raise Refused(why)

    def plain(v):
        return (isinstance(v, str) and v != "") or (isinstance(v, int) and not isinstance(v, bool))

    if not isinstance(spec, dict):
        no("a job spec is a JSON object")
    extra = sorted(set(spec) - set(SPEC_FIELDS), key=str)
    if extra:
        no(f"a job spec has no field named {extra}; its fields are {list(SPEC_FIELDS)}")
    missing = [k for k in REQUIRED if k not in spec]
    if missing:
        no(f"job spec lacks {missing}")
    try:
        canonical(spec)
    except (TypeError, ValueError):
        no("a job spec holds JSON values only")
    if not (isinstance(spec["job"], str) and spec["job"].strip()):
        no("job is a name for people: a string that is not empty")
    key = spec["key"]
    if not (isinstance(key, dict) and all(plain(v) for v in key.values())
            and isinstance(key.get("study"), str) and isinstance(key.get("test"), str)):
        no("key is the idempotency key: an object with study and test, its values strings or whole numbers")
    if ("opening" in key or "lock" in key) and not (sorted(key) == OPENING_KEY and isinstance(key["opening"], int)
                                                    and key["opening"] >= 1 and isinstance(key["lock"], str)):
        no("the key of an opening is exactly study, test, opening (a whole number from 1) and lock (the lock's fingerprint)")
    argv = spec["argv"]
    if not (isinstance(argv, list) and argv and all(isinstance(a, str) and "\0" not in a for a in argv) and argv[0]):
        no("argv is a list of strings, the first of them a command")
    outputs = spec["outputs"]
    if not (isinstance(outputs, list) and all(isinstance(o, str) for o in outputs) and len(set(outputs)) == len(outputs)):
        no("outputs is a list of file names, each named once")
    for o in outputs if strict_outputs else []:
        if output_problem(o):
            no(f"output `{o}` {output_problem(o)}")
    manifest = spec.get("inputs_manifest")
    if manifest is not None and not (isinstance(manifest, dict) and all(
            isinstance(v, str) and SHA.fullmatch(v) and (k.startswith("/") or TOKEN.match(k)) for k, v in manifest.items())):
        no('inputs_manifest is {file: "sha256:<64 hex digits>"}, each file named by a token or an absolute path')
    for a in [*argv, *(manifest or {})]:
        m = TOKEN.match(a)
        if m and m[1] not in tokens:
            no(f"`{a}` starts with a token this runner does not expand; it expands {sorted(tokens)}")
    wanted = spec.get("resources")
    if wanted is not None:
        if not isinstance(wanted, dict):
            no("resources is an object of names to numbers above zero")
        unknown = sorted(set(wanted) - set(resources))
        if unknown:
            no(f"this runner cannot honour the resources {unknown}; it honours {sorted(resources)}")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in wanted.values()):
            no("resources is an object of names to numbers above zero")
    env = spec.get("env")
    if env is not None:
        if not (isinstance(env, list) and all(isinstance(n, str) and NAME.fullmatch(n) for n in env)):
            no("env is a list of environment variable names")
        bad = [n for n in env if n.upper().startswith("PYTHON") or n == TAG]
        if bad:
            no(f"env may not ask for {bad}: no variable whose name starts with PYTHON reaches a job")
    return spec


# ---------------------------------------------------------------- files and processes

def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def write_once(path: Path, obj) -> bool:
    """Write a record whole or not at all; the first writer wins."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True))
    try:
        os.link(tmp, path)
        return True
    except FileExistsError:
        return False
    finally:
        tmp.unlink()


def read_inside(root: Path, name: str) -> bytes:
    """The bytes of a regular file below root, reached without following a symlink at any step."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(root, flags | os.O_DIRECTORY)
    try:
        parts = name.split("/")
        for part in parts[:-1]:
            nxt = os.open(part, flags | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = nxt
        nxt = os.open(parts[-1], flags | os.O_NONBLOCK, dir_fd=fd)
        os.close(fd)
        fd = nxt
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(errno.EINVAL, "not a regular file")
        chunks = []
        while chunk := os.read(fd, 1 << 20):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def job_markers(work: Path) -> list:
    """The markers a job wrote for itself: regular files named marker.<name> in its working directory."""
    found = []
    with contextlib.suppress(OSError):
        for entry in os.scandir(work):
            m = MARKER.fullmatch(entry.name)
            if m and m[1] not in MARKERS and entry.is_file(follow_symlinks=False):
                found.append(m[1])
    return sorted(found)


def freeze(work: Path, outputs: list, keep: Path) -> dict:
    """What a runner does when a job ends: note the job's own markers, hash
    each declared output and copy it into the runner's keep, so that what
    collect hands back later is what was there at the end."""
    hashes, refused = {}, {}
    for name in outputs:
        hashes[name] = None
        why = output_problem(name)
        if why is None:
            try:
                data = read_inside(work, name)
                (keep / name).parent.mkdir(parents=True, exist_ok=True)
                (keep / name).write_bytes(data)
                hashes[name] = sha_bytes(data)
            except FileNotFoundError:
                continue
            except OSError as e:
                why = {errno.ELOOP: "is a symlink", errno.ENOTDIR: "is reached through a symlink or a file, not a folder",
                       errno.EINVAL: "is not a regular file"}.get(e.errno, f"could not be read ({e.strerror})")
        if why:
            refused[name] = why
    return {"outputs": hashes, "outputs_refused": refused, "job_markers": job_markers(work)}


def born(pid) -> int | None:
    """When a process started, in the kernel's own ticks (Linux); None where that cannot be read."""
    try:
        return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])
    except (OSError, ValueError, IndexError):
        return None


def job_processes(tag: str, session, skip=()) -> list:
    """The processes that belong to one job: every one in the session the
    runner started for it, and every one that carries the job's tag in its
    environment. Linux only; elsewhere the list is empty."""
    found = []
    for entry in (os.listdir("/proc") if os.path.isdir("/proc") else []):
        if not entry.isdigit() or int(entry) in skip:
            continue
        try:
            fields = Path(f"/proc/{entry}/stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] in "ZX":
                continue  # already dead, waiting to be counted
            if (session is not None and int(fields[3]) == session) or \
                    tag.encode() in Path(f"/proc/{entry}/environ").read_bytes().split(b"\0"):
                found.append(int(entry))
        except (OSError, ValueError, IndexError):
            continue
    return found


def stop_processes(tag: str, session, skip=(), seconds: float = 10.0) -> bool:
    """SIGKILL everything that belongs to a job until nothing is left. True when nothing is."""
    end = time.monotonic() + seconds
    while left := job_processes(tag, session, skip):
        if time.monotonic() > end:
            return False
        for pid in left:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)
        time.sleep(0.02)
    return True


def stop_under(directory: Path) -> None:
    """Tidy up after a test: stop whatever is still working under its temporary directory (Linux)."""
    root = str(directory.resolve())
    for entry in (os.listdir("/proc") if os.path.isdir("/proc") else []):
        if entry.isdigit() and int(entry) != os.getpid():
            with contextlib.suppress(OSError):
                if os.readlink(f"/proc/{entry}/cwd").startswith(root):
                    os.kill(int(entry), signal.SIGKILL)


def find_program(command: str, work: Path, path: str) -> str | None:
    """The file a command would run, looked for the way the job's environment would."""
    if "/" in command:
        full = command if command.startswith("/") else str(work / command)
        return full if os.path.isfile(full) and os.access(full, os.X_OK) else None
    return shutil.which(command, path=path)


def interpreter_of(program: str, env: dict, cwd: Path) -> dict | None:
    """If the program is a Python interpreter, ask it, inside the job's environment, what it is."""
    if not any(re.match(r"(python|pypy)", Path(p).name) for p in (program, os.path.realpath(program))):
        return None
    ask = ("import json, sys; print(json.dumps({'path': sys.executable, 'version': sys.version.split()[0],"
           " 'implementation': sys.implementation.name}))")
    try:
        said = subprocess.run([program, "-I", "-c", ask], env=env, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=30)
        return json.loads(said.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def has_ended(child) -> bool:
    """True once a job's first process has ended. Where the system allows it the process is left uncounted, so
    its number still names its own session and cannot yet be given to another process."""
    if hasattr(os, "waitid"):
        return os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    return child.poll() is not None


# ---------------------------------------------------------------- the local runner's supervisor

def supervise(state: Path, lock_fd: int) -> int:
    """One of these runs for each job at the local runner, started by
    submit inside the job's environment. It holds the file lock that says
    the job is alive, takes the argv from the pipe submit hands it, checks
    the manifest, writes fetch.started, runs the argv, stops whatever is
    left, and writes the final record. Whatever goes wrong in here, the
    job still gets a final record."""
    os.set_inheritable(lock_fd, False)
    cfg = None

    def end(phase, code, reason) -> int:
        frozen = (freeze(Path(cfg["work"]), cfg["outputs"], state / "keep") if cfg
                  else {"outputs": {}, "outputs_refused": {}, "job_markers": []})
        log = state / "job.log"
        write_once(state / "ended.json", {"phase": phase, "exit": code, "reason": reason, "ended_at": now(),
                                          "log_sha256": sha_file(log), "log_bytes": log.stat().st_size if log.is_file() else None,
                                          **frozen})
        prefix = os.environ.get("PYTHONPYCACHEPREFIX", "")
        if Path(prefix).name.startswith("sf-pycache-"):
            shutil.rmtree(prefix, ignore_errors=True)
        return 0

    try:
        try:
            cfg = json.loads(sys.stdin.buffer.read())
        except ValueError:
            cfg = None
        if not (isinstance(cfg, dict) and cfg.get("release")):
            cfg = None
            if (state / "submitted.json").is_file():
                end("failed", None, "the submitter went away before the job was released: the argv never ran")
            return 1
        return run_job(state, cfg, end)
    except BaseException as e:  # noqa: BLE001
        stop_processes(f"{TAG}={os.environ.get(TAG)}", None, skip={os.getpid()})
        end("failed", None, f"the runner's supervisor stopped ({type(e).__name__}: {e})")
        return 1


def run_job(state: Path, cfg: dict, end) -> int:
    work, env, argv = Path(cfg["work"]), cfg["env"], cfg["argv"]
    try:
        user = getpass.getuser()
    except (OSError, KeyError):
        user = str(os.getuid())
    seen = {"host": socket.gethostname(), "user": user, "platform": sys.platform, "env_names": sorted(env), "inputs": {},
            "program": None, "interpreter": None, "spec_sha256": cfg["spec_sha256"]}
    differs = []
    for name, path, want in cfg["inputs"]:
        got = sha_file(path)
        seen["inputs"][name] = {"declared": want, "observed": f"sha256:{got}" if got else None}
        if seen["inputs"][name]["observed"] != want:
            differs.append(name)
    program = find_program(argv[0], work, env.get("PATH", os.defpath))
    if program:
        seen["program"] = {"path": program, "sha256": sha_file(program)}
        seen["interpreter"] = interpreter_of(program, env, state)
    write_once(state / "observed.json", seen)
    if differs:
        return end("failed", None, f"the inputs manifest does not match for {differs}: the argv never ran")
    if program is None:
        return end("failed", None, f"`{argv[0]}` is not a program the job's environment can run: the argv never ran")
    if (state / "cancel.requested").exists():
        return end("cancelled", None, "cancelled before the argv started")
    (state / "marker.fetch.started").write_text(now())  # from here on the job can reach whatever its environment lets it
    write_once(state / "started.json", {"started_at": now(), "argv_started": argv})
    with open(state / "job.log", "wb") as log:
        try:
            child = subprocess.Popen(argv, cwd=work, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
        except OSError as e:
            return end("failed", None, f"the argv could not be run ({e.strerror or e})")
    write_once(state / "process.json", {"pid": child.pid, "born": born(child.pid)})
    limit, began, why, asked = cfg.get("walltime"), time.monotonic(), None, 0.0
    while not has_ended(child):
        if why is None:
            if (state / "cancel.requested").exists():
                why = "cancel"
            elif limit is not None and time.monotonic() - began > limit:
                why = "limit"
            if why:
                asked = time.monotonic()
                with contextlib.suppress(OSError):
                    os.killpg(child.pid, signal.SIGTERM)
        elif time.monotonic() - asked > cfg["grace"]:
            with contextlib.suppress(OSError):
                os.killpg(child.pid, signal.SIGKILL)
        time.sleep(0.02)
    with contextlib.suppress(OSError):  # the first process has ended; whatever it left in its session ends with it
        os.killpg(child.pid, signal.SIGKILL)
    gone = stop_processes(f"{TAG}={env.get(TAG)}", child.pid, skip={os.getpid()})
    code = child.wait()
    left = "" if gone else "; some of its processes could not be stopped"
    if why == "limit":
        return end("failed", None, f"over the time limit of {limit} s: stopped by the runner{left}")
    if code < 0:
        try:
            name = signal.Signals(-code).name
        except ValueError:
            name = "a signal"
        if why == "cancel":
            return end("cancelled", None, f"stopped by cancel ({name}){left}")
        return end("failed", code, f"killed by signal {-code} ({name}){left}")
    notes = ["a cancel was asked for; the job ended by itself with this code"] if why else []
    return end("done", code, "; ".join(notes + ([left[2:]] if left else [])) or None)


# ---------------------------------------------------------------- the contract and the local runner

class Runner:
    """The contract. A runner is made with one argument, a directory it may
    keep its own records in, and does the four things below. It also says
    how long the conformance test should wait for it."""
    name = "abstract"
    tokens: dict = {}       # what this runner expands besides {python} and {work}
    resources: tuple = ()   # the resources this runner honours; a spec that asks for another is refused
    settle_seconds = 30.0   # how long a job of a few seconds may take to reach a final phase here
    grace_seconds = 2.0     # how long cancel and a time limit wait between SIGTERM and SIGKILL
    poll_seconds = 0.05     # how often it is worth asking for status

    def submit(self, spec: dict) -> dict: raise NotImplementedError
    def status(self, job_id: str) -> dict: raise NotImplementedError
    def collect(self, job_id: str, into) -> dict: raise NotImplementedError
    def cancel(self, job_id: str) -> dict: raise NotImplementedError

    def check(self, spec) -> dict:
        return check_spec(spec, {"python", "work", *self.tokens}, self.resources)

    @contextlib.contextmanager
    def plant_in_environment(self, variables: dict):
        """For the conformance test: put these variables where a job at
        this runner could inherit them from, for as long as the block
        lasts. Here that is the submitting process, which is right for a
        runner whose jobs are its child processes. A runner whose jobs
        inherit from somewhere else (a submit script, a node's profile,
        an image) plants them there."""
        before = {k: os.environ.get(k) for k in variables}
        os.environ.update(variables)
        try:
            yield
        finally:
            for k, v in before.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class LocalRunner(Runner):
    """Jobs as child processes on this machine; see THE LOCAL RUNNER at the top of the file."""
    name = "local"
    resources = ("walltime_seconds",)

    def __init__(self, root, tokens: dict | None = None, grace_seconds: float = 2.0):
        if "work" in (tokens or {}):
            raise Refused("{work} is the job's working directory; a runner cannot give it another meaning")
        self.root = Path(root).resolve()
        self.tokens = {"python": sys.executable, **(tokens or {})}
        self.grace_seconds = grace_seconds
        self.root.mkdir(parents=True, exist_ok=True)

    def _state(self, job_id: str) -> Path:
        return self.root / "state" / job_id

    def _work(self, job_id: str) -> Path:
        return self.root / "work" / job_id

    def _job_id(self, spec: dict) -> str:
        return job_id_of(spec["key"])

    def _same_spec(self, record: dict, spec: dict) -> bool:
        return record.get("spec_sha256") == spec_sha256(spec)

    def _job_env(self, spec: dict) -> dict:
        names = (*PASSED_ON, *(spec.get("env") or []))
        env = {k: os.environ[k] for k in names if k in os.environ and not k.upper().startswith("PYTHON")}
        (self.root / "tmp").mkdir(parents=True, exist_ok=True)
        return {**env, **SET_BY_THE_PLACE, "PYTHONPYCACHEPREFIX": tempfile.mkdtemp(prefix="sf-pycache-", dir=self.root / "tmp")}

    def _config(self, job_id: str, spec: dict) -> dict:
        tokens = {**self.tokens, "work": str(self._work(job_id))}
        return {"release": True, "work": tokens["work"], "argv": [expand(a, tokens) for a in spec["argv"]],
                "inputs": [[name, expand(name, tokens), want] for name, want in sorted((spec.get("inputs_manifest") or {}).items())],
                "outputs": spec["outputs"], "walltime": (spec.get("resources") or {}).get("walltime_seconds"),
                "grace": self.grace_seconds}

    @contextlib.contextmanager
    def _locked(self, job_id: str):
        (self.root / "locks").mkdir(parents=True, exist_ok=True)
        with open(self.root / "locks" / job_id, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield

    def _known(self, job_id) -> None:
        if not (isinstance(job_id, str) and ID.fullmatch(job_id)):
            raise Refused("a job id is 16 hex digits")

    def _start(self, job_id: str, spec: dict, fresh: bool = True) -> None:
        state, work = self._state(job_id), self._work(job_id)
        if fresh:  # anything here was left by a submit that died before its job was released
            for d in (state, work):
                shutil.rmtree(d, ignore_errors=True)
        state.mkdir(parents=True, exist_ok=True)
        work.mkdir(parents=True, exist_ok=True)
        env = self._job_env(spec)
        env[TAG] = f"{job_id}:{secrets.token_hex(8)}"
        cfg = {**self._config(job_id, spec), "env": env, "spec_sha256": spec_sha256(spec)}
        lock, boss = os.open(state / "alive.lock", os.O_CREAT | os.O_RDWR, 0o600), None
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # handed on to the supervisor, which holds it while it lives
            with open(state / "supervisor.log", "ab") as errors:
                boss = subprocess.Popen([sys.executable, "-I", "-B", str(SELF), "supervise", str(state), str(lock)], cwd=state,
                                        env=env, stdin=subprocess.PIPE, stdout=errors, stderr=errors, start_new_session=True,
                                        pass_fds=[lock])
            write_once(state / "submitted.json", {"job_id": job_id, "key": spec["key"], "spec": spec, "spec_sha256": spec_sha256(spec),
                                                  "submitted_at": now(), "tag": f"{TAG}={env[TAG]}",
                                                  "pycache_prefix": env.get("PYTHONPYCACHEPREFIX")})
        except OSError as e:
            if boss is not None:
                boss.kill()
                boss.wait()
            for d in (state, work):
                shutil.rmtree(d, ignore_errors=True)
            if Path(env.get("PYTHONPYCACHEPREFIX") or "").name.startswith("sf-pycache-"):
                shutil.rmtree(env["PYTHONPYCACHEPREFIX"], ignore_errors=True)
            raise Refused(f"the job could not be started ({e.strerror or e}); nothing was recorded, so the submit can be made again") from e
        finally:
            os.close(lock)
        with contextlib.suppress(OSError):  # the record exists: only now is the job released, with the argv it was submitted with
            boss.stdin.write(json.dumps(cfg).encode())
            boss.stdin.close()

    def _settle(self, job_id: str) -> dict | None:
        """The final record of a job whose supervisor died without writing one; None while the supervisor is alive."""
        state = self._state(job_id)
        try:
            lock = os.open(state / "alive.lock", os.O_RDWR)
        except OSError:
            return None
        try:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return None  # the supervisor holds the lock: it is alive
            sub = read_json(state / "submitted.json")
            if sub is not None and not (state / "ended.json").exists():
                proc = read_json(state / "process.json") or {}
                same = proc.get("born") is not None and born(proc.get("pid")) == proc["born"]
                gone = stop_processes(sub["tag"], proc["pid"] if same else None)
                log = state / "job.log"
                write_once(state / "ended.json", {
                    "phase": "failed", "exit": None, "ended_at": now(),
                    "reason": "the runner's supervisor ended without recording an exit (killed, out of memory, or the machine went down)"
                              + ("" if gone else "; some of the job's processes could not be stopped"),
                    "log_sha256": sha_file(log), "log_bytes": log.stat().st_size if log.is_file() else None,
                    **freeze(self._work(job_id), sub["spec"]["outputs"], state / "keep")})
                if Path(sub.get("pycache_prefix") or "").name.startswith("sf-pycache-"):
                    shutil.rmtree(sub["pycache_prefix"], ignore_errors=True)
            return read_json(state / "ended.json") or {
                "phase": "failed", "exit": None, "reason": "the runner's final record of this job cannot be read", "unreadable": True,
                "job_markers": []}
        finally:
            os.close(lock)

    def _ended(self, job_id: str) -> dict | None:
        return read_json(self._state(job_id) / "ended.json") or self._settle(job_id)

    def submit(self, spec: dict) -> dict:
        spec = self.check(spec)
        job_id = self._job_id(spec)
        with self._locked(job_id):
            record = read_json(self._state(job_id) / "submitted.json")
            if record is not None:
                if not self._same_spec(record, spec):
                    raise Refused(f"job {job_id} was already submitted under this key with a different spec "
                                  f"(sha256 {str(record.get('spec_sha256'))[:12]}, this one {spec_sha256(spec)[:12]}); "
                                  "a key names one job, and a new attempt needs a new key")
                return {"job_id": job_id, "runner": self.name, "already_submitted": True}
            self._start(job_id, spec)
        return {"job_id": job_id, "runner": self.name, "already_submitted": False}

    def status(self, job_id: str) -> dict:
        self._known(job_id)
        state = self._state(job_id)
        if read_json(state / "submitted.json") is None:
            return {"job_id": job_id, "phase": "lost", "exit": None, "reason": "this runner has no record of that job",
                    "markers": [], "job_markers": []}
        end = self._ended(job_id)
        markers = [m for m in MARKERS if (state / f"marker.{m}").is_file()]
        if end is not None and end.get("phase") not in FINAL:
            end = {"phase": "failed", "exit": None, "reason": "the runner's final record of this job cannot be read",
                   "unreadable": True, "job_markers": []}
        if end is None:
            return {"job_id": job_id, "phase": "running" if markers else "queued", "exit": None, "reason": None,
                    "markers": markers, "job_markers": job_markers(self._work(job_id))}
        return {"job_id": job_id, "phase": end["phase"], "exit": end.get("exit"), "reason": end.get("reason"), "markers": markers,
                "job_markers": end.get("job_markers", [])}

    def collect(self, job_id: str, into) -> dict:
        st = self.status(job_id)
        if st["phase"] == "lost":
            raise Refused(f"job {job_id} is not known to this runner; there is nothing to collect")
        if st["phase"] not in FINAL:
            raise Refused(f"job {job_id} is {st['phase']} and can still change; collect it when it is done, failed or cancelled")
        state = self._state(job_id)
        sub, end = read_json(state / "submitted.json"), self._ended(job_id)
        seen, started = read_json(state / "observed.json") or {}, read_json(state / "started.json") or {}
        spec = sub.get("spec")
        if end.get("unreadable") or not isinstance(spec, dict) or not isinstance(end.get("outputs"), dict):
            raise Refused(f"the records kept for job {job_id} cannot be read; nothing was collected")
        if (sub.get("job_id") != job_id or self._job_id(spec) != job_id or spec_sha256(spec) != sub.get("spec_sha256")
                or seen.get("spec_sha256", sub.get("spec_sha256")) != sub.get("spec_sha256")):
            raise Refused(f"the spec kept for job {job_id} is not the one that was submitted; nothing was collected")
        into = Path(into).resolve()
        if into == self.root or self.root in into.parents:
            raise Refused("collect into a directory outside the runner's own")
        kept = {}
        for name in spec["outputs"]:
            if end["outputs"].get(name) is not None:
                with contextlib.suppress(OSError):
                    kept[name] = (state / "keep" / name).read_bytes()
                if sha_bytes(kept.get(name, b"")) != end["outputs"][name]:
                    raise Refused(f"the kept copy of `{name}` is not what the job left when it ended; nothing was collected")
        log = {"job_id": job_id, "job": spec["job"], "key": spec["key"], "runner": self.name, "spec_sha256": sub["spec_sha256"],
               "argv": spec["argv"], "argv_started": started.get("argv_started"),
               "phase": st["phase"], "exit": st["exit"], "reason": st["reason"], "markers": st["markers"],
               "job_markers": st["job_markers"], "outputs": {name: end["outputs"].get(name) for name in spec["outputs"]},
               "outputs_refused": end.get("outputs_refused", {}), "inputs": seen.get("inputs", {}),
               "declared_environment": spec.get("environment"), "resources": spec.get("resources") or {},
               "env_names": seen.get("env_names"), "host": seen.get("host"), "user": seen.get("user"),
               "platform": seen.get("platform"), "interpreter": seen.get("interpreter"), "program": seen.get("program"),
               "submitted_at": sub.get("submitted_at"), "started_at": started.get("started_at"), "ended_at": end.get("ended_at"),
               "log_sha256": end.get("log_sha256"), "log_bytes": end.get("log_bytes")}
        into.mkdir(parents=True, exist_ok=True)
        for name, data in kept.items():
            (into / name).parent.mkdir(parents=True, exist_ok=True)
            (into / name).write_bytes(data)
        (into / "run-log.json").write_text(json.dumps(log, indent=1, sort_keys=True) + "\n")
        return log

    def cancel(self, job_id: str) -> dict:
        st = self.status(job_id)
        if st["phase"] not in ("queued", "running"):
            return st  # a job that already ended stays what it was
        with contextlib.suppress(FileExistsError), open(self._state(job_id) / "cancel.requested", "x") as f:
            f.write(now())  # the supervisor reads this and does the stopping: nobody signals a number read from a file
        end = time.monotonic() + self.grace_seconds + 5
        while st["phase"] not in FINAL and time.monotonic() < end:
            time.sleep(0.05)
            st = self.status(job_id)
        return st


# ---------------------------------------------------------------- the conformance test

GOOD = """\
import hashlib, json, os, pathlib, site, sys
said, work = sys.argv[1], sys.argv[2]
open('count', 'a').write('x')
pathlib.Path('marker.analysis.done').write_text('')
pathlib.Path('sub/dir').mkdir(parents=True, exist_ok=True)
pathlib.Path('sub/dir/gain.json').write_text('{"gain": 0.5, "said": "%s"}' % said)
pathlib.Path('undeclared.txt').write_text('never asked for')
prefix = os.environ.get('PYTHONPYCACHEPREFIX')
json.dump({'said': said, 'executable': sys.executable, 'version': sys.version.split()[0],
           'python_sha256': hashlib.sha256(open(sys.executable, 'rb').read()).hexdigest(),
           'work_is_cwd': os.path.samefile(work, os.getcwd()), 'env_names': sorted(os.environ),
           'python_vars': {k: v for k, v in os.environ.items() if k.upper().startswith('PYTHON')},
           'prefix_is_empty_dir': bool(prefix) and os.path.isdir(prefix) and not os.listdir(prefix),
           'optimize': sys.flags.optimize, 'user_site': bool(site.ENABLE_USER_SITE),
           'secret': os.environ.get('SF_CONFORMANCE_SECRET'), 'wanted': os.environ.get('SF_CONFORMANCE_WANTED')},
          open('receipt.json', 'w'))
"""
PLANT = """\
import importlib.util, json, marshal, pathlib, struct, subprocess, sys
code = pathlib.Path('code')
(code / '__pycache__').mkdir(parents=True)
(code / 'helper.py').write_text("def where():\\n    return 'from source'\\n")
planted = compile("def where():\\n    return 'from planted bytecode'\\n", str((code / 'helper.py').resolve()), 'exec')
(code / '__pycache__' / ('helper.%s.pyc' % sys.implementation.cache_tag)).write_bytes(
    importlib.util.MAGIC_NUMBER + struct.pack('<I', 1) + bytes(8) + marshal.dumps(planted))
(code / 'main.py').write_text("import json, helper\\njson.dump({'ran': helper.where()}, open('ran.json', 'w'))\\n")
subprocess.run([sys.executable, str(code / 'main.py')], check=True)
"""
LATE = """\
import pathlib, signal, sys, time
if sys.argv[2] == 'deaf':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
open('count', 'a').write('x')
pathlib.Path('marker.analysis.started').write_text('')
time.sleep(float(sys.argv[1]))
pathlib.Path('late.txt').write_text('written after the runner said the job was over')
pathlib.Path('marker.analysis.done').write_text('')
"""
LINKS = """\
import os, pathlib, sys, tempfile
pathlib.Path('real.json').write_text('real')
for d in ('..', tempfile.gettempdir()):
    try:
        outside = pathlib.Path(d).resolve() / sys.argv[1]
        outside.write_text('OUTSIDE THE WORKING DIRECTORY')
        break
    except OSError:
        pass
os.symlink(outside, 'link.json')
os.symlink(outside.parent, 'via')
os.symlink('real.json', 'inside-link.json')
os.mkdir('folder')
"""
FAILS = ("import pathlib, sys\npathlib.Path('marker.analysis.started').write_text('')\n"
         "pathlib.Path('receipt.json').write_text(sys.argv[1])\nsys.exit(3)\n")
SAYS = "import pathlib, sys\npathlib.Path('receipt.json').write_text(sys.argv[1])\n"
COUNTS = "open('count', 'a').write('x')\n"
KILLED = "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n"
ORPHAN = ("import os, signal, sys\nif os.getppid() not in (1, int(sys.argv[1])):\n    try:\n        os.kill(os.getppid(), signal.SIGKILL)\n"
          "    except OSError:\n        pass\nos.kill(os.getpid(), signal.SIGKILL)\n")


def load_place(ref: str):
    """A runner class from `Class` (in this file), `module:Class` or `path/to/file.py:Class`, and a form of the
    reference that another process can use."""
    here = sys.modules[__name__]
    module, _, cls_name = ref.rpartition(":")
    if not module:
        mod, portable = here, ref
    elif module.endswith(".py"):
        path = Path(module).resolve()
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or not path.is_file():
            raise Refused(f"no runner file at {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = mod
        spec.loader.exec_module(mod)
        portable = f"{path}:{cls_name}"
    else:
        try:
            mod = importlib.import_module(module)
        except ImportError as e:
            raise Refused(f"cannot import the runner's module `{module}` ({e})") from e
        portable = f"{Path(mod.__file__).resolve()}:{cls_name}" if getattr(mod, "__file__", None) else ref
    cls = getattr(mod, cls_name, None)
    if not (isinstance(cls, type) and all(callable(getattr(cls, verb, None)) for verb in ("submit", "status", "collect", "cancel"))):
        raise Refused(f"`{ref}` is not a runner: a class with submit, status, collect and cancel")
    return cls, portable


def other_process(ref: str, root: Path, verb: str, *args) -> dict | None:
    """One verb of a runner from another process, as a retry from a new shell would make it."""
    done = subprocess.run([sys.executable, "-B", str(SELF), verb, "--runner", ref, "--root", str(root), *args],
                          capture_output=True, text=True, timeout=300)
    try:
        return json.loads(done.stdout)
    except ValueError:
        return None


def conformance(ref: str = "LocalRunner") -> list:
    """What any runner must do, asked through the four verbs and judged by
    what collect brings back. Nothing here reads a runner's own disk; the
    interpreter is the runner's and so are the waits. Returns (check,
    passed) pairs."""
    make, ref = load_place(ref)
    out, nonce, numbers = [], secrets.token_hex(4), iter(range(1, 10_000))

    def check(name, test):
        try:
            ok = bool(test())
        except Exception:  # noqa: BLE001  a check that cannot even be made has failed
            ok = False
        out.append((name, ok))

    def attempt(fn, *args):
        try:
            return fn(*args)
        except Exception:  # noqa: BLE001
            return None

    def refuses(fn, *args) -> bool:
        try:
            fn(*args)
        except ValueError:
            return True
        except Exception:  # noqa: BLE001
            return False
        return False

    def spec(code, *args, outputs=("receipt.json",), name=None, **more):
        n = next(numbers)
        return {"job": name or f"CONFORMANCE-{nonce}/held-out/{n}", "argv": ["{python}", "-c", code, *args], "outputs": list(outputs),
                "key": {"study": f"CONFORMANCE-{nonce}", "test": "held-out", "opening": n, "lock": f"7:{nonce * 4}"}, **more}

    def files(d):
        return sorted(str(p.relative_to(d)) for p in Path(d).rglob("*") if p.is_symlink() or not p.is_dir())

    def final(st):
        return st["phase"] in FINAL

    with tempfile.TemporaryDirectory(prefix="sf-conformance-") as tmp:
        tmp = Path(tmp)
        root = tmp / "runner"
        t = make(root)
        settle, long = t.settle_seconds, t.grace_seconds + 2.5
        jobs = []

        def submit(s):
            got = attempt(t.submit, s)
            jobs.extend([got["job_id"]] if isinstance(got, dict) and "job_id" in got else [])
            return got

        def until(job, done):
            end = time.monotonic() + settle + t.grace_seconds
            while True:
                st = attempt(t.status, job["job_id"]) if job else None
                if st is None or done(st) or time.monotonic() > end:
                    return st
                time.sleep(t.poll_seconds)

        def collect(job, name):
            return (attempt(t.collect, job["job_id"], tmp / name) if job else None), tmp / name

        try:
            # Two jobs that would write something seconds from now go first: one to cancel, one to run over its time limit.
            deaf = spec(LATE, str(long), "deaf", outputs=("count", "late.txt"))
            over = spec(LATE, str(long), "hears", outputs=("late.txt",), resources={"walltime_seconds": 1})
            j_deaf, j_over = submit(deaf), submit(over)
            st_run = until(j_deaf, lambda s: "analysis.started" in s["job_markers"] or final(s))
            until(j_over, lambda s: "analysis.started" in s["job_markers"] or final(s))
            written_by = time.monotonic() + long + 0.7  # both have started: past this moment the late file would be there
            early = refuses(t.collect, (j_deaf or {}).get("job_id"), tmp / "early")
            c_deaf = attempt(t.cancel, (j_deaf or {}).get("job_id"))
            st_c = until(j_deaf, final)
            r_c1, d_c1 = collect(j_deaf, "c1")  # at the moment the runner says the job is over
            resub = attempt(t.submit, deaf)
            st_o = until(j_over, final)
            r_o1, _ = collect(j_over, "o1")

            # The plain job, submitted while the submitter's environment holds things no job should inherit.
            said = f"said-{nonce}"
            good = spec(GOOD, said, "{work}", outputs=("receipt.json", "count", "sub/dir/gain.json", "never-written.txt"),
                        environment={"python": "0.0.0", "commit": "feedface"}, env=["SF_CONFORMANCE_WANTED"])
            (tmp / "planted").mkdir()
            (tmp / "planted" / "startup.py").write_text("")
            hostile = {"PYTHONPATH": str(tmp / "planted"), "PYTHONSTARTUP": str(tmp / "planted" / "startup.py"),
                       "PYTHONHOME": sys.base_prefix, "PYTHONINSPECT": "1", "PYTHONUSERBASE": str(tmp / "planted"),
                       "PYTHONOPTIMIZE": "1", "PYTHONPYCACHEPREFIX": str(tmp / "planted"), "PYTHONSOMETHINGNEW": "1",
                       "SF_CONFORMANCE_SECRET": "a credential the job did not ask for", "SF_CONFORMANCE_WANTED": "asked for"}
            with t.plant_in_environment(hostile):
                a = submit(good)
            again = attempt(t.submit, good)
            elsewhere = attempt(make(root).submit, good)
            (tmp / "good.json").write_text(json.dumps(good))
            retried = other_process(ref, root, "submit", "--spec", str(tmp / "good.json"))
            changed = refuses(t.submit, {**good, "argv": ["{python}", "-c", "pass"]})
            st_a = until(a, final)
            r_a, d_a = collect(a, "a1")
            receipt = read_json(d_a / "receipt.json") or {}
            gain = '{"gain": 0.5, "said": "%s"}' % said

            j_p = submit(spec(PLANT, outputs=("ran.json",)))
            until(j_p, final)
            _, d_p = collect(j_p, "p")
            lost = f"lost-{nonce}"
            j_f = submit(spec(FAILS, lost))
            st_f = until(j_f, final)
            r_f, d_f = collect(j_f, "f")
            first, second = spec(SAYS, f"first-{nonce}", name="one name"), spec(SAYS, f"second-{nonce}", name="one name")
            j_1, j_2 = submit(first), submit(second)
            st_1, st_2 = until(j_1, final), until(j_2, final)
            (_, d_1), (r_2, d_2) = collect(j_1, "k1"), collect(j_2, "k2")
            st_k = until(submit(spec(KILLED, outputs=())), final)
            st_m = until(submit({**spec("pass"), "argv": ["{work}/no-such-program"]}), final)
            j_d = submit(spec(ORPHAN, str(os.getpid()), outputs=()))
            st_d = until(j_d, final)
            r_d, _ = collect(j_d, "d")
            learned = "sha256:" + str(receipt.get("python_sha256"))
            j_y = submit(spec(COUNTS, outputs=("count",), inputs_manifest={"{python}": learned}))
            j_n = submit(spec(COUNTS, outputs=("count",), inputs_manifest={"{python}": "sha256:" + "0" * 64}))
            st_y, st_n = until(j_y, final), until(j_n, final)
            (r_y, _), (r_n, d_n) = collect(j_y, "y"), collect(j_n, "n")
            outside = f"outside-{nonce}.txt"
            links = spec(LINKS, outside, outputs=("real.json", "link.json", "inside-link.json", f"via/{outside}", "folder"))
            j_l = submit(links)
            st_l = until(j_l, final)
            r_l, d_l = collect(j_l, "l")
            bad_outputs = all(refuses(t.submit, spec("pass", outputs=(o,)))
                              for o in ("/etc/hostname", "../elsewhere.json", "a/../../b", "run-log.json"))
            bad_resource = refuses(t.submit, spec("pass", resources={"no_such_resource": 1}))
            base = spec("pass")
            halves = all(refuses(t.submit, {k: v for k, v in base.items() if k != gone}) for gone in ("job", "key", "argv", "outputs"))
            base = spec("pass")
            shapes = all(refuses(t.submit, s) for s in (
                ["job", "key", "argv", "outputs"], {**base, "argv": []}, {**base, "argv": [1, 2]}, {**base, "outputs": "receipt.json"},
                {**base, "key": "a string"}, {**base, "key": {"study": "S", "test": "held-out", "opening": 1}}, {**base, "attempt": 2},
                {**base, "argv": ["{nowhere}/method.py"]}, {**base, "inputs_manifest": "sha256:feed"}, {**base, "env": ["PYTHONPATH"]}))
            unknown = attempt(t.status, "0" * 16)
            bad_ids = (refuses(t.status, "../outside/notajob") and refuses(t.collect, "../outside/notajob", tmp / "none")
                       and refuses(t.collect, "0" * 16, tmp / "none"))

            # Later: past the moment the two long jobs would have written, and more than a second after the plain job ended.
            time.sleep(max(0.0, written_by - time.monotonic()))
            st_c2, st_o2 = attempt(t.status, (j_deaf or {}).get("job_id")), attempt(t.status, (j_over or {}).get("job_id"))
            (r_c2, d_c2), (r_o2, _) = collect(j_deaf, "c2"), collect(j_over, "o2")
            r_a2, d_a2 = collect(a, "a2")
            late_again = attempt(t.submit, good)
            st_a3 = until(a, final)
            r_a3, d_a3 = collect(a, "a3")
            c_done = attempt(t.cancel, (a or {}).get("job_id"))
            st_a4 = attempt(t.status, (a or {}).get("job_id"))
        finally:
            for job_id in jobs:
                st = attempt(t.status, job_id)
                if st and st.get("phase") in ("queued", "running"):
                    attempt(t.cancel, job_id)
            stop_under(tmp)

        check("a job runs to done with exit 0; status shows the runner's fetch.started and the job's own marker",
              lambda: set(STATUS_KEYS) <= set(st_a) and (st_a["phase"], st_a["exit"]) == ("done", 0)
              and st_a["markers"] == ["fetch.started"] and st_a["job_markers"] == ["analysis.done"] and receipt["said"] == said)
        check("the job id is the one anyone can work out from the key",
              lambda: a["job_id"] == job_id_of(good["key"]) and ID.fullmatch(a["job_id"]) and a["already_submitted"] is False)
        check("the same spec again, from this runner, a second instance and a second process, is the same job and runs nothing twice",
              lambda: all(r["job_id"] == a["job_id"] and r["already_submitted"] is True for r in (again, elsewhere, retried))
              and (d_a / "count").read_text() == "x")
        check("the same spec again after the job ended starts nothing: same job, same run log, one run",
              lambda: late_again["job_id"] == a["job_id"] and late_again["already_submitted"] is True and final(st_a3)
              and r_a3 == r_a and (d_a3 / "count").read_text() == "x")
        check("a second spec under the same key is refused, and what ran is the first", lambda: changed and receipt["said"] == said)
        check("two keys are two jobs, even under one name, and each brings back its own output",
              lambda: j_1["job_id"] != j_2["job_id"] and j_2["already_submitted"] is False
              and (d_1 / "receipt.json").read_text() == f"first-{nonce}" and (d_2 / "receipt.json").read_text() == f"second-{nonce}"
              and r_2["outputs"]["receipt.json"] == sha_bytes(f"second-{nonce}".encode()))
        check("tokens are expanded by the runner: {python} ran the job, {work} is its working directory, and the run log keeps both forms",
              lambda: receipt["work_is_cwd"] is True and r_a["argv"] == good["argv"] and len(r_a["argv_started"]) == len(good["argv"])
              and r_a["argv_started"][0] == receipt["executable"] and not TOKEN.match(r_a["argv_started"][-1]))
        check("collect brings back the declared outputs that exist, under their relative paths, with the run log, and nothing else",
              lambda: files(d_a) == sorted(["receipt.json", "count", "sub/dir/gain.json", "run-log.json"]))
        check("the collected bytes are the bytes the job wrote, and the run log's hashes are theirs",
              lambda: (d_a / "sub/dir/gain.json").read_text() == gain and r_a["outputs"]["sub/dir/gain.json"] == sha_bytes(gain.encode())
              and r_a["outputs"]["count"] == sha_bytes(b"x") and r_a["outputs"]["receipt.json"] == sha_file(d_a / "receipt.json")
              and r_a["outputs"]["never-written.txt"] is None)
        check("the run log is the file collect wrote, has every field, and says what ran, where and when",
              lambda: read_json(d_a / "run-log.json") == r_a and set(RUN_LOG_KEYS) <= set(r_a)
              and (r_a["job_id"], r_a["job"], r_a["key"], r_a["spec_sha256"]) == (a["job_id"], good["job"], good["key"], spec_sha256(good))
              and r_a["runner"] == t.name and r_a["host"] and r_a["user"] and r_a["log_sha256"]
              and all(STAMP.fullmatch(r_a[k]) for k in ("submitted_at", "started_at", "ended_at"))
              and r_a["submitted_at"] <= r_a["started_at"] <= r_a["ended_at"]
              and all(r_a[k] == st_a[k] for k in ("phase", "exit", "reason", "markers", "job_markers")))
        check("the run log names the interpreter the job itself reports, and calls what the spec expected declared",
              lambda: r_a["interpreter"]["version"] == receipt["version"] and r_a["interpreter"]["path"] == receipt["executable"]
              and r_a["program"]["sha256"] == receipt["python_sha256"] and r_a["declared_environment"] == good["environment"])
        check("collecting again later gives the same run log and the same files",
              lambda: r_a2 == r_a and files(d_a2) == files(d_a) and all((d_a2 / f).read_bytes() == (d_a / f).read_bytes() for f in files(d_a)))
        check("the job's environment has no PYTHON variable but the three the runner sets, and its bytecode cache prefix is new and empty",
              lambda: set(receipt["python_vars"]) == {"PYTHONPYCACHEPREFIX", "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE"}
              and receipt["python_vars"]["PYTHONNOUSERSITE"] == "1" and receipt["python_vars"]["PYTHONDONTWRITEBYTECODE"] == "1"
              and receipt["python_vars"]["PYTHONPYCACHEPREFIX"] != hostile["PYTHONPYCACHEPREFIX"]
              and receipt["prefix_is_empty_dir"] is True and receipt["optimize"] == 0 and receipt["user_site"] is False)
        check("the job's environment is built, not inherited: a variable the spec asked for arrives, and nothing it did not ask for",
              lambda: receipt["wanted"] == hostile["SF_CONFORMANCE_WANTED"] and receipt["secret"] is None
              and set(r_a["env_names"]) - {"LC_CTYPE"} == set(receipt["env_names"]) - {"LC_CTYPE"})  # an interpreter may add that one
        check("bytecode planted beside a source file is not loaded: the job ran from source",
              lambda: read_json(d_p / "ran.json") == {"ran": "from source"})
        check("a job that fails is done with its own exit code, and keeps its markers and its output",
              lambda: (st_f["phase"], st_f["exit"], r_f["exit"]) == ("done", 3, 3) and st_f["markers"] == ["fetch.started"]
              and st_f["job_markers"] == ["analysis.started"] and (d_f / "receipt.json").read_text() == lost)
        check("markers are a job's own: a job that wrote none shows none",
              lambda: st_1["markers"] == ["fetch.started"] and st_1["job_markers"] == [] and st_2["job_markers"] == [])
        check("a job killed by a signal is failed with the reason, never done",
              lambda: st_k["phase"] == "failed" and st_k["exit"] != 0 and st_k["reason"])
        check("an argv that cannot be run is failed with the reason, never done",
              lambda: st_m["phase"] == "failed" and st_m["exit"] != 0 and st_m["reason"])
        check("a job over its time limit is stopped and failed with the reason, and what it would have written later never appears",
              lambda: st_o["phase"] == "failed" and st_o["exit"] != 0 and st_o["reason"] and st_o2 == st_o and r_o2 == r_o1
              and st_o["job_markers"] == ["analysis.started"] and r_o1["outputs"] == {"late.txt": None}
              and r_o1["resources"] == {"walltime_seconds": 1})
        check("a resource the runner cannot honour is refused at submit", lambda: bad_resource)
        check("a job whose supervisor is killed is failed with the reason, not running for ever",
              lambda: st_d["phase"] == "failed" and st_d["reason"] and r_d["phase"] == "failed")
        check("a job whose inputs manifest matches starts, and the run log names what the runner hashed",
              lambda: (st_y["phase"], st_y["exit"]) == ("done", 0) and r_y["outputs"]["count"] == sha_bytes(b"x")
              and r_y["inputs"] == {"{python}": {"declared": learned, "observed": learned}})
        check("a job whose inputs manifest does not match never starts: failed with the reason, no fetch.started, no output",
              lambda: st_n["phase"] == "failed" and st_n["reason"] and st_n["markers"] == [] and r_n["started_at"] is None
              and r_n["outputs"] == {"count": None} and r_n["inputs"]["{python}"]["observed"] == learned
              and files(d_n) == ["run-log.json"])
        check("collect is refused while a job can still change", lambda: st_run["phase"] == "running" and early)
        check("cancel stops the job: it is cancelled only once gone, and what it would have written later never appears",
              lambda: c_deaf["phase"] in ("cancelled", "running") and st_c["phase"] == "cancelled" and st_c2 == st_c and r_c2 == r_c1
              and r_c1["outputs"] == {"count": sha_bytes(b"x"), "late.txt": None} and files(d_c1) == files(d_c2) == ["count", "run-log.json"])
        check("a job cancelled after its markers keeps them, and gains none",
              lambda: st_c["markers"] == st_c2["markers"] == ["fetch.started"]
              and st_c["job_markers"] == st_c2["job_markers"] == ["analysis.started"])
        check("the same spec again after a cancel starts nothing",
              lambda: resub["job_id"] == j_deaf["job_id"] and resub["already_submitted"] is True and st_c2["phase"] == "cancelled"
              and (d_c2 / "count").read_text() == "x")
        check("cancelling a job that already ended leaves it done",
              lambda: (c_done["phase"], c_done["exit"]) == ("done", 0) == (st_a4["phase"], st_a4["exit"]))
        check("an output that is a symlink, is reached through one, or is not a regular file is left behind and named",
              lambda: (st_l["phase"], st_l["exit"]) == ("done", 0) and files(d_l) == ["real.json", "run-log.json"]
              and (d_l / "real.json").read_text() == "real"
              and all(r_l["outputs"][n] is None and r_l["outputs_refused"][n] for n in links["outputs"][1:]))
        check("outputs that name an absolute path, a parent directory or the run log are refused at submit", lambda: bad_outputs)
        check("a spec that lacks a name, a key, an argv or outputs, each alone, is refused", lambda: halves)
        check("a spec with a field in the wrong shape, an unknown field, an unknown token or a PYTHON variable is refused", lambda: shapes)
        check("an unknown job is lost, not invented, and an id that is not 16 hex digits is refused",
              lambda: unknown["phase"] == "lost" and bad_ids)
    return out


# ---------------------------------------------------------------- the test of the test

def local_checks() -> list:
    """What the four verbs cannot show: the local runner's own records, with a hand on its disk."""
    out = []

    def check(name, test):
        try:
            ok = bool(test())
        except Exception:  # noqa: BLE001
            ok = False
        out.append((name, ok))

    def refuses(fn, *args) -> bool:
        try:
            fn(*args)
        except ValueError:
            return True
        return False

    def job(n, code, *args, outputs=("receipt.json",), **more):
        return {"job": f"LOCAL/working-data/{n}", "key": {"study": "LOCAL", "test": "working-data", "run": n},
                "argv": ["{python}", "-c", code, *args], "outputs": list(outputs), **more}

    with tempfile.TemporaryDirectory(prefix="sf-local-") as tmp:
        tmp = Path(tmp).resolve()
        code, prefix, cache = tmp / "code", tmp / "planted-prefix", f"helper.{sys.implementation.cache_tag}.pyc"
        code.mkdir()
        (code / "helper.py").write_text("def where():\n    return 'from source'\n")
        (code / "method.py").write_text("import json, helper\njson.dump({'ran': helper.where()}, open('receipt.json', 'w'))\n")
        header = importlib.util.MAGIC_NUMBER + struct.pack("<I", 1) + bytes(8)  # bytecode whose source is never compared
        for where, said in ((code / "__pycache__" / cache, "from bytecode beside the source"),
                            (prefix / str(code).lstrip("/") / cache, "from bytecode under a cache prefix")):
            where.parent.mkdir(parents=True)
            where.write_bytes(header + marshal.dumps(compile(f"def where():\n    return {said!r}\n", str(code / "helper.py"), "exec")))
        plain = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
        controls = []
        for name, env in (("beside", plain), ("prefix", {**plain, "PYTHONPYCACHEPREFIX": str(prefix)})):
            (tmp / name).mkdir()
            subprocess.run([sys.executable, str(code / "method.py")], cwd=tmp / name, env=env, capture_output=True)
            controls.append((read_json(tmp / name / "receipt.json") or {}).get("ran"))
        runner = LocalRunner(tmp / "runner", tokens={"kit": str(code)})

        def finish(got, p=runner):
            end = time.monotonic() + p.settle_seconds
            while (st := p.status(got["job_id"]))["phase"] not in FINAL and time.monotonic() < end:
                time.sleep(0.05)
            return st

        try:
            method = {"job": "LOCAL/working-data/method", "key": {"study": "LOCAL", "test": "working-data", "run": "method"},
                      "argv": ["{python}", "{kit}/method.py"], "outputs": ["receipt.json"],
                      "inputs_manifest": {f"{{kit}}/{n}": "sha256:" + sha_file(code / n) for n in ("method.py", "helper.py")}}
            with runner.plant_in_environment({"PYTHONPYCACHEPREFIX": str(prefix), "PYTHONOPTIMIZE": "2"}):
                m = runner.submit(method)
            st_m = finish(m)
            log_m = runner.collect(m["job_id"], tmp / "m")
            check("bytecode planted beside a locked source file, and under a cache prefix the submitter set, is not loaded: "
                  "a plain interpreter ran each plant, the job ran the source",
                  lambda: controls == ["from bytecode beside the source", "from bytecode under a cache prefix"]
                  and read_json(tmp / "m" / "receipt.json") == {"ran": "from source"} and st_m["phase"] == "done"
                  and all(v["observed"] == v["declared"] for v in log_m["inputs"].values()) and len(log_m["inputs"]) == 2
                  and [p.name for p in (code / "__pycache__").iterdir()] == [cache] and not os.path.exists(read_json(
                      runner._state(m["job_id"]) / "submitted.json")["pycache_prefix"]))

            counts = job(1, COUNTS, outputs=("count",))
            real = subprocess.Popen

            def no_processes(*a, **k):
                raise OSError(errno.EAGAIN, "Resource temporarily unavailable")

            subprocess.Popen = no_processes
            try:
                first = refuses(runner.submit, counts)
            finally:
                subprocess.Popen = real
            between = runner.status(job_id_of(counts["key"]))["phase"]
            retry = runner.submit(counts)
            finish(retry)
            runner.collect(retry["job_id"], tmp / "r")
            check("a submit that could not start the job leaves no job behind, and the retry runs it once",
                  lambda: first and between == "lost" and retry["already_submitted"] is False and (tmp / "r" / "count").read_text() == "x")

            class NeverReleases(LocalRunner):
                """The state a submitter killed between writing the record and releasing the job leaves behind."""
                def _config(self, job_id, spec):
                    return {"release": False}

            held = job(2, COUNTS, outputs=("count",))
            st_h = finish(NeverReleases(tmp / "runner").submit(held))
            check("a job whose submitter went away before releasing it is failed with the reason, never started, and stays submitted",
                  lambda: st_h["phase"] == "failed" and "never ran" in st_h["reason"] and st_h["markers"] == []
                  and runner.submit(held)["already_submitted"] is True)

            forge = ("import os, pathlib, signal, sys\nos.kill(os.getppid(), signal.SIGKILL)\n"
                     "for name, text in (('exit', '0'), ('ended_at', '2026-01-01T00:00:00Z'), ('pid', '1'), ('cancelled', ''),\n"
                     "                   ('spec.json', '{\"job\": \"another study\"}'), ('receipt.json', '{\"gain\": 1.0}')):\n"
                     "    pathlib.Path(name).write_text(text)\nsys.exit(7)\n")
            f = runner.submit(job(3, forge))
            st_f = finish(f)
            log_f = runner.collect(f["job_id"], tmp / "f")
            check("a job that kills its supervisor and writes exit, pid and spec files in its working directory is failed, not done with exit 0",
                  lambda: st_f["phase"] == "failed" and st_f["exit"] is None and "supervisor" in st_f["reason"]
                  and st_f["markers"] == ["fetch.started"] and log_f["job"] == "LOCAL/working-data/3" and log_f["ended_at"] != "2026-01-01T00:00:00Z")

            g = runner.submit(job(4, SAYS, '{"gain": 0.5}'))
            finish(g)
            before = runner.collect(g["job_id"], tmp / "g1")
            (runner._work(g["job_id"]) / "receipt.json").write_text('{"gain": 1.0}')
            (runner._work(g["job_id"]) / "marker.invented").write_text("")
            after = runner.collect(g["job_id"], tmp / "g2")
            check("what is changed in the working directory after a job ended changes nothing collect brings back",
                  lambda: after == before and (tmp / "g2" / "receipt.json").read_text() == '{"gain": 0.5}' and after["job_markers"] == [])
            kept = runner._state(g["job_id"]) / "keep" / "receipt.json"
            kept.write_text('{"gain": 1.0}')
            edited_output = refuses(runner.collect, g["job_id"], tmp / "g3")
            kept.write_text('{"gain": 0.5}')
            record = runner._state(g["job_id"]) / "submitted.json"
            honest = record.read_text()
            record.write_text(honest.replace("LOCAL/working-data/4", "ANOTHER-STUDY/held-out/7"))
            edited_spec = refuses(runner.collect, g["job_id"], tmp / "g4")
            record.write_text(honest)
            check("collect refuses when a kept output or the stored spec was changed after the fact, and brings nothing",
                  lambda: edited_output and edited_spec and not (tmp / "g3").exists() and not (tmp / "g4").exists()
                  and runner.collect(g["job_id"], tmp / "g5") == before)
            check("collect into the runner's own directory is refused", lambda: refuses(runner.collect, g["job_id"], runner._work(g["job_id"])))

            many = job(5, COUNTS, outputs=("count",))
            with ThreadPoolExecutor(6) as pool:
                got = list(pool.map(lambda _: LocalRunner(tmp / "runner").submit(many), range(6)))
            finish(got[0])
            runner.collect(got[0]["job_id"], tmp / "many")
            check("six submits of one spec at once make one job that runs once",
                  lambda: len({r["job_id"] for r in got}) == 1 and sum(r["already_submitted"] is False for r in got) == 1
                  and (tmp / "many" / "count").read_text() == "x")
        finally:
            stop_under(tmp)
    return out


def self_check() -> int:
    """Run the conformance test against the honest runners (each must pass)
    and the wrong ones (each must fail on the checks written for its
    defect), then the local runner's own checks."""
    def run(cls):
        done = subprocess.run([sys.executable, "-B", str(SELF), "conformance", "--runner", cls.__name__, "--json"],
                              capture_output=True, text=True)
        try:
            return [tuple(pair) for pair in json.loads(done.stdout)]
        except ValueError:
            return []

    def first_line(cls):
        return " ".join(cls.__doc__.split())

    good = True
    print("honest runners (each must pass):")
    with ThreadPoolExecutor(2) as pool:
        honest = list(pool.map(run, HONEST))
    for cls, res in zip(HONEST, honest):
        ok = bool(res) and all(passed for _, passed in res)
        good &= ok
        print(f"  {'PASS  ' if ok else 'FAIL  '}{cls.__name__}: {sum(p for _, p in res)} of {len(res)}"
              + "".join(f"\n          failed: {n}" for n, p in res if not p))
    names = [n for n, _ in honest[0]]
    good &= bool(names)
    print("wrong runners (each must fail, on the checks written for its defect):")
    with ThreadPoolExecutor(4) as pool:
        wrong = list(pool.map(run, WRONG))
    failed_by = {n: [] for n in names}
    for cls, res in zip(WRONG, wrong):
        failed = [n for n, passed in res if not passed]
        meant = [next((n for n in names if want in n), want) for want in cls.caught_by]
        ok = bool(res) and bool(failed) and all(n in failed for n in meant)
        good &= ok
        for n in failed:
            failed_by.setdefault(n, []).append(cls.__name__)
        print(f"  {'CAUGHT' if ok else 'MISSED'}  {cls.__name__}: fails {len(failed)} of {len(res)}. {first_line(cls)}")
        for n in meant:
            print(f"          {'caught by' if n in failed else 'NOT CAUGHT BY'}: {n}")
    idle = [n for n in names if not failed_by.get(n)]
    good &= not idle
    print(f"checks that some wrong runner fails: {len(names) - len(idle)} of {len(names)}" + "".join(f"\n  NEVER FAILED: {n}" for n in idle))
    print("the local runner's own records (what the four verbs cannot show):")
    local = local_checks()
    for n, passed in local:
        good &= passed
        print(f"  {'PASS  ' if passed else 'FAIL  '}{n}")
    print(f"self-check: {'PASS' if good else 'FAIL'} ({sum(bool(r) and all(p for _, p in r) for r in honest)} of {len(HONEST)} honest runners "
          f"pass all {len(names)} checks; {sum(any(not p for _, p in r) for r in wrong)} of {len(WRONG)} wrong runners fail; "
          f"{sum(p for _, p in local)} of {len(local)} local checks pass)")
    return 0 if good else 1


# ---------------------------------------------------------------- deliberately wrong runners
#
# Each of these is the local runner with one thing wrong, and each passed the
# conformance test this file had before (9 of 9). They stay here as the test's
# own test: `conformance --self-check` passes only if every one of them fails,
# on the checks named in caught_by. The first twelve are an outside reviewer's;
# the rest were added so that every defect the reviewer listed, and every
# check, has a wrong runner that trips it. Never use one for anything else.

def _rewrite(into, log) -> dict:
    (Path(into) / "run-log.json").write_text(json.dumps(log, indent=1, sort_keys=True) + "\n")
    return log


class IdFromNameOnly(LocalRunner):
    """The job id is the hash of the job's name alone: a changed spec under the same name is 'already submitted' and never runs."""
    caught_by = ("the job id is the one anyone can work out", "a second spec under the same key is refused", "two keys are two jobs")

    def _job_id(self, spec):
        return sha_bytes(canonical({"job": spec["job"]}))[:16]

    def _same_spec(self, record, spec):
        return True


class SaltedId(LocalRunner):
    """The job id depends on the process that submits: a retry from a new process is a new job and runs again."""
    caught_by = ("the job id is the one anyone can work out", "a second instance and a second process")

    def _job_id(self, spec):
        return sha_bytes(canonical(spec["key"]) + str(os.getpid()).encode())[:16]


class RerunsFinishedJobs(LocalRunner):
    """Knows a resubmission only while the job runs (a scheduler that forgets finished jobs): after it ended the
    same spec runs again in the same directory, and the runner still answers already_submitted."""
    caught_by = ("after the job ended starts nothing", "after a cancel starts nothing")

    def submit(self, spec):
        res = super().submit(spec)
        state = self._state(res["job_id"])
        if res["already_submitted"] and (state / "ended.json").exists():
            with self._locked(res["job_id"]):
                for name in ("ended.json", "observed.json", "started.json", "process.json", "submitted.json", "marker.fetch.started",
                             "cancel.requested"):
                    (state / name).unlink(missing_ok=True)
                self._start(res["job_id"], spec, fresh=False)
        return res


class MarkersOnlyOnSuccess(LocalRunner):
    """Reports markers only for a job that exited 0: one that started, reached the data and then failed or was
    cancelled looks as if it never started."""
    caught_by = ("a job that fails is done with its own exit code", "a job cancelled after its markers keeps them")

    def status(self, job_id):
        st = super().status(job_id)
        if st["phase"] in FINAL and st["exit"] != 0:
            st["markers"], st["job_markers"] = [], []
        return st


class CancelIsALabel(LocalRunner):
    """cancel writes the word and stops nothing."""
    caught_by = ("cancel stops the job",)

    def cancel(self, job_id):
        if self.status(job_id)["phase"] in ("queued", "running"):
            (self._state(job_id) / "cancel.label").write_text(now())
        return self.status(job_id)

    def _ended(self, job_id):
        end, state = super()._ended(job_id), self._state(job_id)
        if end is None and (state / "cancel.label").is_file():
            outputs = read_json(state / "submitted.json")["spec"]["outputs"]
            return {"phase": "cancelled", "exit": None, "reason": "cancelled", "ended_at": (state / "cancel.label").read_text(),
                    "log_sha256": None, "log_bytes": None, **freeze(self._work(job_id), outputs, state / "keep")}
        return end


class CollectsEverything(LocalRunner):
    """collect brings back the whole working directory, declared or not: whatever the job fetched comes home with the receipt."""
    caught_by = ("and nothing else",)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        shutil.copytree(self._work(job_id), into, dirs_exist_ok=True, symlinks=True)
        return log


class SuccessWhenKilledOrMissing(LocalRunner):
    """A job killed by a signal, a job over its time limit and an argv that cannot be run are all reported done, exit 0."""
    caught_by = ("killed by a signal is failed", "cannot be run is failed", "over its time limit")

    def status(self, job_id):
        st = super().status(job_id)
        if st["phase"] == "failed":
            st.update(phase="done", exit=0, reason=None)
        return st


class StaleOutputs(LocalRunner):
    """Keeps the first file it ever collected under each output name and hands it back for every later job that exited 0, with a hash to match."""
    caught_by = ("two keys are two jobs",)
    cache: dict = {}

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        if log["exit"] == 0:
            for name, digest in log["outputs"].items():
                if name in self.cache:
                    (Path(into) / name).write_bytes(self.cache[name])
                    log["outputs"][name] = sha_bytes(self.cache[name])
                elif digest:
                    self.cache[name] = (Path(into) / name).read_bytes()
        return _rewrite(into, log)


class RewritesTheReceipt(LocalRunner):
    """collect edits the numbers in an output and hashes its own edit."""
    caught_by = ("the collected bytes are the bytes the job wrote",)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        for name in log["outputs"]:
            got = read_json(Path(into) / name)
            if isinstance(got, dict) and "gain" in got:
                (Path(into) / name).write_text(json.dumps({**got, "gain": 1.0}))
                log["outputs"][name] = sha_file(Path(into) / name)
        return _rewrite(into, log)


class ScrubsOnlyPythonpath(LocalRunner):
    """Hands the job the submitter's whole environment with PYTHONPATH taken out and nothing set."""
    caught_by = ("no PYTHON variable but the three", "nothing it did not ask for", "bytecode planted beside a source file")

    def _job_env(self, spec):
        return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


class BareRunLog(LocalRunner):
    """The run log says nothing about what ran, where, in what environment or when, and the file on disk is not what collect returned."""
    caught_by = ("the run log is the file collect wrote",)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        (Path(into) / "run-log.json").write_text("{}")
        return {k: log[k] for k in ("outputs", "exit", "inputs")}


class EverythingWrong(IdFromNameOnly, RerunsFinishedJobs, MarkersOnlyOnSuccess, CancelIsALabel, CollectsEverything,
                      SuccessWhenKilledOrMissing, RewritesTheReceipt, ScrubsOnlyPythonpath):
    """Eight of the above at once."""
    caught_by = ("the job id is the one anyone can work out", "and nothing else", "cancel stops the job", "killed by a signal is failed")


class LeaksMarkers(LocalRunner):
    """Shows fetch.started for a job that never started, and every job's own markers under every job."""
    caught_by = ("markers are a job's own", "does not match never starts")

    def status(self, job_id):
        st = super().status(job_id)
        if st["phase"] != "lost":
            st["markers"] = list(MARKERS)
            st["job_markers"] = sorted({m for d in self._work(job_id).parent.iterdir() for m in job_markers(d)})
        return st


class IgnoresTheManifest(LocalRunner):
    """Carries the inputs manifest and checks nothing: the declared hashes come back as if they had been observed."""
    caught_by = ("does not match never starts",)

    def _config(self, job_id, spec):
        return {**super()._config(job_id, spec), "inputs": []}

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        declared = read_json(self._state(job_id) / "submitted.json")["spec"].get("inputs_manifest") or {}
        return _rewrite(into, {**log, "inputs": {k: {"declared": v, "observed": v} for k, v in declared.items()}})


class IgnoresResources(LocalRunner):
    """Accepts any resources and enforces none."""
    caught_by = ("over its time limit", "a resource the runner cannot honour")

    def check(self, spec):
        return check_spec(spec, {"python", "work", *self.tokens}, (spec.get("resources") or {}) if isinstance(spec, dict) else ())

    def _config(self, job_id, spec):
        return {**super()._config(job_id, spec), "walltime": None}


class EchoesTheDeclaredEnvironment(LocalRunner):
    """The run log gives the interpreter the spec expected, not the one that ran."""
    caught_by = ("names the interpreter the job itself reports",)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        if isinstance(log["declared_environment"], dict) and "python" in log["declared_environment"] and log["interpreter"]:
            log["interpreter"]["version"] = log["declared_environment"]["python"]
        return _rewrite(into, log)


class FollowsOutputPaths(LocalRunner):
    """Takes any path as an output and copies whatever it leads to: absolute paths, parent directories and
    symlinks all come back, under their last name."""
    caught_by = ("is left behind and named", "are refused at submit")

    def check(self, spec):
        return check_spec(spec, {"python", "work", *self.tokens}, self.resources, strict_outputs=False)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        for name in log["outputs"]:
            src = self._work(job_id) / name
            if log["outputs"][name] is None and src.is_file():
                shutil.copyfile(src, Path(into) / Path(name).name)
                log["outputs"][name] = sha_file(src)
                log["outputs_refused"].pop(name, None)
        return _rewrite(into, log)


class DeadJobStillRunning(LocalRunner):
    """Never looks whether a job's supervisor is alive: a job that died without a final record is running for ever."""
    caught_by = ("not running for ever",)
    settle_seconds = 6.0

    def _settle(self, job_id):
        return None


class CollectsAnyTime(LocalRunner):
    """collect answers at any moment with whatever is there, so what it brings back while a job runs is not what is there later."""
    caught_by = ("collect is refused while a job can still change",)

    def collect(self, job_id, into):
        if self.status(job_id)["phase"] in ("queued", "running"):
            outputs = read_json(self._state(job_id) / "submitted.json")["spec"]["outputs"]
            Path(into).mkdir(parents=True, exist_ok=True)
            return _rewrite(into, {"job_id": job_id, "phase": "running", **freeze(self._work(job_id), outputs, Path(into))})
        return super().collect(job_id, into)


class AcceptsHalfASpec(LocalRunner):
    """Refuses a spec only when argv and outputs are both missing: one without the other is made up and run."""
    caught_by = ("each alone",)

    def check(self, spec):
        if isinstance(spec, dict) and ("argv" in spec) != ("outputs" in spec):
            spec = {"argv": ["{python}", "-c", "pass"], "outputs": [], **spec}
        return super().check(spec)


class IgnoresUnknownFields(LocalRunner):
    """A field the runner never reads is accepted, so two specs that differ only in it are two jobs or one, as luck has it."""
    caught_by = ("an unknown field",)

    def check(self, spec):
        return super().check({k: v for k, v in spec.items() if k in SPEC_FIELDS} if isinstance(spec, dict) else spec)


class LoadsPlantedBytecode(LocalRunner):
    """Builds the job's environment from the allow-list but sets no bytecode cache prefix, so bytecode beside a source file is loaded in its place."""
    caught_by = ("bytecode planted beside a source file", "no PYTHON variable but the three")

    def _job_env(self, spec):
        env = super()._job_env(spec)
        shutil.rmtree(env.pop("PYTHONPYCACHEPREFIX"), ignore_errors=True)
        return env


class PassesTheSubmittersEnvironment(LocalRunner):
    """Drops the PYTHON variables and passes on everything else the submitter holds, credentials included."""
    caught_by = ("nothing it did not ask for",)

    def _job_env(self, spec):
        return {**{k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}, **super()._job_env(spec)}


class AcceptsAChangedSpec(LocalRunner):
    """Answers already_submitted to a different spec under a used key, as if it were the same job."""
    caught_by = ("a second spec under the same key is refused",)

    def _same_spec(self, record, spec):
        return True


class CancelIsOneSignal(CancelIsALabel):
    """cancel sends one SIGTERM, does not wait, and writes the word: a job that ignores the signal goes on."""
    caught_by = ("cancel stops the job",)

    def cancel(self, job_id):
        proc = read_json(self._state(job_id) / "process.json")
        if proc and self.status(job_id)["phase"] == "running":
            with contextlib.suppress(OSError):
                os.killpg(proc["pid"], signal.SIGTERM)
        return super().cancel(job_id)


class CancelsFinishedJobs(LocalRunner):
    """cancel relabels a job that had already ended as cancelled."""
    caught_by = ("cancelling a job that already ended",)

    def cancel(self, job_id):
        if super().cancel(job_id)["phase"] in ("done", "failed"):
            (self._state(job_id) / "relabelled").write_text("")
        return self.status(job_id)

    def status(self, job_id):
        st = super().status(job_id)
        if st["phase"] in ("done", "failed") and (self._state(job_id) / "relabelled").is_file():
            st.update(phase="cancelled", exit=None)
        return st


class RunLogLosesTheTokens(LocalRunner):
    """The run log gives the argv only as it was expanded on this machine, so the same job reads differently from every checkout."""
    caught_by = ("tokens are expanded by the runner",)

    def collect(self, job_id, into):
        log = super().collect(job_id, into)
        return _rewrite(into, {**log, "argv": log["argv_started"]})


class CollectStampsItself(LocalRunner):
    """Every collect writes the moment it was made into the run log, so no two collects of one job agree."""
    caught_by = ("collecting again later gives the same run log",)

    def collect(self, job_id, into):
        return _rewrite(into, {**super().collect(job_id, into), "collected_at": time.time()})


class RunLogOmitsTheInputs(LocalRunner):
    """Checks the manifest and then says nothing in the run log about what it hashed."""
    caught_by = ("the run log names what the runner hashed",)

    def collect(self, job_id, into):
        return _rewrite(into, {**super().collect(job_id, into), "inputs": {}})


class InventsUnknownJobs(LocalRunner):
    """Takes anything for a job id and reports a job it has never seen as queued."""
    caught_by = ("an unknown job is lost",)

    def _known(self, job_id):
        return None

    def status(self, job_id):
        st = super().status(job_id)
        return {**st, "phase": "queued", "reason": None} if st["phase"] == "lost" else st


class KeepsJobsSomewhereElse(LocalRunner):
    """An honest runner whose records and working directories are laid out differently (as on any scheduler,
    cloud service or platform). It must pass."""

    def _state(self, job_id):
        return self.root / "records" / job_id[:2] / job_id

    def _work(self, job_id):
        return self.root / "nodes" / "n01" / job_id


HONEST = [LocalRunner, KeepsJobsSomewhereElse]
WRONG = [IdFromNameOnly, SaltedId, RerunsFinishedJobs, MarkersOnlyOnSuccess, CancelIsALabel, CollectsEverything,
         SuccessWhenKilledOrMissing, StaleOutputs, RewritesTheReceipt, ScrubsOnlyPythonpath, BareRunLog, EverythingWrong,
         LeaksMarkers, IgnoresTheManifest, IgnoresResources, EchoesTheDeclaredEnvironment, FollowsOutputPaths,
         DeadJobStillRunning, CollectsAnyTime, AcceptsHalfASpec, IgnoresUnknownFields, LoadsPlantedBytecode,
         PassesTheSubmittersEnvironment, AcceptsAChangedSpec, CancelIsOneSignal, CancelsFinishedJobs, RunLogLosesTheTokens,
         CollectStampsItself, RunLogOmitsTheInputs, InventsUnknownJobs]


# ---------------------------------------------------------------- the command line

def main() -> int:
    sys.dont_write_bytecode = True
    sys.modules.setdefault("adapter", sys.modules[__name__])
    if sys.argv[1:2] == ["supervise"]:  # the local runner's own supervisor: started by submit, not a command for people
        return supervise(Path(sys.argv[2]), int(sys.argv[3]))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ref = dict(default="LocalRunner", metavar="REF", help="a class in this file, module:Class or path/to/file.py:Class")
    for name in ("submit", "status", "collect", "cancel"):
        p = sub.add_parser(name, allow_abbrev=False)
        p.add_argument("--root", type=Path, required=True, help="the directory the runner keeps its own records in")
        p.add_argument("--runner", **ref)
        if name == "submit":
            p.add_argument("--spec", type=Path, required=True)
            p.add_argument("--token", action="append", default=[], metavar="NAME=PATH",
                           help="a token this runner expands at the start of an argument, as in gain=/path/to/methods/gain")
        else:
            p.add_argument("--job", required=True)
        if name == "collect":
            p.add_argument("--into", type=Path, required=True)
    c = sub.add_parser("conformance", allow_abbrev=False)
    c.add_argument("--runner", **ref)
    c.add_argument("--self-check", action="store_true",
                   help="test the test: every deliberately wrong runner must fail, the honest ones must pass")
    c.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    try:
        if a.cmd == "conformance":
            if a.self_check:
                return self_check()
            results = conformance(a.runner)
            if a.json:
                print(json.dumps(results))
                return 0
            for name, ok in results:
                print(("PASS  " if ok else "FAIL  ") + name)
            good = all(ok for _, ok in results)
            label = "local" if a.runner == "LocalRunner" else a.runner
            print(f"conformance ({label}): {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
            return 0 if good else 1
        cls, _ = load_place(a.runner)
        tokens = {}
        for item in getattr(a, "token", []):
            name, eq, value = item.partition("=")
            if not (eq and re.fullmatch(r"[a-z][a-z0-9_]*", name) and value):
                raise Refused(f"--token takes NAME=PATH, as in gain=/path/to/methods/gain; got `{item}`")
            tokens[name] = str(Path(value).resolve()) if os.path.exists(value) else value
        runner = cls(a.root, tokens=tokens) if tokens else cls(a.root)
        if a.cmd == "submit":
            try:
                spec = json.loads(a.spec.read_text())
            except OSError as e:
                raise Refused(f"cannot read the spec at {a.spec} ({e.strerror})") from e
            except ValueError as e:
                raise Refused(f"the spec at {a.spec} is not JSON ({e})") from e
            res = runner.submit(spec)
        elif a.cmd == "status":
            res = runner.status(a.job)
        elif a.cmd == "collect":
            res = runner.collect(a.job, a.into)
        else:
            res = runner.cancel(a.job)
    except ValueError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
