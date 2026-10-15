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
| Fixed cost of one subagent | **≈ 54k tokens** for an *unscoped* subagent (`general-purpose`), and **≈ 8k** for one limited to two tools. See "Where the subagent overhead comes from" below. |

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

1. **On small fixtures a split always costs more in total tokens.** Each extra *unscoped* subagent adds ≈54k of fixed context (≈8–15k once scoped, see below), and the fixture work is only 10–20k. Overhead tokens are mostly cache reads, which are much cheaper than fresh input, but they are not free.
2. **Splitting pays off when the bulk is large.** The live job-board run opens 20–60 posting pages a day (the source logs show "50+ screened"). At roughly 3–5k tokens per page, that is 60–300k tokens. Inline, all of it piles into one context that is re-read on every later turn and risks compaction. Split, each scout absorbs its own pages and the parent gets about 150 tokens of JSON per posting. That benefit is extrapolated from page sizes, not measured end to end on a live run.
3. **Parallel fan-out cut wall time by about 30%** (44 s → 31 s) with identical decisions.
4. **Haiku matched the strongest model on classification and extraction** (10/10). That makes it the right tier for classification, scouting, and digesting.
5. **Sonnet was adequate but slightly less skeptical than the inline strongest model** (+2 on P1, mostly by fully crediting SQL experience that was 6 years old). The verifier prompt therefore has an explicit **recency rule**: evidence older than 5 years caps at 75% unless the posting only asks for familiarity. The verifier stays on Sonnet. Users who want maximum skepticism can set `models.verifier` to `opus` in config.
6. **grep beats reading screened-postings.md** by two to three orders of magnitude, so the logs are never read whole.

## Where the subagent overhead comes from (and how the kit cuts it)

The same trivial task ("reply OK", Haiku, no tool calls) was run through built-in agent types that load different toolsets, on 2026-10-15, in a session with about 15 MCP connectors attached:

| Agent type | Tools loaded | Tokens before any work |
|---|---|---|
| `general-purpose` | every built-in tool plus every connected MCP server's tools | **54.7k** |
| `claude-code-guide` | Bash, Read, WebFetch, WebSearch, plus a long system prompt | 24.0k |
| `statusline-setup` | Read, Edit | **7.8k** |

**So the 54k is not inherent to subagents.** About 85% of it is tool definitions. A subagent with no `tools:` list inherits every connector in the session (design tools, meeting recorders, docs search, browser and desktop control, and so on). Whether that is excessive depends on the setup: it is expected for an unscoped agent in a connector-heavy session, and avoidable for career-kit, whose subagents need two to eight tools each. Mitigations, in order of impact:

1. **Scope tools (shipped).** `posting-verifier` (Read, Grep, Glob, WebFetch) and `web-researcher` (Read, Grep, Glob, WebFetch, WebSearch) carry `tools:` lists in the plugin. `posting-scout` and `email-classifier` need connector tools whose exact names differ per account, so `/career-setup` writes scoped user-level copies (`~/.claude/agents/career-kit-*.md`) with the resolved names. The scheduled tasks prefer those copies and fall back to the unscoped plugin agents, then to `general-purpose`. Expected overhead: ≈8–15k per subagent. This is an estimate from the probe above; confirm it with the eval below.
2. **Prompt caching already discounts the overhead.** The fixed context is identical across spawns, so after the first spawn it is mostly cache reads, which are billed at a fraction of fresh input. Raw token counts overstate the cost. That is why the eval compares dollars (`total_cost_usd`), not tokens.
3. **Fewer, larger batches.** Overhead is paid per spawn, so fan out per source (5 scouts), not per company. A possible next step is to verify postings in groups of 2–3 per verifier instead of one each; measure the quality impact first with the eval.
4. **Do bulk fetching without a model (shipped for source C).** `scripts/fetch-feeds.py` (standard library only, deterministic) reads the Greenhouse, Lever and Ashby feed URLs under "Every-run companies" in company-notes.md, fetches them, and keeps only postings that match a `role_targets` title phrase, are not in `excluded_categories` (title, department or team), are remote in `remote_country` or list the home metro or an alias, were posted on or after the cutoff, and are not already in job-search-log.md or screened-postings.md (URL, whole-word job id, or title + company). It prints compact JSON with a 1,500-character plain-text excerpt per candidate. The job-board check runs it first and hands only the survivors (plus companies with no feed, and feeds that errored) to the source-C scout, and skips that scout when nothing survives. If the script is missing or fails, source C uses the old path, where the scout fetches the feeds itself. In a live check on three public boards (2026-10-15), about 12.6 MB of raw feed JSON (812 postings) became 17 candidates in about 33 KB of output. Setup copies the script to `<workspace>/.career-kit/scripts/`. Test it offline with `python3 scripts/fetch-feeds.py --offline --check`, which reads the synthetic fixture in `tests/fixtures/feeds/` and compares the result to its `expected` block.
5. **Thresholds, not always-split.** Below a measured size, run inline. `split_thresholds` in config holds the numbers, and the email scrub already reads `email_min_threads`.
6. **Fewer connectors per task session.** Overhead also scales with what the session has attached. Disconnecting connectors the user doesn't need shrinks both inline and unscoped runs.

### The split-decision eval

`evals/split-decision/run_eval.py` settles inline vs split with measured dollar cost. It runs each flow at several workload sizes N in three variants through headless Claude Code:
- `inline`
- `split-scoped`: subagents defined with `tools:` lists, as shipped
- `split-unscoped`: subagents that inherit every tool, as the original measurement did

For each run it records `total_cost_usd`, tokens (fresh, cache read, cache write, output), wall time, and quality: email label accuracy against ground truth, and job-board keep/screen/exclude accuracy plus mean score drift against the inline run. Its report gives the **break-even N** per flow, the smallest N where split-scoped costs no more than inline with quality within 95%, and prints the `split_thresholds` block to paste into config.

```bash
python3 evals/split-decision/run_eval.py --dry-run                     # free: show the plan
python3 evals/split-decision/run_eval.py --sizes 5 10 20 40            # ~24 headless runs
python3 evals/split-decision/run_eval.py --with-mcp --sizes 10 20      # include your connectors (realistic overhead)
```

### Results (2026-10-15)

The sweep ran on a Pro plan, with the 5-hour usage meter going from 38% to 52%. The parent and inline runs used Sonnet; subagents used their shipped models (Haiku scouts and classifier, Sonnet verifier). Every run was 100% correct against ground truth.

| Flow | N | inline | split, scoped tools | split, all tools |
|---|---|---|---|---|
| email | 10 | $0.048 · 13 s | $0.109 · 18 s | $0.273 · 38 s |
| email | 30 | $0.063 · 14 s | $0.177 · 40 s | $0.446 · 64 s |
| job board | 6 | $0.087 · 52 s | $0.375 · 200 s (4 subagents) | not run |
| job board | 18 | $0.132 · 60 s | $0.872 · 214 s (11 subagents) | not run |

What the results show:
- **No break-even in the tested range.** Inline cost grows slowly with N because the work stays in one cached context. Split cost grows with the number of subagents, since each pays its own overhead and cache writes.
- **Scoping tools cuts the split cost by about 60%** (email: $0.273 → $0.109 and $0.446 → $0.177) but does not close the gap.
- **Split was slower too.** It was slower at every size, and much slower on the job board, because verifiers start only after the scouts finish.
- **Quality is the same.** Final scores differed by 6–8 points on average between the variants, with the same keep/screen/exclude decisions.

**Decision:** both flows now run **inline by default**. `split_thresholds` is set just above the largest tested size (email 31 threads, job board 19 postings), so fan-out happens only on runs larger than anything measured, purely to protect the context.

**Caveat:** the fixtures are small and local. Postings run about 150 words, emails about 400 characters, and nothing is fetched from the web. Real postings are 3–5k tokens each and real emails can be far longer, which favors splitting more than this test does. The prefetch script (`scripts/fetch-feeds.py`) now drops most feed content before any model reads it, which shrinks that gap further. To test real sizes, re-run with larger fixtures or `--with-mcp` against your own data.

## Decision table

| Skill / task | Inline or split | Why | Model tier | Estimated token effect |
|---|---|---|---|---|
| **job-board-check** (scheduled) | **Inline by default** (measured: 4–6.6× cheaper and 3.5–4× faster at 6–18 postings, same decisions). Fans out to `posting-scout` / `posting-verifier` only at 19+ postings to open, to protect the context on unusually large runs. Source C is prefetched and filtered by `scripts/fetch-feeds.py` before any model reads it. | Split overhead exceeded the bulk saving at every measured size; the script removes the bulk without a model | parent: task model; scouts Haiku, verifier Sonnet when split | Measured; see Results. |
| **email-scrub** (scheduled) | **Inline by default** (measured: 2.3–2.8× cheaper at 10–30 threads, same accuracy). Fans out to `email-classifier` batches only at 31+ threads to fetch. Cache-before-write ordering is unchanged. | Split overhead exceeded the saving at every measured size | Haiku classifier when split | Measured; see Results. |
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
