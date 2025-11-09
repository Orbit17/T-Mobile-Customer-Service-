# T-Mobile Customer Happiness Index (CHI) - MVP

## Quick start

1. Install dependencies (prefer venv):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m textblob.download_corpora
```

2. Initialize database and load seed data:

```bash
python -m backend.ingest --seed
```

3. Run backend API (in a terminal):

```bash
uvicorn backend.main:app --reload --port 8000
```

4. Run Streamlit dashboard (in another terminal):

```bash
streamlit run frontend/app.py
```

## Notes on API-driven UI

- The Streamlit app communicates exclusively with the FastAPI server via HTTP.
- Use the sidebar “FastAPI base URL” field (defaults to `http://127.0.0.1:8000`).
- The “Load Seed Data” button triggers `POST /seed` to load CSV seeds on the server.
- “Run Simulation” uses `POST /simulate` and then `POST /recompute` for the region.
- “Refresh CHI Now” calls `POST /recompute` for all regions listed in `data/regions.json`.
- Metrics panel calls `GET /chi?region=...`; map uses `GET /regions`; alerts via `GET /alerts`; kudos via `GET /kudos`; chatbot via `POST /qa`.

## What’s included

- FastAPI backend with endpoints:
  - POST `/ingest` - insert new events
  - GET `/chi?region=XXX` - current CHI and drivers
  - GET `/regions` - CHI summary for all regions
  - GET `/alerts` - recent alerts
  - POST `/simulate` - outage simulation
  - POST `/qa` - engineer chatbot Q&A
  - POST `/seed` - load seed CSV data
  - GET `/kudos` - recent positive events
  - POST `/recompute` - recompute CHI and generate alerts for regions
- SQLite database with schema for sources, events, kpis, chi, alerts, runbook
- CHI engine implementing the provided formula
- Alerts logic on CHI drops, volume spikes, KPI issues
- Outage simulator to inject synthetic negative events and KPI drops
- Lightweight RAG chatbot over recent events, alerts, and runbook
- Predictive module to forecast CHI in the next 1–2 hours
- Streamlit dashboard with a US regional mood map, metrics, alerts feed, kudos, and simulator

## Notes

- NLP sentiment uses TextBlob with a rules-based fallback.
- Keyword extraction uses TF-IDF to keep dependencies light.
- Map uses region centroids rather than full choropleth for simplicity.
- This is an MVP intended for demo; tune constants and thresholds for production.
