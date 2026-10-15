# Screened Postings

Postings the daily job-board check opened and ruled out, so future runs skip them instead of re-checking. Qualifying postings go in job-search-log.md, not here.

Format: `date | job title | company | location | URL | reason`

- One line per posting. Reasons are short and specific: "location: <city>", "salary max $X", "score 42 - <domain>", "second-pass score 51", "closed".
- Before scoring any candidate, check its URL (and company + title) against this file and job-search-log.md. Skip any match.
- This file grows large. Search it with grep; never read it top to bottom.

## Screened

