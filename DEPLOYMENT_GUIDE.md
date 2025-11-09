# 🚀 Complete Deployment Guide

## Prerequisites

1. **Python 3.10+** installed
2. **All dependencies installed**: `pip install -r requirements.txt`
3. **Environment variables configured** (see below)

## 📋 Step 1: Environment Setup

Create a `.env` file in the project root (`/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2/.env`):

```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=t-mobile
PINECONE_NAMESPACE=default
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# GROQ Configuration (for AI chatbot)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Embedding Model (optional, defaults to E5-large)
EMBEDDINGS_MODEL=intfloat/multilingual-e5-large
```

## 🔧 Step 2: Install Dependencies

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
pip install -r requirements.txt
```

## 🖥️ Step 3: Deploy Backend (FastAPI)

### Option A: Using the startup script (Easiest)

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
./start_backend.sh
```

### Option B: Manual command

**Open Terminal 1:**

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### ✅ Verify Backend is Running

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test it:**

```bash
# Check API docs
open http://localhost:8000/docs

# Or test with curl
curl http://localhost:8000/regions
```

## 🎨 Step 4: Deploy Frontend (Streamlit)

**Open Terminal 2** (keep Terminal 1 running):

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2/frontend"
streamlit run app.py
```

### ✅ Verify Frontend is Running

You should see:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Open in browser:** http://localhost:8501

## 📊 Step 5: Verify Full Stack

1. **Backend API**: http://localhost:8000/docs
2. **Frontend App**: http://localhost:8501
3. **Test Chatbot**: Use the sidebar chatbot in the web app
4. **Check CHI**: View regional CHI scores on the map

## 🔍 Quick Test Commands

### Test Backend Endpoints

```bash
# Get all regions
curl http://localhost:8000/regions

# Get CHI for a specific region
curl "http://localhost:8000/chi?region=Dallas"

# Test chatbot
curl -X POST http://localhost:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What are customers saying about roaming issues?"}'
```

### Test Frontend

1. Open http://localhost:8501
2. Check the CHI map displays regions
3. Try the chatbot in the sidebar
4. Verify reviews are searchable

## 🛠️ Troubleshooting

### Backend won't start

**Error: ModuleNotFoundError**

```bash
# Make sure you're in the project root
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"

# Use the correct module path
python -m uvicorn backend.main:app --reload
```

**Error: Port 8000 already in use**

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn backend.main:app --port 8001
```

**Error: PINECONE_API_KEY not found**

```bash
# Make sure .env file exists and has the key
cat .env | grep PINECONE_API_KEY

# Or export manually
export PINECONE_API_KEY=your_key_here
```

### Frontend won't start

**Error: ModuleNotFoundError**

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure streamlit is installed
pip install streamlit
```

**Error: Can't connect to backend**

```bash
# Check backend is running
curl http://localhost:8000/docs

# Update API base URL in frontend sidebar if needed
# Default: http://127.0.0.1:8000
```

### Chatbot not working

1. **Check GROQ API key** is set in `.env`
2. **Check Pinecone** is accessible
3. **Check backend logs** for errors
4. **Verify reviews** were ingested: Check Pinecone dashboard

## 📝 Production Deployment Notes

### For Production (Optional)

**Backend:**

```bash
# Use production server (Gunicorn + Uvicorn workers)
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend:**

```bash
# Streamlit can be deployed to Streamlit Cloud
# Or use Docker/containerization
```

## 🎯 Quick Reference

### Start Everything

```bash
# Terminal 1: Backend
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
./start_backend.sh

# Terminal 2: Frontend
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2/frontend"
streamlit run app.py
```

### Stop Everything

- Press `Ctrl+C` in each terminal
- Or kill processes: `lsof -ti:8000 | xargs kill -9` and `lsof -ti:8501 | xargs kill -9`

### Check Status

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:8501
- Health check: `curl http://localhost:8000/regions`

## ✅ Deployment Checklist

- [ ] `.env` file created with API keys
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Backend API accessible at http://localhost:8000/docs
- [ ] Frontend accessible at http://localhost:8501
- [ ] CHI map displays regions
- [ ] Chatbot responds to queries
- [ ] Reviews are searchable via chatbot

## 🆘 Need Help?

1. Check logs in terminal for error messages
2. Verify all environment variables are set
3. Ensure both services are running
4. Check network connectivity
5. Review `INTEGRATION_SUMMARY.md` for system status
