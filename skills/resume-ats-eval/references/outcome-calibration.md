# Outcome-calibration check (closes the loop)

Read this when the user asks something like "is this skill working," "why is my reject/contact rate off," or periodically when doing a batch of new evals (e.g. every ~10-15 applications). This is not part of the routine per-posting workflow — nothing upstream ever checks this on its own, so it has to be triggered deliberately.

This skill's numeric score is only useful if it actually predicts what happens after the application goes out.

## What to pull

Pull real outcomes from the Job Application Tracker base: `search_bases` for "Job Application Tracker", find `dim_Application` (Current State / All States rollups, linked Resume Used, Job Title, Company) and `dim_Resume` (Notes field holding the logged baseline/tailored scores and gap detail from step 12).

## What to check

Join them by the `Resume Used` link and compare:

- Did applications built on resumes with genuine, hard-filter-flagged gaps (step 6a) convert to contact (Recruiter Contact / Formal Interview / any state past "Application Received" or "Application Rejected") at a meaningfully lower rate than resumes without such flags, or than the person's untailored/generic resume? Applications still sitting at "Application Received" for several weeks are informative too (functionally a non-response, even if not formally rejected) — don't only count explicit rejections.
- Also check, when there's enough data: did resumes that got a narrative/trajectory pass (step 9b) convert to contact more often than resumes that only went through the standard keyword-rubric tailoring? This is the specific hypothesis step 9b exists to test going forward.
- Once several role-type base resumes exist, this is also the place to check whether starting from the right base (vs. the wrong one, vs. no base at all) correlates with contact rate — another directional signal, not proof.

## How to report it

Report this back candidly, including if the finding is uncomfortable (e.g. "none of your contacts came from a heavily-tailored stretch resume"). Treat this as evidence about the ATS/machine-stage gate specifically, not as evidence about resume framing quality or cross-application coherence — a cold application never gets compared side-by-side with another cold application to a different company.

This is observational, not statistically rigorous — sample sizes will usually be small — so frame findings as directional evidence, not proof, and note when a correlation might well be small-sample noise.
