# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Email scrub reports "Airtable connection failed (looks like an expired/revoked authorization)" | The Airtable connector's authorization expired | Reconnect Airtable in Claude → Settings → Connectors. Cached emails sync automatically on the next run, and nothing is lost. |
| A scheduled task didn't run | The Claude app was closed at the scheduled time | It runs on next launch. Check the Scheduled section or `/career-status`. |
| `job-search-runs.md` shows `error` | The workspace or tracker was unreachable, or search tools failed broadly | Read the note on that line. Re-run the task from the Scheduled section ("Run now"). |
| `mode=split` in run notes | The run had more postings or threads than `split_thresholds`, so it fanned out to subagents | Normal for unusually large runs. Inline (`mode=inline`) is the default and was cheaper in the eval. |
| Setup Phase 5 fails with a diff ERROR | A field was created with the wrong type or formula | Read the report. Rollups can't be edited: delete the base in Airtable and re-run `/career-setup airtable`. |
| `resolve` prints UNRESOLVED | A referenced field wasn't created yet, or `ids.json` is stale | Re-read the schema (`list_tables_for_base`), regenerate `ids.json`, and retry that step. |
| Dashboard tiles show 0 | A fresh base, or no stale applications yet | Normal. The Stale tile needs the email scrub's daily refresh of Days in Current State and 14+ days of inactivity. |
| Tracker didn't update | Wrong or missing `tracker.artifact_url`, or the Artifacts tool is unavailable in the task session | Check the URL in config, then re-run the tracker phase to republish to the same URL. |
| Indeed links look like `to.indeed.com/...` | Link resolution needs the browser | Install Claude in Chrome. The task resolves links to `indeed.com/viewjob?jk=...`. |
| A posting page is blank | It's rendered client-side | Scouts fall back to ld+json, ATS JSON feeds, then the browser. Add the company's feed to `company-notes.md`. |
| Same posting shows up again | Its URL changed (tracking params) | The check also matches company + title. Add the canonical URL to `screened-postings.md`. |
| Cover letters or resumes sound generic | Humanizer isn't installed | Install it (see README). The skills otherwise use a built-in checklist. |
| `render-task.py` reports EMPTY or UNKNOWN | A config value is missing | Fill the key it names in `career-kit.config.json`, or run the matching Setup phase. |
| `check-privacy.sh` warns that the denylist is missing | No `.privacy-denylist` file at the repo root | Create it with your name, employers and email, one per line. It's gitignored. |
