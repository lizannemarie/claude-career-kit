# Company Notes

Used by the daily job-board check. Two parts: how to read each company's job listings reliably, and the rotation list of companies to check on a schedule. Scouts grep this file by company name; keep one `###` section per company.

## Every-run companies

Checked on every run (home-metro pass + remote pass). For each: the careers URL, the JSON feed if one exists, query parameters that work, and the ATS vendor if known.

### Example Company
- Careers: https://careers.example.com/jobs
- JSON feed: https://boards-api.greenhouse.io/v1/boards/examplecompany/jobs?content=true
- Filters that work: `?location=Remote`
- ATS: Greenhouse (user-confirmed)
- Last checked: never

## General fetch tips
- If a posting page looks empty, check the page source before giving up. Most job sites (Workday, Greenhouse, Lever, Ashby, iCIMS) embed the full posting as `ld+json` JobPosting data or `og:` meta tags.
- A cut-off page is a size problem, not a blocked site. Try the company's JSON feed or a different URL format before marking it unreadable.
- Indeed: never keep `to.indeed.com` shortlinks; resolve to `https://www.indeed.com/viewjob?jk=<jobkey>`.
- No unofficial LinkedIn scraping.
- Record new workarounds here when you find one, with the date.

## Rotation list

About {{ROTATION_BATCH_SIZE}} per run, oldest "last checked" first. Update the date for every company attempted, even if the site couldn't be read (put the reason in the note). Replace companies that stay unreadable.

Format: `Company | careers URL | last checked YYYY-MM-DD or blank | note`

## Run notes

Dated notes from runs (new feeds found, sites that changed). Newest first.

## Excluded

Role categories never surfaced or recorded (also in career-kit.config.json → search.excluded_categories):
- {{EXCLUDED_CATEGORIES}}
