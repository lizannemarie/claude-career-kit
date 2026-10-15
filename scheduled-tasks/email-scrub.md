---
task_id: career-kit-email-scrub
title: Job application email scrub
default_cron: "0 7 * * *"
connectors: [Gmail, Airtable]
---
Run fully self-contained. Ask nothing. The user's Gmail address: {{USER_GMAIL}}. Workspace: {{WORKSPACE}}.

AIRTABLE base "Job Application Tracker" ({{AT_BASE_ID}}). Tables/fields (IDs from setup):
- dim_Company {{AT_TBL_COMPANY}}: Name {{AT_FLD_COMPANY_NAME}}
- dim_Application {{AT_TBL_APPLICATION}}: Identifier {{AT_FLD_APP_IDENTIFIER}}, Job Title {{AT_FLD_APP_TITLE}}, Company (link) {{AT_FLD_APP_COMPANY}}, Current State {{AT_FLD_APP_CURRENT_STATE}}, Latest Date {{AT_FLD_APP_LATEST_DATE}}, Days in Current State {{AT_FLD_APP_DAYS_IN_STATE}}
- fact_email {{AT_TBL_EMAIL}}: Name {{AT_FLD_EMAIL_NAME}}, Email Body {{AT_FLD_EMAIL_BODY}}, Sender {{AT_FLD_EMAIL_SENDER}}, Email Context {{AT_FLD_EMAIL_CONTEXT}} (single select), Received {{AT_FLD_EMAIL_RECEIVED}}, Application (link) {{AT_FLD_EMAIL_APPLICATION}}, Gmail Deeplink {{AT_FLD_EMAIL_DEEPLINK}}
Use the Airtable MCP; Gmail MCP get_thread with messageFormat PLAIN_TEXT (retry FULL_CONTENT + HTML->text if empty). Chunk writes to 50.

CACHE: {{WORKSPACE}}/{{CACHE_DIR}}/pending-fact-emails.json. Entry: {threadId, subject, sender, receivedIso, emailContext, companyName, roleTitle, jobRefId|null, emailBody, deeplink "https://mail.google.com/mail/u/0/#all/<threadId>"}. Last-run timestamp: {{WORKSPACE}}/{{CACHE_DIR}}/last-run.json.

STEP 0 Resume the cache and check Airtable connectivity (list_tables_for_base). On an auth error retry once; if still failing, leave the cache untouched, skip the Gmail scan, and report "Airtable connection failed (looks like an expired/revoked authorization) — reauthorize the Airtable connector... N records cached and will sync automatically." Other errors: report and stop. If OK and the cache is non-empty: push via STEP 4, clear on success, continue.

STEP 1 Window. Build the date clause FIRST, then the query:
- Read `lastRunIso` from {{WORKSPACE}}/{{CACHE_DIR}}/last-run.json.
- If it exists: START = the calendar date of lastRunIso in {{USER_TIMEZONE}} minus {{SCRUB_LOOKBACK_DAYS}} day(s), written as YYYY/MM/DD with real numbers. DATE_CLAUSE = "after:" + START. Example: lastRunIso 2026-10-15T07:04:00-05:00 with a 1-day lookback gives `after:2026/10/14`.
- If it does not exist (first run) or cannot be parsed: DATE_CLAUSE = "newer_than:{{SCRUB_FIRST_RUN_WINDOW}}" and there is NO after: clause.
- Never send the literal text "YYYY/MM/DD", and never send both after: and newer_than:.
Gmail search: in:anywhere <DATE_CLAUSE> (subject:(applying OR application OR interview OR offer OR "interest in" OR recruiter) OR "thank you for applying" OR "your application" OR "thank you for your interest" OR recruiter OR "talent acquisition" OR label:-job-hunt-) includeTrash:true; pageSize 50, page through all. Keep the exact query string for the STEP 5 summary.

STEP 2 Dedup: don't list all of fact_email. Per threadId get the newest message timestamp; if a fact_email record's Gmail Deeplink contains the threadId (filterByFormula FIND on the deeplink field) and Gmail has no newer message, skip; if newer, reprocess to refresh. Include unpushed cache entries.

STEP 3 Fetch + classify in batches of 10, using the most recent message not sent by {{USER_GMAIL}}. Keep raw text (no HTML/tracking boilerplate), cap 90,000 chars + "[truncated]"; fallback text "(message body unavailable — this Gmail thread could not be retrieved)". Company from explicit patterns else sender domain (never ATS/platform domains). Role from "Job Title:/Role:/Position:" etc. Job Ref ID from Req/Job/App/JR-/R-#### patterns. Email Context: exactly one of Application Received, Automated/ Survey, Recruiter Contact, Formal Interview, Offer Sent, Offer Accept, Offer Reject, Not Job App Related, Application Rejected, Interview Rejected. Append each classified batch to the cache BEFORE any Airtable write.
- Mode: if {{SPLIT_MIN_EMAIL_THREADS}} or more threads need fetching and the Agent tool is available, spawn one classifier per batch of ~10 (in parallel): `career-kit-email-classifier` (tool-scoped copy from Setup) if it exists, else `career-kit:email-classifier`, else `general-purpose` with model `{{MODEL_CLASSIFIER}}` and {{WORKSPACE}}/{{KIT_RUNTIME_DIR}}/agents/email-classifier.md. Give each only its threadIds, {{USER_GMAIL}}, and its own batch file {{WORKSPACE}}/{{CACHE_DIR}}/batch-<n>.json. Each writes its entries (with bodies) to its batch file and returns compact JSON without bodies. When all batches return, merge the batch files into pending-fact-emails.json, then delete the batch files.
- Otherwise (fewer than {{SPLIT_MIN_EMAIL_THREADS}} threads, no Agent tool, or a classifier cannot reach Gmail): do STEP 3 inline with the same rules.

STEP 4 Upsert, reading entries from the cache: company (case-insensitive search, create if missing) -> application (search by company, reuse by title/ref id, else create Identifier "auto::<company-slug>::<role-slug-or-'unspecified-role'>", Job Title = role + " (Job number: ...)" when a ref id exists, Company link) -> fact_email (all fields; Name = subject). Batch <= 50. On a mid-write failure keep unconfirmed entries in the cache, stop, and report. Remove entries from the cache once confirmed. After a successful run, write {"lastRunIso": "<this run's start time, ISO 8601 with offset>"} to last-run.json.

STEP 4b Keep the dashboard's Application Stale tile working: after upserts, for every dim_Application whose Current State is not terminal (Application Rejected, Interview Rejected, Offer Reject, Offer Accept), set 'Days in Current State' = whole days between today ({{USER_TIMEZONE}}) and the application's Latest Date (a plain number field; nothing else updates it). Skip rows already correct. Batch <= 50.

STEP 5 Summary: the exact Gmail query sent; new emails found / classified / pushed; new companies / applications; pending cache count; low-confidence items; mode=split|inline. Push notification only when new emails were pushed or on failure.

READ-ONLY / DRY-RUN: if the prompt that started this run says "dry run" or "read-only", do STEP 0 connectivity, STEP 1 search and STEP 3 classification for at most 5 threads, write nothing to Airtable or the cache, and report what would have been written.
