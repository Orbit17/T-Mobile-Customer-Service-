"""
Fallback rule-based chatbot when GROQ is unavailable.
"""
from typing import Dict, Any


def best_match(question: str) -> str:
    """
    Simple rule-based fallback responses.
    Returns a helpful answer based on keywords in the question.
    """
    question_lower = question.lower()
    
    # CHI-related queries
    if "chi" in question_lower or "happiness" in question_lower or "score" in question_lower:
        if "highest" in question_lower or "best" in question_lower:
            return "Based on current data, regions with the highest CHI scores are typically those experiencing fewer customer issues and better network performance. Check the Overview page for real-time CHI scores by region."
        elif "lowest" in question_lower or "worst" in question_lower:
            return "Regions with lower CHI scores may indicate network issues, customer service problems, or service outages. Check the Alerts page for detailed information about regions experiencing CHI drops."
        else:
            return "CHI (Customer Happiness Index) is calculated from sentiment analysis, network KPIs, and customer feedback. Higher scores (70+) indicate stable service, while lower scores (<50) may indicate issues requiring attention."
    
    # Roaming queries
    if "roaming" in question_lower or "roam" in question_lower:
        return "Roaming issues can include connectivity problems, unexpected charges, or failed text messages while traveling. Common recommendations include: checking roaming settings, contacting customer support for plan adjustments, and considering international data add-ons."
    
    # Billing queries
    if "billing" in question_lower or "bill" in question_lower or "charge" in question_lower:
        return "Billing issues may involve unexpected charges, plan discrepancies, or payment problems. Recommendations: review account online, contact customer service for clarification, and check for any promotional credits or adjustments."
    
    # Coverage queries
    if "coverage" in question_lower or "signal" in question_lower or "network" in question_lower:
        return "Network coverage issues can be caused by tower outages, congestion, or geographic limitations. Recommendations: check network status, report dead zones to customer service, and consider network optimization in affected areas."
    
    # Speed/data queries
    if "slow" in question_lower or "speed" in question_lower or "data" in question_lower:
        return "Slow data speeds can result from network congestion, throttling, or device issues. Recommendations: check data usage, verify network settings, contact support for speed tests, and consider plan upgrades if needed."
    
    # Support queries
    if "support" in question_lower or "service" in question_lower or "help" in question_lower:
        return "Customer support issues may involve wait times, agent quality, or resolution effectiveness. Recommendations: use multiple support channels (chat, phone, store), escalate to supervisors when needed, and provide feedback on support experience."
    
    # Default response
    return "I can help you with questions about T-Mobile services, including CHI scores, customer feedback, network issues, billing, and support. Please try rephrasing your question or check the dashboard for specific metrics."

