#!/usr/bin/env python3
"""fence: how the tools of this package run a script they do not trust.

A look of the exploring tool, and every command of an analysis plan that the
study tool runs (a test, a rehearsal step, a fetch, the opening's analysis),
is somebody's script. This file is the one way such a script is started. It
uses the standard library and nothing else, and the study tool binds it into
every lock together with itself.

What a script started here is given.

  A world of its own. The caller makes a scratch folder; the script may write
  there and nowhere else (shared memory apart, which Python's multiprocessing
  needs: see SHARED_MEMORY), and may read the system's folders, one interpreter,
  and the places the caller lists (a plan's own code folders, the files a
  command names). It is never given the tools of this package, the launcher's
  cache, the home folder, or anything the caller did not list.

  An interpreter prepared beforehand. `uv run SCRIPT` does not run uv inside
  the fence. Before the script starts, and outside the fence, uv builds a
  throwaway environment from the script's own inline dependencies (PEP 723),
  from wheels only, so that no package's build code runs; the script is then
  started with that environment's interpreter, which it can read and cannot
  write. The interpreter of that environment is never run outside the fence.
  `{python}` is the interpreter the tool itself runs under, read-only.

  An environment built by the tool. A short fixed list of variables, with
  values the tool makes (PATH, HOME, TMPDIR and the cache all point into the
  scratch folder or at the interpreter), plus the names a plan step lists.
  Nothing else of the caller's arrives: no UV_ variable, no certificate or
  proxy setting, no XDG folder, no PYTHON variable.

  A parent that outlives it. The script is the child of a small keeper
  process (this file, started as `fence.py --inside`). On Linux the keeper
  adopts whatever the script leaves behind and ends it before it reports;
  the calling tool then looks again, and a run that still has a living
  descendant is a failed run. Every tool of this package refuses to run
  when a keeper, a look or a plan's step is anywhere above it.

The kernel fence. On Linux 5.13 or later with Landlock the process the
keeper makes for the script confines itself, before any of the script runs,
to exactly the lists above and its own entry in /proc; nothing it or the
script does afterwards can widen that. Then it tries: it must fail to
read a file the tool put outside for the purpose and every path the caller
names as never to be read, and must fail to write beside the scratch folder,
into the tool's own environment and into the tools' folder. Only then is the
script started, and the report of that trial is what the receipt records:
`kernel`, with what was tried. On a machine that has Landlock, a fence that
cannot be applied or does not hold is a refusal, never a quiet fall-back.

Where there is no Landlock (`scratch-only`: macOS, Windows, an old kernel)
none of the above is enforced except the scratch folder, the built
environment and the process group. A script there can open and write any
path its user can, the tools and their environments included. The tool
compares its own environment and the tools' folder before and after such a
run and says so when they changed; that is a tripwire a script can step
over, not a wall. docs/WHAT-IS-ENFORCED.md lists which is which.

What the kernel fence does not do, anywhere: stop the network; stop a script
reading what is kept in the system's folders (/etc, /usr); stop it asking a
service that listens on a socket file to act for it. Where the kernel offers
it (Landlock 6), abstract sockets and signals to processes outside the fence
are closed as well.
"""
import sys

sys.dont_write_bytecode = True

import contextlib  # noqa: E402
import ctypes  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

THIS = Path(__file__).resolve()
NO_BYTECODE = "/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(tempfile.gettempdir(), "sf-no-bytecode")  # a cache prefix that cannot exist: no bytecode is read
TOOLS = THIS.parent

KERNEL = "kernel"             # Landlock was applied and tried: the script could open what the receipt lists, nothing else
SCRATCH_ONLY = "scratch-only"  # no kernel fence on this machine: a scratch folder and a built environment, and no more
MARKS = ("SF_INSIDE_A_LOOK", "SF_INSIDE_A_STEP")  # what the tools put in the environment of a script they run
# a process above this one that is one of these is a script's keeper or the tool that runs one
STARTERS = {"explore.py": ("look", "recheck"), "sf.py": ("test", "rehearse", "open-held-out"), "fence.py": ("--inside",)}
SYSTEM_FOLDERS = ("/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc", "/nix", "/sys/devices/system/cpu", "/sys/fs/cgroup",
                  "/proc/cpuinfo", "/proc/meminfo", "/proc/stat", "/proc/filesystems", "/proc/sys/kernel", "/proc/sys/vm",
                  "/dev/null", "/dev/zero", "/dev/random", "/dev/urandom", "/dev/tty", "/run/systemd/resolve")
WRITABLE_DEVICES = ("/dev/null", "/dev/zero", "/dev/tty")
# Shared memory. Python's multiprocessing makes its locks there, so a script that uses several processes needs it.
# It is the one place a fenced script can write that outlives it and that another script can read: the receipt
# lists whatever the user's own processes left there while the script ran. Nothing the tools run or import is there.
SHARED_MEMORY = "/dev/shm"
LOCALE = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")
ZONE = re.compile(r"^[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z0-9_+-]+){0,3}$")
BLOCK = re.compile(r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$")  # PEP 723, as the PEP gives it
# what uv is given when it prepares an interpreter, outside the fence: where its cache and its Pythons are, how it
# reaches an index, and nothing that names a file of settings or code to load (UV_ENV_FILE, UV_PYTHON, a project)
UV_PASSED = ("UV_CACHE_DIR", "UV_NATIVE_TLS", "UV_SYSTEM_CERTS", "UV_OFFLINE", "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_PREFERENCE",
             "UV_PYTHON_DOWNLOADS", "UV_MANAGED_PYTHON", "UV_NO_MANAGED_PYTHON", "UV_LINK_MODE", "UV_HTTP_TIMEOUT",
             "UV_CONCURRENT_DOWNLOADS", "UV_NO_PROGRESS", "UV_NO_CONFIG")
UV_DECIDES = ("UV_INDEX", "UV_DEFAULT_INDEX", "UV_INDEX_URL", "UV_EXTRA_INDEX_URL", "UV_FIND_LINKS", "UV_EXCLUDE_NEWER",
              "UV_CONFIG_FILE", "UV_INDEX_STRATEGY", "UV_PRERELEASE", "UV_RESOLUTION")  # these decide what is installed: recorded
FOR_UV = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TMPDIR", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME",
          "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY",
          "http_proxy", "https_proxy", "no_proxy", "all_proxy")


class Cannot(Exception):
    """A script could not be started the way this file starts one. The words say why."""


# ---- where this process itself comes from -----------------------------------
def own_environment() -> Path:
    """The environment the running tool's packages are installed in: the folder above its interpreter's when that is
    a virtual environment (as under `uv run`), otherwise the interpreter's own prefix."""
    exe = Path(os.path.abspath(sys.executable))
    return exe.parent.parent if (exe.parent.parent / "pyvenv.cfg").is_file() else Path(sys.prefix)


def interpreter_places(python: str) -> list:
    """What must be readable for an interpreter to start: its environment, and the installation that environment
    was made from (pyvenv.cfg says where; the link that is its `python` says so too)."""
    exe = Path(os.path.abspath(python))
    out = [str(exe.parent.parent)]
    cfg = exe.parent.parent / "pyvenv.cfg"
    if cfg.is_file():
        for line in cfg.read_text(errors="replace").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "home" and value.strip():
                out.append(str(Path(value.strip()).parent))
    real = Path(os.path.realpath(python))
    out += [str(real.parent.parent), sys.base_prefix]
    return [q for q in dict.fromkeys(out) if q not in ("/", "") and os.path.isdir(q)]


def snapshot() -> dict:
    """What the tools run from, as it stands: every file of this tool's own environment and of the tools' folder by
    size and time, and, when that environment sits among others in a launcher's cache, the start-up files of each of
    its neighbours (the other tools' environments are there). Compared before and after a script that ran without
    the kernel fence."""
    out = {}

    def walk(root: Path, label: str, only=None):
        for base, dirs, files in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(files):
                if only and not only(name):
                    continue
                p = Path(base) / name
                with contextlib.suppress(OSError):
                    st = p.lstat()
                    out[f"{label}/{p.relative_to(root).as_posix()}"] = (st.st_size, st.st_mtime_ns)
    env = own_environment()
    walk(env, "the tool's own environment")
    walk(TOOLS, "tools")
    if env.parent.name.startswith("environments-"):
        starts = lambda n: n.endswith(".pth") or n in ("sitecustomize.py", "usercustomize.py")  # noqa: E731
        with contextlib.suppress(OSError):
            for other in sorted(env.parent.iterdir()):
                if other != env and other.is_dir():
                    for sp in sorted(other.glob("lib/python*/site-packages")):
                        out[f"a neighbouring environment/{other.name}"] = tuple(sorted(os.listdir(sp)))
                        walk(sp, f"a neighbouring environment/{other.name}", starts)
    return out


def changed_since(before: dict) -> list:
    after = snapshot()
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


# ---- who started this process --------------------------------------------------
def _process(pid: int) -> tuple:
    """(the words of a process's command, its parent), from /proc, or from ps where there is none."""
    try:
        words = [w.decode(errors="replace") for w in Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")]
        parent = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
        return words, parent
    except (OSError, ValueError, IndexError):
        out = subprocess.run(["ps", "-o", "ppid=,args=", "-p", str(pid)], capture_output=True, text=True,
                             stdin=subprocess.DEVNULL).stdout.split()
        return out[1:], int(out[0])


def started_under(environ=None) -> str | None:
    """What says this process was started by a script the tools ran (a look, or a command of a plan), or None.
    Two signs are read. The tools mark the environment of every script they run, which a script can take off. It
    cannot take off its ancestry: every process above this one is read, and one that is a script's keeper
    (`fence.py --inside`), `explore.py look` or `recheck`, or `sf.py test`, `rehearse` or `open-held-out`, says so.
    The interpreter's own options may stand anywhere before the tool's name, with or without a value."""
    environ = os.environ if environ is None else environ
    for mark in MARKS:
        if environ.get(mark):
            return f"the environment says so ({mark})"
    pid = os.getppid()
    base = lambda w: w.replace("\\", "/").rpartition("/")[2]  # noqa: E731
    for _ in range(64):
        if pid <= 1:
            return None
        try:
            words, parent = _process(pid)
        except (OSError, ValueError, IndexError):
            return None
        if words and base(words[0]).lower().startswith(("python", "pypy")):
            for i, w in enumerate(words[1:], 1):
                if i > 1 and words[i - 1] in ("-X", "-W", "--check-hash-based-pycs"):
                    continue  # the value of an interpreter option (`-X pycache_prefix=/a/path`), never the program
                if base(w) in STARTERS:
                    if i + 1 < len(words) and words[i + 1] in STARTERS[base(w)]:
                        return f"process {pid} above this one is `{base(w)} {words[i + 1]}`"
                    break  # the first file named is the program; what follows are its own words
                if not w.startswith("-") and (w.endswith(".py") or "/" in w):
                    break
        pid = parent
    return None


# ---- DuckDB inside a look or a plan's step ----------------------------------------------
# A script the tools run may use DuckDB. Started by the interpreter the tools prepare (or `{python}`), it finds this file
# first on its path, as `sitecustomize`, before any of its own code runs: every DuckDB connection it makes, and the
# default one, gets extension autoloading and autoinstalling off, community and unsigned extensions off, no file outside
# its scratch folder (so no remote file: `enable_external_access` off, the scratch folder allowed by name), and a locked
# configuration that nothing it runs afterwards can change. What this cannot stop: a script that starts another Python with
# `-I` or `-S`, or brings its own build of DuckDB, or reaches the network some other way (docs/WHAT-IS-ENFORCED.md).
GUARD_FOLDER = "sf-guard"
DUCKDB_GUARD = '''"""Put here by the science factory's fence (tools/fence.py): DuckDB in a look or a plan's step runs locked down."""
import importlib.abc
import importlib.machinery
import os
import sys

_ALLOWED = [p for p in os.environ.get("SF_DUCKDB_ALLOWED", "").split(os.pathsep) if p]
_OFF = ("autoload_known_extensions", "autoinstall_known_extensions", "allow_community_extensions", "allow_unsigned_extensions")


def _text(s):
    return "'" + str(s).replace("'", "''") + "'"


def _lock(con):
    for k in _OFF:
        con.execute(f"SET {k} = false")
    if _ALLOWED:
        con.execute("SET allowed_directories = [" + ", ".join(_text(p.rstrip("/") + "/") for p in _ALLOWED) + "]")
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def _guard(*mods):
    real = mods[0].connect

    def connect(*args, **kwargs):
        config = dict(kwargs.pop("config", None) or {})
        for k in ("enable_external_access", "lock_configuration", "allowed_directories", "allowed_paths"):
            config.pop(k, None)
        config.update({k: False for k in _OFF})
        return _lock(real(*args, config=config, **kwargs))
    for m in mods:
        m.connect = connect
    _lock(mods[0].default_connection())


class _Loader(importlib.abc.Loader):
    def __init__(self, inner):
        self.inner = inner

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        self.inner.exec_module(module)
        _guard(*[m for m in (sys.modules.get("_duckdb"), module) if m is not None and hasattr(m, "connect")])


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name != "duckdb":
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None and spec.loader is not None:
            spec.loader = _Loader(spec.loader)
        return spec


sys.meta_path.insert(0, _Finder())
'''


def guard_folder(scratch: Path) -> Path:
    return Path(scratch) / "private" / GUARD_FOLDER


# ---- the environment a script is given --------------------------------------------
def minimal_environment(scratch: Path, python: str, passes: dict | None = None, mark: tuple = ("SF_INSIDE_A_STEP", "1")) -> dict:
    """The whole environment of a script the tools run. Built here, never the caller's: a PATH of the interpreter's
    folder and the system's, a home, a temporary folder and a bytecode cache inside the scratch folder, the
    caller's language and time zone when they are plain names, and the variables a plan step lists by name."""
    env = {"PATH": os.pathsep.join(dict.fromkeys([str(Path(python).parent), "/usr/local/bin", "/usr/bin", "/bin"])),
           "HOME": str(scratch / "home"), "TMPDIR": str(scratch / "tmp"), "LANG": "C.UTF-8",
           "PYTHONPYCACHEPREFIX": str(scratch / "cache"), "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": str(guard_folder(scratch)),  # the DuckDB guard (sitecustomize.py), written by make_scratch
           "SF_DUCKDB_ALLOWED": os.pathsep.join(str(scratch / sub) for sub in ("work", "tmp"))}
    for name in ("LANG", "LC_ALL", "LC_CTYPE"):
        if LOCALE.match(os.environ.get(name, "")):
            env[name] = os.environ[name]
    if ZONE.match(os.environ.get("TZ", "")):
        env["TZ"] = os.environ["TZ"]
    env.update(passes or {})
    env[mark[0]] = mark[1]
    return env


# ---- an interpreter prepared before the script starts ----------------------------------
def inline_metadata(text: str) -> dict | None:
    """The script's own `# /// script` block (PEP 723), read, or None when it has none."""
    import tomllib
    found = [m for m in BLOCK.finditer(text) if m.group("type") == "script"]
    if len(found) != 1:
        return None
    body = "".join(line[2:] if line.startswith("# ") else line[1:] for line in found[0].group("content").splitlines(keepends=True))
    try:
        return tomllib.loads(body)
    except tomllib.TOMLDecodeError:
        return None


def uv_environment() -> tuple:
    """(the environment uv is run under when it prepares an interpreter, the settings among it that decide what
    gets installed). uv runs outside the fence and runs none of the script; it is still given a short list."""
    names = [n for n in (*FOR_UV, *UV_PASSED, *UV_DECIDES) if os.environ.get(n)]
    return {n: os.environ[n] for n in names}, {n: os.environ[n] for n in UV_DECIDES if os.environ.get(n)}


def prepare_interpreter(launcher_words: list, script: Path, private: Path, cwd: Path | None = None) -> dict:
    """The interpreter a script will be started with, made ready outside the fence: {python, read, how, settings}.
    `{python}` (or the tool's own interpreter by its path) is the interpreter this tool runs under. `uv run` gets a
    new environment in `private` (a folder the script cannot write): `uv venv`, then the script's own inline
    dependencies installed from wheels with `uv pip install --no-build`. No interpreter of that environment and no
    package code runs here. A project file above the study or the look is not used."""
    first = launcher_words[0] if launcher_words else ""
    if first in ("{python}", sys.executable):
        return {"python": sys.executable, "read": interpreter_places(sys.executable), "settings": {},
                "how": "the interpreter the tool itself runs under, which the script can read and cannot write"}
    uv = shutil.which("uv")
    if not uv:
        raise Cannot("`uv` is not on the PATH, so the interpreter for `uv run` could not be prepared")
    flags, version, i = launcher_words[2:], None, 0
    while i < len(flags):
        if flags[i] in ("--python", "-p") and i + 1 < len(flags):
            version, i = flags[i + 1], i + 1
        i += 1
    try:
        meta = inline_metadata(script.read_text(errors="replace")) or {}
    except OSError:
        meta = {}
    wanted = version or str(meta.get("requires-python") or f"{sys.version_info.major}.{sys.version_info.minor}")
    env, decides = uv_environment()
    venv = private / "env"
    where = str(cwd or private)

    def run(*words) -> None:
        try:
            done = subprocess.run([uv, *words], cwd=where, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        except OSError as e:
            raise Cannot(f"uv could not be run to prepare the interpreter ({e})")
        if done.returncode != 0:
            said = [ln for ln in (done.stderr or done.stdout).strip().splitlines() if not ln.startswith("warning: ")]
            raise Cannot("uv could not prepare the script's interpreter (" + " ".join(words[:2]) + "): " + " | ".join(said[-4:])[:600])
    offline = ["--offline"] if "--offline" in flags else []
    run("venv", "--quiet", "--no-project", "--python", wanted, *offline, str(venv))
    wants = meta.get("dependencies") or (meta.get("tool") or {}).get("uv")
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if wants:
        run("pip", "install", "--quiet", "--no-build", *offline, "--python", str(python), "-r", str(script))
    return {"python": str(python), "read": interpreter_places(str(python)), "settings": decides,
            "how": "a throwaway environment made before the script started (uv venv, then its inline dependencies from wheels "
                   "only); the script can read it and cannot write it"}


# ---- the kernel fence -----------------------------------------------------------------
def landlock() -> int:
    """The version of the kernel's Landlock this machine has, or 0: Linux 5.13 and later, where it is switched on."""
    if not sys.platform.startswith("linux"):
        return 0
    try:
        v = ctypes.CDLL(None, use_errno=True).syscall(444, None, 0, 1)
    except (OSError, AttributeError):
        return 0
    return v if v > 0 else 0


def _confine(read: list, write: list) -> str | None:
    """From here on this process and everything it starts may open only what is listed. Returns why it could not,
    or None when it is done."""
    libc = ctypes.CDLL(None, use_errno=True)
    v = libc.syscall(444, None, 0, 1)
    if v <= 0:
        return "the kernel has no Landlock"
    handled = (1 << (13 if v == 1 else 14 if v == 2 else 15 if v in (3, 4) else 16)) - 1  # every kind of file access this kernel knows
    if v >= 6:  # also: no abstract socket and no signal to anything outside the fence
        class Attr(ctypes.Structure):
            _fields_ = [("fs", ctypes.c_uint64), ("net", ctypes.c_uint64), ("scoped", ctypes.c_uint64)]
        attr = Attr(handled, 0, 1 | 2)
    else:
        class Attr(ctypes.Structure):
            _fields_ = [("fs", ctypes.c_uint64)]
        attr = Attr(handled)
    ruleset = libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    if ruleset < 0:
        return f"the kernel refused the rule set (errno {ctypes.get_errno()})"

    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed", ctypes.c_uint64), ("fd", ctypes.c_int32)]

    for paths, access in ((read, 1 | 4 | 8), (write, handled)):  # execute, read a file, list a folder; or everything
        for q in paths:
            try:
                fd = os.open(q, os.O_PATH | os.O_CLOEXEC)
            except OSError:
                continue
            allowed = access & handled if os.path.isdir(q) else access & handled & (1 | 2 | 4 | (1 << 14) | (1 << 15))
            rule = Rule(allowed, fd)
            if libc.syscall(445, ruleset, 1, ctypes.byref(rule), 0) != 0:
                return f"the kernel refused a rule for {q} (errno {ctypes.get_errno()})"
            os.close(fd)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.syscall(446, ruleset, 0) != 0:
        return f"the kernel refused to apply the rule set (errno {ctypes.get_errno()})"
    return None


def _try(must_not_read: list, must_not_write: list) -> tuple:
    """After the fence is on: try each thing that must fail. (what was tried and kept out, what was NOT kept out)."""
    kept_out, leaks = [], []
    for q in must_not_read:
        try:
            if os.path.isdir(q):
                os.listdir(q)
            elif os.path.lexists(q):
                os.close(os.open(q, os.O_RDONLY))
            else:
                continue
            leaks.append(f"could read {q}")
        except PermissionError:
            kept_out.append(f"read {q}")
        except OSError:
            continue
    for q in must_not_write:
        probe = os.path.join(q, f".sf-fence-probe-{os.getpid()}") if os.path.isdir(q) else q
        try:
            if os.path.isdir(q):
                os.close(os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
                os.unlink(probe)
            elif os.path.lexists(q):
                os.close(os.open(q, os.O_WRONLY | os.O_APPEND))
            else:
                continue
            leaks.append(f"could write {q}")
        except PermissionError:
            kept_out.append(f"write {q}")
        except OSError:
            continue
    return kept_out, leaks


def _own_children() -> list:
    """The processes whose parent is this one, read where a confined process can still read it."""
    out = []
    with contextlib.suppress(OSError, ValueError):
        for task in os.listdir("/proc/self/task"):
            out += [int(x) for x in Path(f"/proc/self/task/{task}/children").read_text().split()]
    return out


def inside(spec_path: str, fd: int) -> int:
    """The keeper: run as `fence.py --inside SPEC FD` by `run_fenced`, and by nothing else. Makes the script's process,
    which confines itself, tries the fence, reports on FD and becomes the script; then adopts and ends what the script
    leaves, and exits with the script's exit code."""
    spec = json.loads(Path(spec_path).read_text())
    report = {"applied": False, "tried": [], "why_not": None}

    fd_again = os.dup(fd)  # the keeper's own, for what it says after the script has ended
    os.set_inheritable(fd_again, False)
    pipe = os.fdopen(fd, "w")  # the report of the fence, written by the process that becomes the script and closed before it does

    def say(last: bool = True) -> None:
        pipe.write(json.dumps(report) + "\n")
        pipe.flush()
        if last:
            pipe.close()
    if sys.platform.startswith("linux"):
        with contextlib.suppress(OSError, AttributeError):
            ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)  # PR_SET_CHILD_SUBREAPER: the script's orphans come here
    # The process that becomes the script confines itself, after it is forked and before it runs anything of the script's: so
    # the kernel fence can give it its own entry in /proc (DuckDB, among others, reads /proc/self/cgroup to start), and no
    # other process's. It tries the fence, writes the report, closes the report, and only then becomes the script.
    try:
        pid = os.fork()
    except OSError as e:
        report["why_not"] = f"the script's process could not be made ({e})"
        say()
        return 127
    if pid == 0:  # the process that will be the script
        try:
            os.setsid()
            if spec["kernel"]:
                why = _confine([*spec["read"], f"/proc/{os.getpid()}"], spec["write"])
                if why:
                    report["why_not"] = why
                    say()
                    os._exit(120)
                report["applied"] = True
                report["tried"], leaks = _try(spec["must_not_read"], spec["must_not_write"])
                if leaks or not report["tried"]:
                    report["why_not"] = "the fence was applied and did not hold: " + ("; ".join(leaks) or "nothing could be tried")
                    say()
                    os._exit(123)
            else:
                report["why_not"] = spec.get("why_no_kernel") or "this machine has no kernel fence"
            say()
            null = os.open(os.devnull, os.O_RDONLY)
            os.dup2(null, 0)
            os.chdir(spec["cwd"])
            os.execve(spec["argv"][0], spec["argv"], spec["env"])
        except BaseException as e:  # noqa: BLE001  nothing of the script ran
            with contextlib.suppress(BaseException):
                os.write(2, f"could not run: {e}\n".encode())
            os._exit(127)
    pipe.close()  # the keeper's copy: the report is the script's process's, written before it became the script
    pipe = os.fdopen(fd_again, "w")

    class _Proc:
        pid = 0

        @staticmethod
        def wait():
            return os.waitstatus_to_exitcode(os.waitpid(_Proc.pid, 0)[1])
    proc = _Proc
    proc.pid = pid
    code = proc.wait()
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    ended = set()
    for _ in range(400):  # whatever the script left has this process as its parent now
        left = _own_children()
        if not left:
            break
        for pid in left:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, signal.SIGKILL)
                ended.add(pid)
            with contextlib.suppress(ChildProcessError, OSError):
                os.waitpid(pid, 0)
    with contextlib.suppress(OSError, ValueError):
        pipe.write(json.dumps({"ended": len(ended)}) + "\n")
        pipe.close()
    return code if code >= 0 else 128 - code


def children() -> list:
    """The processes whose parent is this one, as (pid, still running). Read from /proc; empty where there is none."""
    out = []
    try:
        names = os.listdir("/proc")
    except OSError:
        return out
    for name in names:
        if name.isdigit():
            try:
                after = Path(f"/proc/{name}/stat").read_text().rsplit(")", 1)[1].split()
            except (OSError, IndexError):
                continue
            if int(after[1]) == os.getpid():
                out.append((int(name), after[0] != "Z"))
    return out


def run_fenced(argv: list, cwd: Path, env: dict, scratch: Path, read: list, write: list, never_read: list = (),
               never_write: list = (), kernel: bool | None = None, merged: bool = False, inherit: bool = False) -> dict:
    """Run one command and wait until nothing it started is left. `argv[0]` is an interpreter by its path.
    Returns {code, out, err, ended, left_alive, confined, fence, not_run}: `confined` is `kernel` only when the
    keeper reported that the fence was applied and that every trial against it failed; `fence` is that report, with
    what the script could read and write. `kernel=None` uses the kernel fence when the machine has one; then a fence
    that cannot be applied or does not hold is an exit code of 120 to 123, `not_run` is true and the script did not
    run. With `inherit` the script prints straight to the caller's own output and nothing is captured."""
    use_kernel = bool(landlock()) if kernel is None else kernel
    for q in write:  # a script never gets to write where the tools run from
        for mine in (own_environment(), TOOLS):
            if Path(os.path.realpath(mine)).is_relative_to(Path(os.path.realpath(q))):
                raise Cannot(f"the place the script may write ({q}) holds what the tool itself runs from ({mine}); nothing is run")
    if sys.platform.startswith("linux"):
        with contextlib.suppress(OSError, AttributeError):
            ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0)  # orphans the keeper could not end come to us
    (scratch / "kept-out.txt").write_text("a script inside the fence cannot read this\n")
    readable = [q for q in dict.fromkeys([*(q for q in SYSTEM_FOLDERS if os.path.exists(q)), *map(str, read), str(THIS)]) if os.path.exists(q)]
    writable = [q for q in dict.fromkeys([*map(str, write), *WRITABLE_DEVICES, SHARED_MEMORY]) if os.path.exists(q)]
    try:
        shared_before = set(os.listdir(SHARED_MEMORY))
    except OSError:
        shared_before = None
    must_not_read = [str(scratch / "kept-out.txt"), *map(str, never_read)]
    must_not_write = [str(scratch), str(own_environment()), str(TOOLS), *map(str, never_write)]
    spec = {"kernel": use_kernel, "argv": [str(w) for w in argv], "cwd": str(cwd), "env": env, "read": readable,
            "write": writable, "must_not_read": must_not_read, "must_not_write": must_not_write,
            "why_no_kernel": None if use_kernel else ("this machine has no Landlock (it is not Linux 5.13 or later with Landlock switched on)"
                                                      if not landlock() else "the caller asked for no kernel fence")}
    spec_file = scratch / "fence-spec.json"
    spec_file.write_text(json.dumps(spec))
    out_file, err_file = scratch / "stdout.txt", scratch / "stderr.txt"
    before = None if use_kernel else snapshot()
    sys.stdout.flush()
    sys.stderr.flush()
    r, w = os.pipe()
    try:
        with out_file.open("w") as o, err_file.open("w") as e:
            proc = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-X", f"pycache_prefix={NO_BYTECODE}", str(THIS), "--inside", str(spec_file), str(w)], cwd=str(scratch),
                                    env=env, stdin=subprocess.DEVNULL, stdout=None if inherit else o,
                                    stderr=None if inherit else (subprocess.STDOUT if merged else e),
                                    start_new_session=True, pass_fds=(w,))
            os.close(w)
            w = None
            with os.fdopen(r, "r") as f:
                r = None
                said = f.read()
            code = proc.wait()
    except (OSError, subprocess.SubprocessError) as failure:
        for fd in (r, w):
            if fd is not None:
                with contextlib.suppress(OSError):
                    os.close(fd)
        return {"code": 127, "out": "", "err": f"could not run: {failure}", "ended": 0, "left_alive": 0, "confined": SCRATCH_ONLY,
                "not_run": True, "fence": {"applied": False, "why_not": f"the keeper could not be started: {failure}"}}
    lines = [ln for ln in said.splitlines() if ln.strip()]
    try:
        report = json.loads(lines[0])
    except (ValueError, IndexError):
        report = {"applied": False, "tried": [], "why_not": "the keeper gave no report"}
        code = code or 124
    ended = 0
    with contextlib.suppress(ValueError, IndexError, KeyError, TypeError):
        ended = int(json.loads(lines[1])["ended"])  # what the keeper ended itself, before it reported
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(proc.pid, signal.SIGKILL)
    for _ in range(200):  # until nothing is left; a process that starts another while it is being ended is met again
        left = children()
        if not left:
            break
        for pid, running in left:
            ended += running
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, signal.SIGKILL)
            with contextlib.suppress(ChildProcessError):
                os.waitpid(pid, 0)
    left_alive = len([1 for _pid, running in children() if running])
    held = bool(use_kernel and report.get("applied") and report.get("tried") and not report.get("why_not"))
    fence = {"applied": held, "tried_and_kept_out": report.get("tried") or [], "why_not": report.get("why_not"),
             "could_read": readable if held else "anything its user can", "could_write": writable if held else "anything its user can",
             "landlock": landlock()}
    if shared_before is not None:
        left = []
        with contextlib.suppress(OSError):
            for name in sorted(set(os.listdir(SHARED_MEMORY)) - shared_before):
                with contextlib.suppress(OSError):
                    if os.lstat(os.path.join(SHARED_MEMORY, name)).st_uid == os.getuid():
                        left.append(name)
        fence["left_in_shared_memory"] = left
    if before is not None:
        moved = changed_since(before)
        fence["what_the_tools_run_from"] = ("changed while the script ran: " + ", ".join(moved[:6])) if moved else "unchanged, by size and time"
        fence["tools_changed"] = moved
    return {"code": code, "out": out_file.read_text(errors="replace"), "err": "" if merged else err_file.read_text(errors="replace"),
            "ended": ended, "left_alive": left_alive, "confined": KERNEL if held else SCRATCH_ONLY, "fence": fence,
            "not_run": bool(use_kernel and not held)}


def make_scratch(prefix: str) -> Path:
    """A new scratch folder with the places every script is given: work, tmp, cache, home; and `private`, which
    the script is never allowed to write (the prepared interpreter goes there)."""
    scratch = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
    for sub in ("work", "tmp", "cache", "home", "private"):
        (scratch / sub).mkdir()
    guard_folder(scratch).mkdir()
    (guard_folder(scratch) / "sitecustomize.py").write_text(DUCKDB_GUARD)
    return scratch


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--inside":
        sys.exit(inside(sys.argv[2], int(sys.argv[3])))
    print("fence.py is used by the tools of this package (tools/sf.py, tools/explore.py); it has no commands of its own",
          file=sys.stderr)
    sys.exit(2)
