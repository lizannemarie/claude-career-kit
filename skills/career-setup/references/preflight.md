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
| Humanizer skill | a skill named `humanizer:humanizer` | cover letters, resume language pass, interview prose | Installed automatically as a dependency of career-kit. If missing, see "Humanizer" below. |

Print a table with: found / missing / what it affects / how to add it.

## Humanizer (third-party dependency)
Humanizer is by blader (MIT), https://github.com/blader/humanizer. career-kit declares it as a plugin dependency, `humanizer@humanizer`, so installing career-kit normally installs it too. It is never copied into this repo. If `humanizer:humanizer` is not available:
1. Check what is installed: `claude plugin list --json` (when the `claude` CLI is on PATH). Look for an entry `humanizer@humanizer`.
2. If it is missing, ask: "career-kit uses the Humanizer plugin from github.com/blader/humanizer (MIT) for its writing pass. Install it now?" On yes, run:
   ```bash
   claude plugin marketplace add blader/humanizer
   claude plugin install humanizer@humanizer
   ```
   Without the CLI (for example in Cowork), tell the user to run `/plugin marketplace add blader/humanizer` and then `/plugin install humanizer@humanizer`.
3. A newly installed plugin loads in the next session. Set `connectors.humanizer` to `"pending-restart"` and tell the user to start a new session before writing letters; the smoke test re-checks it. Declined: set `false`. The skills then use their built-in checklists.
4. If another copy is installed under a different id (for example one uploaded to claude.ai, shown as `humanizer@synced`), both register the same skill name. Tell the user, and suggest keeping only the GitHub copy so updates come from the source (`claude plugin uninstall humanizer@synced` or remove it in claude.ai).
5. Updates: third-party marketplaces don't auto-update by default. `claude plugin update humanizer@humanizer` pulls the latest release.


## Workspace
1. Ask: "Where should your career files live?" Default `~/Documents/ClaudeCareer`. If the folder exists and has files, list the career-kit files already there (Experience-Context.md, logs) and say they will be reused, not overwritten.
2. Create the folder, `<workspace>/.career-kit/agents/`, `<workspace>/.career-kit/scripts/`, `<workspace>/.career-kit/tasks/`, `<workspace>/resumes/`, `<workspace>/.job-tracker-cache/`.
3. Copy `templates/career-kit.config.template.json` → `<workspace>/career-kit.config.json` if missing. Set `paths.workspace`.
4. Copy `<plugin root>/agents/*.md` → `<workspace>/.career-kit/agents/` and `<plugin root>/scripts/fetch-feeds.py` → `<workspace>/.career-kit/scripts/` (the scheduled tasks read them from there).
5. **Install tool-scoped subagents**  A subagent with no `tools:` list loads every connector in the session. `posting-verifier` and `web-researcher` are already scoped in the plugin. `posting-scout` and `email-classifier` need connector tools whose exact names differ per account, so write user-level copies (ask first: this adds two files to `~/.claude/agents/`):
   - `~/.claude/agents/career-kit-posting-scout.md`: the plugin file with `name: career-kit-posting-scout` and `tools: Read, Grep, Glob, WebFetch, WebSearch, ` plus the exact names of the Claude in Chrome tools `navigate`, `get_page_text`, `find`, `tabs_context_mcp`, `tabs_create_mcp`, and each connected job board's `search_jobs` and `get_job_details` tools.
   - `~/.claude/agents/career-kit-email-classifier.md`: `name: career-kit-email-classifier`, `tools: Read, Write, ` plus the Gmail `get_thread` tool's exact name.
   Take the names from your own tool list (for example `mcp__<server-id>__get_thread`). Re-run this step if connectors change.
6. Ask the user's timezone (IANA, for example `America/Chicago`), their Gmail address, the notification email (default: same address), and the display name to use in filenames. Write to `user.*` and `notifications.*`.
7. If the workspace is inside a git repository, add `career-kit.config.json`, `.career-kit/` and `.job-tracker-cache/` to that repo's `.gitignore`.

Set `setup_progress.preflight = true`.
