# Experience-Context rules

1. **Scope.** Career facts and story details only, application-agnostic. A fact belongs here if it would be true and useful for any application.
2. **Never here:** interview outcomes, status, scheduling, recruiter names, feedback, job-posting assessments or scores, salary negotiations. Route them: application status → Airtable (`dim_Application`, `fact_email`, `fact_interview`); interview logistics and outcomes → `Interview-Log.md`; posting assessments → `job-search-log.md` / `screened-postings.md`.
3. **Approval.** Never write new story points unprompted. Other skills (resume-ats-eval, cover-letter-writer, story-bank) propose additions; the user approves each one before it is written.
4. **Evidence and limits.** Every metric records how it was measured and who owned it. Partnerships are recorded as partnerships, not ownership. Keep "do not overstate" caveats next to the fact.
5. **Honest Boundaries and Gaps** lists what is confirmed NOT true (for example "no people-management title", "no CS degree"), so future sessions don't re-ask and no scorer credits it.
6. **Canonical vs archive.** The canonical file is concise and current; when they conflict, it wins for facts. The archive keeps full narratives and history and is never condensed or deleted. Story summaries in the canonical file are retrieval cues that link to archive anchors.
7. **Merge, don't append.** Update the existing entry; record superseded facts as a dated correction note in the archive.
8. **Large files.** Use grep and line ranges. Never load a 50 KB+ archive whole.
