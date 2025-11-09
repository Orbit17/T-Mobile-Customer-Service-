#!/bin/bash
# Start the Streamlit frontend
# Run this from the project root directory

cd "$(dirname "$0")/frontend"

echo "Starting T-Mobile CHI Frontend..."
echo "Frontend will be available at http://localhost:8501"
echo ""

# Start Streamlit
streamlit run app.py

