---
task_id: career-kit-interview-reminders
title: Interview prep and follow-up reminders
default_cron: "0 7 * * *"
connectors: [Airtable, Gmail]
---
Run fully self-contained. Ask nothing. Workspace: {{WORKSPACE}}. Timezone: {{USER_TIMEZONE}}. Today = the current date in that timezone.

Purpose: before each interview, remind the user to prep and point at the right material; one day after, remind them to send a thank-you / follow-up and log the outcome. Drafts only: never send anything to an interviewer or recruiter.

## Find interviews
- If fact_interview is enabled ({{FACT_INTERVIEW_ENABLED}}): Airtable base {{AT_BASE_ID}}, table {{AT_TBL_INTERVIEW}}. Fields: Name {{AT_FLD_INT_NAME}}, Interview Date {{AT_FLD_INT_DATE}}, Round {{AT_FLD_INT_ROUND}}, Interviewers {{AT_FLD_INT_INTERVIEWERS}}, Prep Link {{AT_FLD_INT_PREP_LINK}}, Thank-you Sent {{AT_FLD_INT_THANKYOU}}, Application {{AT_FLD_INT_APPLICATION}}. Query with list_records_for_table and its structured `filters` (never filterByFormula, which the Airtable connector does not accept): prep = Interview Date `isWithin` {"mode":"nextNumberOfDays","numberOfDays":1,"timeZone":"{{USER_TIMEZONE}}"} (then keep only rows within the next {{PREP_HOURS_BEFORE}} hours); follow-up = Interview Date `isWithin` {"mode":"pastNumberOfDays","numberOfDays":N,"timeZone":"{{USER_TIMEZONE}}"} where N is {{FOLLOWUP_DAYS_AFTER}} plus one, and Thank-you Sent = false (then keep only rows at least {{FOLLOWUP_DAYS_AFTER}} day(s) old).
- Always also check interview emails, and use them alone when fact_interview is disabled: fact_email {{AT_TBL_EMAIL}} rows with Email Context {{AT_FLD_EMAIL_CONTEXT}} = "Formal Interview" received in the last 14 days (structured filters: Email Context `=` the "Formal Interview" choice ID from get_table_schema, Received `isWithin` pastNumberOfDays 14). Skip any whose application already has a fact_interview row, so an interview is never reminded twice. Read each row's Email Body {{AT_FLD_EMAIL_BODY}} and extract the interview date/time and interviewer names when stated. Skip rows with no date you can read; list them as "date unknown" in the summary.
- Resolve the linked application (Identifier {{AT_FLD_APP_IDENTIFIER}}, Job Title {{AT_FLD_APP_TITLE}}, Current State {{AT_FLD_APP_CURRENT_STATE}}) in {{AT_TBL_APPLICATION}}. Skip applications whose Current State is Application Rejected, Interview Rejected, Offer Reject or Offer Accept.

## Prep reminder (interview within the window)
For each upcoming interview, grep {{WORKSPACE}} for existing prep: `*interviewer-profile.md` files for the interviewer names, the company's tailored resume, and {{INTERVIEW_LOG}} headings for that company (grep headings only, never read the whole log). List what exists and what is missing (for example "no interviewer profile for <name>: run /interviewer-profile"; "no stories mapped: run /story-bank for <role>"). Do not write prep content in this task.

## Follow-up reminder (interview {{FOLLOWUP_DAYS_AFTER}} day(s) ago, thank-you not marked sent)
Create a Gmail DRAFT (never send) addressed to the interviewer or recruiter address when one is known from the linked fact_email threads, else with no recipient. Body: a short, specific thank-you that references the role and round only; leave a "[one specific thing you discussed]" slot for the user. Follow the user's writing preferences: {{WRITING_PREFERENCES}}. No em dashes. Remind the user to record the outcome in {{INTERVIEW_LOG}} (outcomes never go in {{EXPERIENCE_CONTEXT}}).

## Output
- Nothing due: no notification; one-line summary only.
- Anything due: one push notification plus an email to {{NOTIFY_EMAIL}} from the user's own Gmail, subject "Interview reminders — <Month D>", listing each interview (company, role, round, time in {{USER_TIMEZONE}}, interviewers), the prep found/missing, and links to any drafts created.
- Airtable unreachable: push + short email "Interview reminders — Airtable connection problem".
