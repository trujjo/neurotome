#!/bin/bash

# Start script for Neurotome project
# This script starts both the Flask API server and the Node.js web server

echo "🧠 Starting Neurotome servers..."

# Start Flask API server in the background
echo "Starting Flask API server on port 5000..."
python3 app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 2

# Start Node.js web server in the background
echo "Starting Node.js web server on port 3000..."
npm start &
NODE_PID=$!

echo ""
echo "🎉 Servers started successfully!"
echo "📊 Neo4j Database Explorer: http://localhost:5000/explorer"
echo "🌐 Main website: http://localhost:3000"
echo "🔗 Flask API available at: http://localhost:5000/api/*"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $NODE_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup INT TERM

# Wait for both processes
wait
