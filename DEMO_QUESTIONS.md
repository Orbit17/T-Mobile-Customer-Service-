# AI Chatbot Demo Questions for Judges

## 🎯 Best Questions to Showcase the AI Chatbot

These questions are designed to demonstrate the chatbot's ability to:
- Retrieve customer reviews from Pinecone
- Provide data-driven insights
- Generate actionable recommendations
- Answer operational questions about CHI

---

## 📊 Category 1: Customer Review Analysis (Pinecone RAG)

### Question 1: "What are customers saying about roaming issues?"
**Why it's good:**
- Directly queries Pinecone for customer reviews
- Shows retrieval of actual review text
- Demonstrates issue-specific filtering

**Expected Response:**
- Summary of roaming issues from customer reviews
- Actual customer review quotes as evidence
- Specific recommendations (e.g., "Update roaming partner profiles", "Check APN settings")

---

### Question 2: "Tell me about billing problems in Atlanta"
**Why it's good:**
- Combines region + issue type filtering
- Shows geographic filtering capability
- Demonstrates context-aware answers

**Expected Response:**
- Billing issues specific to Atlanta region
- Customer review quotes from Atlanta
- Region-specific recommendations

---

### Question 3: "What did customers complain about regarding slow data speeds?"
**Why it's good:**
- Tests issue type detection (slow_data)
- Shows sentiment analysis
- Demonstrates problem identification

**Expected Response:**
- Customer complaints about data speeds
- Actual review quotes mentioning throttling/slow speeds
- Technical recommendations (e.g., "Inspect congestion KPIs", "Optimize QoS")

---

## 📈 Category 2: Operational Intelligence (CHI + Reviews)

### Question 4: "Which city has the highest CHI?"
**Why it's good:**
- Tests general query capability
- Shows integration with CHI data
- Demonstrates GROQ reasoning

**Expected Response:**
- Lists regions with highest CHI scores
- Provides context about why those regions score well
- May reference positive customer sentiment

---

### Question 5: "Why is Atlanta's CHI lower than other regions?"
**Why it's good:**
- Combines CHI data with customer feedback
- Shows analytical reasoning
- Demonstrates root cause analysis

**Expected Response:**
- References Atlanta's CHI score
- Mentions customer complaints/issues from Atlanta
- Provides specific reasons (e.g., outages, coverage issues)
- Actionable recommendations

---

### Question 6: "What's causing the CHI drop in Chicago?"
**Why it's good:**
- Tests alert/trend analysis
- Shows integration with alerts system
- Demonstrates proactive insights

**Expected Response:**
- References recent CHI changes in Chicago
- Mentions specific issues (from alerts or reviews)
- Provides root cause analysis
- Recommendations to address the drop

---

## 🔍 Category 3: Issue-Specific Deep Dives

### Question 7: "Show me customer feedback about coverage problems"
**Why it's good:**
- Tests coverage issue detection
- Shows retrieval of coverage-related reviews
- Demonstrates categorization

**Expected Response:**
- Customer reviews mentioning coverage/signal issues
- Specific regions affected
- Recommendations (e.g., "Check tower health", "Investigate dead zones")

---

### Question 8: "What are the main customer support issues?"
**Why it's good:**
- Tests customer_support issue type
- Shows sentiment analysis
- Demonstrates service quality insights

**Expected Response:**
- Reviews about customer support experiences
- Common complaints (wait times, agent quality, etc.)
- Recommendations for improving support

---

## 🎯 Category 4: Multi-Region Analysis

### Question 9: "Compare customer satisfaction between Dallas and Houston"
**Why it's good:**
- Tests comparative analysis
- Shows multi-region data retrieval
- Demonstrates GROQ reasoning

**Expected Response:**
- CHI scores for both regions
- Customer review sentiment comparison
- Key differences and recommendations

---

### Question 10: "What issues are customers reporting across all regions?"
**Why it's good:**
- Tests broad query capability
- Shows aggregation across regions
- Demonstrates pattern recognition

**Expected Response:**
- Summary of common issues across regions
- Most frequently mentioned problems
- Top recommendations for addressing systemic issues

---

## 💡 Category 5: Action-Oriented Questions

### Question 11: "What should we do about the roaming complaints?"
**Why it's good:**
- Tests recommendation generation
- Shows actionable insights
- Demonstrates engineering-focused answers

**Expected Response:**
- Summary of roaming issues
- Specific, actionable recommendations
- Technical steps (e.g., "Update roaming partner profiles", "Verify APN settings")

---

### Question 12: "Give me recommendations for improving CHI in regions with low scores"
**Why it's good:**
- Tests strategic thinking
- Shows data-driven recommendations
- Demonstrates business value

**Expected Response:**
- Identifies low-CHI regions
- Provides region-specific recommendations
- Actionable steps for improvement

---

## 🚀 Quick Demo Script (2-3 minutes)

**For a quick demo, use these 3 questions in order:**

1. **"What are customers saying about roaming issues?"**
   - Shows: Pinecone retrieval, customer quotes, recommendations

2. **"Which city has the highest CHI?"**
   - Shows: Operational intelligence, GROQ reasoning, data integration

3. **"What should we do about billing problems in San Antonio?"**
   - Shows: Region-specific analysis, actionable recommendations, end-to-end RAG

---

## 📝 Tips for Demo

1. **Start with a review-focused question** to show Pinecone integration
2. **Follow with an operational question** to show CHI integration
3. **End with an action-oriented question** to show business value

4. **Point out:**
   - Actual customer review quotes in the response
   - Specific recommendations (not generic)
   - Region/issue filtering working
   - GROQ generating intelligent summaries

5. **If something doesn't work:**
   - The fallback system will provide rule-based answers
   - This shows resilience and reliability

---

## 🎬 Expected Demo Flow

```
Judge: "Show me how the chatbot works"

You: "Let me ask about customer feedback on roaming issues"
→ Shows: Customer review quotes, specific recommendations

Judge: "Can it answer operational questions?"

You: "Yes, let me ask which city has the highest CHI"
→ Shows: Data-driven answer with reasoning

Judge: "What about actionable insights?"

You: "Let me ask what we should do about billing problems"
→ Shows: Specific recommendations with evidence
```

---

## ✅ Success Criteria

A good answer should have:
- ✅ Actual customer review quotes (from Pinecone)
- ✅ Specific recommendations (not generic)
- ✅ Data-driven insights (references CHI, regions, etc.)
- ✅ Actionable steps (engineers can act on it)

