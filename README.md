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

## Groq API Setup (Optional)

The AI chatbot can use Groq's API for enhanced responses. To enable it:

### Method 1: Using .env file (Recommended)

1. Get a Groq API key from [https://console.groq.com](https://console.groq.com)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   On Windows:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Edit `.env` and replace `your-groq-api-key-here` with your actual API key
4. Optionally change `GROQ_MODEL` to use a different model

The `.env` file is automatically loaded when the backend starts. **Note:** `.env` is already in `.gitignore` to protect your API key.

### Method 2: Environment Variables

Alternatively, you can set environment variables directly:

```bash
export GROQ_API_KEY="your-api-key-here"
export GROQ_MODEL="llama-3.1-70b-versatile"  # optional
```

On Windows PowerShell:
```powershell
$env:GROQ_API_KEY="your-api-key-here"
$env:GROQ_MODEL="llama-3.1-70b-versatile"  # optional
```

Available models: `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`, `gemma-7b-it`, etc.

If `GROQ_API_KEY` is not set, the chatbot will use a basic retrieval-based response without AI enhancement.

## Notes

- NLP sentiment uses TextBlob with a rules-based fallback.
- Keyword extraction uses TF-IDF to keep dependencies light.
- Map uses region centroids rather than full choropleth for simplicity.
- This is an MVP intended for demo; tune constants and thresholds for production.
