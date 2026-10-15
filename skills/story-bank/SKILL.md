---
name: story-bank
description: Build and maintain the user's interview story bank in STAR and CLEAR formats, derived from Experience-Context.md and its archive (which stay the source of truth), and map stories to a specific posting, interviewer, or question list. Use when the user wants interview stories written or refreshed, asks "which story should I use for X", wants STAR or CLEAR versions, or is preparing answers for a behavioral or leadership round.
---

# Story bank (STAR + CLEAR)

`Story-Bank.md` is a derived, interview-ready view. `Experience-Context.md` (Detailed Story Index) and `Experience-Context-Archive.md` (full narratives) remain the source of truth. If the bank and the archive disagree, the archive wins: fix the bank and tell the user.

## Config
`<workspace>/career-kit.config.json`: `paths.story_bank`, `paths.experience_context`, `paths.experience_archive`, `preferences.writing`.

## Build or refresh
1. Read the Detailed Story Index in Experience-Context.md. For each story the user wants (or all, on first build), open ONLY the linked archive section (grep the anchor, read that section). Never load the archive whole.
2. Write each story in both formats using `references/formats.md`. Keep the real sequence, the user's role versus partners' roles, constraints, trade-offs, uncertainty, and the outcome. Never invent, round, or "improve" a metric; leave a `[metric?]` slot and ask instead.
3. Every entry gets: id (`S-01`…), title, source link (archive anchor), competencies tags, a 30-second version, and "do not overstate" caveats copied from Experience-Context.
4. Story points that are not in the archive: list them for the user as proposed additions. Write them into the archive (through experience-context-builder rules) only after the user approves.

## Map stories to a role or round
Given a posting, interviewer profile, or question list: build a table of question or competency → best story id → format (STAR for execution questions, CLEAR for leadership/strategy questions) → the one detail to emphasize. Flag any question with no honest match. A gap is a gap; never stretch a story to cover it.

## Rules
- The bank holds career stories only: no interview outcomes, schedules, feedback, or company-specific assessments (those go in `Interview-Log.md` and Airtable).
- Humanizer pass on prose if installed. First person, plain, specific.
