#!/usr/bin/env python3
"""Render a career-kit template with values from career-kit.config.json.

  python3 scripts/render-task.py --config ~/Documents/ClaudeCareer/career-kit.config.json \
      --template scheduled-tasks/job-board-check.md --out <workspace>/.career-kit/tasks/job-board-check.md

  --tracker   also strip the sample day-groups from templates/tracker-template.html
              (keeps the .howto element and the DAY-GROUP TEMPLATE comment)
  --card-out  with --tracker: save the removed sample day-group (header + one card, with its
              runtime placeholders) so the daily task can copy the exact card markup

Every {{PLACEHOLDER}} is looked up in the config's placeholder_map. Runtime placeholders
(card fields the daily task fills) are left as-is. Lists render as comma-separated text,
'~' in the workspace path expands to the user's home directory, and YAML frontmatter
is printed to stderr (schedule info) and removed from the output. Exits 1 if any
placeholder is unknown or renders as an empty string (use --allow-empty to only warn). Numeric
zeros such as salary_floor 0 are valid values.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitconfig import PH, lookup  # noqa: E402


def fmt(name, value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if value is None:
        return ""
    s = str(value)
    if name in ("{{WORKSPACE}}",):
        s = os.path.expanduser(s).rstrip("/")
    return s


def strip_sample_day_groups(html):
    """Return (html without sample day-groups, the first sample day-group as a card template)."""
    marker = "<!-- DAY-GROUP TEMPLATE"
    start = html.find(marker)
    legend = html.find('<p class="legend">')
    if start < 0 or legend < 0:
        raise SystemExit("tracker: markers not found; is this tracker-template.html?")
    comment_end = html.find("-->", start) + 3
    samples = html[comment_end:legend]
    second = samples.find('<div class="day-group">', samples.find('<div class="day-group">') + 1)
    card_template = samples[:second if second > 0 else len(samples)].strip() + "\n"
    return html[:comment_end] + "\n\n" + html[legend:], card_template


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--out")
    ap.add_argument("--tracker", action="store_true")
    ap.add_argument("--card-out")
    ap.add_argument("--allow-empty", action="store_true")
    a = ap.parse_args()

    cfg = json.load(open(os.path.expanduser(a.config)))
    pmap = cfg.get("placeholder_map", {})
    runtime = set(cfg.get("runtime_placeholders", []))
    text = open(a.template).read()

    if text.startswith("---\n"):
        end = text.index("\n---", 4)
        print(text[4:end], file=sys.stderr)
        text = text[end + 4:].lstrip("\n")

    unknown, empty = [], []

    def repl(m):
        name = m.group(0)
        if name in runtime:
            return name
        if name not in pmap:
            unknown.append(name)
            return name
        try:
            v = fmt(name, lookup(cfg, pmap[name]))
        except KeyError:
            unknown.append(name + " (path " + pmap[name] + " missing in config)")
            return name
        if v == "":  # a numeric 0 (for example no salary floor) is a real value, not a missing one
            empty.append(name)
        return v

    out = PH.sub(repl, text)
    if a.tracker:
        out, card = strip_sample_day_groups(out)
        if a.card_out:
            os.makedirs(os.path.dirname(os.path.abspath(a.card_out)), exist_ok=True)
            with open(a.card_out, "w") as f:
                f.write(card)

    for u in sorted(set(unknown)):
        print("UNKNOWN placeholder:", u, file=sys.stderr)
    for e in sorted(set(empty)):
        print(("WARNING" if a.allow_empty else "EMPTY") + " value for:", e, file=sys.stderr)

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            f.write(out)
    else:
        sys.stdout.write(out)
    if unknown or (empty and not a.allow_empty):
        sys.exit(1)


if __name__ == "__main__":
    main()
