#!/bin/bash
# Start both backend and frontend
# This script opens two terminal windows (macOS)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start backend in new terminal
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_backend.sh\""

# Wait a bit for backend to start
sleep 3

# Start frontend in new terminal
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./start_frontend.sh\""

echo "✅ Started backend and frontend in separate terminal windows"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"

