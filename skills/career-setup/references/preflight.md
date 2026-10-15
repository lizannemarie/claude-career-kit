# Phase 1: preflight

## Detect (record each result in `connectors.*` as true/false)
Check your available and deferred tool names. ToolSearch can confirm a deferred tool exists without loading many tools: search once per keyword.

| Connector | Tool name signal | Needed for | If missing, tell the user |
|---|---|---|---|
| Airtable | `list_bases`, `create_base`, `create_field` | Phase 5, email scrub, resume logging | Claude app → Settings → Connectors → add Airtable, then re-run `/career-setup`. |
| Gmail | `search_threads`, `get_thread`, `create_draft` | email scrub, notifications, reminders | Settings → Connectors → add Gmail. |
| Artifacts | the `Artifact` tool | tracker (Phase 6) | Use the Claude desktop app (Code or Cowork), where Artifacts are available. |
| Scheduled tasks | `create_scheduled_task`, `list_scheduled_tasks` | Phase 7 | Use the Claude desktop app; tasks run on your computer while the app is open. |
| Web fetch / search | `WebFetch`, `WebSearch` | job-board check, posting fetch | Usually built in; check your permission settings. |
| Claude in Chrome | `claude-in-chrome` tools | resolving Indeed links, JS-rendered postings | Optional: install the Claude in Chrome extension. |
| Job boards | `search_jobs` from Indeed, Dice, ZipRecruiter, Snagajob, RankedIn connectors | job-board check source A | Optional: add any of them in Settings → Connectors. Without them, source A uses the web. |
| Humanizer skill | a skill named `humanizer` | cover letters, resume language pass | Run `/plugin marketplace add blader/humanizer`, then `/plugin install humanizer@humanizer`. Optional but recommended; skills fall back to a built-in checklist. |

Print a table with: found / missing / what it affects / how to add it.

## Workspace
1. Ask: "Where should your career files live?" Default `~/Documents/ClaudeCareer`. If the folder exists and has files, list the career-kit files already there (Experience-Context.md, logs) and say they will be reused, not overwritten.
2. Create the folder, `<workspace>/.career-kit/agents/`, `<workspace>/.career-kit/tasks/`, `<workspace>/resumes/`, `<workspace>/.job-tracker-cache/`.
3. Copy `templates/career-kit.config.template.json` → `<workspace>/career-kit.config.json` if missing. Set `paths.workspace`.
4. Copy `<plugin root>/agents/*.md` → `<workspace>/.career-kit/agents/` (the scheduled tasks read them from there).
5. Ask the user's timezone (IANA, for example `America/Chicago`), their Gmail address, the notification email (default: same address), and the display name to use in filenames. Write to `user.*` and `notifications.*`.
6. If the workspace is inside a git repository, add `career-kit.config.json`, `.career-kit/` and `.job-tracker-cache/` to that repo's `.gitignore`.

Set `setup_progress.preflight = true`.
