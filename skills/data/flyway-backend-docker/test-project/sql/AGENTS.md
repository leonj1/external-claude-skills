# SQL Migrations Directory

This folder contains Flyway SQL migration files.

## IMPORTANT: Agent Rules

**DO NOT** modify or delete any existing files in this folder.

**ONLY** add new migration files following the Flyway naming convention:
- `V{version}__{description}.sql` for versioned migrations
- `U{version}__{description}.sql` for undo migrations (optional)
- `R__{description}.sql` for repeatable migrations

### Naming Convention Examples

- `V1__create_users_table.sql`
- `V2__add_email_to_users.sql`
- `V3__create_orders_table.sql`
- `R__refresh_views.sql`

### Why This Restriction?

Flyway tracks applied migrations by checksum. Modifying an already-applied migration will cause:
- Migration failures
- Checksum mismatch errors
- Database inconsistency

If you need to change existing schema, create a NEW migration file with the next version number.
