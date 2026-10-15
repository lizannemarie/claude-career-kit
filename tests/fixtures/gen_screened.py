#!/usr/bin/env python3
"""Regenerate the ~145 KB synthetic screened-postings fixture used in docs/ARCHITECTURE.md."""
import os
import random

random.seed(1)
cos = ["Fabrikam", "Tailspin", "Woodgrove", "Litware", "Adatum", "Proseware", "Northwind", "Contoso",
       "Wingtip", "Lucerne", "Margie", "Alpine", "Coho", "Fourth Coffee", "Humongous"]
lines = ["# Screened Postings (FIXTURE)\n\n## Screened\n\n"]
i = 0
while sum(map(len, lines)) < 145000:
    i += 1
    c = random.choice(cos)
    lines.append("2026-0%d-%d | Product Manager %d | %s | Remote (US) | https://boards.example-ats.com/%s/jobs/%d | "
                 "first-pass score %d; domain mismatch\n"
                 % (random.randint(7, 9), random.randint(10, 28), i, c, c.lower().replace(" ", ""), 9000 + i,
                    random.randint(30, 54)))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screened-postings.fixture.md")
open(out, "w").write("".join(lines))
print(out, i, "lines")
