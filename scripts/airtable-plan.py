#!/usr/bin/env python3
"""Deterministic helper for building the Job Application Tracker base from airtable/schema.json.

The model calls the Airtable MCP; this script does the bookkeeping so the model never
hand-derives field order or IDs.

  plan      [--timezone TZ] [--with-interview]       ordered build steps (create_base, then create_field...)
  ids       --listing L.json [--config C.json]       name->id map from a list_tables_for_base/get_table_schema dump
  resolve   --plan PLAN.json --ids IDS.json --step N [...]
                                                     steps from the SAVED plan with every {table.field}
                                                     reference resolved to IDs (never re-planned, so step
                                                     numbers can't drift from the plan that was shown)
  diff      --listing L.json [--with-interview]      compare the live base to the schema (exit 1 on mismatch)
  dashboard --ids IDS.json                           interface sections with field IDs substituted
  check                                              verify every reference in the schema resolves by name

Usage: python3 scripts/airtable-plan.py <cmd> [--schema airtable/schema.json] ...
"""
import argparse
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA = os.path.join(HERE, "..", "airtable", "schema.json")
REF = re.compile(r"^\{([^{}.]+)(?:\.([^{}]+))?\}$")


def load(path):
    with open(os.path.expanduser(path)) as f:
        return json.load(f)


def subst_tz(obj, tz):
    s = json.dumps(obj)
    if tz:
        s = s.replace("{{USER_TIMEZONE}}", tz)
    return json.loads(s)


def clean_field(f):
    """Keep only keys the Airtable API understands for a field definition."""
    return {k: v for k, v in f.items() if k in ("name", "type", "options", "description")}


def build_steps(schema, tz=None, with_interview=False):
    steps = []
    tables = []
    for tname, fields in schema["phase1_tables"].items():
        ordered = sorted(fields, key=lambda f: not f.get("primary", False))
        tables.append({"name": tname, "fields": [clean_field(f) for f in ordered]})
    ext = schema.get("optional_extension_fact_interview")
    if with_interview and ext:
        ordered = sorted(ext["fields"], key=lambda f: not f.get("primary", False))
        tables.append({"name": ext["table"], "fields": [clean_field(f) for f in ordered]})
    steps.append({"step": 0, "phase": "phase1", "tool": "create_base",
                  "args": {"name": schema["name"], "tables": tables}})

    def add(phase, table, field, note=None):
        s = {"step": len(steps), "phase": phase, "tool": "create_field", "table": table, "field": field}
        if note:
            s["note"] = note
        steps.append(s)

    for l in schema["phase2_links"]:
        add("phase2", l["table"], {"name": l["name"], "type": "multipleRecordLinks",
                                   "options": {"linkedTableId": "{%s}" % l["linksTo"]}}, l.get("note"))
    if with_interview and ext:
        add("phase2", ext["table"], {"name": ext["link"]["name"], "type": "multipleRecordLinks",
                                     "options": {"linkedTableId": "{%s}" % ext["link"]["linksTo"]}})
    for d in schema["phase3_derived"] + schema["phase4_formulas"]:
        t = d["table"]
        f = {"name": d["name"], "type": d["type"]}
        if d.get("description"):
            f["description"] = d["description"]
        if d["type"] == "count":
            f["options"] = {"recordLinkFieldId": "{%s.%s}" % (t, d["recordLinkField"])}
        elif d["type"] == "multipleLookupValues":
            f["options"] = {"recordLinkFieldId": "{%s.%s}" % (t, d["recordLinkField"]),
                            "fieldIdInLinkedTable": "{%s}" % d["lookup"]}
        elif d["type"] == "rollup":
            f["options"] = {"recordLinkFieldId": "{%s.%s}" % (t, d["recordLinkField"]),
                            "fieldIdInLinkedTable": "{%s}" % d["rollupField"],
                            "formula": d["formula"]}
        elif d["type"] == "aiText":
            prompt = [p if isinstance(p, str) else {"field": {"fieldId": "{%s.%s}" % (t, p["field"])}}
                      for p in d["prompt"]]
            f["options"] = {"prompt": prompt}
        elif d["type"] == "formula":
            f["options"] = {"formula": d["formula"]}
        add(d.get("phase") or ("phase4" if d in schema["phase4_formulas"] else "phase3"), t, f,
            d.get("warning") or d.get("note"))
    return [subst_tz(s, tz) for s in steps]


def parse_listing(listing):
    """Accept {tables:[...]}, {base:{tables:[...]}}, or [...]; each table has id, name, fields[]."""
    if isinstance(listing, dict):
        for key in ("tables", "base"):
            if key in listing:
                return parse_listing(listing[key])
        raise SystemExit("listing: no 'tables' key found")
    out = {}
    for t in listing:
        out[t["name"]] = {"id": t.get("id", ""), "fields": {f["name"]: f for f in t.get("fields", [])}}
    return out


def ids_from_listing(listing):
    tables = parse_listing(listing)
    return {"tables": {n: t["id"] for n, t in tables.items()},
            "fields": {n: {fn: f.get("id", "") for fn, f in t["fields"].items()} for n, t in tables.items()}}


def resolve(obj, ids):
    missing = []

    def r(v):
        if isinstance(v, str):
            m = REF.match(v)
            if not m:
                return v
            t, f = m.group(1), m.group(2)
            if f is None:
                got = ids["tables"].get(t)
            else:
                got = ids["fields"].get(t, {}).get(f)
            if not got:
                missing.append(v)
                return v
            return got
        if isinstance(v, list):
            return [r(x) for x in v]
        if isinstance(v, dict):
            return {k: r(x) for k, x in v.items()}
        return v

    out = r(copy.deepcopy(obj))
    return out, missing


def expected_fields(schema, with_interview):
    exp = {t: {f["name"]: f["type"] for f in fs} for t, fs in schema["phase1_tables"].items()}
    for l in schema["phase2_links"]:
        exp[l["table"]][l["name"]] = "multipleRecordLinks"
        inv_t, inv_f = l["auto_inverse"].split(".", 1)
        exp[inv_t][inv_f] = "multipleRecordLinks"
    for d in schema["phase3_derived"] + schema["phase4_formulas"]:
        exp[d["table"]][d["name"]] = d["type"]
    ext = schema.get("optional_extension_fact_interview")
    if with_interview and ext:
        exp[ext["table"]] = {f["name"]: f["type"] for f in ext["fields"]}
        exp[ext["table"]][ext["link"]["name"]] = "multipleRecordLinks"
        exp[ext["link"]["linksTo"]][ext["table"]] = "multipleRecordLinks"
    return exp


def cmd_check(schema):
    names = expected_fields(schema, True)
    ids = {"tables": {t: "tbl" + t for t in names},
           "fields": {t: {f: "fld" + f for f in fs} for t, fs in names.items()}}
    problems = []
    for s in build_steps(schema, "UTC", True)[1:]:
        _, missing = resolve(s["field"], ids)
        problems += ["step %d %s.%s -> %s" % (s["step"], s["table"], s["field"]["name"], m) for m in missing]
        if s["table"] not in names:
            problems.append("step %d: unknown table %s" % (s["step"], s["table"]))
    for sec in schema.get("interface_reporting_dashboard", {}).get("sections", []):
        _, missing = resolve(sec, ids)
        problems += ["dashboard '%s' -> %s" % (sec["title"], m) for m in missing]
    for line in problems:
        print("UNRESOLVED", line)
    print("check: %s" % ("FAIL" if problems else "ok (%d build steps)" % len(build_steps(schema, "UTC", True))))
    return 1 if problems else 0


def cmd_diff(schema, listing, with_interview):
    live = parse_listing(listing)
    exp = expected_fields(schema, with_interview)
    errors, warnings = [], []
    for t, fields in exp.items():
        if t not in live:
            errors.append("missing table %s" % t)
            continue
        for fname, ftype in fields.items():
            lf = live[t]["fields"].get(fname)
            if not lf:
                errors.append("missing field %s.%s (%s)" % (t, fname, ftype))
            elif lf.get("type") and lf["type"] != ftype:
                errors.append("type mismatch %s.%s: live %s, schema %s" % (t, fname, lf["type"], ftype))
        for fname in live[t]["fields"]:
            if fname not in fields:
                warnings.append("extra field %s.%s (not in schema)" % (t, fname))
    for d in schema["phase3_derived"] + schema["phase4_formulas"]:
        if d["type"] == "rollup":
            lf = live.get(d["table"], {}).get("fields", {}).get(d["name"], {})
            live_formula = (lf.get("options") or {}).get("formula")
            if not live_formula and lf:
                warnings.append("rollup formula %s.%s not verified: the listing has no field options "
                                "(read back with get_table_schema, not list_tables_for_base)"
                                % (d["table"], d["name"]))
            if live_formula and live_formula.replace(" ", "") != d["formula"].replace(" ", ""):
                errors.append("rollup formula %s.%s: live %r, schema %r"
                              % (d["table"], d["name"], live_formula, d["formula"]))
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("WARNING", w)
    print("diff: %s (%d errors, %d warnings)" % ("FAIL" if errors else "ok", len(errors), len(warnings)))
    return 1 if errors else 0


def fill_config(config_path, ids):
    cfg = load(config_path)
    at = cfg.setdefault("airtable", {})
    for t in at.get("tables", {}):
        at["tables"][t] = ids["tables"].get(t, at["tables"][t])
    for t, fields in at.get("fields", {}).items():
        for fname in fields:
            fields[fname] = ids["fields"].get(t, {}).get(fname, fields[fname])
    with open(os.path.expanduser(config_path), "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "ids", "resolve", "diff", "dashboard", "check"])
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--timezone")
    ap.add_argument("--with-interview", action="store_true")
    ap.add_argument("--listing")
    ap.add_argument("--ids")
    ap.add_argument("--plan", help="plan.json written by `plan` (required for resolve)")
    ap.add_argument("--config")
    ap.add_argument("--step", type=int, nargs="*")
    a = ap.parse_args()
    schema = load(a.schema)

    if a.cmd == "check":
        sys.exit(cmd_check(schema))
    if a.cmd == "plan":
        print(json.dumps(build_steps(schema, a.timezone, a.with_interview), indent=1))
        return
    if a.cmd == "ids":
        ids = ids_from_listing(load(a.listing))
        if a.config:
            fill_config(a.config, ids)
        print(json.dumps(ids, indent=1))
        return
    if a.cmd == "diff":
        sys.exit(cmd_diff(schema, load(a.listing), a.with_interview))
    ids = load(a.ids)
    if a.cmd == "resolve":
        if not a.plan:
            sys.exit("resolve needs --plan <plan.json> (the file written by `plan`), so step numbers match it")
        steps = load(a.plan)
        out, rc = [], 0
        for n in a.step or []:
            if not 0 <= n < len(steps) or steps[n].get("step") != n:
                sys.exit("step %d is not in %s (it has steps 0-%d)" % (n, a.plan, len(steps) - 1))
            s, missing = resolve(steps[n], ids)
            if missing:
                print("UNRESOLVED step %d: %s (create/read back the referenced fields first)" % (n, missing),
                      file=sys.stderr)
                rc = 1
            out.append(s)
        print(json.dumps(out, indent=1))
        sys.exit(rc)
    if a.cmd == "dashboard":
        dash = copy.deepcopy(schema["interface_reporting_dashboard"])
        dash["sections"], missing = resolve(dash["sections"], ids)
        print(json.dumps(dash, indent=1))
        if missing:
            print("UNRESOLVED: %s" % sorted(set(missing)), file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
