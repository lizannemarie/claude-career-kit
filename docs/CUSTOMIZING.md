# Customizing career-kit

All settings live in `<career folder>/career-kit.config.json`. After changing anything a scheduled task uses, re-render and update the task with `/career-setup scheduled_tasks` (Setup re-runs only that phase).

## Search criteria (`search`)
| Key | Effect |
|---|---|
| `role_targets`, `level` | what scouts search for and how postings are scored |
| `home_metro`, `metro_aliases`, `remote_country` | the location filter: fully remote in the country, or the home metro |
| `location_rule` | the plain-English phrase shown in the tracker legend |
| `salary_floor` (number), `salary_floor_display` (text) | applied only when a posting lists pay |
| `excluded_categories` | role types that are never surfaced or recorded |
| `industries_avoid` | used during scoring and discovery |
| `min_score` (55), `second_pass_threshold` (70) | the cutoff for showing a posting, and the score that triggers the skeptical second pass |
| `job_board_queries`, `greenhouse_aggregator_query` | source A and B queries |
| `rotation_batch_size` (5), `discovery_industries` | how many rotation companies per run, and which industries discovery rotates through |

To re-run the interview behind these settings, say "re-run my career-focus interview".

## Companies
Edit `company-notes.md`: add every-run companies (with JSON feeds where possible), rotation companies, and exclusions. The daily task maintains the last-checked dates.

## Preferences (`preferences`)
`resume_rules`, `writing` and `cover_letter` are short imperative rules applied by the resume and letter skills, for example "Don't name domain gaps in cover letters" or "Vary hook and structure across letters to the same company". Edit them directly or with `/career-update-context`.

## Schedules (`schedules`)
Cron expressions in your local time. The email scrub also has `lookback_days` (1: each run re-checks the day before its last run, so nothing slips through) and `first_run_window` (`30d`: how far back the very first run searches). To change them: edit them here and re-run the scheduled_tasks phase, or change them in the app's Scheduled section (then update the config to match).

## Models (`models`)
| Key | Default | Used for |
|---|---|---|
| `scout` | haiku | first-pass posting scouts |
| `verifier` | sonnet | skeptical second pass. Set it to `opus` for the strictest scoring at a higher cost. |
| `classifier` | haiku | email classification |
| `researcher` | haiku | digesting interviewer and company sources |

## Inline vs subagents (`split_thresholds`)
`email_min_threads` (31) and `jobboard_min_postings` (19) set the size at which a daily task fans out to subagents; below them it runs inline, which `evals/split-decision/` measured as cheaper. Re-run that eval on your own data to tune them.

## Templates
`templates/tracker-template.html` controls the tracker look. Keep the `.howto` element, the card markup and the Tailor-button script, because the daily task depends on them. The other `templates/*.template.md` files only seed new files and never overwrite existing ones.

## Airtable
Don't edit `airtable/schema.json` for a live base: rollups can't be changed after creation. Add your own fields in the Airtable UI instead. The tasks only touch the fields listed in their prompts, and the setup diff reports extra fields as warnings, not errors.
