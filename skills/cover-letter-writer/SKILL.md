---
name: cover-letter-writer
description: Draft a tailored one-page cover letter for a specific job posting (URL, pasted job description, or company + role), grounded in the user's Experience-Context, with targeted follow-up questions, the user's saved letter preferences, varied structure across letters, and a Humanizer pass. Use when the user wants a cover letter written or revised, is answering an application prompt, or asks to remove AI-sounding language from a letter draft.
---

# Cover letter writer

A good letter reads like one specific person telling one hiring manager why this role, at this company, now. Every step fights genericness: the real posting, real facts, a real anecdote, and an edit pass for machine-written tells.

## Config
Read `<workspace>/career-kit.config.json`: `paths.*`, `preferences.cover_letter` and `preferences.writing` (standing rules: honor every one, for example "don't name domain gaps", "vary structure across letters to one company"), and `connectors.humanizer`.

## Workflow
1. **Get the real posting.** One URL that fetches cleanly: fetch inline. Several pages to read (posting plus company pages, an empty JS shell needing ATS JSON or browser rendering): hand the fetch to a research subagent (`career-kit:web-researcher`, model haiku) with this digest schema: `{title, team, topRequirements[3-5], unusualSpecifics[], location, missionLanguage[], sources[]}`. Never guess the role from a shell; if nothing works, ask the user to paste the text.
2. **Ground in real background.** Pick the resume closest to the role (`paths.resumes_dir`, role-type bases first). Read only the relevant sections of `Experience-Context.md` with their caveats. Never credit "Honest Boundaries and Gaps".
3. **Map requirements to real parallels**, drawing the connection explicitly when the domain differs. Identify the biggest gap. Handle it the way `preferences.cover_letter` says. With no preference set, ask once whether to name gaps or leave them out, and save the answer to config.
4. **Ask what a resume can't show**: 1-3 targeted questions with concrete multiple-choice options plus "other", after checking Experience-Context. Ask for one authentic human detail if it isn't obvious.
5. **Vary across letters.** Before drafting, list existing letters in the workspace for the same company (filenames containing the company), read their openings, and use a different hook and paragraph order.
6. **Draft.** Opening: a specific hook from the posting. Body: 2-3 paragraphs of concrete nouns, metrics, and tools. Story-based content comes from the full archive section linked from the Detailed Story Index; never reconstruct a story from its summary or invent or round a metric. Close: human, plain call to action. One page.
7. **Humanizer pass.** If the Humanizer skill is installed, run it on the full draft. Otherwise apply `references/ai-writing-markers.md` line by line. Then re-check facts: the pass must not change what is claimed.
8. **Render and verify** with the `docx` skill: US Letter, about 1" margins, 11 pt; render to an image and confirm exactly one page.
9. **Save** as `<Name>_<Company>_CoverLetter.docx` in the workspace and present the file.

## Edit-only requests
For a pasted draft, skip to step 7. Preserve the user's facts, anecdotes, and voice.

## Rules
New facts the user mentions are proposed for Experience-Context, never written there unprompted. Application status and outcomes never go in Experience-Context.
