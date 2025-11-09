# Backend Deployment Guide

## ✅ Correct Way to Start Backend

### Option 1: Using the startup script (Recommended)
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
./start_backend.sh
```

### Option 2: Manual command
**IMPORTANT**: Run from the **project root directory**, not from inside `backend/`

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using uvicorn directly
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## ❌ Common Mistakes

### Wrong: Running from backend directory
```bash
cd backend
uvicorn main:app --reload  # ❌ This will fail with import errors
```

### Wrong: Using wrong module path
```bash
uvicorn main:app --reload  # ❌ Missing 'backend.' prefix
```

## 🔍 Why This Happens

The backend uses **relative imports** (e.g., `from .database import ...`). These only work when:
1. Running from the project root
2. Using the full module path: `backend.main:app`

## ✅ Verification

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Test it:
```bash
curl http://localhost:8000/docs
```

## 🚀 Full Stack Startup

### Terminal 1: Backend
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
./start_backend.sh
```

### Terminal 2: Frontend
```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2/frontend"
streamlit run app.py
```

## 📝 Environment Variables

Make sure you have a `.env` file in the project root with:
```bash
PINECONE_API_KEY=your_key
PINECONE_INDEX=t-mobile
PINECONE_NAMESPACE=default
GROQ_API_KEY=your_key
```

The startup script will automatically load these.

