# 🚀 Quick Start Guide

## Prerequisites

1. **Python 3.10+** installed
2. **API Keys** set in `.env` file:
   - `PINECONE_API_KEY`
   - `GROQ_API_KEY`
   - `PINECONE_INDEX` (default: "t-mobile")
   - `PINECONE_NAMESPACE` (default: "default")

## Step 1: Install Dependencies

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"

# Install Python packages
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Make sure your `.env` file exists in the project root with:

```env
PINECONE_API_KEY=your_pinecone_key_here
GROQ_API_KEY=your_groq_key_here
PINECONE_INDEX=t-mobile
PINECONE_NAMESPACE=default
TOKENIZERS_PARALLELISM=false
```

## Step 3: Initialize Database (First Time Only)

```bash
# The database will be auto-created on first backend start
# But you can also manually initialize:
python3 -c "from backend.database import init_db; init_db()"
```

## Step 4: Run the Application

### Option A: Using Startup Scripts (Recommended)

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
streamlit run frontend/app.py --server.port 8501
```

## Step 5: Access the Application

- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 What You'll See

1. **Overview Tab**: CHI scores, sentiment analysis, region map
2. **Alerts Tab**: CHI drop alerts and recommendations
3. **Outages Tab**: Simulate outages and see CHI impact
4. **Region Map Tab**: Interactive map with CHI scores
5. **AI Support Panel**: Chatbot powered by GROQ and Pinecone

## 🔧 Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `lsof -ti:8000 | xargs kill -9`
- Verify `.env` file exists and has API keys
- Check backend logs for errors

### Frontend won't start
- Check if port 8501 is in use: `lsof -ti:8501 | xargs kill -9`
- Make sure backend is running first
- Check frontend logs

### Database errors
- Delete `chi.db` and let it recreate
- Run: `python3 -c "from backend.database import init_db; init_db()"`

### API connection errors
- Verify backend is running on port 8000
- Check `api_url` in frontend (default: `http://127.0.0.1:8000`)

## 📊 Ingest Sample Data (Optional)

To load the sample reviews into Pinecone:

```bash
python3 ingest_to_pinecone_e5.py tmobile_reviews.jsonl
```

Or update CHI from reviews:

```bash
python3 update_chi_from_reviews.py
```

## 🛑 Stopping the Application

Press `Ctrl+C` in each terminal to stop the services.

