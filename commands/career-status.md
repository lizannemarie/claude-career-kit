---
description: Show career-kit status: setup progress, scheduled task health, recent runs, pipeline counts
---
Report career-kit status in one compact view. Read only what is needed:

1. `<workspace>/career-kit.config.json` → `setup_progress` (phases done or pending), and which connectors were found.
2. `list_scheduled_tasks`: for each career-kit task, its schedule, enabled state, next run and last run. If a task has runs, `list_task_runs` with limit 3 and flag any failures.
3. The last 5 lines of `job-search-runs.md` (tail, never the whole file): ok/error and the notes.
4. The last 5 entries of `job-search-log.md` (tail).
5. If Airtable is configured: counts of dim_Application by Current State (one list_records call with only the Current State field), the number of stale applications (Days in Current State >= 14, non-terminal), and the pending email-cache size from `.job-tracker-cache/pending-fact-emails.json`.
6. The tracker URL.

End with at most three suggested next actions (for example "email scrub failed twice: reauthorize Airtable", "Phase 7 pending: run /career-setup").
