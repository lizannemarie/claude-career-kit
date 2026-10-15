#!/usr/bin/env bash
# Fails (exit 1) if the repo contains personal data.
#
# Generic checks (always on): absolute home paths (/Users/<name>, /home/<name>, C:\Users\<name>),
# email addresses (except example domains and noreply addresses), Airtable record/table/field/base
# IDs, Gmail thread deeplinks with real IDs, phone numbers.
#
# Personal checks: one term per line in .privacy-denylist at the repo root (gitignored, never
# committed): your name, former names, employers, email, interviewer names. Matching is
# case-insensitive on word boundaries. Lines starting with # are comments.
#
# Usage: scripts/check-privacy.sh [repo-root]
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  FILES=$(git ls-files -co --exclude-standard)
else
  FILES=$(find . -type f -not -path './.git/*' | sed 's|^\./||')
fi

if [ ! -f .privacy-denylist ]; then
  echo "WARNING: .privacy-denylist not found; only generic checks will run." >&2
  echo "         Create it with your name, employers and email (one per line)." >&2
fi

printf '%s\n' "$FILES" | python3 -c '
import re, sys, os
files = [f for f in sys.stdin.read().splitlines() if f and f != ".privacy-denylist"]
generic = [
  ("home path", re.compile(r"(/Users/(?!<|\{|USERNAME|you\b)[A-Za-z0-9._-]+|/home/(?!<|\{|user\b)[A-Za-z0-9._-]+|C:\\\\Users\\\\[A-Za-z0-9._-]+)")),
  ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@(?![A-Za-z0-9.-]*\bexample\.(?:com|io|org)\b)(?!users\.noreply\.github\.com\b)(?!anthropic\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
  ("airtable id", re.compile(r"\b(?:app|tbl|fld|rec|viw|pag|pbd|sel|wsp|usr)(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[A-Z])[A-Za-z0-9]{14}\b")),
  ("gmail thread", re.compile(r"mail\.google\.com/mail/u/\d+/#[a-z]+/(?!<)[0-9a-f]{12,}")),
  ("phone", re.compile(r"(?<![\w.-])(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w-])")),
]
deny = []
if os.path.exists(".privacy-denylist"):
  for line in open(".privacy-denylist", encoding="utf-8"):
    t = line.strip()
    if t and not t.startswith("#"):
      deny.append((t, re.compile(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", re.I)))
hits = 0
for f in files:
  if not os.path.isfile(f):
    continue
  try:
    text = open(f, encoding="utf-8").read()
  except (UnicodeDecodeError, OSError):
    continue
  for n, line in enumerate(text.splitlines(), 1):
    for label, rx in generic:
      for m in rx.finditer(line):
        print("%s:%d: %s: %s" % (f, n, label, m.group(0))); hits += 1
    for term, rx in deny:
      if rx.search(line):
        print("%s:%d: denylisted term (%d chars)" % (f, n, len(term))); hits += 1
print("check-privacy: %s (%d files scanned, %d denylist terms, %d hits)" % ("FAIL" if hits else "ok", len(files), len(deny), hits))
sys.exit(1 if hits else 0)
'
