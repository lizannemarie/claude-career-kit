# Phase 4: role-type base resumes

1. Ask for existing resume files (.docx or .pdf). Copy them into `<workspace>/resumes/` (never into the plugin).
2. From `search.role_targets`, propose a set of role-type bases. Always include `BASE-ATS` (the general, most parseable version), plus one per distinct target family, for example Product, Program, Growth/Marketing, Commerce, Strategy/Ops. Only build the ones that match the user's targets; confirm the list.
3. For each base, use the `docx` skill and the resume-ats-eval writing rules (no fabrication; real titles; outcome-first bullets; no years-of-experience number in the summary; story bullets from the full archive; `preferences.resume_rules`). ATS-safe: single column, no tables, no text boxes, contact info in the body (not only the header/footer), standard section headings.
4. Name files `<Name>-Resume-BASE-<RoleType>.docx`. Render each to an image and check the layout.
5. Record each in `resumes.bases` as `{role_type, file, profession_tags}`. After Phase 5, log each to `dim_Resume` with `Type = Base` and matching Profession tags (see the resume-ats-eval skill's `references/airtable-logging.md`).
