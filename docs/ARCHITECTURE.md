# Architecture: efficiency and subagent design

This page explains where career-kit runs work inline and where it hands work to a subagent, why, and what that was measured to cost. The goal is lower token use and a small main context with no loss of quality.

## Rules applied

Split work into a subagent only when at least one of these is true:

- **(a)** the pieces are independent and can run in parallel.
- **(b)** the step is a bulky read whose result fits in a short structured summary.
- **(c)** a cheaper model tier does the job equally well.

Never split small sequential steps. Subagents get file paths and config values, not conversation history, and they return schema-constrained JSON. Each one uses the cheapest model that is good enough. SKILL.md files stay short, and long material lives in `references/`, loaded on demand. Big logs are read with grep or offsets, never whole.

## What we verified (2026-10-15, Claude Code 2.1.x desktop)

| Check | Result |
|---|---|
| Can a **scheduled-task session** spawn subagents with the Agent tool? | **Yes.** A temporary probe task ran with no files and no connectors. It spawned a `model: haiku` subagent in the foreground and got the exact JSON back (54,121 subagent tokens, 4.8 s). The probe was deleted afterwards. |
| Does the `model` override take effect? | The parameter was accepted without error. The tool result does not say which model actually ran, so the override itself is unconfirmed. |
| Can a subagent see MCP connectors? | **Yes**, in an interactive session: Gmail, Airtable, job-board MCPs, WebFetch, WebSearch, Chrome. Not separately probed inside a scheduled-task session, so the task templates keep an **inline fallback** (see below). |
| Fixed cost of one subagent | **≈ 54k tokens** before any work (system prompt and tool definitions, mostly served from the prompt cache). This is the number that decides whether a split pays off. |

## Measurements on fixtures

Every run used synthetic fixtures in `tests/fixtures/` (fictional people and companies). "Total" is the Agent tool's `subagent_tokens`. "Work" is total minus the ≈54k fixed overhead. Inline baselines ran on the session's default (strongest) model.

| Flow | Variant | Total tokens | Work tokens | Wall time | Quality |
|---|---|---|---|---|---|
| Email classify, 10 threads | inline (default model) | 64.5k | ~10k | 8.2 s | 10/10 labels correct |
| | 1 × Haiku classifier | 65.5k | ~11k | 10.8 s | 10/10 labels correct; identical extractions except one role title left null (the expected answer) |
| Job-board scoring, 6 postings | inline (default model) | 69.4k | ~15k | 44.0 s | P1 95→94, P3 89→82; P2/P4/P5 screened; P6 excluded |
| | 2 × Haiku scouts (parallel) | 67.5k + 66.3k | ~25k | 16.7 s | identical keep/screen/exclude decisions; first-pass P1 88, P3 88 |
| | then 2 × Sonnet verifiers (parallel) | 66.2k + 65.0k | ~23k | 13.9 s | final P1 96 (inline 94), P3 81 (inline 82); same gap labels, but P1 was more lenient on dated SQL evidence |
| | **split total** | 265k | ~48k | **30.6 s** (vs 44.0 s) | equivalent |
| Interviewer research, 17 KB bundle | inline profile (default model) | 71.2k | ~17k | 26.4 s | full profile |
| | Haiku digest → JSON | 71.4k | ~17k | 17.7 s | 2.5 KB digest (≈650 tokens) instead of 17 KB (≈4.3k) entering the drafting context; found the same duplicate-recommendation issue |
| screened-postings lookup | read whole 145 KB file | ≈36k tokens | | | |
| | grep per candidate (URL / job id / company+title) | ≈40–160 tokens per lookup | | | |

### What the numbers say

1. **On small fixtures a split always costs more in total tokens.** Each extra subagent adds ≈54k of fixed context, and the fixture work is only 10–20k. Overhead tokens are mostly cache reads, which are much cheaper than fresh input, but they are not free.
2. **Splitting pays off when the bulk is large.** The live job-board run opens 20–60 posting pages a day (the source logs show "50+ screened"). At roughly 3–5k tokens per page, that is 60–300k tokens. Inline, all of it piles into one context that is re-read on every later turn and risks compaction. Split, each scout absorbs its own pages and the parent gets about 150 tokens of JSON per posting. That benefit is extrapolated from page sizes, not measured end to end on a live run.
3. **Parallel fan-out cut wall time by about 30%** (44 s → 31 s) with identical decisions.
4. **Haiku matched the strongest model on classification and extraction** (10/10). That makes it the right tier for classification, scouting, and digesting.
5. **Sonnet was adequate but slightly less skeptical than the inline strongest model** (+2 on P1, mostly by fully crediting SQL experience that was 6 years old). The verifier prompt therefore has an explicit **recency rule**: evidence older than 5 years caps at 75% unless the posting only asks for familiarity. The verifier stays on Sonnet. Users who want maximum skepticism can set `models.verifier` to `opus` in config.
6. **grep beats reading screened-postings.md** by two to three orders of magnitude, so the logs are never read whole.

## Decision table

| Skill / task | Inline or split | Why | Model tier | Estimated token effect |
|---|---|---|---|---|
| **job-board-check** (scheduled) | **Split.** Stage 1: one `posting-scout` per source batch (Indeed/job-board MCP; Greenhouse aggregator; every-run company feeds; rotation; discovery). Stage 2: one `posting-verifier` per posting with first pass ≥ 70. The parent keeps dedup (grep), logging, tracker republish, and notifications. | (a) independent sources run in parallel; (b) bulky page fetches reduce to compact JSON; (c) Haiku is enough for the first pass | scouts: Haiku; verifier: Sonnet (configurable) | Parent context drops from roughly 60–300k of page text to under 10k of JSON. Total tokens rise ≈54k per subagent but shift to cheaper tiers. About 30% faster. **Inline fallback** when the Agent tool or connectors are missing in the task session. |
| **email-scrub** (scheduled) | **Split only when ≥ 10 threads need fetching** (at least one full batch). Each `email-classifier` batch of about 10 does get_thread (PLAIN_TEXT, then FULL_CONTENT/HTML fallback), cleans and caps the body, classifies, **appends entries to the cache file**, and returns compact JSON without bodies. The parent does Airtable upserts from the cache, then STEP 4b and the summary. Under 10 threads it runs inline. | (b) raw thread fetches with HTML fallbacks are bulky; (c) Haiku classified 10/10. Below one batch, the 54k overhead outweighs the saving. | Haiku | Raw/HTML fetch noise and classification reasoning stay out of the parent. Bodies still pass through the parent once at Airtable-write time, as before, so the saving is moderate. Cache-before-write ordering is kept: classifiers append before the parent writes anything. |
| **resume-ats-eval** | **Inline** | The posting text is needed again for tailoring, the re-score, and the cover letter, so a rubric-builder subagent would re-read it and add ≈54k overhead for no context saving. Steps are sequential and interactive. | Session model | No split. Savings come from progressive disclosure (rubric, ledger, ATS signals, logging, and calibration live in `references/`) and a targeted Experience-Context digest instead of a full read. |
| **career-focus-interview** | **Inline** | Interactive, one question at a time, stateful | Session model | None |
| **experience-context-builder** | **Inline.** A subagent is used only to **merge or summarize an archive over about 50 KB** into a section map before editing. | Interactive and stateful; (b) applies only to very large archives | Haiku for the map | Avoids loading a 100 KB+ archive whole; edits target anchored sections. |
| **interviewer-profile** | **Split the research** when sources total over about 15k tokens (several pages or PDFs). Drafting stays inline. | (b) a 17 KB bundle became a 2.5 KB digest with no lost themes | Haiku digest | ≈ −3.7k tokens per profile in the drafting context, more with real PDFs; +54k overhead, mostly cached. Small inputs stay inline. |
| **cover-letter-writer** | **Split the research** (posting plus company pages) when more than one page must be fetched. Drafting, follow-up questions, and the Humanizer pass stay inline. | (b) same as interviewer research | Haiku digest | Same profile as above |
| **yoodli-interview-roleplay** | Inline | Short, generative, uses the interviewer-profile output | Session model | None |
| **story-bank** | Inline | Targeted reads of the Story Index and archive anchors | Session model | Never loads the archive whole |
| **interview-prep-reminders** (scheduled) | Inline | A few Airtable rows and drafts; nothing bulky | Task model | None |
| **career-setup** | Inline orchestrator | Interactive; the Airtable build is strictly sequential (rollups cannot be edited later). `scripts/airtable-plan.py` precomputes payloads and the read-back diff deterministically, so the model never hand-derives field order. | Session model | The deterministic scripts replace long in-context reasoning over the 24 KB schema. |

## Shipped subagents (`agents/`)

| Agent | Model | Input | Output schema |
|---|---|---|---|
| `posting-scout` | haiku | criteria (from config), source batch, workspace paths for grep | `{batch, tried, postings:[{title, company, location, url, pay, setup, firstPass, provisional, status, reason}], newRotationCompanies:[], errors:[]}` |
| `posting-verifier` | sonnet | one posting URL or text, base-resume path, Experience-Context path | `{url, score, hardFilterRisk, riskDriver, rows:[…], fitNote}` |
| `email-classifier` | haiku | thread ids, cache path, enum | `[{threadId, emailContext, companyName, roleTitle, jobRefId, confidence}]` (bodies go to the cache file, not the reply) |
| `web-researcher` | haiku | URLs or local files, digest schema | the JSON digest the caller asks for |

Scheduled-task prompts cannot assume the plugin is loaded in the task session. Setup therefore copies these agent definitions into `<workspace>/.career-kit/agents/`. The task tells the model to use `career-kit:<agent>` when it is available, and otherwise to spawn `general-purpose` with the `model` override and the instructions from that file.

## Inline fallback (scheduled tasks)

Each task checks for the Agent tool at the start. If the tool is missing, or a subagent reports that it cannot reach a required connector, the task runs the same steps inline in the stated order. That inline path is the proven source logic. It records `mode=inline` in `job-search-runs.md` so the user can see which path ran.

## Re-running the measurements

`tests/fixtures/` holds the fixtures. `python3 tests/fixtures/gen_screened.py` regenerates the 145 KB screened-postings fixture, which is gitignored because of its size. Prompts used for each variant are in `tests/fixtures/README.md`.
