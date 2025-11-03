#!/bin/bash
# Quick start script for Gradio Code Analysis App

set -e

WORKSPACE_DIR="/Users/zeihanaulia/Programming/research/agent"
VENV_DIR="$WORKSPACE_DIR/.venv"

echo "🚀 Starting Gradio Code Analysis App"
echo "====================================="
echo ""

# Check if .venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found at $VENV_DIR"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/upgrade requirements
echo "📚 Checking dependencies..."
pip install -q -r "$WORKSPACE_DIR/requirements.txt"

# Verify .env exists
if [ ! -f "$WORKSPACE_DIR/.env" ]; then
    echo "❌ .env file not found"
    echo "Please create .env with:"
    echo "  LITELLM_VIRTUAL_KEY=<your-key>"
    echo "  LITELLM_API=<api-base-url>"
    exit 1
fi

echo "✅ Environment ready"
echo ""
echo "🚀 Starting Gradio server..."
echo "📱 Open http://localhost:7860 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo "====================================="
echo ""

# Start the app
cd "$WORKSPACE_DIR"
python gradio/gradio_code_analysis_repo.py
