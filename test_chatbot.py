#!/usr/bin/env python3
"""
Test script to verify chatbot RAG retrieval from Pinecone.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables if not set
os.environ.setdefault("PINECONE_INDEX", "t-mobile")
os.environ.setdefault("PINECONE_NAMESPACE", "default")

from backend.database import init_db, SessionLocal
from backend.chatbot import answer_question

def test_queries():
    """Test chatbot with sample queries."""
    init_db()
    db = SessionLocal()
    
    test_questions = [
        "What are customers saying about roaming issues?",
        "Tell me about billing problems in San Antonio",
        "What issues are customers reporting in Chicago?",
        "How is customer satisfaction in Dallas?",
    ]
    
    print("=" * 60)
    print("Testing Chatbot RAG Retrieval")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}] Question: {question}")
        print("-" * 60)
        try:
            result = answer_question(db, question)
            print(f"Summary: {result.get('summary', 'N/A')}")
            actions = result.get('actions', [])
            if actions:
                print(f"Actions ({len(actions)}):")
                for a in actions[:3]:
                    print(f"  - {a}")
            evidence = result.get('drivers', {}).get('evidence', [])
            if evidence:
                print(f"Evidence found: {len(evidence)} items")
                if evidence and isinstance(evidence[0], str):
                    print(f"Sample: {evidence[0][:100]}...")
                elif evidence:
                    print(f"Sample: {str(evidence[0])[:100]}...")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    db.close()
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_queries()

