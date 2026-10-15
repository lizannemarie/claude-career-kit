# claude-career-kit

An AI-assisted job search toolkit for **Claude Code** and **Cowork**. It interviews you about what you want and what you've done, then runs the following for you:

- A **daily job-board check** that finds postings, scores each one against your real experience, and posts the best to a tracker page with **Apply** and **Tailor resume** buttons.
- A **daily email scrub** that reads job-application emails from Gmail and keeps an Airtable tracker up to date: applications, current state, and a reporting dashboard.
- **Interview reminders** that flag missing prep before each interview and draft a thank-you note the day after.
- On-demand skills for **ATS-style resume scoring and tailoring**, **cover letters**, **interviewer profiles**, **Yoodli roleplay setup**, and a **STAR + CLEAR story bank**.

Your personal files stay on your computer. See [docs/PRIVACY.md](docs/PRIVACY.md).

## Prerequisites
- The Claude desktop app (Code tab or Cowork). Scheduled tasks and the tracker page need it.
- An **Airtable** account, with the Airtable connector added in Claude → Settings → Connectors.
- **Gmail**, with the Gmail connector added.
- Optional job-board connectors: Indeed, Dice, ZipRecruiter, Snagajob, RankedIn. Without them the check uses web search and company career pages.
- Optional but recommended: the **Humanizer** skill (a third-party skill, not bundled):
  ```
  /plugin marketplace add blader/humanizer
  /plugin install humanizer@humanizer
  ```
- Optional: the Claude in Chrome extension, for JavaScript-heavy job sites and Indeed link resolution.

## 5-minute quickstart
1. Install the plugin:
   ```
   /plugin marketplace add lizannemarie/claude-career-kit
   /plugin install career-kit@claude-career-kit
   ```
2. Run `/career-setup`. Setup checks your connectors and asks where your career folder should live (default `~/Documents/ClaudeCareer`). Then it walks you through the following, saving progress after each step so you can stop and resume any time:
   - a career-focus interview (what you want)
   - an experience interview (what you've done)
   - base resumes
   - building the Airtable base and dashboard
   - publishing your tracker page
   - installing the three scheduled tasks
   - a smoke test
3. Try it on a posting: `/resume-ats-eval <job posting URL>`.
4. Check health any time with `/career-status`.

Commands and skills may also appear namespaced, for example `/career-kit:career-setup` or `/career-kit:resume-ats-eval`.

The interviews take the longest (about 20–40 minutes). Everything after that is mostly automatic.

## What the scheduled tasks do
| Task | Default time | What it does | Connectors |
|---|---|---|---|
| Daily job board check | 08:30 | Searches job boards, a Greenhouse aggregator, your every-run companies, a rotating set of companies, and 1–2 new industries. Opens each real posting, filters by location and salary, and scores it. Postings scoring 70 or more get a second, skeptical score. Qualifying postings go to the tracker, and you get an email and push when any are new. | Web, Chrome (optional), job boards (optional), Artifacts, Gmail |
| Job application email scrub | 07:00 | Finds job-related Gmail threads, classifies each one (Application Received, Recruiter Contact, Formal Interview, Offer Sent, rejections, and so on), and upserts companies, applications and emails into Airtable. It also refreshes "Days in Current State" for the dashboard's Stale tile. If Airtable is unreachable, it caches what it found and syncs on the next run. | Gmail, Airtable |
| Interview prep and follow-up reminders | 07:00 | Before an interview, lists the prep you have and what's missing. The day after, drafts a thank-you note in Gmail. It never sends anything. | Airtable, Gmail |

Scheduled tasks run on your computer while the Claude app is open. A task that comes due while the app is closed runs when you next open it.

## Cost and usage
The scheduled tasks use your Claude plan's usage every day. The job-board check is the heaviest because it opens many web pages. To keep usage down, a script fetches and filters company job feeds before any model reads them, it runs inline (an eval found that cheaper than subagents at typical sizes), and it grep-searches large logs instead of reading them in full. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for measurements. You can change times, pause a task in the app's Scheduled section, or lower the number of rotation companies in the config.

## Commands and skills
| Command / skill | Use it to |
|---|---|
| `/career-setup` | set up, resume, or redo one phase |
| `/career-status` | see setup progress, task health, recent runs, pipeline counts |
| `/career-update-context` | add or fix career facts, stories, or preferences |
| `resume-ats-eval` | score a resume against a posting with visible math and hard-filter risk, then tailor it |
| `cover-letter-writer` | write a one-page letter grounded in your real experience |
| `interviewer-profile` | prep for a specific interviewer from their LinkedIn and recommendations |
| `yoodli-interview-roleplay` | build Yoodli personas and a roleplay form for practice |
| `story-bank` | keep STAR and CLEAR versions of your stories and map them to a role |
| `career-focus-interview`, `experience-context-builder` | the setup interviews, re-runnable any time |

## Docs
- [docs/PRIVACY.md](docs/PRIVACY.md): what stays local and what goes where
- [docs/CUSTOMIZING.md](docs/CUSTOMIZING.md): change criteria, schedules, models, and templates
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): common problems and fixes
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): what runs inline vs in subagents, and why
- [airtable/README.md](airtable/README.md): the tracker base and dashboard

## Contributing
Run the checks before opening a pull request:
```
python3 scripts/validate.py
scripts/check-privacy.sh
```

MIT licensed.
