# Phase 6: Job Search Tracker artifact

1. Fill `tracker.title` (default "Job Search Tracker"); `search.min_score`, `search.location_rule` and `search.salary_floor_display` must be set (Phase 2).
2. Render:
   ```
   python3 <root>/scripts/render-task.py --config <ws>/career-kit.config.json \
     --template <root>/templates/tracker-template.html --tracker \
     --out <ws>/.career-kit/tracker/index.html \
     --card-out <ws>/.career-kit/tracker/card-template.html
   ```
   This fills {{TRACKER_TITLE}}, {{MIN_SCORE}}, {{LOCATION_RULE}} and {{SALARY_FLOOR}}. It removes the sample day-groups and keeps the `.howto` element and the DAY-GROUP TEMPLATE comment, because the daily task inserts each new day-group right after `.howto`. CSS, card markup and the Tailor-button script stay exactly as in the template. The removed sample (one day-group with one card) is saved as `card-template.html`, which the daily task copies card markup from.
3. Check the rendered file: no `{{TRACKER_TITLE}}`-style config placeholders remain (card placeholders in the comment are fine), `.howto` is present, and there are no `.day-group` elements.
4. Show the user the title and legend text, then publish with the Artifact tool (`file_path` = the rendered file, icon `briefcase`, description "Daily job-board results with apply and tailor-resume buttons").
5. Store the returned URL in `tracker.artifact_url`. The daily job-board task republishes to this SAME URL; it never creates a new artifact.
6. If the Artifact tool is unavailable: keep the rendered file, tell the user, and leave `setup_progress.tracker = false`.
