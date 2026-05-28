# DECISIONS.md

## SAP: Flat CSV, not IDoc

SAP exports data in multiple formats. I read the SAP Help Portal documentation on IDoc (Intermediate Document) - it is a binary/EDI-based format with segment definitions that require SAP middleware (ALE/EDI layer) to parse. Setting up an IDoc parser from scratch is 1-2 weeks of work, not 4 days.

I chose flat file CSV export from MM60/MB51 transactions. This is how most SAP implementations actually share data with external systems - the SAP admin runs a transaction and exports a .csv or .txt. German column headers (`WERKS`, `MENGE`, `MEINS`, `BUDAT`) appear because SAP's default language setting in many Indian enterprise deployments is still German from the original implementation.

**What I'd ask the PM:** Which SAP transaction is the client's team using to export? What is the default language setting? Do they have a plant code master data table they can share?

## Utility: Portal CSV, not PDF

PDF bill parsing is fragile. The structure varies by utility provider (MSEDCL, Tata Power, BESCOM all have different layouts), and OCR errors compound. In production, Breathe ESG would use a dedicated document AI tool (AWS Textract or Google Document AI) for PDFs.

I chose portal CSV export — most large enterprise clients have access to utility management portals that offer CSV downloads. MSEDCL's portal exports match the format in my sample data.

**Key decision on billing period:** I store `period_start` and `period_end` as separate fields and do not force alignment to calendar months. A bill from March 15 to April 14 spans two months — splitting it pro-rata (half to Q1, half to Q2) requires a business decision about the client's reporting period. I flag these for analyst review rather than making that call silently.

## Travel: JSON file upload, not live API

Concur's API requires OAuth 2.0 with company-level credentials — an enterprise integration that takes weeks to set up per client. Navan's API is similar. For a prototype, file upload of a JSON export is the right scope.

The JSON structure mirrors what Concur's `/expense/reports` endpoint returns — I read the Concur developer documentation to verify the field names match realistic data.

## Airport distance: Haversine, not actual flight path

Concur and Navan do not provide flight distance. They provide origin/destination airport codes. I implemented the Haversine formula (great-circle distance) with a 1.09 routing uplift factor — this is exactly what DEFRA's travel emission calculator documents specify. It undercounts slightly vs actual flight paths but is the industry standard for carbon accounting purposes.

## Flagging: Rule-based, not ML

INARA AI (Breathe ESG's own system) does anomaly detection with ML. I used a simple rule: if a record's kgCO2e is more than 3x the batch average for that category, flag it. This is honest — I don't have historical training data for an ML model in 4 days. I explicitly note this is where INARA-style intelligence would plug in.

## SQLite for dev, Postgres for prod

Deployment uses DATABASE_URL environment variable. If set, uses dj-database-url for Postgres (Railway/Render provide this automatically). If not set, falls back to SQLite. No manual configuration needed for local development.

## What I would ask the PM

1. Plant code master data - who maintains it, can they export it?
2. Billing period normalization - should non-calendar periods be pro-rated or assigned to the period end month?
3. Emission factor policy - DEFRA or another standard? Which year's factors?
4. Multi-user - do multiple analysts need separate logins, or is one analyst account sufficient for now?
5. Locked records - can an admin unlock an approved record, or is it permanently immutable once approved?
