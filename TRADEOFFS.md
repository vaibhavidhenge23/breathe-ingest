# TRADEOFFS.md

## 1. No emission factor versioning

**What's missing:** DEFRA publishes updated emission factors every year. A record from 2022 used a different factor than one from 2024. If a client wants to recalculate historical records using the current year's factors, this system cannot do that — the factor is stored per-record at ingestion time with no versioning table.

**Why not built:** This requires a `EmissionFactorVersion` table, a migration job to recompute historical records, and a UI for analysts to trigger recalculation. Correct but out of scope for a 4-day prototype.

**Production solution:** Factor versions table with effective date ranges. Recalculation triggered per batch when a new factor version is published.

---

## 2. No PDF ingestion

**What's missing:** Many utility providers only offer PDF bills — no CSV export from their portal. A real deployment needs to handle PDFs.

**Why not built:** PDF parsing requires either a rules-based parser (brittle, breaks on layout changes) or an ML-based document AI tool. The latter is what Breathe ESG's INARA AI is built for. Building a reliable parser from scratch in 4 days would produce something too fragile to trust in a carbon accounting context where errors affect audit outcomes.

**Production solution:** AWS Textract or Google Document AI for extraction, with a human review step for low-confidence parses.

---

## 3. No real authentication or multi-user

**What's missing:** Every request is treated as coming from the same "analyst" user. There is no login, no session management, no role separation (uploader vs reviewer vs admin).

**Why not built:** Auth adds significant complexity — JWT tokens, refresh logic, permission checks on every view. For a prototype evaluating the data model and ingestion logic, fake auth is honest. The data model is fully prepared for multi-user (every record has `approved_by` FK to User).

**Production solution:** Django's built-in auth + DRF token authentication. Role-based access: `uploader` can push files, `analyst` can review and approve, `admin` can unlock approved records.
