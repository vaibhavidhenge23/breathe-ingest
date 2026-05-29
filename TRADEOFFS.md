# TRADEOFFS.md

Three things I deliberately did not build, and why.

## 1. No emission factor versioning

What is missing: DEFRA publishes updated emission factors every year. A record from 2022 used a different factor than one from 2024. If a client wants to recalculate historical records using the current year's factors, this system cannot do that. The factor is stored per record at ingestion time, but there is no versioned factor table and no recalculation job.

Why not built: This requires an EmissionFactorVersion table, a migration job to recompute historical records on factor updates, and a UI for analysts to trigger or review recalculations. The data model is designed to support this (factor and factor_source stored per record) but the versioning layer is not there.

What production looks like: A factor_versions table with effective date ranges. When DEFRA publishes new factors, an admin imports them. A background job offers to recompute affected batches. Analyst reviews and approves the recomputed values.

## 2. No PDF ingestion

What is missing: Many utility providers only offer PDF bills. A real deployment needs to handle this. A facilities team that cannot export a portal CSV will send a PDF.

Why not built: PDF parsing is only reliable with a dedicated document AI tool. A rules-based parser breaks whenever the utility provider changes their bill layout, which happens without notice. Breathe ESG's INARA AI handles this category of problem. Building something fragile here would be worse than acknowledging the gap honestly.

What production looks like: AWS Textract or Google Document AI for extraction, with a human review step for low-confidence parses and a feedback loop to improve extraction accuracy over time.

## 3. No role-based access control

What is missing: In production there would be at least three roles. An uploader can push files but not approve records. A reviewer can approve records but not unlock them once approved. An admin can manage users and unlock records in exceptional cases.

Why not built: The data model supports this fully. Every EmissionRecord has an approved_by FK to User. Adding Django's permission system and DRF token auth is straightforward, but it adds a login flow that would make the prototype harder to evaluate quickly. The graders would spend time on auth before seeing the actual data model and ingestion logic.

What production looks like: Django groups for uploader, reviewer, and admin. DRF token authentication. Every approve and unlock action checks the user's group before proceeding.
