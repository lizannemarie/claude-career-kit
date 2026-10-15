---
name: yoodli-interview-roleplay
description: Create copy/paste Yoodli (yoodli.ai) interviewer personas and fill in a Yoodli roleplay form (description, context, personas, rubric) for a behavioral or strategic interview round, grounded in interviewer profiles and transcripts. Use when the user mentions Yoodli personas or roleplay, shares a Yoodli form screenshot, or wants AI practice for a specific interview loop.
---

# Yoodli personas and roleplay

## Step 1: gather evidence
- Interviewer name, title, employer from the LinkedIn PDF or the prep guide; read any `*-interviewer-profile.md` for them.
- For past interviewers, read the transcript or recap for real behavior: questions, probes, tone. Real behavior beats inference.
- The round format the user describes. Do not build technical or domain quizzes unless the user says the round has them.
- The posting or prep guide for context. The user's known answer gaps come from their own notes or `Interview-Log.md` feedback (grep headings for the company; do not read the whole log).

## Step 2: persona form (one per interviewer, labeled copy/paste blocks)
1. **Name** 2. **Job Title** 3. **Company** (optional)
4. **Demeanor**: exactly one of Yoodli's options with a one-line reason: Friendly, Critical, Frightened, Empathetic, Enthusiastic, Analytical, Curious, Assertive, Aggressive, Blunt, Skeptical, Neutral, Casual, Rude. Default toward Friendly, Neutral, Analytical, Curious or Assertive. Use Skeptical or Blunt only with transcript or recommendation support. Avoid Rude, Aggressive, Frightened.
5. **Background**: up to 10 one-line facts (title, scope, prior employers, results, education). Never interview outcomes, feedback, or status.
6. **Persona Behavior**: question style, probes, what they listen for, speaking pattern, likely objections or reframes. Phrase inferred traits as roleplay behavior, not fact.
Keep each block short enough for a single form field.

## Step 3: roleplay form
1. **Description**: one or two plain sentences on what the practice covers.
2. **Context** (instructions to the AI interviewer, second person, under about 250 words): role and company, round format, number of questions, behavioral "tell me about a time" style with follow-ups, what to probe (trade-offs, what the candidate personally did, numbers), how to open and close, stay in character, and JD details if available.
3. **Persona**: which personas, in what order; multi-persona mode on for a back-to-back loop, off for one interviewer.
4. **Rubric**: goals with name, description, weight summing to 100%, replacing the defaults with goals tied to the user's known gaps (for example: state the decision and trade-off early; concrete ordered steps; "I" for own decisions, "we" for team work; one consistent number; bottom line first; welcome a reframe). If the user uses STAR or CLEAR stories (see `story-bank`), add a goal for that structure.

## Rules
- Facts about people come only from material the user supplied. Never invent.
- `humanizer:humanizer` pass on all prose if available (else: no em dashes, no not-X-but-Y, no forced triads, no bold labels inside sentences).
- Persona text goes to Yoodli, not Experience-Context. Schedules and outcomes go in `Interview-Log.md`.
- Deliver as copy/paste blocks in the reply and, if wanted, as `<workspace>/interview-prep/yoodli-<round>-personas.md`.
- Offer to adjust demeanor or rubric weights afterwards.
