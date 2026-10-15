---
description: Add or correct career facts, stories, or writing/resume preferences in Experience-Context
argument-hint: "[what changed, optional]"
---
Run the `experience-context-builder` skill in update mode. What changed (if given): $ARGUMENTS

Locate the right section with grep, propose the exact edit (canonical file and/or archive section), and write only after the user approves. Never add interview outcomes, application status, scheduling, or posting assessments. Route those to `Interview-Log.md`, `job-search-log.md`, or Airtable instead. Afterwards, offer to refresh affected Story-Bank entries and, if preferences changed, update `preferences.*` in career-kit.config.json.
