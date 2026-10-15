#!/usr/bin/env python3
"""Prefetch and filter the every-run company JSON feeds (job-board check, source C).

No model reads raw feeds: this script fetches each Greenhouse / Lever / Ashby feed listed under
"## Every-run companies" in company-notes.md, applies the deterministic filters, dedups against the
logs, and prints compact JSON. Standard library only.

Filters, in order (from career-kit.config.json -> search):
  1. title: contains one of role_targets as a phrase (case-insensitive, punctuation ignored)
  2. excluded_categories: phrase in the title, department or team -> dropped
  3. location: remote in remote_country (when remote_ok), or home_metro / metro_aliases in any
     listed location
  4. date: posted on or after the cutoff (postings with no date are kept)
  5. dedup: URL, job id (whole word) or title+company already in job-search-log.md or
     screened-postings.md

Usage:
  python3 scripts/fetch-feeds.py --config <workspace>/career-kit.config.json [--cutoff YYYY-MM-DD]
  python3 scripts/fetch-feeds.py --offline --check      # synthetic fixture, compare to expected

Without --cutoff the cutoff is the latest date in the last 40 lines of job-search-log.md and
job-search-runs.md, else today minus search.cutoff_days_default (same rule as the task).

Output: {"cutoff", "offline", "counts", "candidates": [{title, company, location, url, jobId, ats,
posted, pay?, description}], "feeds": [...], "noFeed": [companies], "errors": [...]}
Exit 0 when at least one feed was read (or none are listed), 1 when every feed failed, 2 on a
setup error (config or company-notes unreadable). The task falls back to the inline path on 1 or 2.
"""
import argparse
import concurrent.futures
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "feeds")
DATE_RX = re.compile(r"(?<!\d)(20\d\d-\d\d-\d\d)(?!\d)")
PAY_RX = re.compile(r"\$\s?\d[\d,.]*\s?[kK]?(?:\s?(?:USD|CAD))?\s?(?:-|–|—|to)\s?\$\s?\d[\d,.]*\s?[kK]?")
URL_RX = re.compile(r"https?://[^\s)>\]`\"']+")
COUNTRY_ALIASES = {
    "US": ["us", "usa", "u s", "u s a", "united states", "united states of america", "america"],
    "CA": ["ca", "canada"],
    "GB": ["uk", "gb", "united kingdom", "great britain", "england", "london"],
}
# Places that mean "not the remote country" when a remote posting names them and not ours.
FOREIGN = ["canada", "uk", "united kingdom", "england", "ireland", "germany", "france", "spain",
           "netherlands", "poland", "portugal", "india", "mexico", "brazil", "argentina", "colombia",
           "australia", "new zealand", "singapore", "japan", "philippines", "emea", "europe", "apac",
           "latam", "asia", "united states", "usa", "us"]


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def has_phrase(text, phrase):
    p = norm(phrase)
    return bool(p) and (" %s " % p) in (" %s " % norm(text))


class _Text(HTMLParser):
    BLOCK = {"p", "br", "li", "ul", "ol", "div", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCK:
            self.out.append(" ")

    def handle_endtag(self, tag):
        self.handle_starttag(tag, None)

    def handle_data(self, data):
        self.out.append(data)


def plain(s):
    if not s:
        return ""
    s = html.unescape(s) if "&lt;" in s else s  # Greenhouse escapes its HTML once
    p = _Text()
    p.feed(s)
    return " ".join("".join(p.out).split())


def excerpt(s, n):
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut + "…"


def to_date(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):  # Lever: epoch milliseconds
        return dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).date()
    m = DATE_RX.search(str(v))
    return dt.date.fromisoformat(m.group(1)) if m else None


def money(lo, hi, cur, unit=""):
    def f(x):
        return "{:,.0f}".format(x)
    if lo is None and hi is None:
        return None
    sym = "$" if (cur or "USD").upper() == "USD" else (cur.upper() + " ")
    rng = sym + f(lo) if hi in (None, lo) else "%s%s - %s%s" % (sym, f(lo), sym, f(hi))
    return rng + (" " + unit if unit else "")


# ---- feed adapters: return a list of normalized jobs ----------------------------------------

def from_greenhouse(data):
    jobs = []
    for j in data.get("jobs", []):
        pay = None
        for r in j.get("pay_input_ranges") or []:
            pay = money(r.get("min_cents", 0) / 100, r.get("max_cents", 0) / 100, r.get("currency_type"))
            break
        jobs.append({
            "jobId": str(j.get("id", "")), "title": j.get("title", ""),
            "url": j.get("absolute_url", ""),
            "locations": [(j.get("location") or {}).get("name", "")] + [o.get("name", "") for o in j.get("offices") or []],
            "remote": None, "country": None, "workplace": None,
            "teams": [d.get("name", "") for d in j.get("departments") or []],
            "posted": to_date(j.get("first_published") or j.get("updated_at")),
            "pay": pay, "text": plain(j.get("content", "")),
        })
    return jobs


def from_lever(data):
    jobs = []
    for j in data if isinstance(data, list) else []:
        c = j.get("categories") or {}
        sr = j.get("salaryRange") or {}
        unit = {"per-year-salary": "/yr", "per-hour-wage": "/hr"}.get(sr.get("interval"), "")
        lists = " ".join("%s %s" % (l.get("text", ""), plain(l.get("content", ""))) for l in j.get("lists") or [])
        text = j.get("descriptionPlain") or plain(j.get("description", ""))
        jobs.append({
            "jobId": j.get("id", ""), "title": j.get("text", ""), "url": j.get("hostedUrl", ""),
            "locations": [c.get("location", "")] + list(c.get("allLocations") or []),
            "remote": (j.get("workplaceType") == "remote") if j.get("workplaceType") not in (None, "unspecified") else None,
            "country": j.get("country"), "workplace": j.get("workplaceType"),
            "teams": [c.get("team", ""), c.get("department", "")],
            "posted": to_date(j.get("createdAt")),
            "pay": money(sr.get("min"), sr.get("max"), sr.get("currency"), unit) if sr else None,
            "text": " ".join((text + " " + lists).split()),
        })
    return jobs


def from_ashby(data):
    jobs = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        comp = j.get("compensation") or {}
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        jobs.append({
            "jobId": j.get("id", ""), "title": j.get("title", ""), "url": j.get("jobUrl", ""),
            "locations": [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []],
            "remote": j.get("isRemote"), "country": addr.get("addressCountry"), "workplace": j.get("workplaceType"),
            "teams": [j.get("department", ""), j.get("team", "")],
            "posted": to_date(j.get("publishedAt")),
            "pay": comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary"),
            "text": j.get("descriptionPlain") or plain(j.get("descriptionHtml", "")),
        })
    return jobs


def feed_kind(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    if host == "boards-api.greenhouse.io":
        return "greenhouse"
    if host == "api.lever.co" and "/v0/postings/" in url:
        return "lever"
    if host == "api.ashbyhq.com" and "/posting-api/" in url:
        return "ashby"
    return None


def with_params(url, kind):
    """Add the query params each feed needs for full text and pay."""
    want = {"greenhouse": {"content": "true", "pay_transparency": "true"}, "lever": {"mode": "json"},
            "ashby": {"includeCompensation": "true"}}[kind]
    u = urllib.parse.urlparse(url)
    q = dict(urllib.parse.parse_qsl(u.query))
    for k, v in want.items():
        q.setdefault(k, v)
    return urllib.parse.urlunparse(u._replace(query=urllib.parse.urlencode(q)))


ADAPTERS = {"greenhouse": from_greenhouse, "lever": from_lever, "ashby": from_ashby}


# ---- inputs ---------------------------------------------------------------------------------

def every_run_feeds(notes):
    """[(company, feed_url)] and [companies with no supported feed] from '## Every-run companies'."""
    feeds, no_feed, company, found, in_section = [], [], None, False, False

    def close():
        if company and not found:
            no_feed.append(company)

    for line in notes.splitlines():
        if line.startswith("## "):
            close()
            company = None
            in_section = line[3:].strip().lower().startswith("every-run")
            continue
        if not in_section:
            continue
        if line.startswith("### "):
            close()
            company, found = line[4:].strip(), False
            continue
        if company:
            for url in URL_RX.findall(line):
                url = url.rstrip(".,;")
                if feed_kind(url):
                    feeds.append((company, url))
                    found = True
    close()
    return feeds, no_feed


def tail_dates(paths, n=40):
    best = None
    for p in paths:
        try:
            lines = open(p, encoding="utf-8").read().splitlines()[-n:]
        except OSError:
            continue
        for line in lines:
            for d in DATE_RX.findall(line):
                try:
                    d = dt.date.fromisoformat(d)
                except ValueError:
                    continue
                best = d if best is None or d > best else best
    return best


class Seen:
    """grep -F style lookups over job-search-log.md + screened-postings.md."""

    def __init__(self, texts):
        self.text = "\n".join(texts)
        self.pairs = set()
        for line in self.text.splitlines():
            cells = [c.strip() for c in line.strip().strip("-* ").split("|")]
            if len(cells) >= 4:  # date | title | company | ...
                self.pairs.add((norm(cells[1]), norm(cells[2])))

    def match(self, job, company):
        url = job["url"]
        if url and (url in self.text or url.split("?")[0].rstrip("/") in self.text):
            return "url"
        jid = job["jobId"]
        if jid and len(jid) >= 4 and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(jid), self.text):
            return "jobId"
        if (norm(job["title"]), norm(company)) in self.pairs:
            return "company+title"
        return None


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


# ---- filtering ------------------------------------------------------------------------------

def location_ok(job, s):
    locs = [l for l in job["locations"] if l]
    joined = " / ".join(locs)
    metros = [s.get("home_metro", "")] + list(s.get("metro_aliases") or [])
    metros += [m.split(",")[0] for m in metros if "," in m]
    if any(has_phrase(joined, m) for m in metros if m.strip()):
        return True
    if not s.get("remote_ok", True):
        return False
    remote = job["remote"] if job["remote"] is not None else has_phrase(joined, "remote")
    if not remote:
        return False
    rc = (s.get("remote_country") or "US").upper()
    if job["country"]:
        return job["country"].upper() in (rc, norm(rc)) or norm(job["country"]) in COUNTRY_ALIASES.get(rc, [])
    ours = COUNTRY_ALIASES.get(rc, [norm(rc)])
    if any(has_phrase(joined, a) for a in ours):
        return True
    return not any(has_phrase(joined, f) for f in FOREIGN if f not in ours)


def setup_of(job):
    """Remote / Hybrid / Onsite as far as the feed says; the scout confirms days on the page."""
    w, locs = norm(job["workplace"]), " ".join(job["locations"])
    if job["remote"] or w == "remote" or has_phrase(locs, "remote"):
        return "Remote"
    if w == "hybrid" or has_phrase(locs, "hybrid"):
        return "Hybrid"
    if w in ("on site", "onsite"):
        return "Onsite"
    return "not listed"


def filter_jobs(company, kind, jobs, s, cutoff, seen, chars, counts):
    targets = [t for t in s.get("role_targets") or [] if t.strip()]
    excluded = [e for e in s.get("excluded_categories") or [] if e.strip()]
    out = []
    for j in jobs:
        counts["fetched"] += 1
        j["locations"] = list(dict.fromkeys(l.strip() for l in j["locations"] if l and l.strip()))
        if targets and not any(has_phrase(j["title"], t) for t in targets):
            counts["title"] += 1
            continue
        if any(has_phrase(" ".join([j["title"]] + j["teams"]), e) for e in excluded):
            counts["excluded"] += 1
            continue
        if not location_ok(j, s):
            counts["location"] += 1
            continue
        if j["posted"] and j["posted"] < cutoff:
            counts["date"] += 1
            continue
        if seen.match(j, company):
            counts["dedup"] += 1
            continue
        c = {"title": j["title"], "company": company, "location": " / ".join(j["locations"]) or "not listed",
             "url": j["url"], "jobId": j["jobId"], "ats": kind,
             "posted": j["posted"].isoformat() if j["posted"] else None, "setup": setup_of(j)}
        pay = j["pay"] or (PAY_RX.search(j["text"]) or [None])[0]  # else a range stated in the text
        if pay:
            c["pay"] = " ".join(pay.split())
        c["description"] = excerpt(j["text"], chars)
        out.append(c)
    return out


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "career-kit-fetch-feeds/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", help="career-kit.config.json (default: <workspace>/career-kit.config.json)")
    ap.add_argument("--workspace", help="override paths.workspace")
    ap.add_argument("--cutoff", help="YYYY-MM-DD; default from the log tails")
    ap.add_argument("--company", action="append", help="only this every-run company (repeatable; dry run)")
    ap.add_argument("--offline", nargs="?", const=FIXTURE_DIR, metavar="DIR",
                    help="read config, logs and feed responses from a fixture dir (default tests/fixtures/feeds)")
    ap.add_argument("--check", action="store_true", help="offline only: compare with the fixture's expected block")
    ap.add_argument("--excerpt-chars", type=int, default=1500)
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--pretty", action="store_true")
    a = ap.parse_args()

    responses = expected = None
    if a.offline:
        ws = a.workspace or a.offline
        cfg_path = a.config or os.path.join(a.offline, "config.json")
        fx = json.load(open(os.path.join(a.offline, "feeds.json"), encoding="utf-8"))
        responses, expected = fx["responses"], fx.get("expected")
    else:
        cfg_path = a.config or os.path.join(os.path.expanduser(a.workspace or "~/Documents/ClaudeCareer"), "career-kit.config.json")
    try:
        cfg = json.load(open(os.path.expanduser(cfg_path), encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(json.dumps({"errors": ["config: %s" % e]}))
        return 2
    if not a.offline:
        ws = a.workspace or cfg.get("paths", {}).get("workspace") or os.path.dirname(os.path.abspath(cfg_path))
    ws = os.path.expanduser(ws)
    paths, s = cfg.get("paths", {}), cfg.get("search", {})
    p = lambda key, default: os.path.join(ws, paths.get(key, default))

    notes = read(p("company_notes", "company-notes.md"))
    if not notes:
        print(json.dumps({"errors": ["company-notes: not found in %s" % ws]}))
        return 2
    log_path, runs_path = p("job_search_log", "job-search-log.md"), p("job_search_runs", "job-search-runs.md")
    if a.cutoff:
        cutoff = dt.date.fromisoformat(a.cutoff)
    else:
        cutoff = tail_dates([log_path, runs_path]) or (dt.date.today() - dt.timedelta(days=int(s.get("cutoff_days_default", 3))))
    seen = Seen([read(log_path), read(p("screened_postings", "screened-postings.md"))])

    feeds, no_feed = every_run_feeds(notes)
    if a.company:
        wanted = {norm(c) for c in a.company}
        feeds = [f for f in feeds if norm(f[0]) in wanted]
        no_feed = [c for c in no_feed if norm(c) in wanted]

    def get(item):
        company, url = item
        kind = feed_kind(url)
        full = with_params(url, kind)
        if responses is not None and full not in responses:
            return company, kind, full, [], "no fixture response for %s" % full
        try:
            data = responses[full] if responses is not None else fetch(full, a.timeout)
            return company, kind, full, ADAPTERS[kind](data), None
        except (urllib.error.URLError, OSError, ValueError) as e:
            return company, kind, full, [], "%s: %s" % (type(e).__name__, e)
        except (KeyError, TypeError, AttributeError) as e:  # feed shape changed
            return company, kind, full, [], "unexpected feed format: %s: %s" % (type(e).__name__, e)

    counts = dict.fromkeys(["fetched", "title", "excluded", "location", "date", "dedup", "candidates"], 0)
    candidates, feed_rows, errors = [], [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(get, feeds))  # map keeps company-notes order: deterministic output
    for company, kind, url, jobs, err in results:
        kept = filter_jobs(company, kind, jobs, s, cutoff, seen, a.excerpt_chars, counts)
        candidates += kept
        feed_rows.append({"company": company, "ats": kind, "url": url, "jobs": len(jobs), "kept": len(kept),
                          "error": err})
        if err:
            errors.append("%s: %s" % (company, err))
    counts["candidates"] = len(candidates)
    out = {"cutoff": cutoff.isoformat(), "offline": bool(a.offline), "counts": counts, "candidates": candidates,
           "feeds": feed_rows, "noFeed": no_feed, "errors": errors}
    print(json.dumps(out, ensure_ascii=False, indent=1 if a.pretty else None,
                     separators=None if a.pretty else (",", ":")))

    if a.check:
        if not expected:
            print("check: no expected block in fixture", file=sys.stderr)
            return 1
        got = {"candidates": [c["jobId"] for c in candidates], "counts": counts, "noFeed": no_feed,
               "cutoff": out["cutoff"]}
        bad = [k for k in expected if expected[k] != got.get(k)]
        for k in bad:
            print("check FAIL %s: expected %s, got %s" % (k, expected[k], got.get(k)), file=sys.stderr)
        print("check: %s" % ("FAIL" if bad else "ok"), file=sys.stderr)
        return 1 if bad else 0
    return 1 if feeds and all(r["error"] for r in feed_rows) else 0


if __name__ == "__main__":
    sys.exit(main())
