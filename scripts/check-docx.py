#!/usr/bin/env python3
"""Document tooling and ATS-structure checks for career-kit. Standard library only.

  python3 scripts/check-docx.py --tools [--workspace <ws>]
      Report which .docx builders and renderers are available: the `docx` npm package (global or in
      <ws>/.career-kit/node), python-docx, and LibreOffice (soffice) for the visual render check.
      Exit 0 if at least one builder is available, 1 if none.

  python3 scripts/check-docx.py <file.docx> [...]
      ATS-safety check on each file: no tables, text boxes, multi-column sections, or contact details
      that appear only in a header/footer. Exit 1 if any file fails.

Use the structural check when LibreOffice isn't installed and the visual render check can't run.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

CONTACT_RX = re.compile(r"@|\(\d{3}\)|\d{3}[ .-]\d{3}[ .-]\d{4}|linkedin\.com", re.I)


def text_of(xml):
    return " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def check_file(path):
    problems = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        body = z.read("word/document.xml").decode("utf-8", "replace")
        hf = " ".join(text_of(z.read(n).decode("utf-8", "replace"))
                      for n in names if re.match(r"word/(header|footer)\d*\.xml$", n))
    if "<w:tbl>" in body or "<w:tbl " in body:
        problems.append("contains a table")
    if "txbx" in body or "<v:textbox" in body:
        problems.append("contains a text box")
    if re.search(r'w:cols [^>]*w:num="([2-9])"', body):
        problems.append("uses multiple columns")
    if CONTACT_RX.search(hf) and not CONTACT_RX.search(text_of(body)):
        problems.append("contact details appear only in the header/footer")
    return problems


def tools(workspace):
    found = {}
    node = shutil.which("node")
    local = os.path.join(os.path.expanduser(workspace), ".career-kit", "node") if workspace else None
    found["node"] = bool(node)
    if node:
        env = dict(os.environ)
        if local:
            env["NODE_PATH"] = os.path.join(local, "node_modules")
        r = subprocess.run([node, "-e", "require('docx')"], capture_output=True, env=env)
        found["docx_npm"] = r.returncode == 0
    else:
        found["docx_npm"] = False
    r = subprocess.run([sys.executable, "-c", "import docx"], capture_output=True)
    found["python_docx"] = r.returncode == 0
    found["libreoffice"] = bool(shutil.which("soffice") or shutil.which("libreoffice")
                                or os.path.exists("/Applications/LibreOffice.app"))
    found["builder_available"] = found["docx_npm"] or found["python_docx"]
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--workspace")
    a = ap.parse_args()
    if a.tools:
        t = tools(a.workspace)
        print(json.dumps(t))
        sys.exit(0 if t["builder_available"] else 1)
    bad = 0
    for f in a.files:
        p = check_file(f)
        print("%s: %s" % (f, "ok" if not p else "FAIL - " + "; ".join(p)))
        bad += bool(p)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
