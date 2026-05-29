# MODEL.md

## What this document is

This explains the data model - what tables exist, why they're structured the way they are, and what decisions were made.

## Two-layer storage: RawRecord and EmissionRecord

Every ingested row is stored twice. First as a RawRecord (exact original data, untouched), then as an EmissionRecord (normalized, analysis-ready).

Why? Because normalization can be wrong. If an analyst later says "plant PL01 was Mumbai, not Delhi" or "that SAP unit was gallons not liters," we can recompute from the original without data loss. If we only stored the normalized version and the calculation was wrong, the audit trail would be broken. Breathe ESG's own INARA AI operates on raw documents for the same reason.

## Tables

### Client
Every record belongs to a client. This is how multi-tenancy works :  one analyst cannot see another client's data. The isolation is at the row level, not just at login level. A misconfigured API call cannot leak data across clients.

### IngestionBatch
One file upload equals one batch. Tracks source (sap, utility, travel), filename, who uploaded it, and when. If a wrong file gets uploaded, the entire batch can be deleted and all its records cascade. Without batches, partial deletes would require manual SQL.

### RawRecord
The exact data as uploaded, stored as a JSON blob. Never modified after creation. Also stores parse_error for rows that failed parsing entirely — these show up in the dashboard as failed rows so the analyst knows something was silently dropped.

### EmissionRecord
The normalized record. Key design decisions:

**Scope classification (GHG Protocol standard)**
Scope 1: direct combustion, SAP fuel records
Scope 2: purchased electricity, utility records
Scope 3: value chain emissions, business travel

Auditors expect GHG Protocol categorization. This is not arbitrary — CSRD, BRSR, and GRI frameworks all use this structure.

**Original and normalized quantities stored separately**
quantity_original and unit_original preserve exactly what came in (liters, gallons, kWh, km). quantity_normalized is always in a common unit. An auditor can verify every conversion step.

**Emission factor stored per record**
DEFRA publishes updated factors every year. If we used a global config and it updated, we'd lose which factor was used for which historical record. Storing it per record means the audit trail is complete and reproducible.

**Status lifecycle**
pending means the record came in and hasn't been reviewed. flagged means the system detected something suspicious (missing unit, outlier value, unknown airport code). approved means an analyst has reviewed it and it's locked for audit. Approved records cannot be edited.

**edit_history**
A JSON array storing what changed, who changed it, and when. Auditors ask for this.

## What this model does not handle

Emission factor versioning across years, sub-location hierarchy below plant level, supplier emissions (Scope 3 Category 1 beyond travel), and market-based vs location-based Scope 2 accounting. These are noted in TRADEOFFS.md.
