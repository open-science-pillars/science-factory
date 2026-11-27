#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""verify_acts: ask the platform whether the people really approved a lock or a signature.

A clone cannot prove that people acted. git on a machine shows a merge of a request on a branch with the protected
branch's name, and a clone can make such a merge by itself; a file of approvals on that machine is a file anybody
with the account can write. So the study tool calls an act found that way `merge found, people not verified`, and
moves it to `verified` only on what this program is told by the platform itself, asked over HTTPS with a token
from the environment. The study tool calls it (`sf.py verify-acts --study ...`); this file holds everything that
is about GitHub, and the one function that talks to it.

What it asks, for one act (the endpoints are GitHub's REST API, written here from its documentation):
  GET /repos/{repository}                                   that the repository answers under the name the definition gives
  GET /repos/{repository}/commits/{commit}/pulls            which pull requests the merge commit belongs to
  GET /repos/{repository}/pulls/{number}                    that it was merged, as which commit, into which branch of which repository, by whom
  GET /repos/{repository}/pulls/{number}/reviews            who approved, when, on which commit; every page
  GET /repos/{repository}/commits/{commit}                  the parents of the merge commit as the platform holds it
  GET /repos/{repository}/compare/{commit}...{branch}       that the commit is on the protected branch now
  GET /repos/{repository}/branches/{branch}                 that the branch is protected
  GET /repos/{repository}/branches/{branch}/protection      its rules, where the token may see them (it needs more than read access)
  GET /repos/{repository}/rules/branches/{branch}           the rule sets that apply to it
  GET /repos/{repository}/contents/{path}?ref={commit}      the request's manifest and evidence summary as they stood at each approved commit

What `verified` then means, and no more: the platform said, when asked, that the commit the act cites is the merge
of a pull request into the protected branch of the repository the definition names; that enough accounts other
than the pull request's author, none of them a bot, hold an approving review as their latest word, given before
the merge, on a commit whose request (manifest and evidence summary) is byte for byte the one that was merged;
that the commit is on that branch now; and that the branch is protected. Where the token may read the branch's
rules they are held to the definition too (a pull request required, as many approvals, the check `request-check`
required); where it may not, the answer says the rules were not shown.

It also asks about one comment that carries a person's so what on a lead (`verify_comment`, called by
`explore.py verify-so-what`): GET /repos/{repository}/issues/comments/{id}.

What it does not mean: that the approving accounts are the right people (whoever reads the names judges that; the
repository's code owners say who may approve), or that whoever ran the verification ran this code on an honest
machine. The answer is recorded in the study log with every endpoint that was asked, and anybody can ask again.

With no token, no network, or an answer that cannot be read, the result is `not checked`, which is never a pass.

  verify_acts.py --selftest     everything around the call, on recorded answers written in the platform's shapes
                                (fixtures/verify.answers.json, and hostile ones in fixtures/verify.hostile.json)

This program has never been run against GitHub. The endpoints and the shapes of their answers are written from
the platform's documentation and from memory of it, and the fixtures were written by hand to those shapes. The one
function that makes the request, `platform_call`, has been exercised only against a server this file starts on
the machine's own loopback address for its self-test.
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site and "sf-no-bytecode" in str(sys.pycache_prefix)):
    # A clean start, as in the tools: run again in a Python that reads no PYTHON variable, no user site, no start-up file
    # and no cached bytecode (its cache prefix is a path that cannot exist). What ran before this line has already run.
    import os
    _again = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + ("/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(os.environ.get("TEMP", "."), f"sf-no-bytecode-{os.getpid()}")), os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
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

import copy  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import urllib.error  # noqa: E402
import urllib.parse  # noqa: E402
import ssl  # noqa: E402
import urllib.request  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
PLATFORM = "github"
API = "https://api.github.com"
HOST = "api.github.com"  # the one host a verification asks; harness.yaml must name it as `platform.api`, and nothing else can
# Where the system's own certificate authorities are, tried in order when this program is asked to verify; the first file
# that exists is used, and recorded with its checksum. A certificate setting of the caller's (SSL_CERT_FILE and the like)
# is never read: the program that asks runs with an environment that holds the token and nothing else.
SYSTEM_CERTIFICATES = ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/ca-bundle.pem",
                       "/etc/ssl/cert.pem", "/usr/local/etc/openssl/cert.pem", "/opt/homebrew/etc/openssl@3/cert.pem")
TOKEN_NAMES = ("SF_PLATFORM_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")  # the first that is set; a token is never read from a file
REQUIRED_CHECK = "request-check"  # the job of acts.workflow.yml that the branch protection makes a required status check
DECIDES_THE_ROUTE = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
                     "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")  # read by nothing that asks: recorded as ignored
VERIFIED, REFUTED, NOT_CHECKED = "verified", "refuted", "not checked"
NOT_REACHED = (0, 401, 403, 429)  # no answer, or an answer that says only that this token may not ask
MAX_PAGES = 20


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect is not followed: it would carry the token to wherever the answer points."""

    def redirect_request(self, *args, **kwargs):
        return None


def certificates() -> dict:
    """The certificate authorities a verification trusts: the system's own file, by path and checksum, or the system's
    default store where no such file is found. Never what an environment variable names."""
    defaults = ssl.get_default_verify_paths()
    for f in (defaults.openssl_cafile, *SYSTEM_CERTIFICATES):
        if f and os.path.isfile(f):
            with open(f, "rb") as fh:
                return {"path": f, "sha256": hashlib.sha256(fh.read()).hexdigest()}
    return {"path": None, "sha256": None, "store": "the system's default store (no certificate file was found)"}


def opener_for(proxy: str | None = None) -> tuple:
    """(the opener a verification asks through, how it asks). Only the proxy the definition names (harness.yaml,
    `platform.proxy`) is used, as a tunnel: no proxy setting of the environment is read, and the certificates are the
    system's (`certificates`), whatever the environment says."""
    certs = certificates()
    ctx = ssl.create_default_context(cafile=certs["path"]) if certs["path"] else ssl.create_default_context()
    if not certs["path"]:
        ctx.load_default_certs()
    proxies = {"https": str(proxy)} if proxy else {}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies), urllib.request.HTTPSHandler(context=ctx), _NoRedirect)
    return opener, {"host": HOST, "proxy": str(proxy) if proxy else None, "certificates": certs}


def platform_call(api: str, path: str, token: str, opener=None) -> dict:
    """The one function that talks to the platform: one GET, one answer, as {"status", "body"} or {"status": 0,
    "error"}. Nothing is retried and no redirect is followed. Without an opener it asks the one host this file names
    (HOST), with no proxy and the system's certificates; an opener is given only by `ask` (the definition's proxy) and
    by this file's self-test (a server on the loopback address). Everything else in this file works on what this
    returns, and the self-tests put recorded answers in its place."""
    if opener is None and not str(api).startswith("https://"):
        return {"status": 0, "error": "the platform is asked over https and nothing else"}
    if opener is None and urllib.parse.urlsplit(str(api)).hostname != HOST:
        return {"status": 0, "error": f"the platform is asked at {HOST} and nowhere else"}
    if opener is None:
        opener = opener_for(None)[0]
    req = urllib.request.Request(api.rstrip("/") + path, headers={
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}", "User-Agent": "science-factory-verify-acts"})
    try:
        with opener.open(req, timeout=30) as resp:
            return {"status": resp.status, "body": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except (ValueError, OSError):
            body = None
        return {"status": e.code, "body": body}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"status": 0, "error": f"{type(e).__name__}: {str(e)[:200]}"}


def token_from(environ) -> tuple:
    """(the name of the environment variable the token came from, the token), or (None, None). The name goes into
    the record; the token never does."""
    for name in TOKEN_NAMES:
        if str(environ.get(name) or "").strip():
            return name, str(environ[name]).strip()
    return None, None


def through(environ) -> list:
    """The names of the caller's settings that would decide how a request travels (a proxy, a certificate store). The
    program that asks never sees them (`ask` runs with an environment that holds the token alone), so they are recorded
    by name as ignored: a request sent through a proxy with its own certificates would be answered by that proxy."""
    return sorted(n for n in DECIDES_THE_ROUTE if environ.get(n))


def _login(obj) -> str:
    return str((obj or {}).get("login") or "") if isinstance(obj, dict) else ""


def _flat(reviews) -> list:
    if isinstance(reviews, list) and reviews and all(isinstance(x, list) for x in reviews):
        return [r for page in reviews for r in page]
    return reviews if isinstance(reviews, list) else []


def gather(call, api: str, token: str, expect: dict) -> dict:
    """Ask the platform everything a verification needs about one act, and return what it said: {"asked": every
    endpoint with its status, in order, "answers": {a short name: the body}}. `expect` names the repository, the
    branch, the commit and the request's two files (see `judge`)."""
    asked, answers = [], {}
    repo, commit = expect["repository"], expect["commit"]
    branch = urllib.parse.quote(str(expect["branch"]), safe="")

    def ask(name: str, path: str):
        got = call(api, path, token)
        if not isinstance(got, dict):
            got = {"status": 0, "error": "the call gave no answer"}
        asked.append({"endpoint": api.rstrip("/") + path, "status": got.get("status"), **({"error": got["error"]} if got.get("error") else {})})
        if got.get("status") == 200:
            answers[name] = got.get("body")
        return got

    first = ask("repository", f"/repos/{repo}")
    if first.get("status") != 200:
        return {"asked": asked, "answers": answers}
    ask("pulls_of_commit", f"/repos/{repo}/commits/{commit}/pulls")
    number = None
    for p in answers.get("pulls_of_commit") or []:
        if isinstance(p, dict) and p.get("merge_commit_sha") == commit:
            number = p.get("number")
            break
    if number is None:  # none of them names this commit as its merge: ask about the first, so the record says which pull request it is
        number = next((p.get("number") for p in answers.get("pulls_of_commit") or [] if isinstance(p, dict)), None)
    if isinstance(number, int) and not isinstance(number, bool):
        ask("pull", f"/repos/{repo}/pulls/{number}")
        pages = []
        for page in range(1, MAX_PAGES + 1):
            got = ask(f"reviews_page_{page}", f"/repos/{repo}/pulls/{number}/reviews?per_page=100&page={page}")
            if got.get("status") != 200 or not isinstance(got.get("body"), list):
                break
            pages.append(got["body"])
            if len(got["body"]) < 100:
                break
        answers["reviews"] = pages
    ask("commit", f"/repos/{repo}/commits/{commit}")
    ask("on_branch", f"/repos/{repo}/compare/{commit}...{branch}")
    ask("branch", f"/repos/{repo}/branches/{branch}")
    ask("protection", f"/repos/{repo}/branches/{branch}/protection")
    ask("rules", f"/repos/{repo}/rules/branches/{branch}")
    at_commit = {}
    for r in _flat(answers.get("reviews")):
        cid = str((r or {}).get("commit_id") or "") if isinstance(r, dict) else ""
        if isinstance(r, dict) and str(r.get("state")).upper() == "APPROVED" and re.fullmatch(r"[0-9a-f]{40,64}", cid) and cid not in at_commit and len(at_commit) < 20:
            at_commit[cid] = {}
            for what in ("manifest", "evidence"):
                path = urllib.parse.quote(expect["request"][what]["path"], safe="/")
                got = ask(f"contents:{cid}:{what}", f"/repos/{repo}/contents/{path}?ref={cid}")
                at_commit[cid][what] = (got.get("body") or {}).get("sha") if got.get("status") == 200 and isinstance(got.get("body"), dict) else None
    answers["request_at_commit"] = at_commit
    return {"asked": asked, "answers": answers}


def rules_seen(answers: dict) -> dict:
    """What the platform showed of the branch's rules, from its classic protection and from its rule sets: whether a
    pull request is required, how many approvals, whether stale approvals are dismissed, the required checks, and
    whether administrators are held to it. A key is None when nothing shown says."""
    out = {"shown": [], "pull_request_required": None, "approvals_required": None, "stale_approvals_dismissed": None,
           "checks_required": None, "administrators_included": None, "force_pushes_refused": None}
    prot = answers.get("protection")
    if isinstance(prot, dict):
        out["shown"].append("branch protection")
        rev = prot.get("required_pull_request_reviews")
        out["pull_request_required"] = isinstance(rev, dict)
        if isinstance(rev, dict):
            out["approvals_required"] = rev.get("required_approving_review_count")
            out["stale_approvals_dismissed"] = bool(rev.get("dismiss_stale_reviews"))
        checks = prot.get("required_status_checks")
        if isinstance(checks, dict):
            out["checks_required"] = sorted({str(c) for c in checks.get("contexts") or []}
                                            | {str(c.get("context")) for c in checks.get("checks") or [] if isinstance(c, dict)})
        else:
            out["checks_required"] = []
        out["administrators_included"] = bool((prot.get("enforce_admins") or {}).get("enabled")) if isinstance(prot.get("enforce_admins"), dict) else None
        if isinstance(prot.get("allow_force_pushes"), dict):
            out["force_pushes_refused"] = not prot["allow_force_pushes"].get("enabled")
    rules = answers.get("rules")
    if isinstance(rules, list) and rules:
        out["shown"].append("rule sets")
        for r in rules:
            if not isinstance(r, dict):
                continue
            par = r.get("parameters") if isinstance(r.get("parameters"), dict) else {}
            if r.get("type") == "pull_request":
                out["pull_request_required"] = True
                n = par.get("required_approving_review_count")
                if isinstance(n, int):
                    out["approvals_required"] = max(n, out["approvals_required"] or 0)
                if par.get("dismiss_stale_reviews_on_push"):
                    out["stale_approvals_dismissed"] = True
            elif r.get("type") == "required_status_checks":
                more = {str(c.get("context")) for c in par.get("required_status_checks") or [] if isinstance(c, dict)}
                out["checks_required"] = sorted(set(out["checks_required"] or []) | more)
            elif r.get("type") == "non_fast_forward":
                out["force_pushes_refused"] = True
    if out["checks_required"] is None:
        summary = ((answers.get("branch") or {}).get("protection") or {}).get("required_status_checks") if isinstance(answers.get("branch"), dict) else None
        if isinstance(summary, dict) and isinstance(summary.get("contexts"), list):
            out["shown"].append("the branch's own summary of its required checks")
            out["checks_required"] = sorted(str(c) for c in summary["contexts"])
    return out


def judge(gathered: dict, expect: dict) -> dict:
    """Hold what the platform said to what the act claims. `expect` is what the study tool knows from the definition
    and from git: {"repository": owner/name, "branch", "commit": the merge commit, "approvals": how many,
    "parents": the commit's parents here, "request": {"manifest": {"path", "blob"}, "evidence": {"path", "blob"}}}
    (a blob is git's own checksum of the file as it is in the merge commit). Returns {"result": verified, refuted or
    not checked, "problems": why not, "told": a summary of the platform's answers, small enough for a log}."""
    asked, ans = gathered.get("asked") or [], gathered.get("answers") or {}
    problems, told = [], {}
    not_reached = [a for a in asked if a.get("status") in NOT_REACHED or (isinstance(a.get("status"), int) and a["status"] >= 500)]
    needed = ("repository", "pulls_of_commit", "pull", "reviews", "commit", "on_branch", "branch")

    def done(result: str) -> dict:
        return {"result": result, "problems": problems, "told": told}

    if not asked:
        problems.append("the platform was not asked")
        return done(NOT_CHECKED)
    first = asked[0]
    if first.get("status") != 200:
        if first.get("status") in (301, 302, 307, 308):
            problems.append(f"the platform answered {first['status']} for the repository `{expect['repository']}`: it has moved or been renamed, "
                            "and a redirect is not followed. Name the repository in the definition as it is called now")
        elif first.get("status") == 404:
            problems.append(f"the platform does not show a repository `{expect['repository']}` to this token (404): it does not exist, or "
                            "the token may not read it. Nothing was verified")
        else:
            problems.append(f"the platform could not be asked ({first.get('status')}" + (f", {first['error']}" if first.get("error") else "") + "): no "
                            "network, no access for this token, or too many requests. Nothing was verified")
        return done(NOT_CHECKED)
    repo = ans.get("repository") if isinstance(ans.get("repository"), dict) else {}
    told["repository"] = {"full_name": repo.get("full_name"), "private": repo.get("private"), "default_branch": repo.get("default_branch")}
    if str(repo.get("full_name") or "").casefold() != str(expect["repository"]).casefold():
        problems.append(f"the platform answered for the repository `{repo.get('full_name')}`, and the definition names `{expect['repository']}`")
    blocked = [a for a in not_reached if not a["endpoint"].endswith("/protection")]
    if blocked:
        problems.append("the platform did not answer every question (" + ", ".join(f"{a['status']} for {a['endpoint']}" for a in blocked[:3])
                        + "): nothing is verified on part of an answer")
        return done(NOT_CHECKED)

    # ---- the pull request the commit merged
    pulls = [p for p in ans.get("pulls_of_commit") or [] if isinstance(p, dict)]
    pull = ans.get("pull") if isinstance(ans.get("pull"), dict) else None
    told["pull_requests_of_the_commit"] = [p.get("number") for p in pulls]
    if not pulls or pull is None:
        problems.append(f"the platform knows no pull request that the commit {expect['commit'][:12]} belongs to in `{expect['repository']}`: "
                        "the commit was not brought in by a pull request there (it may be on this machine only)")
        return done(REFUTED)
    author = _login(pull.get("user"))
    base, head = pull.get("base") if isinstance(pull.get("base"), dict) else {}, pull.get("head") if isinstance(pull.get("head"), dict) else {}
    base_repo = str((base.get("repo") or {}).get("full_name") or "") if isinstance(base.get("repo"), dict) else ""
    head_repo = str((head.get("repo") or {}).get("full_name") or "") if isinstance(head.get("repo"), dict) else ""
    told["pull_request"] = {"number": pull.get("number"), "url": pull.get("html_url"), "author": author, "author_type": (pull.get("user") or {}).get("type"),
                            "merged": pull.get("merged"), "merged_at": pull.get("merged_at"), "merged_by": _login(pull.get("merged_by")),
                            "merge_commit": pull.get("merge_commit_sha"), "base": {"branch": base.get("ref"), "repository": base_repo},
                            "head": {"commit": head.get("sha"), "repository": head_repo}}
    if pull.get("merged") is not True or not pull.get("merged_at"):
        problems.append(f"the platform says pull request {pull.get('number')} was not merged")
    if pull.get("merge_commit_sha") != expect["commit"]:
        problems.append(f"the commit the act cites ({expect['commit'][:12]}) is not the merge of pull request {pull.get('number')}: the platform says "
                        f"that pull request was merged as {str(pull.get('merge_commit_sha'))[:12]}. A commit that merely belongs to a pull request is not its merge")
    if base_repo.casefold() != str(expect["repository"]).casefold():
        problems.append(f"pull request {pull.get('number')} is a pull request of another repository (`{base_repo}`), not of `{expect['repository']}`")
    if base.get("ref") != expect["branch"]:
        problems.append(f"pull request {pull.get('number')} was merged into `{base.get('ref')}`, and the definition names `{expect['branch']}` as the protected branch")
    if not author:
        problems.append("the platform's record of the pull request names no author, so nobody can be told apart from the author")

    # ---- the commit, as the platform holds it, and where it is now
    commit = ans.get("commit") if isinstance(ans.get("commit"), dict) else {}
    parents = [str(p.get("sha")) for p in commit.get("parents") or [] if isinstance(p, dict)]
    told["commit"] = {"sha": commit.get("sha"), "parents": parents}
    if commit.get("sha") != expect["commit"]:
        problems.append(f"the platform does not hold the commit {expect['commit'][:12]} in `{expect['repository']}`")
    elif parents != list(expect.get("parents") or []):
        problems.append("the commit's parents on the platform are not its parents here")
    cmp_ = ans.get("on_branch") if isinstance(ans.get("on_branch"), dict) else {}
    told["on_the_branch_now"] = {"status": cmp_.get("status"), "behind_by": cmp_.get("behind_by")}
    if cmp_.get("status") not in ("ahead", "identical") or cmp_.get("behind_by") != 0:
        problems.append(f"the commit {expect['commit'][:12]} is not on the branch `{expect['branch']}` of the platform now (the comparison says "
                        f"`{cmp_.get('status')}`): the branch was moved away from it, or it never was there")

    # ---- who approved: the latest decisive review of each account, the author and every bot apart
    reviews = [r for r in _flat(ans.get("reviews")) if isinstance(r, dict)]
    latest = {}
    for r in sorted(reviews, key=lambda r: str(r.get("submitted_at") or "")):
        login = _login(r.get("user"))
        if login and str(r.get("state")).upper() in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[login.casefold()] = r
    want = {what: expect["request"][what]["blob"] for what in ("manifest", "evidence")}
    counted, set_aside = [], []
    for key, r in sorted(latest.items()):
        login, state = _login(r.get("user")), str(r.get("state")).upper()
        line = {"login": login, "type": (r.get("user") or {}).get("type"), "state": state, "commit": r.get("commit_id"), "submitted_at": r.get("submitted_at")}
        why = None
        if state != "APPROVED":
            why = "the latest word of this account is not an approval (" + {"DISMISSED": "its approval was dismissed", "CHANGES_REQUESTED": "it asked for changes"}[state] + ")"
        elif key == author.casefold():
            why = "this is the pull request's author: an author's own approval does not count"
        elif str(line["type"] or "").casefold() != "user" or login.casefold().endswith("[bot]"):
            why = f"this account is not a person's (the platform calls it `{line['type']}`): an act by people is approved by people"
        elif pull.get("merged_at") and str(r.get("submitted_at") or "") > str(pull.get("merged_at")):
            why = "this approval was given after the merge"
        else:
            seen = (ans.get("request_at_commit") or {}).get(str(r.get("commit_id"))) or {}
            if seen.get("manifest") != want["manifest"] or seen.get("evidence") != want["evidence"]:
                why = ("the request this account approved is not the request that was merged: at the approved commit "
                       f"({str(r.get('commit_id'))[:12]}) the manifest or the evidence summary was another, or the platform does not show it")
        if why:
            set_aside.append({**line, "not_counted_because": why})
        else:
            counted.append(line)
    told["approved_by"] = counted
    told["reviews_not_counted"] = set_aside
    need = int(expect.get("approvals") or 1)
    if len(counted) < need:
        problems.append(f"{len(counted)} approval(s) count, and the definition asks for {need}"
                        + ("".join(f"; {s['login']}: {s['not_counted_because']}" for s in set_aside[:4]) if set_aside else "; nobody approved"))

    # ---- the branch
    branch = ans.get("branch") if isinstance(ans.get("branch"), dict) else {}
    seen = rules_seen(ans)
    told["branch"] = {"name": branch.get("name"), "protected": branch.get("protected"), "rules": seen}
    if branch.get("protected") is not True:
        problems.append(f"the platform says the branch `{expect['branch']}` is not protected: anybody who may push could have put the commit there")
    if seen["pull_request_required"] is False:
        problems.append(f"the rules of `{expect['branch']}` that the platform showed do not require a pull request before merging")
    if isinstance(seen["approvals_required"], int) and seen["approvals_required"] < need:
        problems.append(f"the rules of `{expect['branch']}` ask for {seen['approvals_required']} approval(s), and the definition asks for {need}")
    if seen["checks_required"] is not None and REQUIRED_CHECK not in seen["checks_required"]:
        problems.append(f"the rules of `{expect['branch']}` that the platform showed do not make `{REQUIRED_CHECK}` a required check")
    told["not_shown"] = [x for x, v in (("whether a pull request is required", seen["pull_request_required"]),
                                         ("how many approvals the branch requires", seen["approvals_required"]),
                                         ("which checks the branch requires", seen["checks_required"]),
                                         ("whether administrators are held to the rules", seen["administrators_included"])) if v is None]
    return done(REFUTED if problems else VERIFIED)


def verify(call, api: str, token: str, expect: dict) -> dict:
    """Ask, then judge: {"result", "problems", "told", "asked", "answers_sha256"}. The last is the checksum of every
    answer in full, so that two verifications can be compared without keeping the answers."""
    gathered = gather(call, api, token, expect)
    out = judge(gathered, expect)
    out["asked"] = gathered["asked"]
    out["answers_sha256"] = hashlib.sha256(json.dumps(gathered["answers"], sort_keys=True, default=str).encode()).hexdigest()
    return out


PEOPLE = ("OWNER", "MEMBER", "COLLABORATOR")  # the platform's words for an account that belongs to the repository


def verify_comment(call, api: str, token: str, expect: dict) -> dict:
    """Ask the platform about one comment that carries a person's so what on a lead (explore.py verify-so-what), and
    judge it: {"result", "problems", "told", "asked", "answers_sha256"}. One question:
      GET /repos/{repository}/issues/comments/{id}    the comment: who wrote it, what it says, where it is
    `verified` means: the platform holds that comment in the repository the definition names, its author is the
    account the job recorded, the platform calls that account a user (not a bot) that belongs to the repository,
    and the comment says now, byte for byte, what it said when it was recorded. It does not mean that the account is
    the right person to judge the lead: whoever reads the name judges that."""
    path = f"/repos/{expect['repository']}/issues/comments/{int(expect['id'])}"
    got = call(api, path, token)
    status, body = got.get("status"), got.get("body")
    out = {"result": NOT_CHECKED, "problems": [], "told": {}, "asked": [{"endpoint": path, "status": status}],
           "answers_sha256": hashlib.sha256(json.dumps(got, sort_keys=True, default=str).encode()).hexdigest()}
    if status in NOT_REACHED:
        out["problems"].append(f"the platform did not answer, or this token may not ask it (status {status}): nothing is verified")
        return out
    if status != 200 or not isinstance(body, dict):
        out.update(result=REFUTED, problems=[f"the platform holds no such comment in {expect['repository']} (status {status})"])
        return out
    user = body.get("user") if isinstance(body.get("user"), dict) else {}
    text = str(body.get("body") or "")
    out["told"] = {"author": _login(user), "author_type": user.get("type"), "association": body.get("author_association"),
                   "created_at": body.get("created_at"), "updated_at": body.get("updated_at"), "url": body.get("html_url")}
    p = out["problems"]
    if _login(user).casefold() != str(expect.get("author") or "").casefold():
        p.append(f"the platform says the comment was written by {_login(user) or 'nobody it names'}, not {expect.get('author')}")
    if user.get("type") != "User" or _login(user).endswith("[bot]"):
        p.append("the platform does not call the comment's author a user: an app or a bot gives no person's so what")
    if str(body.get("author_association") or "") not in PEOPLE:
        p.append(f"the comment's author does not belong to the repository (the platform says `{body.get('author_association')}`)")
    if hashlib.sha256(text.encode()).hexdigest() != expect.get("body_sha256"):
        p.append("the comment says something else now than when it was recorded: it was edited, and the answer recorded is not the one it holds")
    if not str(body.get("html_url") or "").startswith(f"https://github.com/{expect['repository']}/issues/"):
        p.append("the comment's address is not an issue of the repository the definition names")
    out["result"] = REFUTED if p else VERIFIED
    return out


# ---- recorded answers, for the self-tests of this file and of the study tool ----------------
def _filled(obj, fill: dict):
    text = json.dumps(obj)
    for k, v in fill.items():
        text = text.replace(k, str(v))
    return json.loads(text)


def _merged(base, change):
    """`change` laid over `base`: a mapping is merged key by key, anything else replaces."""
    if isinstance(base, dict) and isinstance(change, dict):
        out = dict(base)
        for k, v in change.items():
            out[k] = _merged(base.get(k), v)
        return out
    return copy.deepcopy(change)


def hostile_cases() -> list:
    return json.loads((HERE / "fixtures" / "verify.hostile.json").read_text())["cases"]


def recorded(fill: dict, case: str | None = None, number: int = 7, change: dict | None = None):
    """A stand-in for `platform_call` that answers from the recorded answers in fixtures/, with the placeholders
    (REPOSITORY, BRANCH, MERGE_SHA, FIRST_PARENT, SECOND_PARENT, HEAD_SHA, MANIFEST_PATH, EVIDENCE_PATH,
    MANIFEST_BLOB, EVIDENCE_BLOB) filled in, and, when a hostile case is named, with that case's changes laid over
    them, then `change` in the same form. `number` is the pull request's number, for a test with two of them. A
    question the fixtures do not hold is answered 404, as the platform would."""
    answers = json.loads((HERE / "fixtures" / "verify.answers.json").read_text())["answers"]
    for more in ([next(c for c in hostile_cases() if c["name"] == case)["change"]] if case is not None else []) + ([change] if change else []):
        for path, new in more.items():
            answers[path] = _merged(answers.get(path), new)
    answers = _filled(answers, fill)
    if number != 7:
        answers = json.loads(json.dumps(answers).replace("/pulls/7", f"/pulls/{number}").replace("/pull/7", f"/pull/{number}")
                             .replace('"number": 7', f'"number": {number}'))

    def call(api: str, path: str, token: str) -> dict:
        got = answers.get(path)
        return copy.deepcopy(got) if isinstance(got, dict) else {"status": 404, "body": {"message": "Not Found"}}
    return call


FILL = {"REPOSITORY": "example-org/example-studies", "BRANCH": "main", "MERGE_SHA": "a" * 40, "FIRST_PARENT": "b" * 40,
        "SECOND_PARENT": "c" * 40, "HEAD_SHA": "c" * 40, "OLDER_SHA": "d" * 40, "MANIFEST_PATH": "studies/S1/lock-request/manifest.json",
        "EVIDENCE_PATH": "studies/S1/lock-request/EVIDENCE.md", "MANIFEST_BLOB": "1" * 40, "EVIDENCE_BLOB": "2" * 40}
EXPECT = {"repository": FILL["REPOSITORY"], "branch": "main", "commit": FILL["MERGE_SHA"], "approvals": 1,
          "parents": [FILL["FIRST_PARENT"], FILL["SECOND_PARENT"]],
          "request": {"manifest": {"path": FILL["MANIFEST_PATH"], "blob": FILL["MANIFEST_BLOB"]},
                      "evidence": {"path": FILL["EVIDENCE_PATH"], "blob": FILL["EVIDENCE_BLOB"]}}}


def selftest() -> int:
    import http.server
    import threading
    results = []

    def ok(name: str, passed: bool) -> None:
        results.append((name, bool(passed)))
    good = verify(recorded(FILL), API, "a-token", EXPECT)
    ok("on the recorded answers of an approved, merged pull request on a protected branch the act is verified, and the answer names the "
       "pull request, its author, who merged it and who approved, with the commit they approved",
       good["result"] == VERIFIED and not good["problems"] and good["told"]["pull_request"]["number"] == 7
       and good["told"]["pull_request"]["author"] == "example-author" and good["told"]["pull_request"]["merged_by"] == "example-steward"
       and [a["login"] for a in good["told"]["approved_by"]] == ["example-scientist"] and good["told"]["approved_by"][0]["commit"] == FILL["HEAD_SHA"])
    ok("every endpoint that was asked is in the answer, in order, with its status, and the first is the repository",
       good["asked"][0] == {"endpoint": f"{API}/repos/example-org/example-studies", "status": 200} and len(good["asked"]) >= 10
       and all(a["endpoint"].startswith(API + "/repos/example-org/example-studies") for a in good["asked"]))
    ok("the rules the platform showed are read from its branch protection: a pull request required, one approval, stale approvals "
       "dismissed, the request check required, administrators included",
       good["told"]["branch"]["protected"] is True and good["told"]["branch"]["rules"]["approvals_required"] == 1
       and good["told"]["branch"]["rules"]["checks_required"] == [REQUIRED_CHECK] and good["told"]["branch"]["rules"]["administrators_included"] is True
       and good["told"]["not_shown"] == [])
    for case in hostile_cases():
        got = verify(recorded(FILL, case["name"]), API, "a-token", EXPECT)
        ok(f"hostile: {case['name']}: {case['expect']}, and it says why",
           got["result"] == case["expect"] and case["says"] in " | ".join(got["problems"]) and got["result"] != VERIFIED)
    two = verify(recorded(FILL), API, "a-token", {**EXPECT, "approvals": 2})
    ok("one approval where the definition asks for two is not verified", two["result"] == REFUTED and "the definition asks for 2" in two["problems"][0])
    moved = verify(recorded(FILL), API, "a-token", {**EXPECT, "request": {**EXPECT["request"], "manifest": {**EXPECT["request"]["manifest"], "blob": "9" * 40}}})
    ok("a merge whose manifest is not the one the approver saw is not verified: the approval covers the request as it stood",
       moved["result"] == REFUTED and "is not the request that was merged" in " ".join(moved["problems"]))
    local = verify(recorded(FILL), API, "a-token", {**EXPECT, "parents": [FILL["FIRST_PARENT"]]})
    ok("a commit whose parents here are not its parents on the platform is not verified", local["result"] == REFUTED and "parents" in " ".join(local["problems"]))
    silent = verify(lambda api, path, token: {"status": 0, "error": "no route"}, API, "a-token", EXPECT)
    ok("with no network the result is `not checked`, never a pass, and only the first question was asked",
       silent["result"] == NOT_CHECKED and len(silent["asked"]) == 1 and "could not be asked" in silent["problems"][0])
    denied = verify(lambda api, path, token: {"status": 401, "body": {"message": "Bad credentials"}}, API, "a-token", EXPECT)
    ok("a token the platform does not accept gives `not checked`", denied["result"] == NOT_CHECKED)
    part = recorded(FILL)
    halfway = verify(lambda api, path, token: {"status": 403, "body": None} if path.endswith("/reviews?per_page=100&page=1") else part(api, path, token),
                     API, "a-token", EXPECT)
    ok("an answer that stops half way (the reviews refused to this token) gives `not checked`: nothing is verified on part of an answer",
       halfway["result"] == NOT_CHECKED and "did not answer every question" in " ".join(halfway["problems"]))
    ok("a token is taken from the environment by name, the first of the names that is set, and the name is what is kept",
       token_from({"GITHUB_TOKEN": "x", "GH_TOKEN": " y "}) == ("GH_TOKEN", "y") and token_from({}) == (None, None)
       and through({"HTTPS_PROXY": "http://proxy.invalid", "PATH": "/bin"}) == ["HTTPS_PROXY"])
    ok("the call itself refuses any address that is not https, without sending anything",
       platform_call("http://api.github.com", "/repos/a/b", "a-token") == {"status": 0, "error": "the platform is asked over https and nothing else"})

    # the one function, against a server on this machine's own loopback address: no request leaves the machine
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen.append((self.path, self.headers.get("Authorization"), self.headers.get("Accept")))
            if self.path == "/moved":
                self.send_response(301)
                self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/repos/a/b")
                self.end_headers()
                return
            code, body = (200, b'{"full_name": "a/b"}') if self.path == "/repos/a/b" else (200, b"not json") if self.path == "/broken" else (404, b'{"message": "Not Found"}')
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        here = f"http://127.0.0.1:{server.server_port}"
        direct = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
        got = platform_call(here, "/repos/a/b", "a-token", opener=direct)
        ok("the call sends one GET with the token as a bearer and reads the answer as JSON (against a server on the loopback address)",
           got == {"status": 200, "body": {"full_name": "a/b"}} and seen[-1] == ("/repos/a/b", "Bearer a-token", "application/vnd.github+json"))
        ok("an answer of 404 comes back as 404 with its body, and an answer that is not JSON as no answer",
           platform_call(here, "/nowhere", "a-token", opener=direct) == {"status": 404, "body": {"message": "Not Found"}}
           and platform_call(here, "/broken", "a-token", opener=direct)["status"] == 0)
        before = len(seen)
        ok("a redirect is not followed, so the token is not carried to where it points",
           platform_call(here, "/moved", "a-token", opener=direct)["status"] == 301 and len(seen) == before + 1)
    finally:
        server.shutdown()
        server.server_close()
    second = verify(recorded(FILL, number=8), API, "a-token", EXPECT)
    ok("the recorded answers can stand for another pull request, by its number", second["result"] == VERIFIED and second["told"]["pull_request"]["number"] == 8
       and any(a["endpoint"].endswith("/pulls/8") for a in second["asked"]))
    squash = verify(recorded(FILL, change={"/repos/REPOSITORY/commits/MERGE_SHA": {"body": {"parents": [{"sha": "FIRST_PARENT"}]}}}), API, "a-token",
                    {**EXPECT, "parents": [FILL["FIRST_PARENT"]]})
    ok("a squash merge, one commit with one parent, is verified when the platform says that commit is the pull request's merge and the "
       "request the approver saw is the request in it: the platform carries what git cannot",
       squash["result"] == VERIFIED and squash["told"]["commit"]["parents"] == [FILL["FIRST_PARENT"]])
    renamed = verify(lambda api, path, token: {"status": 301, "body": None}, API, "a-token", EXPECT)
    ok("a repository that answers with a redirect is `not checked`, and the answer says to name it as it is called now",
       renamed["result"] == NOT_CHECKED and "has moved or been renamed" in renamed["problems"][0])
    comment = {"id": 41, "html_url": "https://github.com/example-org/example-studies/issues/3#issuecomment-41",
               "user": {"login": "a-scientist", "type": "User"}, "author_association": "MEMBER", "created_at": "2026-11-26T10:00:00Z",
               "body": "so-what: worth-confirming\nexploration: EXPLORATION-1\nlead: 0123456789ab\n"}
    ask = {"repository": FILL["REPOSITORY"], "id": 41, "author": "a-scientist", "body_sha256": hashlib.sha256(comment["body"].encode()).hexdigest()}

    def answering(body, status=200):
        return lambda api, path, token: ({"status": status, "body": body} if path == "/repos/example-org/example-studies/issues/comments/41"
                                         else {"status": 404, "body": {"message": "Not Found"}})
    fine = verify_comment(answering(comment), API, "a-token", ask)
    ok("a so what given as a comment is verified when the platform holds the comment in the named repository, by the recorded user, "
       "unedited", fine["result"] == VERIFIED and fine["told"]["association"] == "MEMBER" and fine["asked"][0]["endpoint"].endswith("/comments/41"))
    ok("a so what whose comment was edited after it was recorded is refuted",
       verify_comment(answering({**comment, "body": comment["body"].replace("worth-confirming", "not-interesting")}), API, "a-token", ask)["result"] == REFUTED)
    ok("a so what whose comment a bot wrote is refuted",
       "not call the comment's author a user" in " ".join(verify_comment(answering({**comment, "user": {"login": "helper[bot]", "type": "Bot"}}), API, "a-token",
                                                                     {**ask, "author": "helper[bot]"})["problems"]))
    ok("a so what by an account that does not belong to the repository is refuted",
       verify_comment(answering({**comment, "author_association": "NONE"}), API, "a-token", ask)["result"] == REFUTED)
    ok("a so what whose comment the platform does not hold is refuted, and one it does not answer for is `not checked`",
       verify_comment(answering(None, 404), API, "a-token", ask)["result"] == REFUTED
       and verify_comment(answering(None, 0), API, "a-token", ask)["result"] == NOT_CHECKED)
    for name, passed in results:
        print(("ok    " if passed else "FAIL  ") + name)
    good_n = sum(1 for _n, p in results if p)
    print(f"verify_acts selftest: {'PASS' if good_n == len(results) else 'FAIL'} ({good_n} of {len(results)}). Recorded answers only: "
          "this program has never been run against GitHub")
    return 0 if good_n == len(results) else 1


def ask(question: dict) -> dict:
    """What the study tool runs in a process of its own (`verify_acts.py --ask`, the question on standard input), so that
    nothing in the study tool's process can stand in for the call: {"what": "act" or "comment", "expect": as `verify` or
    `verify_comment` takes it, "proxy": the definition's proxy or null}. The token is read from this process's
    environment, which the study tool builds to hold the token and nothing else. Returns the verification with `via`:
    the host asked, the proxy used if any, and the certificates trusted."""
    opener, via = opener_for(question.get("proxy"))
    name, token = token_from(os.environ)
    if not token:
        return {"result": NOT_CHECKED, "problems": ["no token in the environment of the program that asks: nothing was asked"], "told": {},
                "asked": [], "answers_sha256": None, "via": via, "token_from": None}

    def call(api: str, path: str, tok: str) -> dict:
        return platform_call(API, path, tok, opener=opener)
    fn = verify if question.get("what") == "act" else verify_comment
    got = fn(call, API, token, question["expect"])
    got.update(via=via, token_from=name)
    return got


def main() -> int:
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    if sys.argv[1:] == ["--ask"]:
        try:
            question = json.loads(sys.stdin.read())
            print(json.dumps(ask(question), sort_keys=True, default=str))
        except (ValueError, KeyError, TypeError) as e:
            print(json.dumps({"result": NOT_CHECKED, "problems": [f"the question could not be read ({type(e).__name__})"], "told": {}, "asked": []}))
        return 0
    print(__doc__)
    print("This file is called by the study tool: `uv run tools/sf.py verify-acts --study studies/<study> --by <name>`.")
    return 0 if sys.argv[1:] in ([], ["--help"], ["-h"]) else 2


if __name__ == "__main__":
    sys.exit(main())
