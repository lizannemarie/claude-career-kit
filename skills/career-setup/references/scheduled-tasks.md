# Phase 7: scheduled tasks

The tasks read and write files in the workspace, so they are installed as **desktop/Cowork scheduled tasks** (`create_scheduled_task`, `list_scheduled_tasks`). These run on the user's computer while the Claude app is open; a task that comes due while the app is closed runs at next launch. Cloud remote triggers can't reach local files and are not supported.

| Template | Default (local time) | Connectors |
|---|---|---|
| `scheduled-tasks/job-board-check.md` | 08:30 daily (`30 8 * * *`) | web fetch/search, Chrome (optional), job-board MCPs (optional), Artifacts, Gmail |
| `scheduled-tasks/email-scrub.md` | 07:00 daily (`0 7 * * *`) | Gmail, Airtable |
| `scheduled-tasks/interview-prep-reminders.md` | 07:00 daily (`0 7 * * *`) | Airtable, Gmail |

For each task:
1. Ask whether the default time works (cron in the user's local timezone). Save it to `schedules.<task>.cron`.
2. Render:
   ```
   python3 <root>/scripts/render-task.py --config <ws>/career-kit.config.json \
     --template <root>/scheduled-tasks/<file>.md --out <ws>/.career-kit/tasks/<file>.md
   ```
   Any UNKNOWN or EMPTY report means a config value is missing: go back and fill it. Exception: when `fact_interview` is declined, render the reminders task with `--allow-empty` (its `{{AT_*INT*}}` values are intentionally empty and the task uses the fact_email fallback).
3. Show the user the final rendered prompt (or its path plus the first 30 lines), the schedule, and the connectors it uses. Explain that each daily run uses Claude usage. Get a yes.
4. `create_scheduled_task` with `taskId` = `schedules.<task>.task_id`, a title, a one-line description, `cronExpression`, and the rendered prompt. If the ID is taken, ask whether to update the existing task (`update_scheduled_task`) or use the free ID the tool suggests.
5. After all three: `list_scheduled_tasks` and confirm each ID, schedule and enabled state. Report the permission mode each task was saved in, as the tool result says.
