#!/usr/bin/env python3
"""Repo validators for career-kit. Run from anywhere: python3 scripts/validate.py

1. Every *.json file parses.
2. Frontmatter: skills (name = folder, description), agents (name = file, description, model),
   commands (description), scheduled-tasks (task_id, title, default_cron).
3. Every {{PLACEHOLDER}} in templates/, scheduled-tasks/, airtable/ and agents/ is defined in
   templates/career-kit.config.template.json (placeholder_map or runtime_placeholders), and every
   placeholder_map path exists in that template.
4. airtable/schema.json references resolve (delegates to airtable-plan.py check).
Exit 1 on any failure.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PH = re.compile(r"\{\{[^{}]+\}\}")
errors = []


def rel(p):
    return os.path.relpath(p, ROOT)


def walk(sub, exts):
    base = os.path.join(ROOT, sub)
    for d, dirs, files in os.walk(base):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(d, f)


def frontmatter(path):
    text = open(path).read()
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


# 1. JSON
for sub in (".claude-plugin", "airtable", "templates", "tests"):
    for p in walk(sub, (".json",)):
        try:
            json.load(open(p))
        except Exception as e:
            errors.append("JSON %s: %s" % (rel(p), e))

# 2. Frontmatter
def need(path, keys, extra=None):
    fm = frontmatter(path)
    if fm is None:
        errors.append("frontmatter missing: %s" % rel(path))
        return
    for k in keys:
        if not fm.get(k):
            errors.append("frontmatter %s: missing '%s'" % (rel(path), k))
    if extra:
        extra(fm)

for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
    p = os.path.join(ROOT, "skills", d, "SKILL.md")
    if not os.path.exists(p):
        errors.append("skills/%s has no SKILL.md" % d)
        continue
    def chk(fm, d=d, p=p):
        if fm.get("name") != d:
            errors.append("skill name '%s' != folder '%s'" % (fm.get("name"), d))
        if len(fm.get("description", "")) > 1024:
            errors.append("%s: description over 1024 chars" % rel(p))
    need(p, ["name", "description"], chk)
for p in walk("agents", (".md",)):
    def chk(fm, p=p):
        if fm.get("name") != os.path.basename(p)[:-3]:
            errors.append("agent name mismatch: %s" % rel(p))
        if fm.get("model") not in ("haiku", "sonnet", "opus", "inherit"):
            errors.append("agent model invalid: %s" % rel(p))
    need(p, ["name", "description", "model"], chk)
for p in walk("commands", (".md",)):
    need(p, ["description"])
for p in walk("scheduled-tasks", (".md",)):
    need(p, ["task_id", "title", "default_cron"])

# 3. Placeholders
cfg = json.load(open(os.path.join(ROOT, "templates", "career-kit.config.template.json")))
pmap = cfg.get("placeholder_map", {})
defined = set(pmap) | set(cfg.get("runtime_placeholders", []))
for name, path in pmap.items():
    cur = cfg
    for part in path.split("/"):
        if not isinstance(cur, dict) or part not in cur:
            errors.append("placeholder_map %s -> missing config path %s" % (name, path))
            break
        cur = cur[part]
used = {}
for sub in ("templates", "scheduled-tasks", "airtable", "agents"):
    for p in walk(sub, (".md", ".html", ".json")):
        if p.endswith("career-kit.config.template.json"):
            continue
        for m in PH.findall(open(p).read()):
            used.setdefault(m, set()).add(rel(p))
for name, files in sorted(used.items()):
    if name not in defined:
        errors.append("undefined placeholder %s in %s" % (name, ", ".join(sorted(files))))

# 3b. Third-party Humanizer: declared as a dependency, never vendored
pj = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
mj = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
dep = {"name": "humanizer", "marketplace": "humanizer"}
if dep not in pj.get("dependencies", []):
    errors.append("plugin.json: missing dependency %s" % dep)
if "humanizer" not in mj.get("allowCrossMarketplaceDependenciesOn", []):
    errors.append("marketplace.json: allowCrossMarketplaceDependenciesOn must include 'humanizer'")
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if not x.startswith(".")]
    if os.path.basename(d).lower() == "humanizer" and "SKILL.md" in files:
        errors.append("vendored Humanizer found at %s: depend on github.com/blader/humanizer instead" % rel(d))

# 4. Schema references
r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "airtable-plan.py"), "check"],
                   capture_output=True, text=True)
if r.returncode != 0:
    errors.append("airtable-plan check failed:\n" + r.stdout + r.stderr)

for e in errors:
    print("FAIL", e)
print("validate: %s (%d placeholders used, %d defined)" % ("FAIL" if errors else "ok", len(used), len(defined)))
sys.exit(1 if errors else 0)
