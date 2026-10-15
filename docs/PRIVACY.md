# Privacy

**The short version:** the plugin contains only instructions and templates. Everything about you is kept in your own career folder on your computer, plus the services you connect (Airtable, Gmail), and never in this repository.

## What stays local (your career folder, default `~/Documents/ClaudeCareer`)
- `career-kit.config.json`: your criteria, preferences, timezone, email address, Airtable IDs, and tracker URL. It is gitignored in this repo, and Setup adds it to `.gitignore` if your career folder is a git repository.
- Career-Aspirations.md, Experience-Context.md and its archive, Story-Bank.md, Interview-Log.md, and the job-search logs.
- Resumes and cover letters (`.docx` and `.pdf` are gitignored here too).
- `.job-tracker-cache/` (emails waiting to sync to Airtable) and `.career-kit/` (rendered task prompts and agent copies).

## What goes to connected services
- **Airtable:** companies, applications, classified emails (subject, sender, body up to 90,000 characters, date, Gmail link), resume records, and optional interview rows. These go to *your* base.
- **Gmail:** the tasks read job-related threads. They send notification emails *to you, from your own account*, and create thank-you **drafts** that they never send.
- **Artifacts:** the Job Search Tracker page (posting titles, companies, scores, fit notes). Artifacts start private to your account.
- **Claude:** like any Claude session, the content the tasks read is processed by Claude under your account's data settings.

## What never happens
- No passwords or API keys are requested or stored. Connectors are authorized in the Claude app.
- Nothing is posted publicly, and no message is sent to employers or recruiters.
- Interview outcomes, status and posting assessments are never written into your Experience-Context file. They live in the logs and Airtable.

## For contributors
`scripts/check-privacy.sh` fails the build if the repo contains:
- absolute home paths
- real email addresses
- Airtable IDs
- Gmail thread links
- phone numbers
- any term in your local, gitignored `.privacy-denylist` (your name, employers, email)

Run it before every commit.
