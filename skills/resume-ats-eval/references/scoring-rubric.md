# Building the weighted scoring rubric

This is the core technique that makes the eval a real analysis rather than a vibe check. It has three parts: derive the criteria, weight them, score against them. Do all three visibly — the reasoning is as valuable to the user as the final number.

## 1. Derive the criteria from the posting

Read the whole posting, not just the bullet list — context paragraphs ("About the role") often reveal what the team actually cares about more than the bulleted requirements do. Pull out every distinct, checkable requirement: a title/experience type, a degree or equivalent, a specific technology or platform, a scope of scale, a soft-skill/behavioral trait, a location/logistics constraint.

Split into two buckets. Most postings label this themselves:

- **Required** — "You have," "Requirements," "Minimum qualifications," "Must have."
- **Preferred / bonus** — "Exceptional candidates will have," "Nice to have," "Preferred," "A plus."

If a posting doesn't separate them, use the strength of the language ("must," "required," "X years of Y" read as required; "familiarity with," "exposure to," "ideally" read as preferred).

## 2. Assign weights

Total should sum to a clean number — 100 is easiest for the user to read as a percentage. Split roughly 70–80 points to required, 20–30 to preferred, then distribute within each bucket by emphasis, not evenly. Signals of higher emphasis: how many sentences/paragraphs the posting spends on it, whether it's mentioned more than once (e.g. once in "About the role" and again in the bullets), and whether it's central to the role's stated mission (a role explicitly about "doubling developer productivity via AI tooling" should weight AI/tooling fluency higher than a role that mentions it once in passing).

A location/logistics requirement (e.g. "must be based in Seattle" or "must relocate") is usually a hard gate in real ATS systems rather than a scored dimension — but for this proxy, including it as a small-weight scored item (e.g. 5 points) works fine and keeps the total legible, as long as you note that in practice it may function as pass/fail rather than partial credit.

## 3. Score the resume against each criterion

For each row, estimate a match percentage from 0–100% based on actual evidence in the resume text — direct mentions, closely adjacent terminology, or demonstrated scope that clearly implies the requirement. Don't award match percentage for things the person *probably* also knows but that aren't reflected anywhere in the document; an ATS can only see what's written down, and so should this proxy.

Multiply match % × weight = points earned for that row. Sum all rows for the total score out of 100.

## Presentation format

Always show a table like this (illustrative: a fictional Staff TPM posting scored against an early-stage resume):

| Requirement | Weight | Match % | Points |
|---|---|---|---|
| TPM/Eng Lead/EM title language | 10 | 10% | 1.0 |
| CS degree or equivalent | 8 | 20% | 1.6 |
| Large-scale technical transformation, measurable impact | 12 | 65% | 7.8 |
| Executive presence / matrix influence | 10 | 90% | 9.0 |
| ... | ... | ... | ... |
| **Total** | **100** | | **43.1** |

When re-scoring an updated resume, put both the "before" and "after" columns in one table (weight stays fixed; only match % and points change) so the delta is visible per-row, not just in the total. Close by naming which remaining point losses are framing issues (still fixable with better wording) vs. genuine gaps (honestly about as good as they'll get without new real experience).

## Common failure modes to avoid

- **Padding every score toward the middle.** If a requirement isn't mentioned anywhere in the resume, that's 0-20%, not 50%. Resist rounding up out of politeness — an inflated proxy score is worse than useless, it's actively misleading about how the real system will behave.
- **Scoring the person, not the document.** The eval is specifically about what's *written down*. A brilliant engineer with a resume that doesn't mention engineering will score low, correctly — that's the whole reason the tailoring step exists.
- **Hiding the math.** A single number with no table defeats the purpose. Always show weight × match% = points.
