---
name: resume-ats-eval
description: Score a resume against a specific job posting the way an ATS/AI screening tool would, using a transparent weighted rubric built from the posting's own requirements, report hard-filter risk separately, then close honest gaps and produce a tailored ATS-safe .docx resume logged to Airtable. Use when the user shares a job posting (URL or text) and wants a match score, a tailored resume, or "run resume-ats-eval", including from the tracker's Tailor resume button.
---

# Resume ATS / AI-screening proxy eval and tailor

Build an honest, explainable proxy for automated screening: a rubric from the posting's own language, visible math (weight × match% = points), and tailoring that traces every change to something true. The score is a proxy, not a verdict; a hard structural requirement can sink an application regardless of the composite. Tailoring one resume per role is correct practice. Why: `references/rationale.md`.

## Config
Read `<workspace>/career-kit.config.json` (workspace default `~/Documents/ClaudeCareer`; ask if not found). Use `paths.*` for files, `resumes.bases` for role-type bases, `preferences.resume_rules` as standing rules, and `airtable.*` IDs when present (otherwise resolve the "Job Application Tracker" base by name).

## Inputs
1. A job posting (URL or text). 2. A resume. Prefer role-type bases (`BASE-<RoleType>` files or `dim_Resume` records with Type = Base): infer the closest base from the posting and state it in one line as an assumption. Sanity-check the base even when the user says "reuse the resume": if another base clearly fits better, say so. Ask only if the posting reads evenly across two bases or none fit. Missing input: ask first.

## Workflow
0. **Duplicate check.** Search `dim_Application` by JD Link, else Company + Job Title. If found, name the record, its Current State and last activity, and ask: re-tailor or stop. Airtable unavailable: say so and continue.
1. **Fetch the posting** in full. Empty JS shell: use ATS JSON APIs, else render in the browser. Never infer the JD from a shell. Details: `references/ats-signals.md`.
2. **Infer the ATS** from URL, on-page AI disclosure (quote it briefly), and user-confirmed vendor notes in `company-notes.md`. Unknown: say so and assume generic keyword/semantic matching.
3. **Experience-Context digest.** Build a compact digest of only the facts relevant to this posting, with their caveats (`references/context-digest.md`). Use grep/section reads; never load the archive whole. Stories: follow the Detailed Story Index and read the linked archive section before using one.
3a. **Scan prior tailored resumes** in `paths.resumes_dir` for proven phrasing aimed at similar roles before writing new language. A scan, not a blocking search.
4. **Rubric.** Required vs Preferred, weights sum to 100 (about 70-80 / 20-30), weighted by emphasis. Mark hard filters (degree/field, certification, required title/level, min years in a named tool, location/sponsorship). Method and format: `references/scoring-rubric.md`.
5. **Evidence ledger, then baseline score.** Every row gets evidence, source, confidence (`references/evidence-ledger.md`). Unverified rows stay unscored. Never credit anything in "Honest Boundaries and Gaps".
6. **Gap labels** for every row under ~80%: framing, missing-information, or genuine. Classify skeptically: take a second look at every "framing" label; if in doubt, downgrade. Never relabel genuine as framing to raise a score.
6a. **Hard-filter risk** (none/low/moderate/high, name the driver), reported separately from the score, before tailoring.
7. **Ask** only about missing-information gaps, 2-4 per round with a "not really / skip" option. Check Experience-Context first.
8. **New facts** the user confirms: do not write them into Experience-Context unprompted. Show the proposed addition and where it goes; write only on approval (see the experience-context-builder rules). Never write posting assessments, outcomes, or status there.
9. **Draft the tailored resume** with the `docx` skill, from the chosen base's structure and style. Apply `preferences.resume_rules`. Real titles stay real. Lead the headline/summary with the posting's vocabulary and the strongest 1-2 qualifications. No literal years-of-experience number in the summary. Story-based bullets come from the full archive narrative. ATS-safe: no tables, columns, text boxes, or header/footer-only contact info. Render to an image and look at it.
9a. **AI-language check** on every new or edited line (invoke `humanizer:humanizer` if available; else `references/rationale.md` § language checklist).
9b. **Narrative pass**: rising trajectory, builder identity where real, executive-communication proof, outcome-first bullets.
10. **Re-score** with the identical rubric (same rows, weights, hard-filter flags). Before/after table, remaining framing vs genuine loss, restate hard-filter risk.
11. **Deliver**: save as `<Name>-Resume-<Company>-<Role>.docx` in the resumes folder; summarize score change, hard-filter risk, top 1-2 things to watch.
12. **Log** to `dim_Resume`, then **12a** create/update the stub `dim_Application` (never touch status fields). Mechanics and the Attachments limitation: `references/airtable-logging.md`.
13. **Outcome calibration** when asked "is this working" or every ~10-15 applications: `references/outcome-calibration.md`.

## Re-running after a manual edit
"Re-score it" without a new posting: reuse the last posting and rubric; go to step 5.

## Never
Fabricate degrees, titles, tools, metrics, or projects. Hide the math. Skip step 0, the ledger, the hard-filter report, the AI-language check, or the Airtable logging. Overwrite application status with a stub write. Put a years-of-experience number in the summary.
