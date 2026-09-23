# Validation — 23 September 2026

- 18 automated tests cover duration/start boundaries, uncertain eligibility, computer-engineering exclusion, multidisciplinary inclusion, query-string job IDs, duplicate handling, history, CSV formula safety, and report generation on successful and empty discovery runs.
- Initial full free-search experiment: 90 of 116 planned queries attempted, only 3 successful, 57 unique hits. It exposed unreliable engine timeouts. That version was replaced.
- Revised live test: 4 of 4 queries returned results, 63 unique hits, completed in 39 seconds including direct employer-board attempts. One direct source returned an access gap. This is a smoke test, not proof that every employer or GitHub cloud IP will work.
- Each revised query is isolated in a subprocess with a 12-second timeout; checkpoints retain partial evidence. GitHub has a 20-minute job limit.
- The workbook contains 19 reviewed records: 2 verified matches, 11 leads requiring confirmation, 6 known timing/staleness exclusions. Source links and evidence are included. The workbook was rendered and checked for formula errors.
- GitHub run 35892383441 completed successfully in 3m 58s. Its 65 searches returned 390 unique links with partial coverage. Review exposed non-vacancy pages; a follow-up version improves their classification.
