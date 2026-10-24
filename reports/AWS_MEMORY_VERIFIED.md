# TriageGrid AWS memory — verified

- Region: ap-south-1 (Mumbai)
- IAM user: triagegrid-app; console login disabled.
- Inline policy: TriageGridMemoryOnly; limited to triagegrid_memory.
- DynamoDB table: triagegrid_memory, ACTIVE, on-demand.
- Partition key: session_id (String). Sort key: sk (String).
- Project credentials saved in ignored local .env with mode 0600. No secret values are included in this report.

## Validation
Actual AWS authentication succeeded as the project IAM user. Real synthetic verification passed for ordered message writes/reads, structured facts, session isolation and deletion. Verification records were removed and deletion checked.

Backend /assistant/status reports memory_provider=aws. Backend health is OK.

55 backend tests passed with MEMORY_PROVIDER=sqlite to avoid storing unit-test fixtures in AWS. Three dedicated AWS-provider tests cover key conditions/order, pagination and readiness checks.

## Implementation corrections
Added boto3 dependency; corrected sort-key queries; paginated session deletion; added active-table readiness checks; enabled standard AWS credential resolution; loaded .env before Settings construction; removed silent SQLite fallback when AWS is selected.

## Notes
DynamoDB storage is not model training. TTL retention is not implemented by this provider; do not claim automatic 24-hour deletion. Credentials must stay out of Git/frontend/logs. AWS account verification blocked CloudShell, but IAM and DynamoDB setup and actual data operations succeeded.
