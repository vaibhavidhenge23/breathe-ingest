# Breathe ESG Data Ingestion Prototype

Django REST + React app for ingesting SAP, utility, and corporate travel data, normalizing it, and surfacing an analyst review dashboard.

## Live Demo
[Deployed URL here]

## Local Setup

**Backend**
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Deploy (Railway)

Backend: connect GitHub repo, set root to `/backend`, add `DATABASE_URL` env var (Railway provides Postgres automatically).

Frontend: set root to `/frontend`, build command `npm run build`, publish directory `dist`. Set `VITE_API_URL` to backend URL.

## Sample Data

`sample_data/` has realistic test files:
- `sap_export.csv` : SAP MM export with German headers, mixed units, one flagged row
- `utility_export.csv` : MSEDCL-style portal CSV, non-calendar billing periods
- `travel_records.json` : Concur-style JSON, flights/hotel/ground, one unknown airport to trigger flag

## Credentials
Username: analyst (auto-created on first run)
