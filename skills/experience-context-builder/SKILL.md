---
name: experience-context-builder
description: Guided, role-by-role interview that builds and maintains Experience-Context.md (concise canonical career facts, capabilities, evidence, tools, metrics, Honest Boundaries and Gaps, Detailed Story Index) and Experience-Context-Archive.md (full story narratives), and captures the user's standing resume rules and writing preferences into config. Use during /career-setup, for /career-update-context, or whenever the user wants to add, correct, or review career facts or stories.
---

# Experience-Context builder

Interactive and stateful: run inline. The only delegation: if the archive is over about 50 KB, ask a haiku subagent (`career-kit:web-researcher` or `general-purpose`, model haiku) to return a section map `{sections:[{heading, anchor, lineStart, lineEnd, topics[]}]}` so you can open sections by line range instead of reading the whole file.

## The rules (encode in every write)
`references/rules.md` holds the full list. The core rules:
- Experience-Context holds career facts and story details only, and it is application-agnostic.
- NEVER interview outcomes, status, scheduling, or job-posting assessments. Those go to Airtable, `Interview-Log.md`, and `job-search-log.md`.
- Never write new story points unprompted. Surface them as proposed additions, and write only after the user approves each one.
- Merge, don't duplicate. Resolve superseded facts in place and note the correction date in the archive.
- Preserve full stories in the archive. The canonical file holds retrieval cues and links only.

## Phase 1: inputs
Ask for existing resumes, LinkedIn PDF, performance reviews, and brag docs (paths in the workspace). Read resumes fully. Extract a draft role list (employer, title, dates) and confirm it with the user.

## Phase 2: role-by-role interview (one question at a time)
For each role, newest first, use `references/role-interview.md`: scope, team size and reporting line, ownership vs partnership, metrics (with how they were measured), tools, notable projects, stories worth keeping, and honest boundaries. Reflect back after each role and confirm before writing it.

## Phase 3: write
- `Experience-Context.md` from `templates/Experience-Context.template.md`: Career Snapshot, Career History, Cross-Career Capabilities and Evidence, Tools and Platforms, Education and Development, Honest Boundaries and Gaps, Related References, Detailed Story Index (links to archive anchors).
- `Experience-Context-Archive.md` from `templates/Experience-Context-Archive.template.md`: one anchored section per story (`<a id="story-<slug>"></a>`) with the full narrative and datapoints; dated session notes below.
- Show a diff-style summary of what changes, and write after the user says yes.

## Phase 4: preferences
Ask about standing resume rules (for example: no years-of-experience number in the summary; title bridging allowed or not; one page vs two; section order) and writing / cover-letter preferences (for example: don't name domain gaps in letters; vary hook and structure across letters to one company; tone; words to avoid). Save them to `career-kit.config.json` → `preferences.resume_rules`, `preferences.writing`, `preferences.cover_letter` as short imperative strings.

## Update mode (`/career-update-context`)
Ask what changed, locate the right section with grep, propose the edit, write on approval. Offer to refresh affected Story-Bank entries afterwards.
