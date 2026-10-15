---
name: career-setup
description: Idempotent, resumable setup for career-kit. Checks connectors and the Humanizer skill, creates the workspace, runs the career-focus and Experience-Context interviews, builds role-type base resumes, builds the Airtable Job Application Tracker base and Reporting dashboard from airtable/schema.json, publishes the Job Search Tracker artifact, installs the three scheduled tasks, seeds the log files, and smoke-tests everything. Use for /career-setup, first-time setup, or re-running a failed or skipped setup step.
---

# career-kit setup

Progress lives in `<workspace>/career-kit.config.json` → `setup_progress`. On every run, read it and skip phases already `true`, unless the user asks to redo one. Set a phase to `true` only after it fully succeeds. Tell the user which phase you are on.

**Plugin root** = two directories above this SKILL.md (the skill's base directory is shown when it loads). Scripts: `<plugin root>/scripts/`. Templates: `<plugin root>/templates/`.

## Phase 0: config
If `<workspace>/career-kit.config.json` doesn't exist yet, Phase 1 creates it from `templates/career-kit.config.template.json`. Never write the config anywhere inside the plugin folder.

## Phases
1. **Preflight**: `references/preflight.md`. Detect connectors, install the Humanizer dependency from GitHub if missing, report what's missing and how to add it, ask for the workspace folder (default `~/Documents/ClaudeCareer`), create it and `.career-kit/`, write the config, ask for timezone and Gmail address.
2. **Discovery interview**: run the `career-focus-interview` skill. Output `Career-Aspirations.md` + `search.*` in config.
3. **Experience-Context interview**: run the `experience-context-builder` skill. Output `Experience-Context.md`, `Experience-Context-Archive.md`, `preferences.*`. Offer `story-bank` afterwards (optional).
4. **Resumes**: `references/resumes.md`. Role-type base resumes, ATS-safe.
5. **Airtable**: `references/airtable-build.md`. Build from `airtable/schema.json` with the deterministic helper, verify with a read-back diff, build and verify the Reporting dashboard, store IDs. Any diff mismatch fails this phase with a clear report.
6. **Tracker artifact**: `references/tracker.md`. Publish "Job Search Tracker" and store the URL.
7. **Scheduled tasks**: `references/scheduled-tasks.md`. Render each template, show prompt + schedule + connectors, confirm, create, list to verify.
8. **Seed files**: create `company-notes.md`, `job-search-log.md`, `screened-postings.md`, `job-search-runs.md`, `Interview-Log.md` from `templates/*.template.md` (only if missing; never overwrite) with `scripts/render-task.py --allow-empty --template <template> --out <ws>/<file>`. Ask for 3-10 every-run companies and their careers or JSON feed URLs, and 5-20 rotation companies, to fill company-notes.md.
9. **Smoke test**: `references/smoke-test.md`. Report pass/fail per connector and print the "what to do next" checklist.

## Rules
- Ask one thing at a time. Never ask for passwords or API keys; connectors are added by the user in their app settings.
- Personal files stay in the workspace. Nothing is written into the plugin folder.
- If a connector is missing, skip the dependent phase, leave it `false`, and say how to resume (`/career-setup` again).
- Before any external write (create base, publish artifact, create scheduled task), show what will be created and get a yes.
