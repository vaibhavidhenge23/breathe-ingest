# Breathe ESG Data Ingestion Prototype

A Django REST and React app that ingests emissions data from three source types, normalizes it, and surfaces a review dashboard where an analyst can see what came in, what failed, what looks suspicious, and approve rows before they are locked for audit.

## Live URLs

Frontend: https://breathe-ingest-git-main-vaibhavi-dhenges-projects.vercel.app
Backend API: https://breathe-ingest-backend.onrender.com
GitHub: https://github.com/vaibhavidhenge23/breathe-ingest

Login: username is "analyst" (auto-created, no password required in prototype)

## What it does

Upload tab accepts three file types. SAP CSV exports with German column headers (WERKS, MENGE, MEINS, BUDAT) for fuel and procurement data. Utility portal CSV exports for electricity consumption. Concur-style JSON exports for business travel including flights, hotels, and ground transport.

Each file is parsed, normalized to a common format, and queued for analyst review. Records are automatically flagged if a unit is missing, a date cannot be parsed, an airport code is not recognized, or a value is more than 3x the batch average for that category.

The Review dashboard shows all records with their status. Clicking a row shows the original raw data alongside the normalized values. Analysts can approve records individually or bulk approve all non-flagged records. Approved records are locked and cannot be edited. Every approval is recorded in the Audit Log with the user, timestamp, and detail.

## Sample data

The sample_data folder contains realistic test files. sap_export.csv has German headers, mixed units (liters and gallons), and one row with a missing unit that triggers a flag. utility_export.csv has non-calendar billing periods of the kind MSEDCL portal exports produce. travel_records.json has flights with IATA airport codes, hotel nights, ground transport, and one record with an unknown airport code to trigger the distance flag.

## Local setup

Backend:
```
cd backend
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Frontend:
```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Architecture

Backend is Django REST Framework with two apps. The ingestion app handles file uploads and parsing. The analyst app handles review, approval, and audit logging. Each source has its own parser (sap.py, utility.py, travel.py) kept separate from views so format changes only touch the parser file.

Frontend is React with no UI framework. Three pages: Upload, Review dashboard, Audit Log.

## Documents

MODEL.md explains the data model and design decisions.
DECISIONS.md explains every ambiguity resolved and what would be asked of the PM.
TRADEOFFS.md covers three things deliberately not built and why.
SOURCES.md covers the real-world research behind each data source.