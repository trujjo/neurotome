#!/bin/bash

# Start script for Artery Mapper
# This script starts the Flask API server

echo "🧬 Starting Artery Mapper..."

# Kill any existing Flask processes on port 5001
lsof -i :5001 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Wait a moment
sleep 1

# Start Flask API server in the background
echo "Starting Flask API server on port 5001..."
cd /Users/jonptrujillo/Documents/Github/neuronetwork
python3 app_new.py > /tmp/artery-mapper.log 2>&1 &
FLASK_PID=$!

echo "✅ Artery Mapper started (PID: $FLASK_PID)"
echo "📍 Open http://127.0.0.1:5001/ in your browser"
echo "📝 Logs: tail -f /tmp/artery-mapper.log"

# Save PID for reference
echo $FLASK_PID > /tmp/artery-mapper.pid

# Keep script running and monitor the process
wait $FLASK_PID
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup INT TERM

# Wait for both processes
wait
