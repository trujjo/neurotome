#!/bin/bash

# Quick restart script for Artery Mapper

echo "🔄 Restarting Artery Mapper..."

# Kill existing Flask process
if [ -f /tmp/artery-mapper.pid ]; then
    PID=$(cat /tmp/artery-mapper.pid)
    kill $PID 2>/dev/null || true
    rm /tmp/artery-mapper.pid
fi

# Also try killing by port
lsof -i :5001 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Wait a moment
sleep 1

# Start Flask
cd /Users/jonptrujillo/Documents/Github/neuronetwork
python3 app_new.py > /tmp/artery-mapper.log 2>&1 &
FLASK_PID=$!

echo $FLASK_PID > /tmp/artery-mapper.pid

echo "✅ Artery Mapper restarted (PID: $FLASK_PID)"
echo "📍 Open http://127.0.0.1:5001/ in your browser"
echo "📝 Logs: tail -f /tmp/artery-mapper.log"
