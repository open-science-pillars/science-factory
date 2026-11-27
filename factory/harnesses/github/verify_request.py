#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""verify_request: the required check on a pull request that carries a lock request or a signature request.

The lock and the steward's signature are acts by people. In a real study each is a pull request, approved and
merged on a protected branch of the repository where the study lives, so that who acted is the platform's
record and not a name typed on a machine that agents share. This program is the check that pull request must
pass. It is run by the workflow beside it (acts.workflow.yml) and can be run by hand:

  verify_request.py --repo CHECKOUT --event EVENT.json --reviews REVIEWS.json
                    [--tools DIR] [--factory DIR] [--summary-out FILE] [--image-base URL]

  --repo      the pull request's head, checked out with its history
  --event     the platform's event payload for the pull request (a `pull_request` or `pull_request_review` event)
  --reviews   the platform's list of reviews of the pull request (the reviews API, one page or several)
  --tools     the science factory's tools/ to check with (default: tools/ in --repo). The workflow gives the
              protected branch's, so that a pull request cannot bring its own check with it
  --factory   the definition to check against (default: factory/ beside --tools)
  --image-base  the address the request's figures are served from at the head of the pull request (the workflow
              gives https://github.com/OWNER/REPO/raw/HEAD_SHA): a figure the evidence summary links by a path
              relative to its folder is shown in the comment from there, so a reviewer sees each picture

What it checks, each said in plain words when it fails:
  1. the pull request targets the protected branch the definition names for the act;
  2. a pull request that carries a request changes nothing in tools/, factory/ or .github/;
  3. the request's manifest matches the files at the head of the pull request (`sf.py check-request`);
  4. enough people other than the pull request's author approve it now (the latest review of each counts), as many
     as the definition asks: the author's own approval never counts;
  5. no commit after a counted approval changed what the approval covered: the request's manifest and evidence
     summary at the approved commit are the ones at the head (the manifest binds every other file by checksum).

It prints the evidence summary of each request with the result of each check, and writes the same to
--summary-out for the workflow to put on the pull request. Exit 0: every check passed, or the pull request touches
no request. Exit 1: a check failed. Exit 2: it could not check.

What it cannot check: that the branch is protected and this check required, and who the approvers are beyond their
login. Those are the repository's settings (README.md beside this file). It has never been run by GitHub. It is a
check on the platform, where the event and the reviews are the platform's own; run by hand on a clone, with files
somebody wrote, it proves nothing about people, and the study tool never takes its word for who approved: that is
asked of the platform by `sf.py verify-acts` (verify_acts.py beside this file).
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import posixpath  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
REQUEST = re.compile(r"^(?P<study>(?:.*/)?[^/]+)/(?P<act>lock|signature)-request/(?:manifest\.json|EVIDENCE\.md)$")
NOT_WITH_A_REQUEST = ("tools/", "factory/", ".github/")


def uv_env() -> dict:
    """The environment uv is called with: this one, without a setting of uv's own that is set and empty, which uv refuses
    before it runs anything (UV_NATIVE_TLS=, found by the first real run of the factory)."""
    return {k: v for k, v in os.environ.items() if not (k.startswith("UV_") and not v.strip())}


def git(repo: Path, *words, text: bool = True):
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "LC_ALL") if k in os.environ}
    return subprocess.run(["git", "-C", str(repo), *words], capture_output=True, text=text, env=env, stdin=subprocess.DEVNULL)


def flat(reviews) -> list:
    """The reviews as one list, whether the platform's answer came as one page or as a list of pages."""
    if isinstance(reviews, list) and reviews and all(isinstance(x, list) for x in reviews):
        return [r for page in reviews for r in page]
    return reviews if isinstance(reviews, list) else []


def approvals(reviews, author: str) -> list:
    """Who approves the pull request now, the author and every bot apart: for each account the latest review that is
    an approval, a request for changes or a dismissal decides (a later comment does not withdraw an approval). An
    account the platform does not call a user (an app, a bot) approves nothing: an act by people is approved by
    people. An entry that is not a review in the platform's shape is passed over."""
    latest = {}
    for r in sorted((r for r in flat(reviews) if isinstance(r, dict) and isinstance(r.get("user"), dict)), key=lambda r: str(r.get("submitted_at") or "")):
        login = str(r["user"].get("login") or "")
        if login and str(r.get("state")).upper() in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[login.casefold()] = r
    person = lambda r: str(r["user"].get("type") or "User").casefold() == "user" and not str(r["user"].get("login")).casefold().endswith("[bot]")  # noqa: E731
    return [{"login": r["user"]["login"], "commit_id": r.get("commit_id"), "submitted_at": r.get("submitted_at")}
            for key, r in sorted(latest.items()) if str(r.get("state")).upper() == "APPROVED" and key != author.casefold() and person(r)]


def requests_touched(repo: Path, base: str, head: str) -> tuple:
    """(the requests the pull request touches, as (study folder, act); every path it changes)."""
    done = git(repo, "diff", "--name-only", f"{base}...{head}")
    if done.returncode != 0:
        raise SystemExit(f"verify_request: could not list what the pull request changes ({done.stderr.strip()[:200]})")
    paths = [p for p in done.stdout.splitlines() if p.strip()]
    found = sorted({(m.group("study"), m.group("act")) for m in map(REQUEST.match, paths) if m})
    return found, paths


def declared(factory: Path) -> dict:
    spec = yaml.safe_load((factory / "factory.yaml").read_text())
    return (spec.get("procedure") or {}).get("acts_by_people") or {}


IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def with_images(text: str, base: str | None, folder: str) -> str:
    """The evidence summary with each figure it links by a relative path pointed at `base`, so that a comment on the pull
    request, which resolves no relative path, still shows the picture. A link that leaves the repository is left as it is."""
    if not base:
        return text

    def at(m) -> str:
        target = m.group(2)
        if re.match(r"^[a-z]+:", target) or target.startswith("/"):
            return m.group(0)
        path = posixpath.normpath(posixpath.join(folder, target))
        return m.group(0) if path.startswith("..") else f"![{m.group(1)}]({base.rstrip('/')}/{path})"
    return IMAGE.sub(at, text)


def verify(repo: Path, event: dict, reviews, tools: Path, factory: Path, image_base: str | None = None) -> tuple:
    """(exit code, the summary as Markdown lines)."""
    pr = event.get("pull_request") or {}
    try:
        author, head, base_ref, base_sha = pr["user"]["login"], pr["head"]["sha"], pr["base"]["ref"], pr["base"]["sha"]
    except (KeyError, TypeError):
        return 2, ["The event payload is not a pull request's: it has no author, head or base."]
    found, paths = requests_touched(repo, base_sha, head)
    if not found:
        return 0, []
    if not isinstance(reviews, list):
        return 2, ["The reviews are not a list, as the platform gives them: the check could not read who approved, and nothing is passed on an answer it cannot read."]
    acts, failed, out = declared(factory), False, []
    for study, act in found:
        rules = acts.get(act) or {}
        need, branch = int(rules.get("approvals") or 1), rules.get("protected_branch")
        checks = []
        checks.append((f"the pull request targets `{branch}`, the protected branch the definition names for the {act}",
                       base_ref == branch, f"it targets `{base_ref}`"))
        beside = [p for p in paths if p.startswith(NOT_WITH_A_REQUEST)]
        checks.append(("the pull request changes nothing in tools/, factory/ or .github/", not beside,
                       "it also changes " + ", ".join(beside[:5]) + ": a change to the tools, the definition or the workflows is a pull "
                       "request of its own, merged before the request is prepared"))
        done = subprocess.run(["uv", "run", "--quiet", str(tools / "sf.py"), "check-request", "--study", str(repo / study), "--act", act,
                               "--factory", str(factory)], capture_output=True, text=True, stdin=subprocess.DEVNULL, env=uv_env())
        said = [ln for ln in (done.stderr + done.stdout).strip().splitlines() if not ln.startswith("warning: ")]
        checks.append(("the request's manifest matches the files at the head of the pull request", done.returncode == 0,
                       " ".join(said)[-900:] or "the study tool gave no answer"))
        who = approvals(reviews, author)
        checks.append((f"{need} or more people other than the author ({author}) approve it now", len(who) >= need,
                       (f"{len(who)} do" + (": " + ", ".join(w["login"] for w in who) if who else "")
                        + ". The author's own approval does not count, and an act by people needs somebody else's")))
        stale = []
        for w in who:
            if w["commit_id"] == head:
                continue
            for name in ("manifest.json", "EVIDENCE.md"):
                rel = f"{study}/{act}-request/{name}"
                then, now = git(repo, "show", f"{w['commit_id']}:{rel}", text=False), git(repo, "show", f"{head}:{rel}", text=False)
                if then.returncode != 0 or now.returncode != 0 or then.stdout != now.stdout:
                    stale.append(w["login"])
                    break
        checks.append(("no commit after an approval changed what the approval covered", not stale,
                       "the request changed after the approval of " + ", ".join(sorted(set(stale))) + ": they approve it again as it now stands"))
        ok = all(passed for _what, passed, _why in checks)
        failed = failed or not ok
        out += [f"## The {act} of `{study}`: " + ("every check passed" if ok else "NOT READY TO MERGE"), ""]
        out += [("- passed: " if passed else "- FAILED: ") + what + ("" if passed else f" ({why})") for what, passed, why in checks]
        out += ["", "Approving now, by the platform's record: " + (", ".join(w["login"] for w in who) or "nobody but the author") + ".", ""]
        summary = repo / study / f"{act}-request" / "EVIDENCE.md"
        out += ["<details><summary>The evidence summary a person reads before approving</summary>", "",
                with_images(summary.read_text(), image_base, f"{study}/{act}-request") if summary.is_file() else "(the request has no EVIDENCE.md)",
                "", "</details>", ""]
    head_line = ["# Acts by people: " + ("ready to merge" if not failed else "not ready to merge"), "",
                 "Merging this pull request is the act itself. It is made by the people who approve and merge it here, on the "
                 "protected branch; this check only says whether what they are shown still matches the files.", ""]
    return (1 if failed else 0), head_line + out


def selftest() -> int:
    """The checks of this file are tested together with the recording, on one throwaway repository: record_act.py
    holds that self-test, and this runs the part of it that is about the required check."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("record_act", HERE / "record_act.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["record_act"] = mod
    spec.loader.exec_module(mod)
    return mod.selftest(only="the required check")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--repo")
    ap.add_argument("--event")
    ap.add_argument("--reviews")
    ap.add_argument("--tools", default=None)
    ap.add_argument("--factory", default=None)
    ap.add_argument("--summary-out", dest="summary_out", default=None)
    ap.add_argument("--image-base", dest="image_base", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.repo and a.event and a.reviews):
        ap.error("--repo, --event and --reviews are required")
    repo = Path(a.repo).resolve()
    tools = Path(a.tools).resolve() if a.tools else repo / "tools"
    factory = Path(a.factory).resolve() if a.factory else tools.parent / "factory"
    try:
        event, reviews = json.loads(Path(a.event).read_text()), json.loads(Path(a.reviews).read_text())
    except (OSError, ValueError) as e:
        print(f"verify_request: the event or the reviews could not be read ({e})", file=sys.stderr)
        return 2
    code, lines = verify(repo, event, reviews, tools, factory, a.image_base)
    text = "\n".join(lines) + ("\n" if lines else "")
    if a.summary_out:
        Path(a.summary_out).write_text(text)
    print(text or "verify_request: this pull request touches no lock request and no signature request; nothing to check")
    print("verify_request: " + {0: "PASS", 1: "FAIL", 2: "NOT CHECKED"}[code])
    return code


if __name__ == "__main__":
    sys.exit(main())
