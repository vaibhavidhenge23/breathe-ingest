# DECISIONS.md

## Live URLs

Frontend: https://breathe-ingest-git-main-vaibhavi-dhenges-projects.vercel.app
Backend API: https://breathe-ingest-backend.onrender.com
GitHub: https://github.com/vaibhavidhenge23/breathe-ingest

Login: username is "analyst" (auto-created on first run, no password required in prototype)

---

## SAP: flat CSV export, not IDoc

I read the SAP Help Portal documentation on IDoc (Intermediate Document format). IDoc is a binary/EDI-based format used for SAP-to-SAP communication via ALE middleware. Setting up an IDoc parser from scratch requires understanding segment definitions, control records, and EDI layers. That is several weeks of work.

I chose flat file CSV export from the MM60 and MB51 transactions. This is how most SAP implementations actually share data with external systems in practice. The SAP admin runs a transaction, exports a .csv or .txt, and sends it over. German column headers (WERKS, MENGE, MEINS, BUDAT) appear because SAP's default language setting in many Indian enterprise deployments is still German from the original implementation in the 90s and early 2000s.

What I would ask the PM: which SAP transaction is the client's team using to export? What is the default language setting? Can they share the plant code master data table?

## Utility: portal CSV, not PDF

PDF bill parsing is fragile. MSEDCL, Tata Power, and BESCOM all have different PDF layouts. OCR errors compound. In production, a tool like AWS Textract or Google Document AI handles this. Building a reliable PDF parser from scratch produces something too fragile to trust in a carbon accounting context where errors affect audit outcomes.

I chose portal CSV export. Most large enterprise clients have utility management portal access with CSV download capability. MSEDCL's portal export matches the format in my sample data.

Billing period decision: I store period_start and period_end separately and do not force alignment to calendar months. A bill from March 15 to April 14 spans two quarters. Splitting it pro-rata requires a business decision about the client's reporting period. I flag these for analyst review rather than making that call silently.

## Travel: JSON file upload, not live API

Concur's API requires OAuth 2.0 with company-level credentials. That is an enterprise integration that takes weeks to set up per client. For a prototype, a JSON file export is the right scope. The JSON structure mirrors what Concur's expense and travel endpoints actually return. I read the Concur developer documentation to verify field names.

## Airport distance: Haversine formula

Concur and Navan do not provide flight distance. They provide IATA airport codes. I implemented the Haversine formula (great-circle distance) with a 1.09 routing uplift factor. This is exactly what DEFRA's travel emission calculator documents specify. It slightly undercounts vs actual flight paths but is the industry standard for carbon accounting.

## Flagging: rule-based threshold

INARA AI (Breathe ESG's own system) does anomaly detection with ML. I used a simple rule: if a record's kgCO2e is more than 3x the batch average for that category, flag it. I do not have historical training data for an ML model. This is an honest simplification and I have noted it explicitly.

## Auth: single analyst user

The data model is fully prepared for multi-user (every record has approved_by as a FK to User). For the prototype, a single analyst user is auto-created. Adding Django's built-in auth with DRF token authentication is straightforward but adds login flow complexity that would obscure the actual data model and ingestion logic during review.

## What I would ask the PM

1. Plant code master data: who maintains it, can they export it before onboarding?
2. Billing period normalization: should non-calendar periods be pro-rated or assigned to the period-end month?
3. Emission factor standard: DEFRA or CEA or another? Which year's factors?
4. Locked records policy: can an admin unlock an approved record, or is it permanently immutable?
5. Multi-user: do multiple analysts need separate logins from day one?
