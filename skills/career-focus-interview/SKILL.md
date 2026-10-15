---
name: career-focus-interview
description: Run a conversational career-focus discovery interview, one question at a time, covering what energizes and drains the user, values, ideal environment, role targets, level, location constraints, compensation floor, industries to avoid, and categories to never surface; then write Career-Aspirations.md and the job-search criteria into career-kit.config.json after the user confirms a summary. Use during /career-setup, or when the user wants to rethink their target roles or search criteria.
---

# Career-focus interview

Interactive and stateful: always inline, never delegated.

## How to run it
- One question per message. Reflect back what you heard in a sentence before the next question, and follow up when an answer is vague ("what about that drained you?").
- Offer short multiple-choice options when it helps, always with an "other / in my own words" option.
- Topics and sample questions: `references/question-guide.md`. Cover every topic; order can follow the conversation.
- If `Career-Aspirations.md` already exists, show its summary first and ask what changed instead of starting over. Add a new dated section; never delete earlier ones.

## Close
1. Show a summary in two parts: **What you said** (the user's own words, lightly edited) and **Assessment** (your observations, clearly labeled as Claude's and not the user's words: patterns, tensions, role families that fit).
2. Show the proposed search criteria as a short table: role targets, level, home metro and aliases, remote country, relocation, location rule text, salary floor (number and display string), industries to avoid, excluded categories, discovery industries.
3. Ask the user to confirm or edit. Write nothing until they confirm.

## Write (after confirmation)
- `<workspace>/Career-Aspirations.md` from `templates/Career-Aspirations.template.md`: a dated "Career focus interview" section with both parts.
- `career-kit.config.json` → `search.*`. Set `search.location_rule` to a plain phrase used in the tracker legend (for example "fully remote (US) or the <metro> area").
- Append the criteria to the "Fit Criteria" section of `job-search-log.md` if that file exists.
- Never put interview outcomes, application status, or posting assessments in Career-Aspirations.md.
