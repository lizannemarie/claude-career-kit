# Evidence Ledger

Create this ledger before scoring. It makes every score auditable and prevents unknown evidence from being treated as a match.

## Required Fields

- `requirement_id`
- `requirement_text`
- `classification`: Required or Preferred
- `weight`
- `match_percent`
- `points`
- `hard_filter`: true or false
- `source`: resume, Experience Context, user confirmation, prior tailored resume, or posting
- `source_id`: specific section, bullet, or fact identifier
- `confidence`: Confirmed, Partial, or Unverified
- `gap_classification`: Framing, Missing-information, Genuine, or Unverified
- `evidence_text`
- `notes`

## Evidence Confidence

- **Confirmed:** direct evidence in the resume or Experience Context.
- **Partial:** related evidence exists, but the exact requirement is not fully demonstrated.
- **Unverified:** no reliable evidence exists and no user confirmation is available.

Partial evidence may receive a nonzero match score only when the relationship is clear. Unverified evidence must remain unscored and must be reported separately.

## Hard-Filter Rule

A hard-filter requirement is any requirement that a structured screen may enforce, such as a required degree/field, certification, minimum years in a named tool, required title/level, or required location/sponsorship constraint.

A hard-filter miss caps the achievable total. It is not an ordinary deduction.

## Unscored Gate Rule

For every Unverified requirement:

1. Preserve its weight in the rubric.
2. Show `Unverified`, not a fabricated match percentage.
3. State whether it is likely to be a hard filter or human-review concern.
4. Ask only when the requirement is plausible and materially affects the result.
5. Do not add it to the composite score until evidence is confirmed.

## Re-score State

Store the rubric rows after initial scoring. The final re-score must reuse the same requirement text, weight, evidence, and hard-filter flags. Only match percentage, points, and gap classification may change.
