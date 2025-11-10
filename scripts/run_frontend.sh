#!/bin/bash
# Script to run the Anny Body Fitter frontend

set -e

echo "🚀 Starting Anny Body Fitter Frontend..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! python -c "import gradio" 2>/dev/null; then
    echo "📥 Installing frontend dependencies..."
    pip install -e ".[frontend]"
fi

# Default settings
SERVER_NAME="${SERVER_NAME:-0.0.0.0}"
SERVER_PORT="${SERVER_PORT:-7860}"
SHARE="${SHARE:-false}"

echo "⚙️  Configuration:"
echo "   Server: $SERVER_NAME:$SERVER_PORT"
echo "   Share: $SHARE"
echo ""

# Run the application
python -m frontend.app \
    --server_name "$SERVER_NAME" \
    --server_port "$SERVER_PORT" \
    --share "$SHARE"
