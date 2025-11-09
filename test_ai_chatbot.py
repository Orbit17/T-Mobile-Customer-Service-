#!/usr/bin/env python3
"""
Test script to check if the AI chatbot is using Groq AI for responses.

This script will:
1. Check if GROQ_API_KEY is configured
2. Make a test API call to the chatbot endpoint
3. Compare the response to determine if AI was used

Run this while your backend server is running on http://127.0.0.1:8000
"""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

def test_chatbot_ai():
    """Test if the chatbot is using AI"""
    
    print("=" * 60)
    print("AI Chatbot Test")
    print("=" * 60)
    
    # Check API key configuration
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key or groq_key == "your-groq-api-key-here" or groq_key.strip() == "":
        print("[X] GROQ_API_KEY not configured or is placeholder")
        print("    The chatbot will use retrieval-based fallback mode")
        api_key_configured = False
    else:
        masked_key = groq_key[:8] + "..." + groq_key[-4:] if len(groq_key) > 12 else "***"
        print(f"[OK] GROQ_API_KEY is configured: {masked_key}")
        api_key_configured = True
    
    print("\n" + "-" * 60)
    print("Testing chatbot endpoint...")
    print("-" * 60)
    
    # Test question
    test_question = "What regions have the lowest CHI scores and why?"
    api_url = "http://127.0.0.1:8000/qa"
    
    try:
        response = requests.post(
            api_url,
            json={"question": test_question},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\nQuestion: {test_question}")
        print(f"\nResponse Summary:")
        print(f"  {result.get('summary', 'N/A')}")
        
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\nRecommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Analyze if AI was likely used
        print("\n" + "-" * 60)
        print("Analysis:")
        print("-" * 60)
        
        summary = result.get('summary', '')
        has_error = 'error' in result.get('drivers', {})
        
        # Indicators of AI usage:
        # 1. More detailed, contextual responses (not just "Top regions: ...")
        # 2. Recommendations are specific and contextual (not generic)
        # 3. No error messages about Groq API
        
        is_ai_likely = False
        indicators = []
        
        if api_key_configured and not has_error:
            # Check if summary is more than just "Top regions: ..."
            if summary and not summary.startswith("Top regions:"):
                is_ai_likely = True
                indicators.append("Summary is detailed and contextual (not just region list)")
            
            # Check if recommendations are specific
            if recommendations:
                generic_recs = [
                    "Check tower health and restart impacted cells",
                    "Notify customers in affected regions",
                    "Open incident and assign on-call engineer"
                ]
                if not all(rec in generic_recs for rec in recommendations):
                    is_ai_likely = True
                    indicators.append("Recommendations are specific and contextual")
            
            if not has_error:
                indicators.append("No API errors detected")
        else:
            if not api_key_configured:
                indicators.append("API key not configured - using fallback mode")
            if has_error:
                error_msg = result.get('drivers', {}).get('error', 'Unknown error')
                indicators.append(f"API error detected: {error_msg}")
        
        if is_ai_likely:
            print("[LIKELY AI] The response appears to be AI-generated")
            print("\nIndicators:")
            for indicator in indicators:
                print(f"  + {indicator}")
        else:
            print("[FALLBACK MODE] The response appears to be retrieval-based")
            print("\nReasons:")
            for indicator in indicators:
                print(f"  - {indicator}")
        
        # Show full response for debugging
        print("\n" + "-" * 60)
        print("Full Response (for debugging):")
        print("-" * 60)
        print(json.dumps(result, indent=2))
        
    except requests.exceptions.ConnectionError:
        print("\n[X] ERROR: Could not connect to backend server")
        print("    Make sure the backend is running on http://127.0.0.1:8000")
        print("    Start it with: uvicorn backend.main:app --reload --port 8000")
    except requests.exceptions.Timeout:
        print("\n[X] ERROR: Request timed out")
        print("    The chatbot might be taking too long to respond")
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_chatbot_ai()

