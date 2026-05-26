#!/bin/bash

# Sentrix Browser - Startup Script
# This script starts both the backend and frontend components

echo "🌐 Starting Sentrix Browser..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama is not running. Please start Ollama first."
    echo "   Run: ollama serve"
    echo ""
fi

# Check for execution token
if [ ! -f "$HOME/.sentrix/execution_token" ]; then
    echo "📝 Generating new execution token..."
    mkdir -p "$HOME/.sentrix"
    openssl rand -hex 32 > "$HOME/.sentrix/execution_token"
    chmod 600 "$HOME/.sentrix/execution_token"
    echo "✅ Token generated at: $HOME/.sentrix/execution_token"
fi

# Start backend in background
echo "🚀 Starting backend server..."
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if ! pip show fastapi > /dev/null 2>&1; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

if ! playwright install chromium 2>/dev/null; then
    echo "📦 Installing Playwright browsers..."
    playwright install chromium
fi

echo "🔧 Starting FastAPI backend on http://127.0.0.1:8765"
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check logs for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend started successfully (PID: $BACKEND_PID)"

# Start frontend
echo "🖥️  Starting frontend application..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    npm install
fi

echo "🌟 Launching Sentrix Browser UI..."
npm start

# Cleanup on exit
trap "echo 'Stopping backend...'; kill $BACKEND_PID 2>/dev/null" EXIT
