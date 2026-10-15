# Airtable: Job Application Tracker

`schema.json` is the exact specification of the base, validated by building it in a scratch base through the Airtable MCP. `/career-setup` builds it for you; you shouldn't need to touch this folder.

## Tables
| Table | Holds | Filled by |
|---|---|---|
| `dim_Company` | one row per employer | email scrub, resume-ats-eval |
| `dim_Application` | one row per application; Current State, All States, Latest/First Date, Count Emails, Days in Current State | email scrub (auto rows `auto::<company>::<role>`), resume-ats-eval stubs |
| `fact_email` | one row per job-related Gmail thread, classified into Email Context | email scrub |
| `dim_Resume` | one row per tailored or base resume, with scores in Notes | resume-ats-eval, setup |
| `fact_interview` (optional) | one row per interview round | you, or interview prep; powers reminders |

**Current State** is the Email Context of an application's newest email. It's built as `fact_email.IsLatest` → `fact_email.Latest Context` → rollup `ARRAYUNIQUE(ARRAYCOMPACT(values))`, because the API cannot create filtered rollups.

## Build order
`scripts/airtable-plan.py` reads `build_order` and the phase lists: `create_base` (phase 1 plain fields), then `create_field` for links (phase 2), lookups/counts/rollups/aiText (phase 3), formulas, then Current State (phase 4). `{table.field}` references resolve to real IDs at run time, and `{{USER_TIMEZONE}}` is substituted. Rollup formulas can't be edited after creation, which is why the order and formulas are fixed.

```bash
python3 scripts/airtable-plan.py check                  # every reference resolves
python3 scripts/airtable-plan.py plan --timezone America/Chicago --with-interview
python3 scripts/airtable-plan.py diff --listing listing.json   # live base vs schema
```

## Reporting dashboard
`interface_reporting_dashboard` fully specifies the "Reporting" interface. Its page "Applications Reporting Dashboard" has 6 big-number tiles, each in its own section with its own record filter: Total, Stale, Rejected, Real Engagement, Interview Loops, Interview Rejected. A shared unfiltered section holds 3 bar charts, a pivot table and a list. Setup creates it with `create_interface` / `create_page` / `publish_interface` and verifies each tile with `list_records_for_page`. A fresh base shows 0 on filtered tiles.

**Application Stale** counts applications with `Days in Current State >= 14` that aren't rejected or at an offer. `Days in Current State` is a plain number refreshed daily by the email scrub's STEP 4b. Note: the field's note in `schema.json` still mentions a "weekly digest task"; in the kit, the email scrub maintains it.

## Placeholders
`scheduled_task_field_map` lists the `AT_*` placeholders the task templates use. The kit adds a few more (JD Link, Current State, Latest Date, Days in Current State, and the fact_interview fields) in `templates/career-kit.config.template.json` → `placeholder_map`. Setup fills all of them from the read-back.

## Known limits
- "Prefer single record" on the Company and Resume Used links is UI-only.
- The `Latest Context` helper field intentionally replaces the source design's filtered rollup.
- aiText "Attachment Summary" cells generate on demand in the Airtable UI.
- Attachments (resume files) can't be uploaded by the connector; drag files into the record by hand.
