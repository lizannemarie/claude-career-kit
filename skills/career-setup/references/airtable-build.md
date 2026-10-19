# Phase 5: Airtable base + Reporting dashboard

Source of truth: `<plugin root>/airtable/schema.json`. Do not redesign it. The helper `scripts/airtable-plan.py` turns it into ordered steps and resolves `{table.field}` references to real IDs. Work files go in `<workspace>/.career-kit/airtable/`.

## 0. Ask first
- Workspace for the base (`list_workspaces` if the tool needs one).
- Include the optional `fact_interview` table? It powers interview reminders. If declined, reminders fall back to `fact_email` rows with Email Context = Formal Interview. Save the answer to `airtable.fact_interview_enabled`.
- If a base named "Job Application Tracker" already exists (`search_bases`), ask whether to reuse it (skip to step 4's diff) or create a new one.

## 1. Plan
```
python3 <root>/scripts/airtable-plan.py plan --timezone <user.timezone> [--with-interview] > <ws>/.career-kit/airtable/plan.json
```
Step 0 is the `create_base` payload (phase-1 tables, plain fields, field order kept, primary first, timezone substituted). Steps 1+ are `create_field` calls in the required order: phase 2 links, phase 3 lookups/counts/rollups/aiText, phase 4 formulas, then Current State.

## 2. Build
1. Call `create_base` with step 0's args, adapting key names to the MCP tool's input schema if they differ.
2. Read back: `list_tables_for_base` (and `get_table_schema` for all tables). Save the raw JSON to `listing.json`, then:
   `python3 <root>/scripts/airtable-plan.py ids --listing listing.json > ids.json`
3. For each later step N, in order:
   `python3 <root>/scripts/airtable-plan.py resolve --plan plan.json --ids ids.json --step N`
   Call `create_field` with the resolved table ID and field. After each **link** field (it auto-creates an inverse field named after the source table), and at the end of each phase, re-read the schema and regenerate `ids.json`. `resolve` reads the steps from the saved `plan.json`, so the numbering always matches the plan you built from (with or without `fact_interview`). It exits 1 with UNRESOLVED if a referenced field doesn't exist yet. Never guess an ID.
4. **Rollups cannot be edited later** (update_field only edits formulas, and fields can't be deleted through the connector). Before creating each rollup, show the resolved payload and check that the formula matches the schema exactly (`Current State` must use `ARRAYUNIQUE(ARRAYCOMPACT(values))`).

## 3. Verify (hard gate)
Read the schema back again, save `listing.json`, then:
```
python3 <root>/scripts/airtable-plan.py diff --listing listing.json [--with-interview]
```
Any ERROR fails Phase 5. Show the report verbatim, leave `setup_progress.airtable = false`, and tell the user which field to fix in the Airtable UI (or to delete the base and re-run). WARNINGs (extra fields) are reported but don't fail.

## 4. Store IDs
`python3 <root>/scripts/airtable-plan.py ids --listing listing.json --config <ws>/career-kit.config.json` fills `airtable.tables.*` and `airtable.fields.*`. Also set `airtable.base_id`. These IDs feed every `{{AT_*}}` placeholder (`scheduled_task_field_map` in the schema, plus the kit's extra field placeholders).

## 5. Reporting dashboard (fully specified, validated)
```
python3 <root>/scripts/airtable-plan.py dashboard --ids ids.json > dashboard.json
```
1. `create_interface` named "Reporting".
2. `create_page` with pageType `dashboard`, name "Applications Reporting Dashboard". Create the sections in file order. Each filtered big-number tile is its own single-element section, because `recordScopeFilters` are set per section. Map each section's `filter` to the section's recordScopeFilters, and the elements as given (number / barChart / pivotTable / list), using the resolved field IDs.
3. `publish_interface`.
4. Verify: `list_pages_for_base`, then `list_records_for_page` per tile. A fresh base legitimately returns 0 on every filtered tile; that is a pass. A tool error or a missing tile is a fail. Save `interface_id` and `dashboard_page_id` to config.

## 6. Tell the user (known limits)
a. "Prefer single record" on the Company and Resume Used links is UI-only. Optionally tick it in the field settings (cosmetic).
b. `Latest Context` (on fact_email) is a helper field. It intentionally replaces the source design's filtered rollup, which the API cannot create; Current State gives the same result.
c. The three "Attachment Summary" aiText cells generate on demand in the Airtable UI.
d. The **Application Stale** tile depends on `Days in Current State`, which the daily email scrub refreshes (its STEP 4b). The field's note in schema.json mentions a "weekly digest task"; in the kit, the email scrub is what maintains it.
e. `dim_Resume.Profession` starts with the seed list in the schema. Offer to add choices that match the user's own role-type bases (`update_field` on that select, adding options only).

## If the Airtable MCP is unavailable
Print manual steps: create the base "Job Application Tracker" and the four tables with the phase-1 fields, then each phase-2/3/4 field in plan order (print `plan` output as a table: table, field, type, settings), then the dashboard tiles with their filters. Leave `setup_progress.airtable = false` until the user confirms, then run step 3's diff from a fresh read-back.
