# Phase 9: smoke test

Run both checks in this session. Don't wait for the schedule.

1. **Job-board check, dry run, 1 company**: read `<ws>/.career-kit/tasks/job-board-check.md` and follow it with "dry run" in effect: one every-run company plus one job-board query, no writes, no tracker update, no notifications. If the Agent tool is available, use one posting-scout to exercise the split path.
2. **Email scrub, read-only**: follow `<ws>/.career-kit/tasks/email-scrub.md` in read-only mode: Airtable connectivity check, the Gmail search, and classification of at most 5 threads. Write nothing.
3. **Tasks registered**: `list_scheduled_tasks` shows all three with the expected schedules.
4. **Humanizer**: `humanizer:humanizer` is available (if `connectors.humanizer` was `pending-restart`, set it to `true` now; if still missing, repeat the preflight Humanizer steps).
5. **Tracker**: read the artifact URL back with the Artifact tool's `read` action and confirm `.howto` is present.
6. **Validators**: `python3 <root>/scripts/airtable-plan.py diff` against a fresh read-back.

Report a table: check | connector | pass/fail | note. Any fail: name the fix and the phase to re-run.

## What to do next (print this)
- Tailor a resume: `/resume-ats-eval <job posting URL>`, or click **Tailor resume** on a tracker card and paste the prompt.
- Write a cover letter: "write a cover letter for <URL>".
- Prep for an interview: share the interviewer's LinkedIn PDF and say "profile this interviewer"; then "set up a Yoodli roleplay".
- Build your story bank: "build my STAR and CLEAR stories".
- Check status any time: `/career-status`.
- Add new facts or stories: `/career-update-context`.
- The tracker updates daily at the job-board time; open it at <tracker URL>.
