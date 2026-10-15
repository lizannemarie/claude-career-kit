#!/usr/bin/env python3
"""Split-decision eval: should a career-kit flow run inline or fan out to subagents?

For each flow and workload size N it runs the same job three ways through headless Claude Code
(`claude -p --output-format json`), then compares dollar cost, tokens, latency and quality:

  inline            one session does everything
  split-scoped      parent + subagents defined with a minimal `tools:` list (what career-kit ships)
  split-unscoped    parent + subagents that inherit every tool (the 54k-overhead case)

Flows (synthetic fixtures from tests/fixtures/, scaled to N by cloning with new IDs):
  email      classify N Gmail-like threads; quality = label accuracy vs ground truth
  jobboard   filter + first pass + skeptical second pass on N postings; quality = keep/screen/exclude
             agreement with ground truth and mean |final score - inline score|

Output: evals/split-decision/results/<timestamp>/{runs.jsonl, report.md}. report.md gives the
break-even N per flow: the smallest N at which split-scoped costs no more than inline while
quality stays within tolerance. Copy those numbers into career-kit.config.json -> split_thresholds.

Usage:
  python3 evals/split-decision/run_eval.py --flows email jobboard --sizes 5 10 20 40
  python3 evals/split-decision/run_eval.py --dry-run          # print commands, spend nothing
  python3 evals/split-decision/run_eval.py --with-mcp         # keep your connectors loaded (realistic overhead)
  python3 evals/split-decision/run_eval.py --max-budget-usd 3 # cap each run

Requires a logged-in `claude` CLI. Each run spends real usage; the default sweep is ~18 runs.
"""
import argparse
import copy
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIX = os.path.join(ROOT, "tests", "fixtures")
HERE = os.path.dirname(os.path.abspath(__file__))

POSTING_TRUTH = {"P1": "candidate", "P2": "screened", "P3": "candidate",
                 "P4": "screened", "P5": "screened", "P6": "excluded"}

# Subagent definitions passed with --agents. "tools" is the whole point of the scoped variant.
AGENTS = {
    "email": {
        "classifier": {
            "description": "Classifies a batch of job-application email threads into the Email Context enum.",
            "model": "haiku",
            "tools": ["Read"],
            "prompt": open(os.path.join(ROOT, "agents", "email-classifier.md")).read().split("---", 2)[2],
        }
    },
    "jobboard": {
        "scout": {
            "description": "First-pass scout for a batch of postings; returns compact JSON.",
            "model": "haiku",
            "tools": ["Read", "Grep"],
            "prompt": open(os.path.join(ROOT, "agents", "posting-scout.md")).read().split("---", 2)[2],
        },
        "verifier": {
            "description": "Skeptical second-pass scorer for one posting; returns compact JSON.",
            "model": "sonnet",
            "tools": ["Read", "Grep"],
            "prompt": open(os.path.join(ROOT, "agents", "posting-verifier.md")).read().split("---", 2)[2],
        },
    },
}

ENUM = ("Application Received, Automated/ Survey, Recruiter Contact, Formal Interview, Offer Sent, "
        "Offer Accept, Offer Reject, Not Job App Related, Application Rejected, Interview Rejected")


# ---------------------------------------------------------------- workloads
def build_email(n, work):
    src = json.load(open(os.path.join(FIX, "emails.fixture.json")))
    threads, expected = [], {}
    for i in range(n):
        t = copy.deepcopy(src["threads"][i % len(src["threads"])])
        base = t["threadId"]
        t["threadId"] = "%s-%03d" % (base, i)
        threads.append(t)
        expected[t["threadId"]] = src["expected"][base]["emailContext"]
    p = os.path.join(work, "emails.json")
    json.dump({"threads": threads}, open(p, "w"), indent=1)
    return {"input": p, "expected": expected}


def build_jobboard(n, work):
    text = open(os.path.join(FIX, "postings.fixture.md")).read()
    header, *blocks = text.split("\n=====\n")
    out, truth = [header.strip()], {}
    for i in range(n):
        b = blocks[i % len(blocks)]
        pid = re.search(r"ID: (P\d)", b).group(1)
        new = "%s-%03d" % (pid, i)
        b = b.replace("ID: %s" % pid, "ID: %s" % new)
        b = re.sub(r"(Company: .+)", r"\1 %03d" % i, b, count=1)
        b = re.sub(r"(/jobs/\d+)", r"\1%03d" % i, b, count=1)
        out.append(b.strip())
        truth[new] = POSTING_TRUTH[pid]
    p = os.path.join(work, "postings.md")
    open(p, "w").write("\n\n=====\n".join(out) + "\n")
    shutil.copy(os.path.join(FIX, "Experience-Context.fixture.md"), os.path.join(work, "Experience-Context.md"))
    return {"input": p, "expected": truth, "context": os.path.join(work, "Experience-Context.md")}


# ---------------------------------------------------------------- prompts
def prompt(flow, variant, w, batch):
    if flow == "email":
        ask = ("For each thread in %s classify the newest message into exactly one of: %s. "
               "Output ONLY a JSON array of {\"threadId\",\"emailContext\"} for every thread, nothing else."
               % (w["input"], ENUM))
        if variant == "inline":
            return "Do this yourself without subagents. " + ask
        return ("Split the threads in %s into batches of %d. For each batch spawn the `classifier` subagent "
                "(all batches in parallel), giving it only the file path and its threadIds, and telling it to "
                "return the JSON array (skip the cache-file step: no cache path is provided). Then merge. %s"
                % (w["input"], batch, ask))
    ask = ("Postings: %s (criteria at the top). Candidate facts: %s (never credit 'Honest Boundaries and Gaps'). "
           "Apply the filters, first-pass score, and the skeptical second pass for first-pass >= 70. "
           "Output ONLY a JSON array of {\"id\",\"status\":\"candidate|screened|excluded\",\"score\":int|null} "
           "for every posting, where score is the final score. Status definitions: excluded = an excluded "
           "category (no score needed); screened = opened and ruled out by location, pay below the floor, or a "
           "final score below the minimum; candidate = passes every filter with a final score at or above the "
           "minimum (after the second pass when one applies)." % (w["input"], w["context"]))
    if variant == "inline":
        return "Do this yourself without subagents. " + ask
    return ("Split the postings into batches of %d and spawn the `scout` subagent per batch, in parallel, giving each "
            "only the file paths and its posting IDs (no dedup files exist; skip that step). Then spawn one "
            "`verifier` subagent per posting with first-pass >= 70, in parallel. Merge the results. %s" % (batch, ask))


# ---------------------------------------------------------------- run + score
def run_claude(p, flow, variant, work, a):
    cmd = ["claude", "-p", p, "--output-format", "json", "--no-session-persistence",
           "--permission-mode", "bypassPermissions", "--add-dir", work]
    if a.model:
        cmd += ["--model", a.model]
    if not a.with_mcp:
        cmd += ["--strict-mcp-config"]
    if a.max_budget_usd:
        cmd += ["--max-budget-usd", str(a.max_budget_usd)]
    if variant == "inline":
        cmd += ["--tools", "Read,Grep"]
    else:
        agents = copy.deepcopy(AGENTS[flow])
        if variant == "split-unscoped":
            for d in agents.values():
                d.pop("tools", None)
        cmd += ["--agents", json.dumps(agents)]
        if variant == "split-scoped":
            cmd += ["--tools", "Read,Grep,Agent"]
    if a.dry_run:
        return {"cmd": cmd[:3] + ["<prompt>"] + cmd[3:], "dry_run": True}
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=work, timeout=a.timeout)
    wall = time.time() - t0
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": (r.stderr or r.stdout)[:500], "wall_s": wall}
    if d.get("is_error"):
        return {"error": d.get("result", "")[:500], "wall_s": wall}
    u = d.get("usage", {})
    return {"cost_usd": d.get("total_cost_usd"), "wall_s": round(wall, 1),
            "input": u.get("input_tokens"), "cache_read": u.get("cache_read_input_tokens"),
            "cache_create": u.get("cache_creation_input_tokens"), "output": u.get("output_tokens"),
            "models": d.get("modelUsage"), "subagents": (d.get("subagent_stats") or {}).get("completed"),
            "result": d.get("result", "")}


def parse_array(text):
    m = re.search(r"\[.*\]", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        return []


def score(flow, w, res, baseline):
    rows = parse_array(res.get("result"))
    if flow == "email":
        got = {r.get("threadId"): r.get("emailContext") for r in rows}
        ok = sum(got.get(k) == v for k, v in w["expected"].items())
        return {"accuracy": round(ok / len(w["expected"]), 3), "returned": len(got)}
    got = {r.get("id"): r for r in rows}
    ok = sum((got.get(k) or {}).get("status") == v for k, v in w["expected"].items())
    q = {"status_accuracy": round(ok / len(w["expected"]), 3), "returned": len(got)}
    if baseline:
        diffs = [abs(got[k]["score"] - baseline[k]["score"]) for k in got
                 if k in baseline and isinstance(got[k].get("score"), (int, float))
                 and isinstance(baseline[k].get("score"), (int, float))]
        q["mean_abs_score_diff_vs_inline"] = round(sum(diffs) / len(diffs), 1) if diffs else None
    return q


def report(rows, out, tol):
    lines = ["# Split-decision eval", "", "Generated %s. Cost is `total_cost_usd` from headless Claude Code "
             "(includes subagents). Quality tolerance: %.0f%% of inline accuracy." % (dt.datetime.now().isoformat(timespec="minutes"), tol * 100), ""]
    rec = {}
    for flow in sorted({r["flow"] for r in rows}):
        lines += ["## %s" % flow, "", "| N | variant | cost $ | wall s | input | cache read | output | quality |",
                  "|---|---|---|---|---|---|---|---|"]
        fr = [r for r in rows if r["flow"] == flow and "cost_usd" in r]
        for r in sorted(fr, key=lambda r: (r["n"], r["variant"])):
            lines.append("| %d | %s | %.4f | %s | %s | %s | %s | %s |" % (
                r["n"], r["variant"], r["cost_usd"] or 0, r["wall_s"], r["input"], r["cache_read"], r["output"],
                json.dumps(r["quality"])))
        be = None
        for n in sorted({r["n"] for r in fr}):
            inl = next((r for r in fr if r["n"] == n and r["variant"] == "inline"), None)
            spl = next((r for r in fr if r["n"] == n and r["variant"] == "split-scoped"), None)
            if not inl or not spl:
                continue
            qk = "accuracy" if flow == "email" else "status_accuracy"
            if spl["cost_usd"] <= inl["cost_usd"] and spl["quality"][qk] >= inl["quality"][qk] * tol:
                be = n
                break
        rec[flow] = be
        lines += ["", "**Break-even N (split-scoped <= inline cost, quality within tolerance): %s**" %
                  (be if be is not None else "not reached in this sweep; keep inline below the largest N tested"), ""]
    lines += ["## Recommended config", "", "```json", json.dumps({"split_thresholds": {
        "email_min_threads": rec.get("email"), "jobboard_min_postings": rec.get("jobboard")}}, indent=2), "```", ""]
    open(os.path.join(out, "report.md"), "w").write("\n".join(lines))
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--flows", nargs="+", default=["email", "jobboard"], choices=["email", "jobboard"])
    ap.add_argument("--sizes", nargs="+", type=int, default=[5, 10, 20])
    ap.add_argument("--variants", nargs="+", default=["inline", "split-scoped", "split-unscoped"])
    ap.add_argument("--batch", type=int, default=10, help="items per subagent")
    ap.add_argument("--model", help="parent/inline model (default: your CLI default)")
    ap.add_argument("--with-mcp", action="store_true", help="keep your MCP connectors loaded")
    ap.add_argument("--max-budget-usd", type=float)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--tolerance", type=float, default=0.95)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", help="results folder to append to (lets you run one size/variant at a time)")
    ap.add_argument("--report-only", action="store_true", help="rebuild report.md from --out/runs.jsonl")
    a = ap.parse_args()
    if not a.dry_run and not shutil.which("claude"):
        sys.exit("claude CLI not found on PATH")

    out = a.out or os.path.join(HERE, "results", dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out, exist_ok=True)
    runs_path = os.path.join(out, "runs.jsonl")
    prior = [json.loads(l) for l in open(runs_path)] if os.path.exists(runs_path) else []
    if a.report_only:
        print(json.dumps(report(prior, out, a.tolerance)))
        return
    rows = list(prior)
    for flow in a.flows:
        for n in a.sizes:
            work = tempfile.mkdtemp(prefix="ck-eval-")
            w = (build_email if flow == "email" else build_jobboard)(n, work)
            baseline = next(({r.get("id"): r for r in p["parsed"]} for p in prior
                             if p["flow"] == flow and p["n"] == n and p["variant"] == "inline" and p.get("parsed")),
                            None)
            for variant in a.variants:
                res = run_claude(prompt(flow, variant, w, a.batch), flow, variant, work, a)
                row = {"flow": flow, "n": n, "variant": variant, **{k: v for k, v in res.items() if k != "result"}}
                if "cost_usd" in res:
                    row["parsed"] = parse_array(res["result"])
                    row["quality"] = score(flow, w, res, baseline)
                    if variant == "inline" and flow == "jobboard":
                        baseline = {r.get("id"): r for r in parse_array(res["result"])}
                rows.append(row)
                print(json.dumps({k: v for k, v in row.items() if k not in ("parsed", "models")}), flush=True)
                with open(os.path.join(out, "runs.jsonl"), "a") as f:
                    f.write(json.dumps(row) + "\n")
            shutil.rmtree(work, ignore_errors=True)
    if not a.dry_run:
        print(json.dumps(report(rows, out, a.tolerance)))
        print("report:", os.path.join(out, "report.md"))


if __name__ == "__main__":
    main()
