# Database Bug Fix Scripts

These scripts help diagnose and fix inconsistencies between memberships,
participants, and purchases.

Run them from the repo root. Use `--dry-run` when available before writing.

## cleanup_memberships.py

- Rebuilds `attended_events` from `participants_event`.
- If multiple memberships share the same email, clears the email for those
  with 0 attended events.
- Attempts to repair `attended_events` for 0-attended memberships by matching
  phone numbers in `participants_event`.

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/cleanup_memberships.py --dry-run
```

## fix_missing_memberships.py

- Finds participants that have a `purchase_id` but no `membershipId`.
- Links an existing membership by email/phone when possible.
- Otherwise creates a new membership using the event date as start date.

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/fix_missing_memberships.py --dry-run
```

## report_membership_discrepancies.py

- Reports discrepancies between membership `attended_events`/`purchases` and
  the data derived from `participants_event`.
- Also lists participants with `purchase_id` but missing `membershipId`.

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/report_membership_discrepancies.py
```

Optional limits:
```bash
python mcp-backend/functions/scripts/database_bug_fix/report_membership_discrepancies.py \
  --limit-participants 2000 --limit-memberships 200
```

## fix_membership_first_event.py

- For each membership, compares the event date tied to `purchase_id` with the
  earliest event actually attended by that membership.
- If the stored `purchase_id` points to a later event, updates:
  - `purchase_id`
  - `start_date`
  - `end_date`

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/fix_membership_first_event.py --dry-run
```

## set_free_participants_payment_method.py

- Sets `payment_method=omaggio` for participants with `price=0`
  (skips those that have a `purchase_id`).

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/set_free_participants_payment_method.py --dry-run
```

## report_participant_payment_method_stats.py

- Counts total participants and explains why some records are not updated
  by `migrate_firestore_data.py --participants` (i.e. they already have a
  `payment_method`).
- Shows how missing `payment_method` values would be assigned.

Example:
```bash
python mcp-backend/functions/scripts/database_bug_fix/report_participant_payment_method_stats.py
```

## Targeting test vs prod

To run against the test project:
```bash
MCP_ENV=test \
GOOGLE_APPLICATION_CREDENTIALS=/Users/vittoriodigiorgio/Desktop/MCP-WEB-PROJECT/mcp-backend/functions/service_.account_test.json \
python mcp-backend/functions/scripts/database_bug_fix/report_membership_discrepancies.py
```
