---
task_id: career-kit-job-board-check
title: Daily job board check
default_cron: "30 8 * * *"
connectors: [web fetch/search, Claude in Chrome (Indeed link resolution), job-board MCPs (optional), Artifacts, Gmail (notifications)]
---
Run fully self-contained. Do not ask the user anything.

Config: {{WORKSPACE}}/career-kit.config.json. Workspace: {{WORKSPACE}}.
Search criteria: role targets {{ROLE_TARGETS}} at level {{LEVEL}}; location rule: {{LOCATION_RULE}} (fully remote in {{REMOTE_COUNTRY}}, or home metro {{HOME_METRO}} incl. {{METRO_ALIASES}}); salary floor {{SALARY_FLOOR}} ({{SALARY_FLOOR_NUMBER}}, applies only when pay is listed); excluded categories {{EXCLUDED_CATEGORIES}}; industries to avoid {{INDUSTRIES_AVOID}}; min score {{MIN_SCORE}}; second pass required at first-pass >= {{SECOND_PASS_THRESHOLD}}.

## Setup
1. Confirm access to {{WORKSPACE}}. If unreachable: status error (see Run status) and stop.
2. Read {{WORKSPACE}}/{{EXPERIENCE_CONTEXT}}: verified facts and honest scope boundaries. Never credit skills it doesn't record; never write posting assessments into it.
3. Read only the last ~40 lines of {{WORKSPACE}}/{{JOB_SEARCH_LOG}} and {{WORKSPACE}}/{{JOB_SEARCH_RUNS}} (tail, not the whole file). Cutoff = latest date found in either, else today minus {{CUTOFF_DAYS_DEFAULT}} days.
4. Read the section headings of {{WORKSPACE}}/{{COMPANY_NOTES}} plus "Every-run companies", "Rotation list" and "Excluded". Per-company fetch instructions are read by the scout that needs them.
5. NEVER read {{WORKSPACE}}/{{SCREENED_POSTINGS}} top to bottom. It is large. Use `grep -F` per candidate (URL, job id, "company | title").

## Sources (one batch each)
- A. Job boards: queries {{JOB_BOARD_QUERIES}} (job-board MCP search_jobs when connected, else the board's site via web), remote and home-metro variants.
- B. Greenhouse aggregator via direct query params: {{GREENHOUSE_AGGREGATOR_QUERY}}.
- C. Every-run company JSON feeds listed in company-notes.md (home-metro pass + remote pass).
- D. Rotation: the {{ROTATION_BATCH_SIZE}} companies with the oldest or blank last-checked date. Replace unreadable ones (up to ~3).
- E. Discovery, EVERY run: 1-2 easy-to-miss industries from {{DISCOVERY_INDUSTRIES}}, rotating; WebSearch for career pages; any company with a verified posting gets added to the rotation list. Report how many outside companies were tried.

## Stage 1: scouts (fan-out)
If the Agent tool is available: spawn one subagent per source batch A-E, in parallel. Use subagent_type `career-kit-posting-scout` (the tool-scoped copy Setup installs; about 8k tokens of overhead instead of about 54k) if it exists, else `career-kit:posting-scout`, otherwise `general-purpose` with model `{{MODEL_SCOUT}}` and the instructions in {{WORKSPACE}}/{{KIT_RUNTIME_DIR}}/agents/posting-scout.md. Give each scout ONLY: its batch, the criteria above, the cutoff date, and the absolute paths of Experience-Context.md, company-notes.md, job-search-log.md and screened-postings.md. No conversation history. Each returns compact JSON (title, company, location, url, pay, setup, firstPass, provisional, status, one-line reason, rotation/notes updates, errors).

INLINE FALLBACK: if the Agent tool is missing, or a scout reports it cannot reach a needed connector, run that batch yourself with the same posting-scout rules and note `mode=inline` for the run.

Scout rules (also the inline rules): open the real posting to confirm URL/location/pay before scoring. A posting counts only if the page shows a real JD (title + responsibilities/qualifications); if the page looks empty check ld+json JobPosting / og meta; a truncated page is a size problem, try the JSON feed. No unofficial LinkedIn scraping. Full-text rule: when found via an aggregator, open the employer's own page and score from full text; otherwise mark the score provisional. Links: never use Indeed to.indeed.com shortlinks; resolve to https://www.indeed.com/viewjob?jk=<jobkey> via the browser. Non-Indeed URLs as-is. Capture team/org, setup (Remote / Hybrid - N days / Onsite), pay range only when plainly stated, else "not listed".

## Filter (parent, after stage 1)
1. Dedup again across batches (same URL/job key, or same company+title). Grep the log and screened files once more for each kept candidate.
2. Excluded categories: drop without recording.
3. Keep only fully remote or home metro.
4. If salary listed, require >= floor; else keep.
5. First-pass Match Score from the scouts (resume-ats-eval weighting); discard < {{MIN_SCORE}}.

## Stage 2: skeptical second pass (REQUIRED for first-pass >= {{SECOND_PASS_THRESHOLD}})
For each such posting spawn one verifier in parallel: `career-kit:posting-verifier` (tool-scoped) if it exists, else `general-purpose` with model `{{MODEL_VERIFIER}}` and {{WORKSPACE}}/{{KIT_RUNTIME_DIR}}/agents/posting-verifier.md. Give it the URL, first-pass score, the closest role-type base resume in {{WORKSPACE}}/{{RESUMES_DIR}} (BASE-*.docx) and the Experience-Context path. Inline fallback: do the same method yourself.
Method: rubric from the posting (Required vs Preferred, weights sum 100, ~70-80 Required / 20-30 Preferred); weight x match% using actual evidence against the base resume + Experience-Context.md, never credit Honest Boundaries and Gaps; mark hard filters (min years by titles, required degree/field, named cert, required prior title/level, named tool w/ min years); hard-filter risk none/low/moderate/high naming the driver; label every requirement < 80% as framing / missing-information / genuine (if unsure, genuine; never relabel genuine as framing). The second-pass total is the reported/logged Match Score. < {{MIN_SCORE}} => screened out, with a "second-pass score N" line in screened-postings.md. Keep the first-pass number only in job-search-runs.md (e.g. "Company 84 -> 59").
6. Sort by final score, descending.

## Record
- Every posting opened and ruled out gets ONE line under "## Screened" in {{SCREENED_POSTINGS}} (append; do not rewrite the file): date | title | company | location | direct URL | short specific reason.
- Append qualifying postings to {{JOB_SEARCH_LOG}}: date | title | company | location | URL/job ID | final score.
- Apply the scouts' company-notes updates (last-checked dates, notes, new rotation companies, replacements).

## Output and tracker
Report for each qualifying posting: Title, Company, Location, Setup, Pay, final Match Score (provisional flag), hard-filter risk, and a one-line fit note (top two strengths, main genuine gap).
Update the Job Search Tracker artifact at {{TRACKER_URL}}: read the currently published HTML, insert a new day-group immediately after the `.howto` element, one card per qualifying posting using the card markup in {{WORKSPACE}}/{{KIT_RUNTIME_DIR}}/tracker/card-template.html exactly (same as the cards already on the page) (`.actions` with `<a class="apply">` and `<button class="tailor">` with the existing data attributes; href and data-url = resolved direct URL); score-high (>= 70) / score-mid ({{MIN_SCORE}}-69). Zero postings (or a run error) => one `.empty-day` div stating it (or the error reason). Republish to the SAME artifact URL. Never create a new artifact.

## Run status (every run)
Append one line to {{JOB_SEARCH_RUNS}} (create with header if missing): date | ok or error | note, e.g. "3 new; 14 screened; rotation: ...; discovery: N tried, ...; first->second: A 84->59; mode=split|inline". Use "error" when the workspace or tracker is unreachable or search tools failed broadly. Never record ok for a broken run.

## Notifications
- ok + zero postings: no email or push (the artifact still gets its empty-day).
- ok + >= 1: push notification + email from the user's own Gmail to {{NOTIFY_EMAIL}}, subject "Job board check — N new posting(s), <Month D>", body listing each posting (all fields + fit note + direct URL) and the tracker link {{TRACKER_URL}}.
- error: push + short email "Job board check — run problem, <Month D>".
Tone factual and concise.

## Dry run (smoke test)
If the prompt that started this run says "dry run" (Setup's smoke test does this): search only ONE company from the every-run list plus one job-board query, skip discovery and rotation, do not write to any log, company-notes, the tracker, or send notifications. Report per connector: pass/fail and what would have been recorded.
