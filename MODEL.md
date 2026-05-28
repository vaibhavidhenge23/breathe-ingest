# MODEL.md

## Core Design Decision

Two-layer storage: `RawRecord` (original) and `EmissionRecord` (normalized).

This separation exists because normalization can be wrong. If an analyst later says "plant PL01 was Mumbai, not Delhi" or "that SAP unit was gallons not liters," we can recompute from the original without data loss. Breathe ESG's own INARA AI operates on raw documents — the same principle applies here.

---

## Tables

### Client
Multi-tenancy at the data level. Every record has a `client` FK. An analyst only sees their client's data. This is row-level isolation, not just login-level -a misconfigured API call cannot leak one client's data to another.

### IngestionBatch
One upload = one batch. Tracks source (sap/utility/travel), filename, uploader, timestamp, row counts. If a batch needs to be voided - wrong file uploaded -  we can delete the batch and all its records cascade. Without batches, partial deletes would be manual and error-prone.

### RawRecord
Exact data as uploaded, stored as JSON. Never modified after creation. Also stores `parse_error` for rows that failed parsing — these are visible in the dashboard as "failed rows" so the analyst knows something was dropped.

### EmissionRecord
The normalized, analysis-ready record. Key fields:

**Scope (GHG Protocol)**
- Scope 1: direct combustion - SAP fuel records
- Scope 2: purchased electricity - utility records  
- Scope 3: value chain - business travel

**Quantities**
Both original and normalized are stored. `quantity_original` + `unit_original` preserve what came in. `quantity_normalized` is always in kWh (electricity) or liters (fuel) or km (travel). This way an auditor can verify the conversion.

**Emission calculation**
`emission_factor` and `emission_factor_source` are stored per-record, not as a global config. Reason: factors change yearly (DEFRA publishes annually). If we used a global factor and it updated, we'd lose which factor was used for which record. Per-record storage means the audit trail is complete.

**Status lifecycle**
`pending` → `flagged` (auto, by flagging.py) or `approved` (by analyst)
Approved records are locked - `approved_by` and `approved_at` are set. UI prevents editing after approval.

**edit_history**
JSONField storing `[{field, old_value, new_value, changed_by, changed_at}]`. If an analyst corrects a value before approving, the change is traceable. This is what auditors ask for: not just the final number, but how it got there.

---

## Multi-tenancy

`Client` FK on `EmissionRecord`, `IngestionBatch`. In production, all queryset filters would include `client=request.user.client`. For this prototype, a single "Demo Client" is used — the structure is production-ready, the auth layer is not.

---

## What this model does not handle

- Emission factor versioning (which DEFRA year applies to historical records)
- Sub-location hierarchy (plant → department → cost center)
- Supplier emissions (Scope 3 Category 1) - only travel covered
- Market-based vs location-based Scope 2 accounting

These are noted in TRADEOFFS.md.
