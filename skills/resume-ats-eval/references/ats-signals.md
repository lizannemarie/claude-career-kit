# Identifying the ATS / AI-screening tool

Read this when you need to figure out what system is standing between the resume and a human recruiter. Knowing the specific vendor is a nice-to-have, not a blocker — if you can't tell, say so and fall back to the generic keyword/semantic-matching assumption described in SKILL.md step 2.

## Signal 1: the posting URL

| Domain / URL pattern | Platform | Notes |
|---|---|---|
| `*.greenhouse.io`, `boards.greenhouse.io`, `job-boards.greenhouse.io`, or `gh_jid=` param on a custom careers domain | Greenhouse | Public JSON API available — see below. Many postings disclose "Talent Matching" (Greenhouse's AI resume-to-requirement matcher) directly in the page footer/fine print. |
| `*.myworkdayjobs.com` | Workday | Uses "Skills Cloud" for skills extraction/matching. No public JSON API; render with browser tools. |
| `jobs.lever.co`, `*.lever.co` | Lever | Has a public JSON API: `https://api.lever.co/v0/postings/{company}?mode=json`. Lever's AI features are less consistently disclosed than Greenhouse's. |
| `*.icims.com` | iCIMS | Has AI-assisted screening features (iCIMS AI); postings vary in how much they disclose. |
| `*.smartrecruiters.com` | SmartRecruiters | Has a public API pattern (`api.smartrecruiters.com/v1/companies/{company}/postings/{id}`). |
| `jobs.ashbyhq.com` | Ashby | Modern ATS, growing AI-matching features; smaller/startup-heavy customer base. |
| `*.taleo.net` | Oracle Taleo | Older enterprise ATS, keyword-matching-heavy by reputation; no modern public API. |
| `*.successfactors.com`, `career*.sap.com` | SAP SuccessFactors | Enterprise ATS, common at large legacy companies. |
| `jobs.jobvite.com` | Jobvite | Has AI screening add-ons. |
| LinkedIn "Easy Apply" postings | LinkedIn | LinkedIn itself surfaces a "Skills match" indicator to the poster; the underlying company ATS behind Easy Apply may still be one of the above. |

## Signal 2: on-page AI disclosure

Increasingly common due to state (e.g. NYC Local Law 144, Illinois, Colorado) and EU AI Act transparency requirements. Look near the bottom of the posting for language like "AI in Hiring," "automated employment decision tool," "Talent Matching," or a link to an AI opt-out request. When present, this is the single best evidence you'll get — quote it (briefly) to the user so they know it's not speculation, and note any specifics it gives about how matching works (e.g. Greenhouse's disclosure explicitly says recruiters set the weighting per requirement, which is exactly what step 4's rubric is a proxy for).

## Company-level ATS knowledge, independent of URL domain

Some companies run in-house or vendor career portals (for example `careers.<company>.com` or `jobs.<company>.com`) that don't map to a Greenhouse/Workday/Lever URL pattern but still sit on a known backend.

**Eightfold.ai** is a widely used AI-native talent-intelligence platform at large employers. Its screening is deep-learning/skills-graph matching against a broad semantic skills taxonomy, not literal keyword overlap. When the posting is from a company known or suspected to use Eightfold, say so, weight adjacent/transferable-skill language more generously than pure keyword overlap, and note the assumption in the scoring writeup.

When the user tells you which ATS/vendor an employer actually uses, treat that as ground truth for that employer. Record it under the company's section in `company-notes.md` ("ATS: <vendor> (user-confirmed)") so later runs reuse it instead of re-guessing.

## Signal 3: company size / maturity as a weak prior

If neither of the above resolves it: large, established companies (5,000+ employees) are likely on Workday, SuccessFactors, or Taleo. Mid-size tech companies commonly run Greenhouse or Lever. Startups and smaller tech companies increasingly use Ashby or Greenhouse. This is a weak prior only — state it as such, don't present it as a finding.

## Fetching the posting content

- Try `web_fetch` on the posting URL first.
- If the response is a near-empty shell ("enable JavaScript," a loading spinner, boilerplate nav with no real body text), the page is client-rendered — don't try to extract anything from that shell, and don't retry `web_fetch` on the same URL expecting a different result.
- For Greenhouse: construct `https://boards-api.greenhouse.io/v1/boards/{board-token}/jobs/{job-id}` and fetch that instead. The board token is typically the company's slug (visible in the careers domain or in `gh_jid`/`for=` params); the job id is the number in the URL path or the `gh_jid` query param. This returns full JSON including the description HTML and, often, the `ai_disclaimer` field verbatim — check for that field specifically, it's a direct quote of the AI-screening disclosure when one exists.
- For Lever: try `https://api.lever.co/v0/postings/{company}?mode=json` and find the matching posting by title/id.
- Otherwise, fall back to Claude in Chrome (`navigate` + `get_page_text`) to render the page and read the text directly.
