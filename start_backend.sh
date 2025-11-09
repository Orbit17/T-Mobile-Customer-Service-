#!/bin/bash
# Start the backend API server
# Run this from the project root directory

cd "$(dirname "$0")"

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use!"
    echo "Killing existing process on port 8000..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
    echo "✅ Port 8000 freed"
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    # Use a more robust method to load .env file
    # First, clean up any spaces after = signs
    export $(grep -v '^#' .env | sed 's/ *= */=/' | xargs)
fi

# Ensure required environment variables are set
export PINECONE_INDEX="${PINECONE_INDEX:-t-mobile}"
export PINECONE_NAMESPACE="${PINECONE_NAMESPACE:-default}"

echo "Starting T-Mobile CHI Backend API..."
echo "PINECONE_INDEX: $PINECONE_INDEX"
echo "PINECONE_NAMESPACE: $PINECONE_NAMESPACE"
if [ -z "$PINECONE_API_KEY" ]; then
    echo "⚠️  WARNING: PINECONE_API_KEY is not set!"
    echo "   Set it in .env file or export it before running."
else
    echo "✅ PINECONE_API_KEY is set"
fi
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  WARNING: GROQ_API_KEY is not set!"
else
    echo "✅ GROQ_API_KEY is set"
fi
echo "Backend will be available at http://localhost:8000"
echo ""

# Run uvicorn from project root with correct module path
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
