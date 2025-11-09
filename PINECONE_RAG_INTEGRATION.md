# Pinecone RAG Integration - Complete Guide

## ✅ Integration Status

### 1. **Data Ingestion** ✅
- **80 customer reviews** ingested into Pinecone (`t-mobile` index, `default` namespace)
- Reviews include metadata: `region`, `rating`, `issue_type`, `source`, `sentiment`
- Reviews also ingested into SQL DB for CHI computation

### 2. **Pinecone Configuration** ✅
- **Index**: `t-mobile`
- **Namespace**: `default`
- **Embedding Model**: `intfloat/multilingual-e5-large` (1024 dimensions)
- **Query Prefix**: Automatically adds "query: " prefix for E5 models
- **Vector Search**: Cosine similarity with top_k=8

### 3. **RAG Pipeline** ✅
The chatbot now:
- **Prioritizes Pinecone reviews** over SQL DB context
- **Extracts metadata** (region, rating, issue_type) from reviews
- **Enriches context** with review metadata for better answers
- **Shows source attribution** in responses (review count, regions, avg rating)
- **Uses GROQ LLM** to generate contextual answers based on customer feedback

### 4. **CHI Updates** ✅
- CHI automatically computed from ingested reviews
- Reviews stored as Events in SQL DB
- CHI recomputed for all affected regions (15 regions)
- Real-time updates when new reviews are ingested

## 🔍 How It Works

### Chatbot Query Flow

1. **User asks question** (e.g., "What do customers think about roaming issues?")
2. **Pinecone Vector Search**:
   - Query embedded with E5 model ("query: " prefix)
   - Searches `t-mobile` index in `default` namespace
   - Returns top 8 most relevant reviews
3. **Metadata Extraction**:
   - Extracts region, rating, issue_type from each review
   - Builds enriched context strings
4. **GROQ LLM Processing**:
   - Combines Pinecone reviews + SQL DB context
   - Generates summary with citations
   - Provides actionable recommendations
5. **Response Display**:
   - Shows answer with source attribution
   - Displays review count, regions, average rating

### Example Query Flow

**Question**: "What do customers think about roaming issues?"

**Pinecone Retrieval**:
- Finds reviews mentioning "roaming", "international", "overseas"
- Returns reviews with metadata:
  - Region: "Chicago, IL", Rating: 4/5, Issue: "roaming"
  - Region: "San Antonio, TX", Rating: 2/5, Issue: "roaming"

**GROQ Response**:
- Summarizes customer feedback
- Cites specific regions and ratings
- Provides recommendations based on actual reviews

## 📊 Frontend Enhancements

### Chatbot Display
- Shows "Searching Pinecone knowledge base..." spinner
- Displays review source count: "📊 Based on 5 customer review(s) from Pinecone"
- Shows regions: "📍 Regions: Chicago, San Antonio, Houston"
- Shows average rating: "⭐ Average rating: 3.2/5"

### Status Indicators
- Pinecone connection status in sidebar
- Index name display
- Real-time connection check

## 🚀 Testing the Integration

### Test Queries

Try these questions in the chatbot:

1. **"What do customers think about roaming issues?"**
   - Should return reviews about international roaming
   - Shows regions affected
   - Provides average rating

2. **"Tell me about billing problems in San Antonio"**
   - Should find San Antonio billing reviews
   - Shows specific customer feedback

3. **"What issues are customers reporting in Chicago?"**
   - Should return Chicago-specific reviews
   - Shows issue types and ratings

4. **"How is customer satisfaction in Dallas?"**
   - Should aggregate Dallas reviews
   - Shows sentiment and ratings

### Verify Pinecone Connection

Check `/pinecone_status` endpoint:
```bash
curl http://localhost:8000/pinecone_status
```

Should return:
```json
{
  "status": "connected",
  "index": "t-mobile",
  "namespace": "default",
  "test_query_success": true,
  "api_key_set": true
}
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Pinecone
PINECONE_API_KEY=your_key_here
PINECONE_INDEX=t-mobile
PINECONE_NAMESPACE=default
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1

# GROQ (for LLM)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Embedding Model (optional)
EMBEDDINGS_MODEL=intfloat/multilingual-e5-large
```

## 📈 CHI Updates

### How CHI Uses Ingested Reviews

1. **Reviews → Events**: Each review becomes an Event in SQL DB
2. **Sentiment Analysis**: Sentiment computed for each review
3. **Keyword Extraction**: Top keywords extracted
4. **CHI Computation**: CHI calculated per region using:
   - Sentiment scores
   - Volume metrics
   - KPI health
   - Keyword trends
5. **Real-time Updates**: CHI refreshes as new reviews ingested

### Viewing CHI Updates

- **Overview Tab**: Shows overall CHI and regional map
- **Region Map Tab**: Detailed regional CHI scores
- **Alerts Tab**: CHI drops trigger alerts with AI recommendations

## 🎯 Key Features

1. **Semantic Search**: Vector search finds relevant reviews even with different wording
2. **Metadata Enrichment**: Reviews include region, rating, issue type for context
3. **Source Attribution**: Responses show which reviews were used
4. **Real-time Updates**: CHI updates automatically from ingested reviews
5. **Hybrid Retrieval**: Combines Pinecone (reviews) + SQL DB (alerts, events)

## 🔍 Troubleshooting

### Chatbot not finding reviews?

1. **Check Pinecone connection**:
   ```bash
   curl http://localhost:8000/pinecone_status
   ```

2. **Verify reviews ingested**:
   - Check Pinecone dashboard
   - Verify namespace is "default"
   - Check index name is "t-mobile"

3. **Check API keys**:
   - Ensure PINECONE_API_KEY is set
   - Ensure GROQ_API_KEY is set (for LLM)

### CHI not updating?

1. **Verify reviews in SQL DB**:
   ```sql
   SELECT COUNT(*) FROM events WHERE region = 'Dallas';
   ```

2. **Trigger recompute**:
   ```bash
   curl -X POST http://localhost:8000/recompute \
     -H "Content-Type: application/json" \
     -d '{"regions": ["Dallas", "Chicago"]}'
   ```

## ✨ Next Steps

1. **Add more reviews**: Ingest additional customer feedback
2. **Monitor performance**: Track query response times
3. **Refine prompts**: Adjust GROQ prompts for better answers
4. **Expand metadata**: Add more metadata fields to reviews
5. **Analytics**: Track which reviews are most frequently retrieved

