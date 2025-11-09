# 🎬 AI Chatbot Demo Script for Judges

## Quick 2-Minute Demo (Recommended)

### Question 1: "What are customers saying about roaming issues?"
**Why this is perfect:**
- ✅ Shows Pinecone retrieval working (5 matches found)
- ✅ Returns actual customer review quotes
- ✅ Provides specific, actionable recommendations
- ✅ Demonstrates issue-type filtering

**What to highlight:**
- "Notice how it found 5 relevant customer reviews from our Pinecone database"
- "It's showing actual customer feedback, not generic responses"
- "The recommendations are specific to roaming issues"

---

### Question 2: "Which city has the highest CHI?"
**Why this is perfect:**
- ✅ Shows operational intelligence
- ✅ Demonstrates GROQ reasoning with CHI data
- ✅ Shows integration between Pinecone and database
- ✅ Provides data-driven answer

**What to highlight:**
- "The chatbot is querying our CHI database and reasoning about the results"
- "It's using GROQ to analyze operational data, not just customer reviews"
- "This shows the full RAG pipeline working"

---

### Question 3: "What should we do about billing problems in San Antonio?"
**Why this is perfect:**
- ✅ Combines region + issue filtering
- ✅ Shows actionable recommendations
- ✅ Demonstrates end-to-end RAG
- ✅ Real-world engineering question

**What to highlight:**
- "It's filtering by both region and issue type"
- "The recommendations are specific and actionable"
- "Engineers can immediately act on these suggestions"

---

## Extended 5-Minute Demo

### Additional Questions to Showcase:

**4. "What issues are customers reporting in Chicago?"**
- Shows region-specific analysis
- Multiple issue types detected
- Comprehensive recommendations

**5. "Compare customer satisfaction between Dallas and Houston"**
- Shows comparative analysis
- Multi-region data retrieval
- GROQ reasoning across datasets

**6. "What are the main customer support issues?"**
- Tests issue categorization
- Shows sentiment analysis
- Service quality insights

---

## 🎯 What Judges Should See

### ✅ Evidence of Working RAG:
1. **Customer Review Quotes** - Actual text from Pinecone
2. **Region Filtering** - Questions about specific cities work
3. **Issue Type Detection** - Roaming, billing, coverage, etc.
4. **Data Integration** - CHI scores + customer reviews
5. **Actionable Recommendations** - Not generic, specific to the problem

### ✅ Technical Highlights:
- **Pinecone Vector Search** - Semantic similarity matching
- **GROQ LLM** - Intelligent reasoning and summarization
- **Context-Aware** - Uses both reviews and operational data
- **Resilient** - Fallback system if GROQ fails

---

## 📊 Sample Answers (What to Expect)

### Example 1: Roaming Issues
```
Summary: Customers are experiencing issues with international roaming, 
including unexpected charges, failed texts, and lack of LTE connectivity abroad.

Customer Reviews Found:
1. "I am frustrated about my T‑Mobile service in San Antonio, TX. 
   Problem: roaming; keywords: text fail overseas, charges unexpected. 
   Rating: 2/5."

AI Recommendations:
- Review and optimize international roaming settings
- Provide clear information about roaming rates
- Investigate LTE connectivity issues abroad
```

### Example 2: CHI Analysis
```
Summary: Based on current CHI data, regions with the highest scores 
include [list of regions]. These regions show strong network performance 
and positive customer sentiment.

AI Recommendations:
- Continue monitoring high-performing regions
- Apply best practices from top regions to others
- Investigate factors contributing to high CHI scores
```

---

## 🚀 Demo Flow

1. **Start the app** (if not already running)
   ```bash
   ./start_backend.sh    # Terminal 1
   ./start_frontend.sh   # Terminal 2
   ```

2. **Navigate to the chatbot** (in sidebar)

3. **Ask Question 1** - Show customer review retrieval
   - Point out the actual review quotes
   - Highlight the specific recommendations

4. **Ask Question 2** - Show operational intelligence
   - Point out CHI data integration
   - Show GROQ reasoning

5. **Ask Question 3** - Show actionable insights
   - Point out region + issue filtering
   - Emphasize engineering value

---

## 💡 Pro Tips

1. **If a question doesn't return reviews:**
   - That's okay! Show how it still provides intelligent answers
   - The fallback system ensures it always responds

2. **If GROQ is slow:**
   - Explain it's generating intelligent summaries
   - Show the "Analyzing feedback..." indicator

3. **Highlight the evidence:**
   - Always point out the "Customer Reviews Found" section
   - Show judges the actual review text, not just summaries

4. **Show the data flow:**
   - "Question → Pinecone (vector search) → GROQ (reasoning) → Answer"
   - This demonstrates the full RAG pipeline

---

## ✅ Success Metrics

A successful demo shows:
- ✅ Actual customer review quotes (not generic text)
- ✅ Specific recommendations (not "contact support")
- ✅ Region/issue filtering working
- ✅ GROQ generating intelligent summaries
- ✅ System resilience (fallback if needed)

---

## 🎯 One-Liner for Judges

**"This chatbot uses Pinecone to retrieve actual customer reviews from our database, then uses GROQ to generate intelligent, actionable recommendations that engineers can immediately act on."**

