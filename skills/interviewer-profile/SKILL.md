---
name: interviewer-profile
description: Build an interviewer profile (background, how others describe them, what they value, expected interview style, how to show up, questions to ask) from the interviewer's LinkedIn profile PDF, recommendations they wrote and received, public posts, or past interview transcripts. Use when the user shares material about an upcoming or past interviewer and wants prep, or asks to "profile" an interviewer.
---

# Interviewer profile

## Inputs
Look for, or ask for: the LinkedIn profile PDF; recommendations the person wrote for others (the best evidence of what they value); recommendations others wrote about them; recent public posts or comments; for a past interviewer, the transcript or recap. Build from what exists and say what is missing.

## Research step (keeps the main context small)
If the sources total more than about 15k tokens (several PDFs, long recommendation exports, transcripts, several web pages), hand the reading to a research subagent: `career-kit:web-researcher` (model haiku), or `general-purpose` with model haiku and the instructions in this plugin's `agents/web-researcher.md`. Pass only the file paths or URLs and this schema:
`{name, currentRole, history:[{org,title,years}], education, selfDescription, recentPublicThemes[], recommendationThemes:[{theme,count,example}], valuesWrittenAboutOthers[], likelyQuestionStyle[], dataCaveats[], sources:[{type,note}]}`.
Small inputs: read them inline. Drafting always happens here, not in the subagent.

## Output: one markdown file per interviewer
`<workspace>/interview-prep/<first-last>-interviewer-profile.md` (create the folder if needed). Sections in order:
1. `# Interviewer Profile: <Name>` and an italic line with sources and counts.
2. **Data caveat** (quoted block): sample size, source dates, what the data cannot show. Call out old or tiny samples plainly, and duplicated or templated recommendations.
3. **Background**: facts from the PDF only.
4. **How others describe them**: short bullets, each grounded in a recommendation, with counts.
5. **What they value in others**: ranked by emphasis; one "Key insight" line only if the evidence supports it.
6. **Expected interview style**: likely question types, tone, probes. Label as inferred.
7. **How to show up**: which of the user's stories to lead with (by Story-Bank name/id, read from the full archive section), how to structure answers, what to avoid. Keep the user's real scope limits.
8. **Comparison table** when profiling two or more interviewers in one loop: center of gravity, what wins them over, leadership lens, likely probe; then the common thread.
9. **Questions to ask them**: three or four, tied to their scope and the round format.

## Rules
- Separate verified facts from inferences, and label the inferences. No trait without at least one supporting source.
- Work style and values only. Never infer protected attributes, health, family, or personality types.
- Match prep to the round format the user describes.
- Never invent stories, numbers, or outcomes.
- Run the prose through `humanizer:humanizer` if available (else: no em dashes, no not-X-but-Y contrasts, no forced triads, no bold labels inside sentences).
- Logistics, schedules, outcomes, and feedback go in `Interview-Log.md` (and Airtable `fact_interview` if enabled), never in Experience-Context.

## After building
Offer to fold the profile into the round's prep guide, and to run `yoodli-interview-roleplay` for practice. Note any likely question that has no matching story.
