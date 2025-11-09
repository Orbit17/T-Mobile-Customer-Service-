# CHI Update and RAG Integration Guide

## Overview

The system now uses Pinecone to store customer reviews and automatically updates CHI scores on the dashboard. The same data powers the AI chatbot through a RAG (Retrieval-Augmented Generation) pipeline.

## How It Works

### 1. Data Flow
```
tmobile_reviews.jsonl 
  → Pinecone (t-mobile index) 
  → SQL Database (Events table)
  → CHI Score Calculation
  → Dashboard Display
  → Chatbot RAG Pipeline
```

### 2. Components

#### **update_chi_from_reviews.py**
Unified script that:
- ✅ Upserts reviews to Pinecone (t-mobile index, default namespace)
- ✅ Inserts reviews as Events into SQL database
- ✅ Recomputes CHI scores for all regions
- ✅ Generates alerts for regions with CHI drops

#### **Simplified Chatbot (backend/chatbot.py)**
- Queries Pinecone for relevant customer reviews
- Uses GROQ to generate intelligent answers
- Returns contextual insights based on actual review data

## Usage

### Update CHI Scores from Reviews

Run the update script:

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
python3 update_chi_from_reviews.py
```

This will:
1. Load reviews from `tmobile_reviews.jsonl`
2. Upsert to Pinecone (t-mobile index)
3. Insert into database
4. Recompute CHI scores
5. Generate alerts

### Using the Chatbot

The chatbot automatically:
- Queries Pinecone when you ask questions
- Filters by region/issue type when detected
- Uses GROQ to generate answers from retrieved reviews

**Example Questions:**
- "What do customers think about roaming issues?"
- "Tell me about billing problems in Atlanta"
- "Which city has the highest CHI?"
- "What are customers saying about coverage?"

## Configuration

Ensure your `.env` file has:
```
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=t-mobile
PINECONE_NAMESPACE=default
GROQ_API_KEY=your_groq_key
EMBEDDINGS_MODEL=intfloat/multilingual-e5-large
```

## Dashboard Updates

After running the update script:
1. Restart the backend: `./start_backend.sh`
2. Refresh the frontend dashboard
3. CHI scores will be updated for all regions
4. The chatbot will have access to all review data

## Troubleshooting

- **Pinecone not connecting**: Check `PINECONE_API_KEY` in `.env`
- **CHI scores not updating**: Check database connection and review file path
- **Chatbot not finding reviews**: Verify Pinecone data was upserted successfully

