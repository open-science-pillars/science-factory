#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""record_act: after a pull request that carried a lock request or a signature request is merged, write the act
into the study log.

Run by the job that follows the merge on the protected branch (acts.workflow.yml), under the repository's own
identity. It reads the platform's record of the merged pull request and of its reviews, and hands the study tool
a small file made from them: the pull request, its author, who merged it, and each person other than the author
whose latest review is an approval, with the commit they approved. The study tool then checks the merge with git
(`sf.py lock --record-merge`, `sf.py signature --record-merge`) and writes the lock or the signature under the
actor `platform:github`, naming those people. No name is typed by anybody: every name in the log entry comes
from the platform's record.

  record_act.py --repo CHECKOUT --pull PULL.json --reviews REVIEWS.json --commit MERGE_SHA [--tools DIR] [--factory DIR]
  record_act.py --which-pull PULLS.json --commit MERGE_SHA     the number of the pull request that commit merged, or nothing
  record_act.py --selftest

  --pull      the platform's pull request object (the pulls API), after the merge
  --reviews   the platform's list of reviews of that pull request, one page or several
  --commit    the merge commit on the protected branch

Exit 0: every request the merge brought in is recorded, or it brought none. Exit 1: the study tool refused one
(the merge does not check out, too few people approved, a request changed after its approval), and says why.

What this cannot do: prove to someone who has only the git history who approved. The log entry is a copy of the
platform's record made by this job; the record itself stays on the platform. This program has never been run by
GitHub: it is tested here on payloads written in the platform's shapes and a throwaway repository.
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent  # the repository: this file is in factory/harnesses/github/


def _load(name: str, path: Path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


check = _load("verify_request", HERE / "verify_request.py")  # the one reading of reviews and of which requests a change touches


def which_pull(pulls, commit: str) -> str:
    for p in pulls if isinstance(pulls, list) else []:
        if isinstance(p, dict) and p.get("merge_commit_sha") == commit and p.get("merged_at"):
            return str(p.get("number"))
    return ""


def platform_record(repo: Path, pull: dict, reviews, study: str, act: str) -> dict:
    """What the study tool is handed: the platform's record of one merged pull request, for one request."""
    author = str((pull.get("user") or {}).get("login") or "")
    approved = []
    for w in check.approvals(reviews, author):
        shown = check.git(repo, "show", f"{w['commit_id']}:{study}/{act}-request/manifest.json", text=False)
        approved.append({**w, "manifest_sha_at_review": hashlib.sha256(shown.stdout).hexdigest() if shown.returncode == 0 else "not in this repository"})
    return {"platform": "github", "pull_request": pull.get("number"), "url": pull.get("html_url"), "author": author,
            "merged": bool(pull.get("merged")), "merge_commit": pull.get("merge_commit_sha"), "merged_at": pull.get("merged_at"),
            "merged_by": (pull.get("merged_by") or {}).get("login"), "base": (pull.get("base") or {}).get("ref"), "approved": approved}


def record(repo: Path, pull: dict, reviews, commit: str, tools: Path, factory: Path) -> int:
    if not pull.get("merged") or pull.get("merge_commit_sha") != commit:
        print(f"record_act: the platform's record does not say this pull request was merged as {commit[:12]}; nothing is recorded", file=sys.stderr)
        return 1
    found, _paths = check.requests_touched(repo, f"{commit}^1", commit)
    if not found:
        print("record_act: this merge brought in no lock request and no signature request; nothing to record")
        return 0
    worst = 0
    for study, act in found:
        with tempfile.TemporaryDirectory() as t:
            rec = Path(t) / "platform-record.json"
            rec.write_text(json.dumps(platform_record(repo, pull, reviews, study, act), indent=1))
            done = subprocess.run(["uv", "run", "--quiet", str(tools / "sf.py"), act, "--study", str(repo / study), "--record-merge", commit,
                                   "--platform-record", str(rec), "--by", "platform:github", "--factory", str(factory)],
                                  capture_output=True, text=True, stdin=subprocess.DEVNULL)
        said = "\n".join(ln for ln in (done.stdout + done.stderr).splitlines() if not ln.startswith("warning: "))
        print(f"record_act: the {act} of {study}: " + ("recorded" if done.returncode == 0 else "NOT RECORDED") + "\n" + said)
        worst = max(worst, 1 if done.returncode else 0)
    return worst


def selftest(only: str | None = None) -> int:
    """One throwaway repository under the temporary folder, with a protected-branch stand-in (a branch named main),
    a study, a lock request on a branch of its own, the required check on payloads in the platform's shapes, a
    merge, the recording, the opening, and the same for the signature. Nothing here is a real person: the logins
    are the placeholders the fixtures carry."""
    import contextlib
    import io
    import shutil
    sf = _load("sf", ROOT / "tools" / "sf.py")
    results = []

    def ok(name: str, passed: bool, part: str) -> None:
        if only is None or only == part:
            results.append((name, bool(passed)))
    fixture = lambda name, **fill: json.loads(_fill((HERE / "fixtures" / name).read_text(), fill))  # noqa: E731

    def _fill(text: str, fill: dict) -> str:
        for k, v in fill.items():
            text = text.replace(k, v)
        return text
    A = sf.A
    V, R = "the required check", "recording the merge"
    with tempfile.TemporaryDirectory() as t, contextlib.redirect_stdout(io.StringIO()):
        tmp = Path(t).resolve()
        repo = tmp / "repo"
        (repo / "studies").mkdir(parents=True)
        g = lambda *w: check.git(repo, "-c", "user.name=selftest", "-c", "user.email=s@example.invalid", "-c", "commit.gpgsign=false", *w)  # noqa: E731
        sha = lambda ref="HEAD": g("rev-parse", ref).stdout.strip()  # noqa: E731
        g("init", "-q", "-b", "main")
        (repo / "README.md").write_text("a throwaway repository for a self-test\n")
        g("add", "-A"), g("commit", "-q", "-m", "start")
        base = sha()
        sf.Study.default_model, sf.Study.default_route = "selftest-model", None  # the real route: nothing here is typed as a person's act
        try:
            g("checkout", "-q", "-b", "lock/S1")
            study = sf._fresh(repo / "studies", "S1", start=A(id="STUDY-TEST", question=sf.PLAN["question"], by="agent:coordinating"))
            sf.cmd_test(study, A(what="known-answers", by="agent:analysis"))
            sf.cmd_test(study, A(what="working-data", by="agent:analysis"))
            sf.cmd_request_lock(study, A(by="agent:coordinating"))
            g("add", "-A"), g("commit", "-q", "-m", "lock request")
            head = sha()
            event = lambda **more: fixture("pull_request.opened.json", **{"HEAD_SHA": head, "BASE_SHA": base, "HEAD_REF": "lock/S1", "BASE_REF": "main", **more})  # noqa: E731
            tools, factory = ROOT / "tools", ROOT / "factory"
            run = lambda ev, reviews: check.verify(repo, ev, reviews, tools, factory)  # noqa: E731
            said = lambda got: "\n".join(got[1])  # noqa: E731

            ok("a study whose lock is only requested is not locked: no lock is in its log, and its status says the request waits",
               not study.last("lock.recorded") and "requested" in str(sf.acts_report(study)["lock"]), V)
            none = run(event(), fixture("reviews.none.json"))
            ok("a request nobody has approved fails the check, and the evidence summary is shown all the same",
               none[0] == 1 and "nobody but the author" in said(none) and "# Lock request: STUDY-TEST" in said(none), V)
            own = run(event(), fixture("reviews.author-only.json", HEAD_SHA=head))
            ok("the author's own approval does not count, and a bystander's comment is not an approval",
               own[0] == 1 and "0 do" in said(own), V)
            good = run(event(), fixture("reviews.approved.json", APPROVED_SHA=head))
            ok("approved at its head by somebody other than the author, with a manifest that matches the files, the request passes",
               good[0] == 0 and "every check passed" in said(good) and "octo-steward" in said(good), V)
            gone = run(event(), fixture("reviews.approval-withdrawn.pages.json", APPROVED_SHA=head))
            ok("an approval its giver later replaced by a request for changes does not count, read from an answer that came in pages",
               gone[0] == 1 and "nobody but the author" in said(gone), V)
            ok("a pull request against another branch than the protected one fails",
               run(event(BASE_REF="develop"), fixture("reviews.approved.json", APPROVED_SHA=head))[0] == 1, V)
            # a bound file changed after the approval, with the request left as it was
            (study.d / "toy.py").write_text((study.d / "toy.py").read_text() + "\n# changed after the approval\n")
            g("add", "-A"), g("commit", "-q", "-m", "a change after the approval")
            later = sha()
            late = check.verify(repo, event(HEAD_SHA=later), fixture("reviews.approved.json", APPROVED_SHA=head), tools, factory)
            ok("a commit after the approval that changes a bound file fails the check: the manifest no longer matches the files",
               late[0] == 1 and "FAILED: the request's manifest matches the files" in said(late) and "toy.py" in said(late), V)
            # the request prepared again: the files match, and the old approval no longer covers it
            sf.cmd_test(study, A(what="known-answers", by="agent:analysis"))
            sf.cmd_test(study, A(what="working-data", by="agent:analysis"))
            sf.cmd_request_lock(study, A(by="agent:coordinating"))
            g("add", "-A"), g("commit", "-q", "-m", "the request, prepared again")
            again = sha()
            stale = check.verify(repo, event(HEAD_SHA=again), fixture("reviews.approved.json", APPROVED_SHA=head), tools, factory)
            ok("a request prepared again after an approval passes the manifest check and fails for the stale approval, by name",
               stale[0] == 1 and "passed: the request's manifest matches" in said(stale) and "changed after the approval of octo-steward" in said(stale), V)
            fresh = check.verify(repo, event(HEAD_SHA=again), fixture("reviews.approved.json", APPROVED_SHA=again), tools, factory)
            ok("approved again as it now stands, it passes", fresh[0] == 0, V)
            # a pull request that carries a request and also changes the tools
            g("checkout", "-q", "-b", "with-tools")
            (repo / "tools").mkdir()
            (repo / "tools" / "sf.py").write_text("# not the study tool\n")
            g("add", "-A"), g("commit", "-q", "-m", "a request and a change to the tools together")
            both = check.verify(repo, event(HEAD_SHA=sha()), fixture("reviews.approved.json", APPROVED_SHA=sha()), tools, factory)
            ok("a pull request that carries a request and also changes tools/ fails: the check is not brought along by what it checks",
               both[0] == 1 and "it also changes tools/sf.py" in said(both), V)
            g("checkout", "-q", "lock/S1")
            shutil.rmtree(repo / "tools", ignore_errors=True)
            g("checkout", "-q", "-b", "no-request", base)
            (repo / "notes.md").write_text("nothing to do with a study\n")
            g("add", "-A"), g("commit", "-q", "-m", "an ordinary change")
            ok("a pull request that touches no request has nothing to check and passes",
               check.verify(repo, event(HEAD_SHA=sha()), [], tools, factory) == (0, []), V)
            g("checkout", "-q", "lock/S1")

            # ---- the merge, and the recording
            pull = lambda **more: fixture("pull.merged.json", **{"HEAD_SHA": again, "BASE_SHA": base, "HEAD_REF": "lock/S1", "BASE_REF": "main", **more})  # noqa: E731
            reviews = fixture("reviews.approved.json", APPROVED_SHA=again)
            ok("the number of the pull request a commit merged is read from the platform's list, and a commit that merged none gives nothing",
               which_pull(fixture("commit.pulls.json", MERGE_SHA="abc"), "abc") == "7" and which_pull(fixture("commit.pulls.json", MERGE_SHA="abc"), "def") == "", R)
            ok("before the merge nothing can be recorded: the commit the request sits on is not on the protected branch",
               record(repo, pull(MERGE_SHA=again), reviews, again, tools, factory) == 1 and not study.last("lock.recorded"), R)
            g("checkout", "-q", "main")
            g("merge", "-q", "--no-ff", "-m", "Merge the lock request", "lock/S1")
            merge = sha()
            ok("a pull request the platform does not call merged is not recorded",
               record(repo, {**pull(MERGE_SHA=merge), "merged": False}, reviews, merge, tools, factory) == 1 and not study.last("lock.recorded"), R)
            ok("a merge approved by nobody but its author is not recorded",
               record(repo, pull(MERGE_SHA=merge), fixture("reviews.author-only.json", HEAD_SHA=again), merge, tools, factory) == 1
               and not study.last("lock.recorded"), R)
            ok("a merge whose only approval was given before the request changed is not recorded",
               record(repo, pull(MERGE_SHA=merge), fixture("reviews.approved.json", APPROVED_SHA=head), merge, tools, factory) == 1
               and not study.last("lock.recorded"), R)
            ok("a merge into another branch than the protected one is not recorded",
               record(repo, pull(MERGE_SHA=merge, BASE_REF="develop"), reviews, merge, tools, factory) == 1 and not study.last("lock.recorded"), R)
            done = record(repo, pull(MERGE_SHA=merge), reviews, merge, tools, factory)
            lock = study.last("lock.recorded")
            ok("the merge is recorded as the lock: under the platform's name, citing the merge commit, the pull request and the people "
               "who approved by the platform's record, with nothing typed",
               done == 0 and lock is not None and lock["actor"] == "platform:github" and lock["data"]["route"] == "pull-request"
               and lock["data"]["merge"]["commit"] == merge and lock["data"]["merge"]["pull_request"] == 7
               and lock["data"]["merge"]["people"] == {"author": "octo-author", "approved": ["octo-steward"], "merged_by": "octo-steward"}
               and not any(e["actor"].startswith("human:") for e in study.events()), R)
            g("add", "-A"), g("commit", "-q", "-m", "Record the act merged in " + merge)
            sf.cmd_open_held_out(study, A(test="held-out", by="agent:coordinating"))
            ok("with the lock recorded from the merge and committed, the held-out data is opened, with no practice flag anywhere",
               study.last("opening.finished") is not None and study.last("opening.started")["data"]["lock_route"] == "pull-request", R)

            # ---- the signature, the same way
            g("checkout", "-q", "-b", "sign/S1")
            (tmp / "finding.md").write_text("a finding drafted from receipts\n")
            (tmp / "verdict.md").write_text("APPROVE\n")
            sf.cmd_attach(study, A(by="agent:analysis", file=str(tmp / "finding.md")))
            sf.cmd_review(study, A(by="agent:review", verdict="approve", file=str(tmp / "verdict.md")))
            posted = sf._posted(study)
            sf.cmd_request_signature(study, A(by="agent:coordinating", decision="signed", anchor=posted, evidence=None, comment=None))
            g("add", "-A"), g("commit", "-q", "-m", "signature request")
            s_head = sha()
            s_event = fixture("pull_request.opened.json", HEAD_SHA=s_head, BASE_SHA=merge, HEAD_REF="sign/S1", BASE_REF="main")
            s_check = check.verify(repo, s_event, fixture("reviews.approved.json", APPROVED_SHA=s_head), tools, factory)
            ok("a signature request passes the same check, and its summary shows the finding and the review",
               s_check[0] == 0 and "# Signature request: STUDY-TEST" in said(s_check) and "a finding drafted from receipts" in said(s_check)
               and "agent:review: approve" in said(s_check), V)
            g("checkout", "-q", "main")
            g("merge", "-q", "--no-ff", "-m", "Merge the signature request", "sign/S1")
            s_merge = sha()
            s_pull = fixture("pull.merged.json", HEAD_SHA=s_head, BASE_SHA=merge, HEAD_REF="sign/S1", BASE_REF="main", MERGE_SHA=s_merge)
            s_done = record(repo, s_pull, fixture("reviews.approved.json", APPROVED_SHA=s_head), s_merge, tools, factory)
            sig = study.last("signature.recorded")
            ok("the merged signature request is recorded as the steward's signature, with the decision the request carried",
               s_done == 0 and sig is not None and sig["actor"] == "platform:github" and sig["data"]["decision"] == "signed"
               and sig["data"]["merge"]["commit"] == s_merge and sig["data"]["finding"]["sha"] == sf.sha_file(tmp / "finding.md"), R)
            g("add", "-A"), g("commit", "-q", "-m", "Record the act merged in " + s_merge)
            sf.cmd_close(study, A(by="agent:coordinating", outcome="finding-signed", cite=None, comment=None, anchor=posted))
            ok("a study whose lock and signature were merged pull requests closes as a signed finding",
               study.last("study.closed")["data"]["outcome"] == "finding-signed", R)
        finally:
            sf.Study.default_model = sf.Study.default_route = None
    for name, passed in results:
        print(("PASS  " if passed else "FAIL  ") + name)
    good = bool(results) and all(passed for _n, passed in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(p for _n, p in results)} of {len(results)})")
    return 0 if good else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--repo")
    ap.add_argument("--pull")
    ap.add_argument("--reviews")
    ap.add_argument("--commit")
    ap.add_argument("--which-pull", dest="which_pull", default=None)
    ap.add_argument("--tools", default=None)
    ap.add_argument("--factory", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        if a.which_pull:
            print(which_pull(json.loads(Path(a.which_pull).read_text()), str(a.commit)))
            return 0
        if not (a.repo and a.pull and a.reviews and a.commit):
            ap.error("--repo, --pull, --reviews and --commit are required")
        repo = Path(a.repo).resolve()
        tools = Path(a.tools).resolve() if a.tools else repo / "tools"
        factory = Path(a.factory).resolve() if a.factory else tools.parent / "factory"
        return record(repo, json.loads(Path(a.pull).read_text()), json.loads(Path(a.reviews).read_text()), a.commit, tools, factory)
    except (OSError, ValueError) as e:
        print(f"record_act: a file could not be read ({e})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
